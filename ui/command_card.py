from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from models import CommandContext
from app.i18n import tr


class CommandCard(QFrame):
    clicked = Signal(object)

    def __init__(self, context: CommandContext, hotkey: str | None, developer: bool = False, parent=None):
        super().__init__(parent)
        self.context = context
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(132, 176)
        self.setObjectName("commandCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        self.icon = QLabel()
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon.setFixedHeight(76)
        if context.icon_path and context.icon_path.is_file():
            pixmap = QPixmap(str(context.icon_path))
            self.icon.setPixmap(pixmap.scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            self.icon.setText("?")
            self.icon.setStyleSheet("font-size: 30pt; color: #718090;")
        self.name = QLabel(context.display_name)
        self.name.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.name.setWordWrap(True)
        self.name.setFixedHeight(52)
        self.key = QLabel(hotkey or "—")
        self.key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key.setFixedHeight(26)
        self.key.setStyleSheet("font-size: 15pt; font-weight: 700; color: #f1c76a;")
        layout.addWidget(self.icon)
        layout.addWidget(self.name, 1)
        layout.addWidget(self.key)
        technical = (f"\n\nCommandButton: {context.button.id}\nCommandSet: {context.command_set_id}"
                     f"\nTextLabel: {context.button.text_label}\nMappedImage: {context.button.button_image}") if developer else ""
        self.setToolTip(f"{context.display_name}\n{context.faction} / {context.general}\n{tr('tooltip.produced')}: {context.producer_name}\n{tr('tooltip.hotkey')}: {hotkey or tr('none')}{technical}")
        self.set_selected(False)

    def set_hotkey(self, key: str | None) -> None:
        self.key.setText(key or "—")

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.context)
        super().mousePressEvent(event)
