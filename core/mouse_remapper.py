from __future__ import annotations

import ctypes
import logging
import os
import threading
from ctypes import wintypes
from pathlib import Path


KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
INPUT_KEYBOARD = 1
MAPVK_VK_TO_VSC = 0


class _MouseInput(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class _KeyboardInput(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    )


class _HardwareInput(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class _InputValue(ctypes.Union):
    _fields_ = (("mi", _MouseInput), ("ki", _KeyboardInput), ("hi", _HardwareInput))


class _Input(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = (("type", wintypes.DWORD), ("value", _InputValue))


class MouseRemapper:
    """Translate standard Windows mouse buttons to keys while Zero Hour is active."""

    def __init__(self, game_dir: str | Path):
        self.game_dir = Path(game_dir).resolve()
        self.mapping: dict[str, str] = {}
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._hook = None
        self._callback = None
        self._ready = threading.Event()
        self._last_foreground_state: bool | None = None

    def update(self, mapping: dict[str, str], enabled: bool = True) -> None:
        self.mapping = dict(mapping) if enabled else {}
        self._last_foreground_state = None
        logging.getLogger(__name__).info("Mouse remapping updated: %s", self.mapping or "disabled")
        if self.mapping and not self._thread:
            self._ready.clear()
            self._thread = threading.Thread(target=self._run, name="ZeroHourMouseRemapper", daemon=True)
            self._thread.start()
            self._ready.wait(timeout=1.0)
        elif not self.mapping:
            self.stop()

    def stop(self) -> None:
        thread = self._thread
        if thread and not self._thread_id:
            self._ready.wait(timeout=1.0)
        if self._thread_id and os.name == "nt":
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT
        if thread and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self._thread = None
        self._thread_id = 0

    def _game_is_foreground(self) -> bool:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = (
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
        )
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return False

        # GeneralsOnline can start the game through a protected/wrapped process,
        # so its executable path is not guaranteed to be the configured Steam
        # directory.  The SAGE engine keeps its distinctive window class in both
        # launch modes, which is also the fallback we already use when Windows
        # denies process-path access because of a higher integrity level.
        class_name = ctypes.create_unicode_buffer(64)
        if user32.GetClassNameW(hwnd, class_name, len(class_name)) \
                and class_name.value == "Game Window":
            return True

        process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        process = kernel32.OpenProcess(0x1000, False, process_id.value)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not process:
            return False
        try:
            size = ctypes.c_ulong(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(process, 0, buffer, ctypes.byref(size)):
                return False
            executable = Path(buffer.value).resolve()
            return executable.parent == self.game_dir and executable.name.casefold() in {"generals.exe", "game.dat"}
        finally:
            kernel32.CloseHandle(process)

    @staticmethod
    def _button_for_message(message: int, mouse_data: int) -> str | None:
        if message in (0x0207, 0x0208):  # WM_MBUTTONDOWN / WM_MBUTTONUP
            return "M3"
        if message in (0x020B, 0x020C):  # WM_XBUTTONDOWN / WM_XBUTTONUP
            return "M4" if (mouse_data >> 16) & 0xFFFF == 1 else "M5"
        return None

    @staticmethod
    def _send_key(user32, key: str, is_up: bool) -> bool:
        """Inject a hardware-style scan code that legacy DirectInput can observe."""
        virtual_key = ord(key)
        scan_code = user32.MapVirtualKeyW(virtual_key, MAPVK_VK_TO_VSC)
        if not scan_code:
            return False
        event = _Input(
            type=INPUT_KEYBOARD,
            ki=_KeyboardInput(
                wVk=0,
                wScan=scan_code,
                dwFlags=KEYEVENTF_SCANCODE | (KEYEVENTF_KEYUP if is_up else 0),
                time=0,
                dwExtraInfo=0,
            ),
        )
        return user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(_Input)) == 1

    def _run(self) -> None:
        if os.name != "nt":
            self._ready.set()
            return
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()

        class Point(ctypes.Structure):
            _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))

        class MouseHookStruct(ctypes.Structure):
            _fields_ = (
                ("pt", Point), ("mouseData", ctypes.c_ulong), ("flags", ctypes.c_ulong),
                ("time", ctypes.c_ulong), ("dwExtraInfo", ctypes.c_void_p),
            )

        callback_type = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int, ctypes.c_size_t, ctypes.c_void_p)
        user32.SetWindowsHookExW.argtypes = (ctypes.c_int, callback_type, wintypes.HINSTANCE, wintypes.DWORD)
        user32.SetWindowsHookExW.restype = wintypes.HANDLE
        user32.CallNextHookEx.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_size_t, ctypes.c_void_p)
        user32.CallNextHookEx.restype = ctypes.c_ssize_t
        user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
        user32.MapVirtualKeyW.restype = wintypes.UINT
        user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int)
        user32.SendInput.restype = wintypes.UINT

        injection_error_logged = False
        injection_success_logged = False

        def callback(code, message, data):
            nonlocal injection_error_logged, injection_success_logged
            if code >= 0:
                event = ctypes.cast(data, ctypes.POINTER(MouseHookStruct)).contents
                button = self._button_for_message(message, event.mouseData)
                key = self.mapping.get(button or "")
                game_is_foreground = self._game_is_foreground() if key else False
                if key and game_is_foreground != self._last_foreground_state:
                    logging.getLogger(__name__).info(
                        "Mouse button %s observed; Zero Hour foreground: %s", button, game_is_foreground
                    )
                    self._last_foreground_state = game_is_foreground
                if key and game_is_foreground:
                    is_up = message in (0x0208, 0x020C)
                    if self._send_key(user32, key, is_up):
                        if not injection_success_logged:
                            logging.getLogger(__name__).info(
                                "Mouse proxy input sent successfully: %s -> %s", button, key
                            )
                            injection_success_logged = True
                        return 1
                    if not injection_error_logged:
                        logging.getLogger(__name__).error(
                            "Could not inject mouse proxy key %s. If Zero Hour is elevated, "
                            "run the editor with the same administrator privileges.", key,
                        )
                        injection_error_logged = True
            return user32.CallNextHookEx(self._hook, code, message, data)

        self._callback = callback_type(callback)
        self._hook = user32.SetWindowsHookExW(14, self._callback, None, 0)  # WH_MOUSE_LL
        if not self._hook:
            logging.getLogger(__name__).error("Could not install Windows mouse hook")
            self._thread = None
            self._thread_id = 0
            self._ready.set()
            return
        logging.getLogger(__name__).info("Windows mouse hook installed")
        self._ready.set()
        try:
            message = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
        finally:
            user32.UnhookWindowsHookEx(self._hook)
            self._hook = None
            self._callback = None
            self._thread = None
            self._thread_id = 0
