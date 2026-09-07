from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path


class CsfFormatError(ValueError):
    pass


FILE_MAGIC = b" FSC"
LABEL_MAGIC = b" LBL"
STRING_MAGIC = b" RTS"
STRING_EXTRA_MAGIC = b"WRTS"


def _read_exact(stream: io.BytesIO, size: int) -> bytes:
    data = stream.read(size)
    if len(data) != size:
        raise CsfFormatError("Unexpected end of CSF")
    return data


def _u32(stream: io.BytesIO) -> int:
    return struct.unpack("<I", _read_exact(stream, 4))[0]


def _decode_value(raw: bytes) -> str:
    return bytes((~byte) & 0xFF for byte in raw).decode("utf-16-le", errors="strict")


def _encode_value(value: str) -> bytes:
    return bytes((~byte) & 0xFF for byte in value.encode("utf-16-le"))


@dataclass(slots=True)
class CsfValue:
    text: str
    extra: bytes | None = None


@dataclass(slots=True)
class CsfLabel:
    name: str
    values: list[CsfValue] = field(default_factory=list)


@dataclass(slots=True)
class CsfFile:
    version: int = 3
    language: int = 0
    reserved: int = 0
    labels: list[CsfLabel] = field(default_factory=list)
    _name_index: dict[str, CsfLabel] | None = field(default=None, init=False, repr=False)

    @classmethod
    def from_bytes(cls, data: bytes) -> "CsfFile":
        stream = io.BytesIO(data)
        if _read_exact(stream, 4) != FILE_MAGIC:
            raise CsfFormatError("Invalid CSF signature")
        version, label_count, string_count, reserved, language = struct.unpack("<5I", _read_exact(stream, 20))
        if label_count > 5_000_000 or string_count > 10_000_000:
            raise CsfFormatError("Implausible CSF counts")
        labels: list[CsfLabel] = []
        observed_strings = 0
        for _ in range(label_count):
            if _read_exact(stream, 4) != LABEL_MAGIC:
                raise CsfFormatError("Invalid CSF label marker")
            value_count, name_length = struct.unpack("<II", _read_exact(stream, 8))
            if name_length > 1_000_000 or value_count > 100_000:
                raise CsfFormatError("Implausible CSF label size")
            name = _read_exact(stream, name_length).decode("latin-1")
            values: list[CsfValue] = []
            for _ in range(value_count):
                marker = _read_exact(stream, 4)
                if marker not in (STRING_MAGIC, STRING_EXTRA_MAGIC):
                    raise CsfFormatError(f"Invalid CSF string marker {marker!r}")
                char_count = _u32(stream)
                text = _decode_value(_read_exact(stream, char_count * 2))
                extra = None
                if marker == STRING_EXTRA_MAGIC:
                    extra_length = _u32(stream)
                    extra = _read_exact(stream, extra_length)
                values.append(CsfValue(text, extra))
                observed_strings += 1
            labels.append(CsfLabel(name, values))
        if observed_strings != string_count:
            raise CsfFormatError(f"CSF string count mismatch: expected {string_count}, got {observed_strings}")
        if stream.read(1):
            raise CsfFormatError("Trailing data after CSF labels")
        return cls(version, language, reserved, labels)

    @classmethod
    def read(cls, path: str | Path) -> "CsfFile":
        return cls.from_bytes(Path(path).read_bytes())

    def to_bytes(self) -> bytes:
        output = io.BytesIO()
        string_count = sum(len(label.values) for label in self.labels)
        output.write(FILE_MAGIC)
        output.write(struct.pack("<5I", self.version, len(self.labels), string_count, self.reserved, self.language))
        for label in self.labels:
            encoded_name = label.name.encode("latin-1")
            output.write(LABEL_MAGIC)
            output.write(struct.pack("<II", len(label.values), len(encoded_name)))
            output.write(encoded_name)
            for value in label.values:
                output.write(STRING_EXTRA_MAGIC if value.extra is not None else STRING_MAGIC)
                encoded = _encode_value(value.text)
                output.write(struct.pack("<I", len(encoded) // 2))
                output.write(encoded)
                if value.extra is not None:
                    output.write(struct.pack("<I", len(value.extra)))
                    output.write(value.extra)
        return output.getvalue()

    def by_name(self) -> dict[str, CsfLabel]:
        if self._name_index is None:
            self._name_index = {label.name.casefold(): label for label in self.labels}
        return self._name_index

    def get(self, name: str) -> str | None:
        label = self.by_name().get(name.casefold())
        return label.values[0].text if label and label.values else None


def extract_hotkey(text: str) -> str | None:
    i = 0
    while i < len(text):
        if text[i] == "&":
            if i + 1 < len(text) and text[i + 1] == "&":
                i += 2
                continue
            if i + 1 < len(text):
                return text[i + 1].upper()
        i += 1
    return None


def set_hotkey_marker(text: str, key: str | None) -> str:
    # Strip mnemonic markers while preserving escaped literal ampersands.
    generated_fallback = bool(re.search(r"\s*\(&[A-Za-z0-9]\)$", text))
    clean: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "&" and i + 1 < len(text):
            if text[i + 1] == "&":
                clean.extend(("&", "&"))
                i += 2
                continue
            i += 1
            continue
        clean.append(text[i])
        i += 1
    result = "".join(clean)
    # A previous generated fallback is safe to remove. This enables changing a
    # label such as "Humvee (&F)" without accumulating visible suffixes.
    if generated_fallback:
        result = re.sub(r"\s*\([A-Za-z0-9]\)$", "", result)
    if not key:
        return result
    key = key.upper()
    if len(key) != 1:
        raise ValueError("CSF mnemonic keys must be one character")
    index = result.casefold().find(key.casefold())
    if index < 0:
        # SAGE reads the character after '&'. Appending the conventional
        # mnemonic suffix supports any alphanumeric key without corrupting text.
        return f"{result} (&{key})"
    return result[:index] + "&" + result[index:]
