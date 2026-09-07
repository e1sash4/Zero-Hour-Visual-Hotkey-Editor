from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from models import CommandContext
from .command_card import CommandCard


@lru_cache(maxsize=1)
def _layout_overrides() -> dict[str, dict[str, list[int]]]:
    path = Path(__file__).resolve().parents[1] / "data/overrides/layouts.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def command_grid_positions(contexts: list[CommandContext]) -> dict[str, tuple[int, int]]:
    """Map SAGE slots to the compact two-row layout used by the reference UI.

    Populated production slots 1–10 are balanced across two rows. Slots 11/12
    occupy the sixth column and the standard rally/sell slots 13/14 the seventh.
    """
    primary = sorted((item for item in contexts if item.slot <= 10), key=lambda item: item.slot)
    split = (len(primary) + 1) // 2
    positions: dict[str, tuple[int, int]] = {}
    for index, context in enumerate(primary[:split]):
        positions[context.identity] = (0, index)
    for index, context in enumerate(primary[split:]):
        positions[context.identity] = (1, index)
    fixed = {11: (0, 5), 12: (1, 5), 13: (0, 6), 14: (1, 6)}
    for context in contexts:
        if context.slot in fixed:
            positions[context.identity] = fixed[context.slot]
    if contexts:
        override = _layout_overrides().get(contexts[0].command_set_id, {})
        for context in contexts:
            if context.button.id in override:
                row, column = override[context.button.id]
                positions[context.identity] = (int(row), int(column))
    return positions


class CommandGrid(QWidget):
    command_clicked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setAlignment(__import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignTop | __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.AlignmentFlag.AlignLeft)
        self.cards: dict[str, CommandCard] = {}

    def populate(self, contexts: list[CommandContext], hotkey_getter, developer: bool = False) -> None:
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards.clear()
        positions = command_grid_positions(contexts)
        for context in sorted(contexts, key=lambda c: c.slot):
            card = CommandCard(context, hotkey_getter(context), developer)
            card.clicked.connect(self.command_clicked)
            row, column = positions.get(context.identity, divmod(max(0, context.slot - 1), 7))
            self.layout.addWidget(card, row, column)
            self.cards[context.identity] = card

    def select(self, identity: str | None) -> None:
        for key, card in self.cards.items():
            card.set_selected(key == identity)

    def refresh_keys(self, hotkey_getter) -> None:
        for card in self.cards.values():
            card.set_hotkey(hotkey_getter(card.context))
