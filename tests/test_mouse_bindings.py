from core.mouse_bindings import MouseBindingStore
import ctypes

from core.mouse_remapper import KEYEVENTF_KEYUP, KEYEVENTF_SCANCODE, MouseRemapper, _Input


def test_mouse_binding_store_round_trip(tmp_path):
    store = MouseBindingStore(tmp_path / "mouse-bindings.json")
    store.save({"CONTROLBAR:Humvee": "M4", "invalid": "M9"}, {"M3": "7", "M4": "8", "M5": "9"})

    assert store.load() == {"controlbar:humvee": "M4"}
    assert store.load_proxies() == {"M3": "7", "M4": "8", "M5": "9"}


def test_windows_mouse_messages_map_to_supported_buttons():
    assert MouseRemapper._button_for_message(0x0207, 0) == "M3"
    assert MouseRemapper._button_for_message(0x020B, 1 << 16) == "M4"
    assert MouseRemapper._button_for_message(0x020B, 2 << 16) == "M5"
    assert MouseRemapper._button_for_message(0x0201, 0) is None


def test_mouse_proxy_uses_scan_code_send_input():
    class FakeUser32:
        def MapVirtualKeyW(self, virtual_key, _mode):
            assert virtual_key == ord("I")
            return 0x17

        def SendInput(self, count, pointer, size):
            self.event = ctypes.cast(pointer, ctypes.POINTER(_Input)).contents
            self.call = count, size
            return 1

    user32 = FakeUser32()
    assert MouseRemapper._send_key(user32, "I", True)
    assert user32.call == (1, ctypes.sizeof(_Input))
    assert user32.event.ki.wVk == 0
    assert user32.event.ki.wScan == 0x17
    assert user32.event.ki.dwFlags == KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
