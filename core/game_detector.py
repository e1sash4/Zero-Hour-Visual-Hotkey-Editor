from __future__ import annotations

import os
import winreg
from pathlib import Path


KNOWN_RELATIVE = (
    Path("steamapps/common/Command & Conquer Generals - Zero Hour"),
    Path("steamapps/common/Command and Conquer Generals - Zero Hour"),
)


def is_game_directory(path: Path) -> bool:
    return path.is_dir() and (path / "INIZH.big").is_file() and (path / "TexturesZH.big").is_file()


def _registry_candidates() -> list[Path]:
    candidates: list[Path] = []
    keys = (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Electronic Arts\EA Games\Command and Conquer Generals Zero Hour"),
    )
    for hive, key_name in keys:
        try:
            with winreg.OpenKey(hive, key_name) as key:
                value, _ = winreg.QueryValueEx(key, "InstallPath")
                candidates.append(Path(value))
        except OSError:
            pass
    return candidates


def detect_game(explicit: str | Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if env := os.environ.get("ZERO_HOUR_PATH"):
        candidates.append(Path(env))
    candidates.extend(_registry_candidates())
    for drive in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        root = Path(f"{drive}:/")
        candidates.extend(root / rel for rel in KNOWN_RELATIVE)
        candidates.extend(root / "SteamLibrary" / rel for rel in KNOWN_RELATIVE)
    candidates.extend([
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")) / "EA Games/Command and Conquer Generals Zero Hour",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "EA Games/Command and Conquer Generals Zero Hour",
    ])
    seen: set[str] = set()
    for candidate in candidates:
        normalized = str(candidate.resolve(strict=False)).casefold()
        if normalized not in seen and is_game_directory(candidate):
            return candidate.resolve()
        seen.add(normalized)
    return None
