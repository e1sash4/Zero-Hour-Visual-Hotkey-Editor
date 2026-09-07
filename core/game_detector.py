from __future__ import annotations

import os
import re
import winreg
from collections.abc import Iterable
from pathlib import Path


GAME_DIRECTORY_NAMES = (
    "Command & Conquer Generals - Zero Hour",
    "Command and Conquer Generals - Zero Hour",
    "Command and Conquer Generals Zero Hour",
    "Command & Conquer Generals Zero Hour",
    "C&C Generals Zero Hour",
)


def is_game_directory(path: Path) -> bool:
    return path.is_dir() and (path / "INIZH.big").is_file() and (path / "TexturesZH.big").is_file()


def _registry_value(hive: int, key_name: str, value_name: str) -> str | None:
    try:
        with winreg.OpenKey(hive, key_name) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return str(value).strip().strip('"') or None
    except OSError:
        return None


def _registry_candidates() -> list[Path]:
    candidates: list[Path] = []
    game_keys = (
        r"SOFTWARE\WOW6432Node\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour",
        r"SOFTWARE\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour",
        r"SOFTWARE\WOW6432Node\EA Games\Command and Conquer Generals Zero Hour",
        r"SOFTWARE\EA Games\Command and Conquer Generals Zero Hour",
    )
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for key_name in game_keys:
            for value_name in ("InstallPath", "Install Dir", "InstallLocation"):
                if value := _registry_value(hive, key_name, value_name):
                    candidates.append(Path(value))
    candidates.extend(_uninstall_registry_candidates())
    return candidates


def _uninstall_registry_candidates() -> list[Path]:
    """Find EA/retail installs registered in Windows at arbitrary paths."""
    candidates: list[Path] = []
    uninstall_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    views = (winreg.KEY_READ | winreg.KEY_WOW64_32KEY, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for access in views:
            try:
                root = winreg.OpenKey(hive, uninstall_key, 0, access)
            except OSError:
                continue
            with root:
                index = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(root, index)
                    except OSError:
                        break
                    index += 1
                    try:
                        with winreg.OpenKey(root, subkey_name) as subkey:
                            display_name = str(winreg.QueryValueEx(subkey, "DisplayName")[0]).casefold()
                            if "generals" not in display_name or "zero hour" not in display_name:
                                continue
                            location = str(winreg.QueryValueEx(subkey, "InstallLocation")[0]).strip().strip('"')
                            if location:
                                candidates.append(Path(location))
                    except OSError:
                        continue
    return candidates


def _steam_roots() -> list[Path]:
    roots: list[Path] = []
    registry_values = (
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamPath"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam", "SteamExe"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
    )
    for hive, key_name, value_name in registry_values:
        if value := _registry_value(hive, key_name, value_name):
            path = Path(value)
            roots.append(path.parent if path.suffix.casefold() == ".exe" else path)
    roots.append(Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "Steam")
    return roots


def _steam_library_paths(steam_root: Path) -> list[Path]:
    """Read Steam's configured libraries from libraryfolders.vdf."""
    libraries = [steam_root]
    vdf = steam_root / "steamapps/libraryfolders.vdf"
    try:
        text = vdf.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return libraries
    for match in re.finditer(r'"path"\s*"((?:\\.|[^"\\])*)"', text, re.IGNORECASE):
        value = match.group(1).replace("\\\\", "\\")
        if value:
            libraries.append(Path(value))
    return libraries


def _children(path: Path) -> Iterable[Path]:
    try:
        yield from (item for item in path.iterdir() if item.is_dir())
    except OSError:
        return


def _steam_candidates() -> list[Path]:
    candidates: list[Path] = []
    for steam_root in _steam_roots():
        for library in _steam_library_paths(steam_root):
            common = library / "steamapps/common"
            candidates.extend(common / name for name in GAME_DIRECTORY_NAMES)
            # Steam package names can vary. The archive signature below is
            # authoritative, so also inspect each immediate common child.
            candidates.extend(_children(common))
    return candidates


def _non_steam_candidates() -> list[Path]:
    candidates: list[Path] = []
    program_files = Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))
    program_files_x86 = Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))
    for base in (program_files / "EA Games", program_files_x86 / "EA Games"):
        candidates.extend(base / name for name in GAME_DIRECTORY_NAMES)
        candidates.extend(_children(base))

    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        drive = Path(f"{letter}:/")
        for folder in ("Games", "EA Games", "Electronic Arts", "Origin Games"):
            base = drive / folder
            candidates.extend(base / name for name in GAME_DIRECTORY_NAMES)
            candidates.extend(_children(base))
        candidates.extend(drive / name for name in GAME_DIRECTORY_NAMES)
    return candidates


def detect_game(explicit: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if env := os.environ.get("ZERO_HOUR_PATH"):
        candidates.append(Path(env))
    candidates.extend(_registry_candidates())
    candidates.extend(_steam_candidates())
    candidates.extend(_non_steam_candidates())

    seen: set[str] = set()
    for candidate in candidates:
        normalized = os.path.normcase(os.path.abspath(candidate))
        if normalized in seen:
            continue
        seen.add(normalized)
        if is_game_directory(candidate):
            return candidate.resolve()
    return None
