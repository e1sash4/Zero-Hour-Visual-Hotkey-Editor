from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget


class KeyboardWidget(QWidget):
    key_clicked = Signal(str)
    key_context_requested = Signal(str, object)

    ROWS = ("1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(4)
        self.buttons: dict[str, QPushButton] = {}
        for row, keys in enumerate(self.ROWS):
            offset = (row - 1) if row > 1 else 0
            for column, key in enumerate(keys):
                button = QPushButton(key)
                button.setFixedSize(38, 34)
                button.clicked.connect(lambda _checked=False, value=key: self.key_clicked.emit(value))
                button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                button.customContextMenuRequested.connect(
                    lambda position, value=key, source=button:
                    self.key_context_requested.emit(value, source.mapToGlobal(position))
                )
                layout.addWidget(button, row, column + offset)
                self.buttons[key] = button

    def update_usage(self, states: dict[str, str], details: dict[str, list[str]] | None = None,
                     theme: str = "dark", faction: str = "USA") -> None:
        colors = {"unused": "#26323e", "used": "#38556d", "conflict": "#8a5a42", "reserved": "#4a4655"}
        if theme == "zero_hour":
            colors = {
                "USA": {"unused": "#071d25", "used": "#16566a", "conflict": "#74402b", "reserved": "#344b50"},
                "China": {"unused": "#2a100c", "used": "#76281b", "conflict": "#8d3b20", "reserved": "#4c392d"},
                "GLA": {"unused": "#0b1b0d", "used": "#315932", "conflict": "#765028", "reserved": "#463f31"},
            }.get(faction, colors)
        for key, button in self.buttons.items():
            state = states.get(key, "unused")
            button.setStyleSheet(f"background:{colors[state]};")
            assigned = (details or {}).get(key, [])
            button.setToolTip("\n".join(assigned) if assigned else state.title())
