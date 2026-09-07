import struct

import pytest

from core.big_reader import BigArchive, BigFormatError
from core.archive_index import ArchiveIndex


def make_big(path, files: dict[str, bytes]):
    index_size = 16 + sum(8 + len(name.encode("latin-1")) + 1 for name in files)
    offset = index_size
    records = []
    payloads = []
    for name, payload in files.items():
        records.append(struct.pack(">II", offset, len(payload)) + name.encode("latin-1") + b"\0")
        payloads.append(payload)
        offset += len(payload)
    path.write_bytes(b"BIGF" + struct.pack("<I", offset) + struct.pack(">II", len(files), index_size) + b"".join(records + payloads))


def test_big_enumerate_search_and_extract(tmp_path):
    path = tmp_path / "tiny.big"
    make_big(path, {r"Data\INI\One.ini": b"hello", r"Art\Textures\X.tga": b"pixels"})
    archive = BigArchive(path)
    assert archive.names() == [r"Data\INI\One.ini", r"Art\Textures\X.tga"]
    assert archive.read("data/ini/one.ini") == b"hello"
    assert archive.search("textures")[0].name.endswith("X.tga")


def test_big_rejects_out_of_bounds_entry(tmp_path):
    path = tmp_path / "bad.big"
    path.write_bytes(b"BIGF" + struct.pack("<I", 30) + struct.pack(">II", 1, 26) + struct.pack(">II", 999, 4) + b"x\0")
    with pytest.raises(BigFormatError):
        BigArchive(path)


def test_archive_index_can_bypass_loose_override(tmp_path):
    archived = b"archive default"
    make_big(tmp_path / "EnglishZH.big", {r"Data\English\generals.csf": archived})
    loose = tmp_path / "Data/English/generals.csf"
    loose.parent.mkdir(parents=True)
    loose.write_bytes(b"user override")

    index = ArchiveIndex(tmp_path, archives=["EnglishZH.big"])

    assert index.read(r"Data\English\generals.csf") == b"user override"
    assert index.read_archive(r"Data\English\generals.csf") == archived
