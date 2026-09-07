from __future__ import annotations

import os
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resource_path(relative: str | Path) -> Path:
    """Resolve a bundled read-only resource in development and PyInstaller."""
    base = Path(getattr(sys, "_MEIPASS", project_root()))
    return base / relative


def data_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "ZeroHourHotkeyEditor"
    return project_root()
