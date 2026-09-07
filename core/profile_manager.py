from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Profile:
    name: str
    bindings: dict[str, str | None]
    read_only: bool = False


class ProfileManager:
    VERSION = 1

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()
        if not safe:
            raise ValueError("Profile name is empty")
        return safe

    def save(self, profile: Profile) -> Path:
        path = self.directory / f"{self._safe_name(profile.name)}.json"
        payload = {"version": self.VERSION, "name": profile.name, "read_only": profile.read_only, "bindings": profile.bindings}
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)
        return path

    def load(self, path: str | Path) -> Profile:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if payload.get("version") != self.VERSION or not isinstance(payload.get("bindings"), dict):
            raise ValueError("Unsupported or invalid profile")
        bindings = {str(k): (None if v is None else str(v).upper()) for k, v in payload["bindings"].items()}
        return Profile(str(payload.get("name") or Path(path).stem), bindings, bool(payload.get("read_only", False)))

    def list(self) -> list[Path]:
        return sorted(self.directory.glob("*.json"))

    def delete(self, path: str | Path) -> None:
        profile = self.load(path)
        if profile.read_only:
            raise PermissionError("This profile is read-only")
        Path(path).unlink()

    def duplicate(self, path: str | Path, new_name: str) -> Path:
        profile = self.load(path)
        return self.save(Profile(new_name, dict(profile.bindings), False))

    def rename(self, path: str | Path, new_name: str) -> Path:
        profile = self.load(path)
        if profile.read_only:
            raise PermissionError("This profile is read-only")
        new_path = self.save(Profile(new_name, profile.bindings, False))
        if Path(path).resolve() != new_path.resolve():
            Path(path).unlink()
        return new_path

