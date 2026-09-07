from __future__ import annotations

from pathlib import Path

from .big_reader import BigArchive, BigEntry, normalize_member


class ArchiveIndex:
    """Case-insensitive game resource overlay. Loose files beat later BIG files."""

    def __init__(self, game_dir: str | Path, archives: list[str] | None = None):
        self.game_dir = Path(game_dir)
        names = archives or [
            "PatchINI.big", "PatchZH.big", "INIZH.big", "EnglishZH.big", "TexturesZH.big", "WindowZH.big",
            # Steam's combined installation keeps the base Generals assets in
            # this subdirectory. Zero Hour still references several control-bar
            # textures from these archives.
            "ZH_Generals/Patch.big", "ZH_Generals/INI.big", "ZH_Generals/English.big",
            "ZH_Generals/Textures.big", "ZH_Generals/Window.big",
        ]
        self.archives: list[BigArchive] = []
        self.members: dict[str, tuple[BigArchive, BigEntry]] = {}
        for name in names:
            path = self.game_dir / name
            if not path.is_file():
                continue
            archive = BigArchive(path)
            self.archives.append(archive)
            # Earlier archives have overlay priority.
            for entry in archive.entries:
                self.members.setdefault(normalize_member(entry.name), (archive, entry))

    def find_basename(self, name: str) -> tuple[BigArchive, BigEntry] | None:
        needle = Path(name.replace("\\", "/")).name.casefold()
        for archive, entry in self.members.values():
            if Path(entry.name.replace("\\", "/")).name.casefold() == needle:
                return archive, entry
        return None

    def read(self, name: str) -> bytes:
        loose = self.game_dir / name.replace("/", "\\")
        if loose.is_file():
            return loose.read_bytes()
        item = self.members.get(normalize_member(name)) or self.find_basename(name)
        if not item:
            raise KeyError(name)
        return item[0].read(item[1])

    def source(self, name: str) -> str | None:
        item = self.members.get(normalize_member(name)) or self.find_basename(name)
        return item[0].path.name if item else None
