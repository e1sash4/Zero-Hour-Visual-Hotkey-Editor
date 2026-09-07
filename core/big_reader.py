from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class BigFormatError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BigEntry:
    name: str
    offset: int
    size: int


def normalize_member(name: str) -> str:
    return str(PurePosixPath(name.replace("\\", "/"))).casefold()


class BigArchive:
    """Validated, dependency-free, read-only EA BIG4/BIGF reader."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.magic = b""
        self.entries: list[BigEntry] = []
        self._lookup: dict[str, BigEntry] = {}
        self._read_index()

    def _read_index(self) -> None:
        actual_size = self.path.stat().st_size
        with self.path.open("rb") as stream:
            header = stream.read(16)
            if len(header) != 16:
                raise BigFormatError("Truncated BIG header")
            self.magic = header[:4]
            if self.magic not in (b"BIGF", b"BIG4"):
                raise BigFormatError(f"Unsupported BIG signature: {self.magic!r}")
            declared_le = struct.unpack_from("<I", header, 4)[0]
            declared_be = struct.unpack_from(">I", header, 4)[0]
            count, index_end = struct.unpack_from(">II", header, 8)
            if count > 2_000_000:
                raise BigFormatError("Implausible BIG entry count")
            if index_end < 16 or index_end > actual_size:
                raise BigFormatError("Invalid BIG index boundary")
            if actual_size not in (declared_le, declared_be) and max(declared_le, declared_be) != 0:
                # Some official archives carry a stale size; offsets remain authoritative.
                pass
            for _ in range(count):
                fixed = stream.read(8)
                if len(fixed) != 8:
                    raise BigFormatError("Truncated BIG entry")
                offset, size = struct.unpack(">II", fixed)
                name_bytes = bytearray()
                while True:
                    char = stream.read(1)
                    if not char:
                        raise BigFormatError("Unterminated BIG filename")
                    if char == b"\0":
                        break
                    name_bytes.extend(char)
                    if len(name_bytes) > 4096:
                        raise BigFormatError("BIG filename is too long")
                if offset + size > actual_size:
                    raise BigFormatError("BIG entry points beyond archive")
                name = name_bytes.decode("latin-1")
                entry = BigEntry(name, offset, size)
                self.entries.append(entry)
                self._lookup[normalize_member(name)] = entry
            if stream.tell() > index_end:
                raise BigFormatError("BIG index exceeds declared boundary")

    def names(self) -> list[str]:
        return [entry.name for entry in self.entries]

    def find(self, name: str) -> BigEntry | None:
        return self._lookup.get(normalize_member(name))

    def search(self, text: str) -> list[BigEntry]:
        needle = normalize_member(text)
        return [entry for entry in self.entries if needle in normalize_member(entry.name)]

    def read(self, member: str | BigEntry) -> bytes:
        entry = member if isinstance(member, BigEntry) else self.find(member)
        if entry is None:
            raise KeyError(member)
        with self.path.open("rb") as stream:
            stream.seek(entry.offset)
            data = stream.read(entry.size)
        if len(data) != entry.size:
            raise BigFormatError(f"Truncated payload: {entry.name}")
        return data

