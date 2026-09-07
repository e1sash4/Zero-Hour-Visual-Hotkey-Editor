from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QFileDialog, QHBoxLayout, QInputDialog, QListWidget, QMessageBox,
    QPushButton, QVBoxLayout,
)

from core.profile_manager import ProfileManager
from app.i18n import tr


class ProfileDialog(QDialog):
    def __init__(self, manager: ProfileManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.selected_path: Path | None = None
        self.setWindowTitle(tr("profiles"))
        self.resize(520, 360)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        layout.addWidget(self.list)
        row = QHBoxLayout()
        for text, handler in ((tr("duplicate"), self.duplicate), (tr("rename"), self.rename), (tr("delete"), self.delete),
                              (tr("import"), self.import_profile), (tr("export"), self.export_profile)):
            button = QPushButton(text)
            button.clicked.connect(handler)
            row.addWidget(button)
        layout.addLayout(row)
        apply = QPushButton(tr("apply_profile"))
        apply.clicked.connect(self.apply)
        layout.addWidget(apply)
        self.refresh()

    def refresh(self) -> None:
        self.paths = self.manager.list()
        self.list.clear()
        for path in self.paths:
            profile = self.manager.load(path)
            self.list.addItem(profile.name + (f"  • {tr('game_default')}" if profile.read_only else ""))

    def current(self) -> Path | None:
        row = self.list.currentRow()
        return self.paths[row] if 0 <= row < len(self.paths) else None

    def duplicate(self) -> None:
        if not (path := self.current()): return
        name, ok = QInputDialog.getText(self, tr("duplicate_profile"), tr("new_name"))
        if ok and name.strip():
            self.manager.duplicate(path, name.strip()); self.refresh()

    def rename(self) -> None:
        if not (path := self.current()): return
        name, ok = QInputDialog.getText(self, tr("rename_profile"), tr("new_name"))
        if ok and name.strip():
            try: self.manager.rename(path, name.strip()); self.refresh()
            except Exception as exc: QMessageBox.warning(self, tr("profile"), str(exc))

    def delete(self) -> None:
        if not (path := self.current()): return
        if QMessageBox.question(self, tr("delete_profile"), tr("delete_profile_q", name=path.stem)) == QMessageBox.StandardButton.Yes:
            try: self.manager.delete(path); self.refresh()
            except Exception as exc: QMessageBox.warning(self, tr("profile"), str(exc))

    def import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("import_profile"), "", tr("json_profiles"))
        if path:
            try:
                profile = self.manager.load(path)
                profile.read_only = False
                self.manager.save(profile)
                self.refresh()
            except Exception as exc: QMessageBox.warning(self, tr("import"), str(exc))

    def export_profile(self) -> None:
        if not (path := self.current()): return
        target, _ = QFileDialog.getSaveFileName(self, tr("export_profile"), path.name, tr("json_profiles"))
        if target:
            shutil.copy2(path, target)

    def apply(self) -> None:
        if path := self.current():
            self.selected_path = path
            self.accept()
