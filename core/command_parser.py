from __future__ import annotations

import re

from models import CommandButton, CommandSet, ObjectDefinition
from .ini_parser import parse_blocks


def parse_command_buttons(text: str, source: str = "") -> dict[str, CommandButton]:
    result = {}
    for block in parse_blocks(text, {"CommandButton"}, source):
        f = block.fields
        result[block.name] = CommandButton(
            id=block.name, command=f.get("Command", ""), object_id=f.get("Object", ""),
            upgrade=f.get("Upgrade", ""), special_power=f.get("SpecialPower", ""),
            button_image=f.get("ButtonImage", ""), text_label=f.get("TextLabel", ""),
            description_label=f.get("DescriptLabel", ""), fields=f, source=source,
        )
    return result


def parse_command_sets(text: str, source: str = "") -> dict[str, CommandSet]:
    return {b.name: CommandSet(b.name, b.numbered, source) for b in parse_blocks(text, {"CommandSet"}, source)}


def parse_objects(text: str, source: str = "") -> dict[str, ObjectDefinition]:
    # Object modules contain their own nested End markers. Segmenting on the next
    # top-level object declaration is both tolerant and sufficient for metadata.
    result: dict[str, ObjectDefinition] = {}
    starts = list(re.finditer(r"(?im)^(?:Object|ChildObject|ObjectReskin)\s+([^\s;=]+)[^\r\n]*", text))
    for index, match in enumerate(starts):
        body = text[match.end(): starts[index + 1].start() if index + 1 < len(starts) else len(text)]
        def value(key: str) -> str:
            found = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^;\r\n]*)", body)
            return found.group(1).strip() if found else ""
        name = match.group(1)
        fields = {key: value(key) for key in ("CommandSet", "DisplayName", "Side", "KindOf", "BuildVariations", "ButtonImage")}
        result[name] = ObjectDefinition(
            id=name, command_set=fields["CommandSet"], display_name=fields["DisplayName"],
            side=fields["Side"], kind_of=set(fields["KindOf"].split()),
            build_variations=fields["BuildVariations"].split(), fields=fields, source=source,
        )
    return result
