from __future__ import annotations

import os
import shutil
from datetime import datetime
from pathlib import Path

from .csf_parser import CsfFile


class BackupManager:
    def __init__(self, directory: str | Path, filename: str = "generals.csf", validator=None):
        self.directory = Path(directory)
        self.filename = filename
        self.validator = validator or CsfFile.from_bytes
        self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, target: str | Path, fallback_data: bytes | None = None) -> Path:
        target = Path(target)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
        folder = self.directory / stamp
        folder.mkdir(parents=True)
        backup = folder / self.filename
        if target.is_file():
            shutil.copy2(target, backup)
        elif fallback_data is not None:
            backup.write_bytes(fallback_data)
        else:
            raise FileNotFoundError(target)
        self.validator(backup.read_bytes())
        return backup

    def atomic_write(self, target: str | Path, data: bytes) -> None:
        target = Path(target)
        self.validator(data)
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_name(target.name + ".tmp")
        with temp.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        self.validator(temp.read_bytes())
        os.replace(temp, target)

    def latest(self) -> Path | None:
        backups = sorted(self.directory.glob(f"*/{self.filename}"), reverse=True)
        return backups[0] if backups else None

    def restore(self, backup: str | Path, target: str | Path) -> None:
        data = Path(backup).read_bytes()
        self.atomic_write(target, data)
