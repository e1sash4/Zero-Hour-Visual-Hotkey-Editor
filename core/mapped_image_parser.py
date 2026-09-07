from __future__ import annotations

import re

from models import MappedImage
from .ini_parser import parse_blocks


def parse_mapped_images(text: str, source: str = "") -> dict[str, MappedImage]:
    result: dict[str, MappedImage] = {}
    for block in parse_blocks(text, {"MappedImage"}, source):
        coords = {k.casefold(): int(v) for k, v in re.findall(r"(Left|Top|Right|Bottom)\s*:\s*(-?\d+)", block.fields.get("Coords", ""), re.I)}
        def number(name: str) -> int:
            try:
                return int(block.fields.get(name, "0"))
            except ValueError:
                return 0
        result[block.name] = MappedImage(
            id=block.name, texture=block.fields.get("Texture", ""),
            texture_width=number("TextureWidth"), texture_height=number("TextureHeight"),
            left=coords.get("left", 0), top=coords.get("top", 0),
            right=coords.get("right", 0), bottom=coords.get("bottom", 0), source=source,
        )
    return result

