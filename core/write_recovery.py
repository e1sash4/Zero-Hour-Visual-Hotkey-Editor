from __future__ import annotations

import ctypes
import errno
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .command_map import CommandMapFile
from .csf_parser import CsfFile


INSTALL_ARGUMENT = "--install-config"


def is_access_error(error: BaseException) -> bool:
    """Recognize Windows and POSIX write-access failures through exception chains."""
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current, PermissionError):
            return True
        if isinstance(current, OSError) and (
                current.errno in {errno.EACCES, errno.EPERM} or getattr(current, "winerror", None) == 5):
            return True
        current = current.__cause__ or current.__context__
    return False


def is_running_as_admin() -> bool:
    if os.name != "nt":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def create_recovery_package(
        app_root: Path, game_dir: Path, files: dict[str, bytes]) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    folder = app_root / "manual-configs" / stamp
    folder.mkdir(parents=True)
    entries = []
    for filename, data in files.items():
        if filename not in {"generals.csf", "CommandMap.ini"}:
            raise ValueError(f"Unsupported recovery file: {filename}")
        _validate(filename, data)
        (folder / filename).write_bytes(data)
        entries.append({"source": filename, "target": f"Data/English/{filename}"})
    manifest = {"game_dir": str(game_dir.resolve()), "files": entries}
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    return folder


def install_recovery_package(folder: str | Path) -> tuple[Path, list[Path]]:
    folder = Path(folder).resolve()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    game_dir = Path(manifest["game_dir"])
    installed = []
    for entry in manifest["files"]:
        filename = entry["source"]
        if filename not in {"generals.csf", "CommandMap.ini"}:
            raise ValueError(f"Unsupported recovery file: {filename}")
        source = (folder / filename).resolve()
        if source.parent != folder:
            raise ValueError("Recovery source escaped its package directory")
        expected_target = Path("Data/English") / filename
        if Path(entry["target"]) != expected_target:
            raise ValueError("Unexpected recovery target")
        target = game_dir / expected_target
        data = source.read_bytes()
        _validate(filename, data)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".tmp")
        with temp.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, target)
        installed.append(target)
    return game_dir, installed


def manual_copy_instructions(folder: str | Path) -> str:
    folder = Path(folder).resolve()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    game_dir = Path(manifest["game_dir"])
    return "\n".join(
        f"{folder / entry['source']}  →  {game_dir / Path(entry['target'])}"
        for entry in manifest["files"]
    )


def restart_as_admin(folder: str | Path) -> bool:
    if os.name != "nt":
        return False
    folder = str(Path(folder).resolve())
    if getattr(sys, "frozen", False):
        executable = sys.executable
        arguments = [INSTALL_ARGUMENT, folder]
    else:
        executable = sys.executable
        arguments = [str(Path(sys.argv[0]).resolve()), INSTALL_ARGUMENT, folder]
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, subprocess.list2cmdline(arguments), None, 1,
    )
    return result > 32


def take_install_argument(arguments: list[str]) -> tuple[Path | None, list[str]]:
    remaining = list(arguments)
    if INSTALL_ARGUMENT not in remaining:
        return None, remaining
    index = remaining.index(INSTALL_ARGUMENT)
    if index + 1 >= len(remaining):
        raise ValueError(f"{INSTALL_ARGUMENT} requires a package path")
    folder = Path(remaining[index + 1])
    del remaining[index:index + 2]
    return folder, remaining


def _validate(filename: str, data: bytes) -> None:
    if filename == "generals.csf":
        CsfFile.from_bytes(data)
    elif filename == "CommandMap.ini":
        CommandMapFile.parse(data.decode("utf-8-sig", errors="strict"))
