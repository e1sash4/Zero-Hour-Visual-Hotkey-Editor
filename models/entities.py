from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MappedImage:
    id: str
    texture: str = ""
    texture_width: int = 0
    texture_height: int = 0
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0
    source: str = ""

    @property
    def box(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.right, self.bottom


@dataclass(slots=True)
class CommandButton:
    id: str
    command: str = ""
    object_id: str = ""
    upgrade: str = ""
    special_power: str = ""
    button_image: str = ""
    text_label: str = ""
    description_label: str = ""
    fields: dict[str, str] = field(default_factory=dict)
    source: str = ""


@dataclass(slots=True)
class CommandSet:
    id: str
    slots: dict[int, str] = field(default_factory=dict)
    source: str = ""


@dataclass(slots=True)
class ObjectDefinition:
    id: str
    command_set: str = ""
    display_name: str = ""
    side: str = ""
    kind_of: set[str] = field(default_factory=set)
    build_variations: list[str] = field(default_factory=list)
    fields: dict[str, str] = field(default_factory=dict)
    source: str = ""


@dataclass(slots=True)
class CommandContext:
    faction: str
    general: str
    producer_id: str
    producer_name: str
    command_set_id: str
    slot: int
    button: CommandButton
    icon_path: Path | None = None
    display_name: str = ""

    @property
    def identity(self) -> str:
        return f"{self.command_set_id}:{self.slot}:{self.button.id}"


@dataclass(slots=True)
class GameDatabase:
    game_dir: Path
    language_archive: Path | None = None
    csf_member: str = ""
    mapped_images: dict[str, MappedImage] = field(default_factory=dict)
    buttons: dict[str, CommandButton] = field(default_factory=dict)
    command_sets: dict[str, CommandSet] = field(default_factory=dict)
    objects: dict[str, ObjectDefinition] = field(default_factory=dict)
    contexts: list[CommandContext] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
