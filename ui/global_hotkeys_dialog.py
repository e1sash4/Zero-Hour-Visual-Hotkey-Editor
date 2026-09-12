from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon, QKeySequence
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox,
                               QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QKeySequenceEdit)

from core.backup_manager import BackupManager
from core.write_recovery import is_access_error
from core.command_map import CommandMapFile, GlobalBinding
from models import CommandContext
from app.i18n import tr


IMAGE_IDS = {"ATTACK_MOVE": "SSAttackMove2", "STOP": "SSStop", "SCATTER": "SSStop"}
CATEGORY_IMAGES = {"CONTROL": "SSAttackMove2", "SELECTION": "SSGuard", "TEAM": "SSGuard",
                   "INTERFACE": "GeneralsLogo", "OTHER": "SSStop"}


class GlobalHotkeysDialog(QDialog):
    def __init__(self, source: bytes, csf, assets, db, hotkeys, game_dir: Path, app_root: Path, apply_csf, parent=None):
        super().__init__(parent)
        self.source = source
        self.applied = False
        self.csf, self.assets, self.db, self.hotkeys, self.game_dir = csf, assets, db, hotkeys, game_dir
        self.apply_csf = apply_csf
        self.manager = BackupManager(app_root / "backups-command-map", "CommandMap.ini",
                                     lambda data: CommandMapFile.parse(data.decode("utf-8-sig", errors="strict")))
        self.command_map = CommandMapFile.parse(source.decode("utf-8-sig", errors="replace"))
        wanted = ("Command_AttackMove", "Command_Guard", "Command_GuardWithoutPursuit",
                  "Command_GuardFlyingUnitsOnly", "Command_Stop", "Command_Sell")
        self.universal = []
        for slot, button_id in enumerate(wanted, 1):
            if button := db.buttons.get(button_id):
                icon = assets.get_icon(button.button_image) if button.button_image else None
                self.universal.append(CommandContext("Global", "Universal", "Global", "Universal Commands",
                                                     "GLOBAL_CSF", slot, button, icon,
                                                     (csf.get(button.text_label) or button_id).replace("&", "")))
        self.setWindowTitle(tr("global_hotkeys"))
        self.resize(760, 620)
        layout = QVBoxLayout(self)
        self.category = QComboBox()
        self.category.addItem(tr("all"), "ALL")
        self.category.addItem(tr("universal"), "UNIVERSAL")
        self.category.addItems(sorted({item.category for item in self.command_map.bindings}))
        self.category.currentTextChanged.connect(self.refresh)
        layout.addWidget(self.category)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("action"), tr("key"), tr("category")])
        self.tree.setColumnWidth(0, 430)
        self.tree.currentItemChanged.connect(self.selected)
        layout.addWidget(self.tree)
        self.description = QLabel(tr("select_global"))
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        row = QHBoxLayout()
        self.capture = QKeySequenceEdit()
        change = QPushButton(tr("assign"))
        clear = QPushButton(tr("remove"))
        change.clicked.connect(self.assign)
        clear.clicked.connect(self.clear)
        row.addWidget(self.capture, 1); row.addWidget(change); row.addWidget(clear)
        layout.addLayout(row)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self.apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.refresh()

    def label(self, item: GlobalBinding) -> str:
        return (self.csf.get(item.display_label) or item.id).replace("&", "")

    def refresh(self) -> None:
        selected = self.category.currentData() or self.category.currentText()
        self.tree.clear()
        for binding in self.command_map.bindings:
            if selected != "ALL" and binding.category != selected:
                continue
            row = QTreeWidgetItem([self.label(binding), binding.shortcut or "—", binding.category])
            row.setData(0, 256, ("map", binding))
            image_id = IMAGE_IDS.get(binding.id, CATEGORY_IMAGES.get(binding.category, "GeneralsLogo"))
            image = self.assets.get_icon(image_id)
            if image:
                row.setIcon(0, QIcon(str(image)))
            description = (self.csf.get(binding.description_label) or binding.id).replace("&", "")
            row.setToolTip(0, description)
            self.tree.addTopLevelItem(row)
        if selected in ("ALL", "UNIVERSAL"):
            for context in self.universal:
                row = QTreeWidgetItem([context.display_name, self.hotkeys.get_hotkey(context) or "—", "UNIVERSAL"])
                row.setData(0, 256, ("csf", context))
                if context.icon_path:
                    row.setIcon(0, QIcon(str(context.icon_path)))
                description = (self.csf.get(context.button.description_label) or context.button.id).replace("&", "")
                row.setToolTip(0, description)
                self.tree.addTopLevelItem(row)

    def selected(self, row, _old=None) -> None:
        if not row:
            return
        kind, binding = row.data(0, 256)
        if kind == "map":
            description = self.csf.get(binding.description_label) or binding.id
            shortcut = binding.shortcut
        else:
            description = self.csf.get(binding.button.description_label) or binding.button.id
            shortcut = self.hotkeys.get_hotkey(binding) or ""
        self.description.setText(description.replace("&", ""))
        self.capture.setKeySequence(QKeySequence(shortcut))

    def current(self):
        row = self.tree.currentItem()
        return row.data(0, 256) if row else None

    @staticmethod
    def encode(sequence: str) -> tuple[str, str]:
        parts = sequence.replace(" ", "").split("+")
        mods = [p.upper() for p in parts[:-1]]
        aliases = {"CONTROL": "CTRL", "DEL": "DEL", "DELETE": "DEL", "ESCAPE": "ESC", "RETURN": "ENTER"}
        mods = [aliases.get(p, p) for p in mods]
        key = aliases.get(parts[-1].upper(), parts[-1].upper()) if parts and parts[-1] else "NONE"
        return "KEY_" + key, "_".join(mods) or "NONE"

    def assign(self) -> None:
        selected = self.current()
        sequence = self.capture.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
        if not selected or not sequence:
            return
        kind, binding = selected
        key, modifiers = self.encode(sequence)
        if kind == "csf" and (modifiers != "NONE" or len(key.removeprefix("KEY_")) != 1):
            QMessageBox.warning(self, tr("unsupported_key"), tr("unsupported_key_text"))
            return
        map_conflicts = self.command_map.conflicts(binding, key, modifiers) if kind == "map" else [
            item for item in self.command_map.bindings if item.key == key and item.modifiers == modifiers and item.transition == "DOWN"]
        csf_conflicts = []
        seen_labels = set()
        selected_label = binding.button.text_label.casefold() if kind == "csf" else ""
        if modifiers == "NONE":
            for item in [*self.universal, *self.hotkeys.contexts]:
                label = item.button.text_label.casefold()
                if label == selected_label or label in seen_labels:
                    continue
                if self.hotkeys.get_hotkey(item) == key.removeprefix("KEY_"):
                    csf_conflicts.append(item)
                    seen_labels.add(label)
        conflicts = map_conflicts + csf_conflicts
        if conflicts:
            names = ", ".join(self.label(item) if isinstance(item, GlobalBinding) else
                              f"{item.display_name} ({item.faction}/{item.producer_name})" for item in conflicts)
            answer = QMessageBox.question(self, tr("global_conflict"),
                                          tr("global_conflict_text", key=sequence, names=names))
            if answer != QMessageBox.StandardButton.Yes:
                return
            for item in map_conflicts:
                item.key, item.modifiers = "KEY_NONE", "NONE"
            for item in csf_conflicts:
                self.hotkeys.set_hotkey(item, None)
        if kind == "map":
            binding.key, binding.modifiers = key, modifiers
        else:
            self.hotkeys.set_hotkey(binding, key.removeprefix("KEY_"))
        self.refresh()

    def clear(self) -> None:
        if selected := self.current():
            kind, binding = selected
            if kind == "map":
                binding.key, binding.modifiers = "KEY_NONE", "NONE"
            else:
                self.hotkeys.set_hotkey(binding, None)
            self.refresh()

    def apply(self) -> None:
        target = self.game_dir / "Data/English/CommandMap.ini"
        command_map_data = self.command_map.to_text().encode("utf-8")
        recovery_files = {"CommandMap.ini": command_map_data}
        if self.hotkeys.pending:
            recovery_files["generals.csf"] = self.hotkeys.materialize().to_bytes()
        try:
            self.manager.create(target, self.source)
            self.manager.atomic_write(target, command_map_data)
            if self.hotkeys.pending:
                self.apply_csf()
            self.applied = True
            QMessageBox.information(self, tr("applied"), tr("global_applied"))
        except Exception as exc:
            handler = getattr(self.parent(), "handle_write_access_error", None)
            if is_access_error(exc) and handler is not None:
                handler(exc, recovery_files)
            else:
                QMessageBox.critical(self, tr("apply_failed"), str(exc))
