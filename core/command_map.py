from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class GlobalBinding:
    id: str
    key: str
    modifiers: str
    category: str
    display_label: str
    description_label: str
    usable_in: str
    transition: str = "DOWN"

    @property
    def shortcut(self) -> str:
        if self.key in ("", "KEY_NONE"):
            return ""
        parts = [] if self.modifiers == "NONE" else self.modifiers.split("_")
        names = {"CTRL": "Ctrl", "SHIFT": "Shift", "ALT": "Alt"}
        parts = [names.get(part, part.title()) for part in parts]
        key = self.key.removeprefix("KEY_").replace("DEL", "Delete").replace("ESC", "Escape")
        return "+".join(parts + [key.title() if len(key) > 1 else key]) if self.key else ""


_BLOCK = re.compile(r"(?ims)^CommandMap\s+(\S+)\s*\r?\n(.*?)(^End\s*$|^END\s*$)")


class CommandMapFile:
    def __init__(self, text: str, bindings: list[GlobalBinding]):
        self.text = text
        self.bindings = bindings

    @classmethod
    def parse(cls, text: str) -> "CommandMapFile":
        bindings = []
        for match in _BLOCK.finditer(text):
            fields = {}
            for line in match.group(2).splitlines():
                field = re.match(r"\s*(\w+)\s*(?:=\s*)?(.*?)\s*$", line)
                if field and not line.lstrip().startswith(";"):
                    fields[field.group(1).casefold()] = field.group(2)
            if "GAME" not in fields.get("useablein", "").upper() or not fields.get("key"):
                continue
            bindings.append(GlobalBinding(match.group(1), fields.get("key", ""), fields.get("modifiers", "NONE"),
                                          fields.get("category", "OTHER"), fields.get("displayname", match.group(1)),
                                          fields.get("description", ""), fields.get("useablein", ""),
                                          fields.get("transition", "DOWN")))
        return cls(text, bindings)

    def to_text(self) -> str:
        by_id = {item.id.casefold(): item for item in self.bindings}
        def replace(match: re.Match) -> str:
            item = by_id.get(match.group(1).casefold())
            if not item:
                return match.group(0)
            body = match.group(2)
            body = re.sub(r"(?im)^(\s*Key\s*=\s*).*$", rf"\g<1>{item.key or 'KEY_NONE'}", body, count=1)
            body = re.sub(r"(?im)^(\s*Modifiers\s*=\s*).*$", rf"\g<1>{item.modifiers or 'NONE'}", body, count=1)
            return f"CommandMap {match.group(1)}\n{body}{match.group(3)}"
        return _BLOCK.sub(replace, self.text)

    def conflicts(self, current: GlobalBinding, key: str, modifiers: str) -> list[GlobalBinding]:
        return [item for item in self.bindings if item is not current and item.key == key
                and item.modifiers == modifiers and item.transition == current.transition]
