from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class MouseWidget(QWidget):
    key_clicked = Signal(str)
    key_context_requested = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(155, 150)
        self.states = {key: "unused" for key in ("M3", "M4", "M5")}
        self.details = {key: [] for key in self.states}
        self.colors = {"unused": "#26323e", "used": "#38556d", "conflict": "#8a5a42", "reserved": "#4a4655"}
        self.visuals = {"body": "#17222c", "outline": "#60788b", "text": "#dce7ef", "label": "#8fa5b6"}
        self.regions = {
            "M3": QRect(84, 18, 18, 40),
            "M4": QRect(8, 51, 35, 27),
            "M5": QRect(8, 84, 35, 27),
        }
        self.setToolTip("LMB / RMB are shown for orientation and remain reserved by Zero Hour.")

    def update_usage(self, states, details, colors, visuals=None) -> None:
        self.states = {key: states.get(key, "unused") for key in self.states}
        self.details = {key: details.get(key, []) for key in self.details}
        self.colors = colors
        if visuals:
            self.visuals = visuals
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        outline = QPen(QColor(self.visuals["outline"]), 2)
        painter.setPen(outline)
        painter.setBrush(QColor(self.visuals["body"]))
        painter.drawRoundedRect(QRectF(40, 5, 105, 140), 48, 48)

        painter.drawLine(92, 6, 92, 62)
        painter.setPen(QColor(self.visuals["text"]))
        painter.drawText(QRect(48, 17, 38, 22), Qt.AlignmentFlag.AlignCenter, "LMB")
        painter.drawText(QRect(99, 17, 38, 22), Qt.AlignmentFlag.AlignCenter, "RMB")

        for key, region in self.regions.items():
            painter.setPen(QPen(QColor(self.visuals["outline"]), 1))
            painter.setBrush(QColor(self.colors[self.states[key]]))
            painter.drawRoundedRect(QRectF(region), 6, 6)
            painter.setPen(QColor(self.visuals["text"]))
            painter.drawText(region, Qt.AlignmentFlag.AlignCenter, key)

        painter.setPen(QColor(self.visuals["label"]))
        painter.drawText(QRect(45, 112, 95, 22), Qt.AlignmentFlag.AlignCenter, "MOUSE")

    def mousePressEvent(self, event) -> None:
        point: QPoint = event.position().toPoint()
        for key, region in self.regions.items():
            if region.contains(point):
                if event.button() == Qt.MouseButton.LeftButton:
                    self.key_clicked.emit(key)
                elif event.button() == Qt.MouseButton.RightButton:
                    self.key_context_requested.emit(key, event.globalPosition().toPoint())
                return
        super().mousePressEvent(event)
