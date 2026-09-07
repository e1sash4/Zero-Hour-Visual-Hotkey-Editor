from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QPushButton, QWidget

from .mouse_widget import MouseWidget


_INPUT_THEMES = {
    "dark": {
        "keys": {"unused": "#26323e", "used": "#38556d", "conflict": "#8a5a42", "reserved": "#4a4655"},
        "key_text": "#f4f7fa", "key_border": "#536779",
        "mouse": {"body": "#17222c", "outline": "#60788b", "text": "#dce7ef", "label": "#8fa5b6"},
    },
    "light": {
        "keys": {"unused": "#ffffff", "used": "#b9dcf3", "conflict": "#f4c1ac", "reserved": "#ddd5ea"},
        "key_text": "#182733", "key_border": "#718696",
        "mouse": {"body": "#f8fafc", "outline": "#60798b", "text": "#1c2c38", "label": "#4d6576"},
    },
}

_ZERO_HOUR_INPUT_THEMES = {
    "USA": {
        "keys": {"unused": "#071d25", "used": "#16566a", "conflict": "#74402b", "reserved": "#344b50"},
        "key_text": "#edf4ee", "key_border": "#82969b",
        "mouse": {"body": "#071d25", "outline": "#82969b", "text": "#edf4ee", "label": "#d7a53e"},
    },
    "China": {
        "keys": {"unused": "#2a100c", "used": "#76281b", "conflict": "#8d3b20", "reserved": "#4c392d"},
        "key_text": "#f3e7d7", "key_border": "#89745e",
        "mouse": {"body": "#2a100c", "outline": "#89745e", "text": "#f3e7d7", "label": "#d73a27"},
    },
    "GLA": {
        "keys": {"unused": "#0b1b0d", "used": "#315932", "conflict": "#765028", "reserved": "#463f31"},
        "key_text": "#eee7cf", "key_border": "#82765f",
        "mouse": {"body": "#0b1b0d", "outline": "#82765f", "text": "#eee7cf", "label": "#c98d34"},
    },
}


def input_theme(theme: str, faction: str) -> dict:
    if theme == "zero_hour":
        return _ZERO_HOUR_INPUT_THEMES.get(faction, _ZERO_HOUR_INPUT_THEMES["USA"])
    return _INPUT_THEMES.get(theme, _INPUT_THEMES["dark"])


class KeyboardWidget(QWidget):
    key_clicked = Signal(str)
    key_context_requested = Signal(str, object)

    ROWS = ("1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM")

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addStretch(1)
        keyboard = QWidget()
        layout = QGridLayout(keyboard)
        layout.setSpacing(4)
        outer.addWidget(keyboard)
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
        self.mouse = MouseWidget()
        self.mouse.key_clicked.connect(self.key_clicked)
        self.mouse.key_context_requested.connect(self.key_context_requested)
        outer.addWidget(self.mouse)
        outer.addStretch(1)

    def update_usage(self, states: dict[str, str], details: dict[str, list[str]] | None = None,
                     theme: str = "dark", faction: str = "USA") -> None:
        appearance = input_theme(theme, faction)
        colors = appearance["keys"]
        self.mouse.update_usage(states, details or {}, colors, appearance["mouse"])
        for key, button in self.buttons.items():
            state = states.get(key, "unused")
            button.setStyleSheet(
                f"background:{colors[state]}; color:{appearance['key_text']}; "
                f"border:1px solid {appearance['key_border']}; font-weight:600;"
            )
            assigned = (details or {}).get(key, [])
            button.setToolTip("\n".join(assigned) if assigned else state.title())
