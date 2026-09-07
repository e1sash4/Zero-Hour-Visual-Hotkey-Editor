from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class IniBlock:
    kind: str
    name: str
    fields: dict[str, str] = field(default_factory=dict)
    numbered: dict[int, str] = field(default_factory=dict)
    source: str = ""


_START = re.compile(r"^\s*([A-Za-z][\w]*)\s+([^;\s]+)")
_FIELD = re.compile(r"^\s*([^=;]+?)\s*=\s*(.*?)\s*$")


def decode_ini(data: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1")


def parse_blocks(text: str, kinds: set[str] | None = None, source: str = "") -> list[IniBlock]:
    wanted = {item.casefold() for item in kinds} if kinds else None
    blocks: list[IniBlock] = []
    current: IniBlock | None = None
    nested_depth = 0
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if current is None:
            match = _START.match(line)
            if match and (wanted is None or match.group(1).casefold() in wanted):
                current = IniBlock(match.group(1), match.group(2), source=source)
                nested_depth = 0
            continue
        if line.casefold() == "end":
            if nested_depth:
                nested_depth -= 1
            else:
                blocks.append(current)
                current = None
            continue
        # Object modules contain nested Behavior/Body/Draw blocks. Their fields are
        # intentionally ignored while keeping the outer Object alive.
        if re.match(r"^(Behavior|Body|Draw|ClientUpdate|Physics|LocomotorSet|WeaponSet|ArmorSet)\b", line, re.I):
            nested_depth += 1
            continue
        if nested_depth:
            continue
        match = _FIELD.match(line)
        if match:
            key, value = match.group(1).strip(), match.group(2).strip()
            if key.isdigit():
                current.numbered[int(key)] = value
            else:
                current.fields[key] = value
    return blocks

