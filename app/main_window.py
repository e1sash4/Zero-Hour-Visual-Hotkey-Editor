from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSettings, QSize, QThread, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
    QMainWindow, QMenu, QMessageBox, QProgressBar, QPushButton, QScrollArea, QSplitter, QListWidgetItem,
    QStackedWidget, QToolBar, QVBoxLayout, QWidget,
)

from core.backup_manager import BackupManager
from core.csf_parser import CsfFile
from core.command_map import CommandMapFile
from core.hotkey_manager import (
    DEFAULT_MOUSE_KEYS, LEGACY_MOUSE_KEYS, MOUSE_BUTTONS, HotkeyManager, VALID_BINDINGS, VALID_KEYS,
)
from core.indexer import CsfLoadError, GameIndexer
from core.mouse_bindings import MouseBindingStore
from core.mouse_remapper import MouseRemapper
from core.profile_manager import Profile, ProfileManager
from core.write_recovery import (
    create_recovery_package, is_access_error, is_running_as_admin,
    manual_copy_instructions, restart_as_admin,
)
from models import CommandContext
from ui.command_grid import CommandGrid
from ui.conflict_dialog import ask_conflict
from ui.global_hotkeys_dialog import GlobalHotkeysDialog
from ui.keyboard_widget import KeyboardWidget
from ui.profile_dialog import ProfileDialog
from ui.settings_dialog import SettingsDialog
from .i18n import set_language, tr
from .theme import FACTION_ACCENTS, style_for


FACTION_LOGOS = {"USA": "SAFactionLogo144_US", "China": "SNFactionLogo144_China", "GLA": "SUFactionLogo144_GLA"}
FACTION_HUD_LOGOS = {"USA": "SALogo", "China": "SNLogo", "GLA": "SULogo"}
GENERAL_KEYS = {
    "Vanilla": "general.vanilla", "Air Force": "general.air_force", "Laser": "general.laser",
    "Superweapon": "general.superweapon", "Tank": "general.tank", "Infantry": "general.infantry",
    "Nuclear": "general.nuclear", "Toxin": "general.toxin", "Stealth": "general.stealth",
    "Demolition": "general.demolition",
}
GENERAL_ICONS = {
    "USA": {"Vanilla": "SAFactionLogo96_US", "Air Force": "AirGeneral_blue",
            "Laser": "LaserGeneral_blue", "Superweapon": "SuperWGeneral_blue"},
    "China": {"Vanilla": "SNFactionLogo96_China", "Tank": "TankGeneral_blue",
              "Infantry": "InfantryGeneral_blue", "Nuclear": "NukeGeneral_blue"},
    "GLA": {"Vanilla": "SUFactionLogo96_GLA", "Toxin": "ToxinGeneral_blue",
            "Stealth": "StealthGeneral_blue", "Demolition": "DemoGeneral_blue"},
}
ACTION_GROUP_KEYS = {
    "Unit Actions": "unit_actions",
    "Building Actions": "building_actions",
    "Infantry Actions": "infantry_actions",
}


class IndexWorker(QObject):
    progress = Signal(int, str)
    ready = Signal(object, object, object, object)
    failed = Signal(str)

    def __init__(self, game_dir: Path, app_root: Path):
        super().__init__()
        self.game_dir = game_dir
        self.app_root = app_root

    @Slot()
    def run(self) -> None:
        try:
            indexer = GameIndexer(self.game_dir, self.app_root)
            db, csf, assets = indexer.build(lambda p, m: self.progress.emit(p, m))
            self.ready.emit(db, csf, assets, indexer.csf_source)
        except CsfLoadError as exc:
            logging.exception("Could not read CSF")
            message_id = "loose_csf_invalid" if exc.loose_override else "archive_csf_invalid"
            self.failed.emit(tr(message_id, path=exc.path, error=exc.reason))
        except Exception as exc:
            logging.exception("Indexing failed")
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self, game_dir: Path, app_root: Path, settings: QSettings):
        super().__init__()
        self.game_dir = game_dir
        self.app_root = app_root
        self.settings = settings
        self.developer = settings.value("developerMode", False, bool)
        self.language = settings.value("language", "uk", str)
        self.theme_name = settings.value("theme", "dark", str)
        self.mouse_remapping_enabled = settings.value("mouseRemapping", True, bool)
        self.db = None
        self.csf = None
        self.source_csf = b""
        self.command_map_source = b""
        self.command_map: CommandMapFile | None = None
        self.command_map_pending: set[str] = set()
        self.assets = None
        self.hotkeys: HotkeyManager | None = None
        self.current_context: CommandContext | None = None
        self.capture_active = False
        self.context_by_search_row: list[CommandContext] = []
        self.profiles = ProfileManager(app_root / "data/profiles")
        self.mouse_binding_store = MouseBindingStore(app_root / "data/mouse-bindings.json")
        self.saved_mouse_bindings = self.mouse_binding_store.load()
        stored_proxies = self.mouse_binding_store.load_proxies()
        fallback_proxies = stored_proxies or (LEGACY_MOUSE_KEYS if self.saved_mouse_bindings else DEFAULT_MOUSE_KEYS)
        configured_proxies = {
            button: settings.value(f"mouseProxy{button}", fallback_proxies[button], str).upper()
            for button in MOUSE_BUTTONS
        }
        if (not set(configured_proxies.values()) <= VALID_KEYS
                or len(set(configured_proxies.values())) != len(configured_proxies)):
            configured_proxies = dict(fallback_proxies)
        self.mouse_proxy_keys = configured_proxies
        self.applied_mouse_proxy_keys = dict(configured_proxies)
        self.mouse_remapper = MouseRemapper(game_dir)
        self.backups = BackupManager(app_root / "backups")
        self.command_map_backups = BackupManager(
            app_root / "backups-command-map",
            "CommandMap.ini",
            lambda data: CommandMapFile.parse(data.decode("utf-8-sig", errors="strict")),
        )
        self.setWindowTitle("Zero Hour Visual Hotkey Editor")
        self.resize(1180, 780)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_ui()
        self._build_actions()
        QApplication.instance().installEventFilter(self)
        self._start_indexing()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(12, 10, 12, 10)
        top = QHBoxLayout()
        self.faction_logo = QLabel()
        self.faction_logo.setFixedSize(72, 72)
        self.faction_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(self.faction_logo)
        self.faction_buttons = {}
        for faction in ("USA", "China", "GLA"):
            button = QPushButton(faction.upper())
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, value=faction: self.select_faction(value))
            self.faction_buttons[faction] = button
            top.addWidget(button)
        self.general = QComboBox()
        self.general.setIconSize(QSize(40, 40))
        self.general.setMinimumHeight(48)
        self.general.currentTextChanged.connect(self._refresh_producers)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("search"))
        self.search.textChanged.connect(self._update_search)
        top.addWidget(self.general, 1)
        top.addWidget(self.search, 2)
        outer.addLayout(top)

        self.search_results = QListWidget()
        self.search_results.setMaximumHeight(150)
        self.search_results.hide()
        self.search_results.itemClicked.connect(self._open_search_result)
        outer.addWidget(self.search_results)

        splitter = QSplitter()
        self.producer_list = QListWidget()
        self.producer_list.setMinimumWidth(235)
        self.producer_list.setIconSize(QSize(32, 32))
        self.producer_list.currentItemChanged.connect(self._producer_item_selected)
        splitter.addWidget(self.producer_list)
        center = QWidget()
        center_layout = QVBoxLayout(center)
        self.breadcrumb = QLabel(tr("indexing"))
        self.breadcrumb.setStyleSheet("font-size: 13pt; font-weight: 600;")
        self.capture_label = QLabel(tr("select_command"))
        self.capture_label.setObjectName("captureHint")
        self.linked_label = QLabel()
        self.linked_label.setWordWrap(True)
        self.linked_label.setObjectName("linkedHint")
        self.grid = CommandGrid()
        self.grid.command_clicked.connect(self._begin_capture)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.grid)
        self.keyboard = KeyboardWidget()
        self.keyboard.key_clicked.connect(self._assign_key)
        self.keyboard.key_context_requested.connect(self._show_key_context_menu)
        center_layout.addWidget(self.breadcrumb)
        center_layout.addWidget(self.capture_label)
        center_layout.addWidget(self.linked_label)
        center_layout.addWidget(scroll, 1)
        center_layout.addWidget(self.keyboard)
        splitter.addWidget(center)
        splitter.setStretchFactor(1, 1)
        outer.addWidget(splitter, 1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        outer.addWidget(self.progress)
        self.setCentralWidget(root)
        self.unsaved = QLabel(tr("unsaved", count=0))
        self.statusBar().addPermanentWidget(self.unsaved)

    def _build_actions(self) -> None:
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        self.apply_action = QAction(tr("apply"), self)
        self.apply_action.setEnabled(False)
        self.apply_action.triggered.connect(self.apply_changes)
        toolbar.addAction(self.apply_action)
        self.undo_action = QAction(tr("undo"), self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        self.redo_action = QAction(tr("redo"), self)
        self.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo_action.triggered.connect(self.redo)
        toolbar.addActions([self.undo_action, self.redo_action])
        self.clear_all_action = QAction(tr("clear_all_bindings"), self)
        self.clear_all_action.setEnabled(False)
        self.clear_all_action.triggered.connect(self.clear_all_bindings)
        toolbar.addAction(self.clear_all_action)
        toolbar.addSeparator()
        self.profile_action = QAction(tr("save_profile"), self)
        self.profile_action.triggered.connect(self.save_profile)
        self.load_profile_action = QAction(tr("manage_profiles"), self)
        self.load_profile_action.triggered.connect(self.manage_profiles)
        toolbar.addActions([self.profile_action, self.load_profile_action])
        toolbar.addSeparator()
        self.global_action = QAction(tr("global_hotkeys"), self)
        self.global_action.triggered.connect(self.show_global_hotkeys)
        toolbar.addAction(self.global_action)
        self.settings_action = QAction(tr("settings"), self)
        self.settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(self.settings_action)

        self.file_menu = self.menuBar().addMenu(tr("file"))
        self.file_menu.addAction(self.apply_action)
        self.restore_latest_action = self.file_menu.addAction(tr("restore_latest"), self.restore_latest)
        self.restore_original_action = self.file_menu.addAction(tr("restore_original"), self.restore_original)
        self.open_backup_action = self.file_menu.addAction(tr("open_backup"), lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.backups.directory))))
        self.profile_menu = self.menuBar().addMenu(tr("profiles"))
        self.profile_menu.addAction(self.profile_action)
        self.profile_menu.addAction(self.load_profile_action)
        QShortcut(QKeySequence("Escape"), self, activated=self._cancel_capture)

    def _start_indexing(self) -> None:
        self.thread = QThread(self)
        self.worker = IndexWorker(self.game_dir, self.app_root)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self._on_progress)
        self.worker.ready.connect(self._on_ready)
        self.worker.failed.connect(self._on_failed)
        self.worker.ready.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.start()

    @Slot(int, str)
    def _on_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(percent)
        self.progress.setFormat(message + " — %p%")

    @Slot(object, object, object, object)
    def _on_ready(self, db, csf, _assets, source_csf: bytes) -> None:
        self.db, self.csf, self.assets, self.source_csf = db, csf, _assets, source_csf
        self.command_map_source = self.assets.index.read(r"Data\English\CommandMap.ini")
        self.command_map = CommandMapFile.parse(self.command_map_source.decode("utf-8-sig", errors="replace"))
        self.hotkeys = HotkeyManager(csf, db.contexts, self.saved_mouse_bindings, self.mouse_proxy_keys)
        self.clear_all_action.setEnabled(True)
        self.progress.hide()
        self.select_faction("USA")
        current_bindings = None
        if (self.game_dir / "Data/English/generals.csf").is_file():
            current_bindings = {
                context.button.text_label: self.hotkeys.get_hotkey(context)
                for context in db.contexts if context.button.text_label
            }
        _path, imported_profile_created = self.profiles.capture_initial_game_settings(current_bindings)
        # Refresh this on every indexing pass. Packaged builds keep profiles in
        # LocalAppData, so a create-once snapshot could otherwise retain the
        # user's old bindings indefinitely. Always derive it from the pristine
        # archive CSF, never from the active loose override.
        default_hotkeys = HotkeyManager(CsfFile.from_bytes(source_csf), db.contexts)
        default_bindings = {
            context.button.text_label: default_hotkeys.get_hotkey(context)
            for context in db.contexts if context.button.text_label
        }
        self.profiles.save_game_default(default_bindings)
        self._sync_mouse_remapper()
        status = tr("indexed", count=len(db.contexts), warnings=len(db.warnings))
        if imported_profile_created:
            status += " • " + tr("existing_profile_imported")
        self.statusBar().showMessage(status, 12000 if imported_profile_created else 8000)

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self.progress.setFormat(tr("index_failed"))
        QMessageBox.critical(self, tr("index_failed"), message)

    def select_faction(self, faction: str) -> None:
        if not self.db:
            return
        self.faction = faction
        QApplication.instance().setStyleSheet(style_for(self.theme_name, faction))
        if self.assets:
            logo_id = FACTION_HUD_LOGOS[faction] if self.theme_name == "zero_hour" else FACTION_LOGOS[faction]
            logo = self.assets.get_icon(logo_id)
            self.faction_logo.setPixmap(QPixmap(str(logo)).scaled(68, 68, Qt.AspectRatioMode.KeepAspectRatio,
                                                               Qt.TransformationMode.SmoothTransformation)) if logo else self.faction_logo.clear()
        for name, button in self.faction_buttons.items():
            button.setChecked(name == faction)
            if name == faction:
                button.setStyleSheet(f"background:{FACTION_ACCENTS[name]}; font-weight:700;")
            else:
                button.setStyleSheet("")
        order = {"USA": ["Vanilla", "Air Force", "Laser", "Superweapon"],
                 "China": ["Vanilla", "Tank", "Infantry", "Nuclear"],
                 "GLA": ["Vanilla", "Toxin", "Stealth", "Demolition"]}[faction]
        self.general.blockSignals(True)
        self.general.clear()
        for internal in order:
            image = self.assets.get_icon(GENERAL_ICONS[faction][internal]) if self.assets else None
            if image:
                self.general.addItem(QIcon(str(image)), tr(GENERAL_KEYS[internal]), internal)
            else:
                self.general.addItem(tr(GENERAL_KEYS[internal]), internal)
        self.general.blockSignals(False)
        self._refresh_producers()

    def _filtered(self) -> list[CommandContext]:
        if not self.db:
            return []
        return [c for c in self.db.contexts if c.faction == self.faction and c.general == self._current_general()]

    def _current_general(self) -> str:
        return self.general.currentData() or "Vanilla"

    def _refresh_producers(self) -> None:
        contexts = self._filtered()
        preferred_names = ("Worker", "Dozer", "Command Center", "Barracks", "War Factory", "Arms Dealer",
                           "Airfield", "Strategy Center", "Propaganda Center", "Palace", "Black Market",
                           "Supply Center", "Supply Stash")
        def producer_order(name: str) -> tuple[int, str]:
            if name in ACTION_GROUP_KEYS:
                return list(ACTION_GROUP_KEYS).index(name), name
            if name == "General Powers":
                return 1000, name
            return 10 + next((index for index, token in enumerate(preferred_names)
                              if token.casefold() in name.casefold()), 99), name
        producers = sorted({c.producer_name for c in contexts}, key=producer_order)
        self.producer_list.blockSignals(True)
        self.producer_list.clear()
        for producer in producers:
            if producer in ACTION_GROUP_KEYS:
                display_producer = tr(ACTION_GROUP_KEYS[producer])
            else:
                display_producer = tr("general_powers") if producer == "General Powers" else producer
            item = QListWidgetItem(display_producer)
            item.setData(Qt.ItemDataRole.UserRole, producer)
            context = next((c for c in contexts if c.producer_name == producer), None)
            obj = self.db.objects.get(context.producer_id) if context else None
            if context and context.producer_id == "__general_powers__":
                image_id = GENERAL_ICONS[context.faction][context.general]
            elif context and producer in ACTION_GROUP_KEYS:
                image_id = context.button.button_image
            else:
                image_id = obj.fields.get("ButtonImage", "") if obj else ""
            icon_path = self.assets.get_icon(image_id) if self.assets and image_id else None
            if icon_path:
                item.setIcon(QIcon(str(icon_path)))
            self.producer_list.addItem(item)
        self.producer_list.blockSignals(False)
        if producers:
            self.producer_list.setCurrentRow(0)
            self._producer_selected(producers[0])

    def _producer_item_selected(self, item, _previous=None) -> None:
        if item:
            self._producer_selected(item.data(Qt.ItemDataRole.UserRole) or item.text())

    def _producer_selected(self, producer: str) -> None:
        if not producer or not self.hotkeys:
            return
        contexts = [c for c in self._filtered() if c.producer_name == producer]
        display_producer = tr(ACTION_GROUP_KEYS[producer]) if producer in ACTION_GROUP_KEYS else producer
        self.breadcrumb.setText(f"{self.faction}  →  {self.general.currentText()}  →  {display_producer}")
        self.grid.populate(contexts, self.hotkeys.get_hotkey, self.developer)
        self.current_context = None
        self.capture_active = False
        self.linked_label.clear()
        self._update_keyboard()

    def _begin_capture(self, context: CommandContext) -> None:
        self.current_context = context
        self.capture_active = True
        self.grid.select(context.identity)
        current = self.hotkeys.get_hotkey(context) if self.hotkeys else None
        self.capture_label.setText(tr("current_capture", key=current or tr("none")))
        linked = self.hotkeys.get_linked_commands(context) if self.hotkeys else []
        if len(linked) > 1:
            names = sorted({c.display_name for c in linked})
            self.linked_label.setText(tr("shared", count=len(linked), names=', '.join(names[:6])))
        else:
            self.linked_label.clear()
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def keyPressEvent(self, event) -> None:
        if self.capture_active:
            if event.key() == Qt.Key.Key_Escape:
                self._cancel_capture()
                return
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
                self._assign_key("")
                return
            text = event.text().upper()
            if text in VALID_KEYS:
                self._assign_key(text)
                return
        super().keyPressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if (self.capture_active and self.isActiveWindow()
                and event.type() == QEvent.Type.MouseButtonPress):
            mouse_keys = {
                Qt.MouseButton.MiddleButton: "M3",
                Qt.MouseButton.XButton1: "M4",
                Qt.MouseButton.XButton2: "M5",
            }
            if key := mouse_keys.get(event.button()):
                self._assign_key(key)
                return True
        if self.capture_active and self.isActiveWindow() and event.type() == QEvent.Type.KeyPress:
            if event.isAutoRepeat():
                return True
            if event.key() == Qt.Key.Key_Escape:
                self._cancel_capture()
                return True
            if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
                self._assign_key("")
                return True
            text = event.text().upper()
            if text in VALID_KEYS:
                self._assign_key(text)
                return True
        return super().eventFilter(watched, event)

    def _assign_key(self, key: str) -> None:
        if not self.capture_active or not self.current_context or not self.hotkeys:
            return
        key_or_none = key or None
        try:
            conflicts = self.hotkeys.get_conflicts(self.current_context, key) if key else []
            if conflicts:
                decision = ask_conflict(self, key, conflicts)
                if decision != "replace":
                    if decision == "cancel":
                        self._cancel_capture()
                    return
                for conflict in conflicts:
                    self.hotkeys.set_hotkey(conflict, None)
            self.hotkeys.set_hotkey(self.current_context, key_or_none)
        except (ValueError, KeyError) as exc:
            QMessageBox.warning(self, tr("cannot_assign"), str(exc))
            return
        self._cancel_capture()
        self._refresh_after_change()

    def _cancel_capture(self) -> None:
        self.capture_active = False
        self.grid.select(None)
        self.capture_label.setText(tr("select_command"))
        self.linked_label.clear()

    def _refresh_after_change(self) -> None:
        if not self.hotkeys:
            return
        self.grid.refresh_keys(self.hotkeys.get_hotkey)
        count = len(self.hotkeys.pending) + len(self.command_map_pending)
        self.unsaved.setText(tr("unsaved", count=count))
        self.apply_action.setEnabled(bool(count))
        self._update_keyboard()

    def _update_keyboard(self) -> None:
        if not self.hotkeys:
            return
        states = {key: "unused" for key in VALID_BINDINGS}
        details = {key: [] for key in VALID_BINDINGS}
        for context in self._filtered():
            if key := self.hotkeys.get_hotkey(context):
                states[key] = "used"
                details[key].append(f"{context.display_name} — {context.producer_name}")
        if self.command_map:
            for binding in self.command_map.bindings:
                key = binding.key.removeprefix("KEY_")
                if binding.modifiers == "NONE" and key in VALID_KEYS:
                    name = (self.csf.get(binding.display_label) or binding.id).replace("&", "")
                    details[key].append(f"{name} — Global")
                    states[key] = "conflict" if len(details[key]) > 1 else "reserved"
        self.keyboard.update_usage(states, details, self.theme_name, self.faction)

    def _show_key_context_menu(self, key: str, position) -> None:
        if not self.hotkeys:
            return
        menu = QMenu(self)
        title = menu.addAction(tr("bindings_for_key", key=key))
        title.setEnabled(False)
        menu.addSeparator()

        csf_bindings: list[CommandContext] = []
        seen_labels: set[str] = set()
        for context in self.hotkeys.contexts:
            label = context.button.text_label.casefold()
            if not label or label in seen_labels or self.hotkeys.get_hotkey(context) != key:
                continue
            seen_labels.add(label)
            csf_bindings.append(context)
            action = menu.addAction(
                tr("remove_named_binding", name=context.display_name,
                   location=f"{context.faction} / {context.general} / {context.producer_name}")
            )
            action.triggered.connect(lambda _checked=False, item=context: self._remove_csf_binding(item))

        global_bindings = []
        if self.command_map:
            global_bindings = [item for item in self.command_map.bindings if item.key == f"KEY_{key}"]
            for binding in global_bindings:
                name = (self.csf.get(binding.display_label) or binding.id).replace("&", "")
                action = menu.addAction(
                    tr("remove_named_binding", name=name,
                       location=tr("global_binding_location", shortcut=binding.shortcut))
                )
                action.triggered.connect(lambda _checked=False, item=binding: self._remove_global_binding(item))

        if not csf_bindings and not global_bindings:
            empty = menu.addAction(tr("no_bindings_for_key"))
            empty.setEnabled(False)
        else:
            menu.addSeparator()
            clear = menu.addAction(tr("clear_key_bindings", key=key))
            clear.triggered.connect(lambda _checked=False, value=key: self._clear_key_bindings(value))
        menu.exec(position)

    def _remove_csf_binding(self, context: CommandContext) -> None:
        if not self.hotkeys:
            return
        self.hotkeys.set_hotkey(context, None)
        self._refresh_after_change()

    def _remove_global_binding(self, binding) -> None:
        binding.key, binding.modifiers = "KEY_NONE", "NONE"
        self.command_map_pending.add(binding.id.casefold())
        self._refresh_after_change()

    def _clear_key_bindings(self, key: str) -> None:
        if not self.hotkeys:
            return
        answer = QMessageBox.question(
            self,
            tr("clear_key_bindings", key=key),
            tr("clear_key_bindings_text", key=key),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.hotkeys.clear_key(key)
        if self.command_map:
            for binding in self.command_map.bindings:
                if binding.key == f"KEY_{key}":
                    binding.key, binding.modifiers = "KEY_NONE", "NONE"
                    self.command_map_pending.add(binding.id.casefold())
        self._refresh_after_change()

    def undo(self) -> None:
        if self.hotkeys and self.hotkeys.undo():
            self._refresh_after_change()

    def redo(self) -> None:
        if self.hotkeys and self.hotkeys.redo():
            self._refresh_after_change()

    def clear_all_bindings(self) -> None:
        if not self.hotkeys:
            return
        answer = QMessageBox.question(
            self,
            tr("clear_all_bindings"),
            tr("clear_all_bindings_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        count = self.hotkeys.clear_all()
        self._cancel_capture()
        self._refresh_after_change()
        self.statusBar().showMessage(tr("bindings_cleared", count=count), 5000)

    def apply_changes(self) -> None:
        if not self.hotkeys or (not self.hotkeys.pending and not self.command_map_pending):
            return
        recovery_files = {}
        if self.hotkeys.pending:
            recovery_files["generals.csf"] = self.hotkeys.materialize().to_bytes()
        if self.command_map_pending and self.command_map:
            recovery_files["CommandMap.ini"] = self.command_map.to_text().encode("utf-8")
        try:
            backups = []
            if self.hotkeys.pending:
                backups.append(self._apply_csf_changes())
            if self.command_map_pending and self.command_map:
                target = self.game_dir / "Data/English/CommandMap.ini"
                backups.append(self.command_map_backups.create(target, self.command_map_source))
                data = self.command_map.to_text().encode("utf-8")
                self.command_map_backups.atomic_write(target, data)
                self.command_map_source = data
                self.command_map_pending.clear()
            self._refresh_after_change()
            logging.info("Applied hotkey changes; backups %s", backups)
            QMessageBox.information(self, tr("applied"), tr("applied_text", backup="\n".join(map(str, backups))))
        except Exception as exc:
            logging.exception("Apply failed")
            if is_access_error(exc):
                self.handle_write_access_error(exc, recovery_files)
            else:
                QMessageBox.critical(self, tr("apply_failed"), tr("apply_failed_text", error=exc))

    def handle_write_access_error(self, error: Exception, files: dict[str, bytes]) -> None:
        """Offer elevation and retain install-ready files for manual recovery."""
        try:
            package = create_recovery_package(self.app_root, self.game_dir, files)
        except Exception as package_error:
            logging.exception("Could not create manual config package")
            QMessageBox.critical(
                self, tr("apply_failed"), tr("apply_failed_text", error=package_error),
            )
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr("write_access_denied"))
        box.setText(tr(
            "write_access_denied_admin_text" if is_running_as_admin() else "write_access_denied_text",
            game=self.game_dir, error=error,
        ))
        admin_button = None
        if not is_running_as_admin():
            admin_button = box.addButton(tr("restart_as_admin"), QMessageBox.ButtonRole.AcceptRole)
        manual_button = box.addButton(tr("save_for_manual_copy"), QMessageBox.ButtonRole.ActionRole)
        box.addButton(tr("cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()

        if admin_button is not None and box.clickedButton() is admin_button:
            try:
                if restart_as_admin(package):
                    QApplication.quit()
                    return
            except Exception:
                logging.exception("Could not restart as administrator")
            self._show_manual_copy(package, error)
        elif box.clickedButton() is manual_button:
            self._show_manual_copy(package, error)

    def _show_manual_copy(self, package: Path, error: Exception) -> None:
        instructions = manual_copy_instructions(package)
        QMessageBox.information(
            self, tr("manual_config_saved"),
            tr("manual_copy_text", folder=package, files=instructions, error=error),
        )
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(package)))

    def _apply_csf_changes(self) -> Path:
        if not self.hotkeys or not self.hotkeys.pending:
            raise RuntimeError("No pending CSF hotkey changes")
        target = self.game_dir / "Data/English/generals.csf"
        backup = self.backups.create(target, self.source_csf)
        data = self.hotkeys.materialize().to_bytes()
        self.backups.atomic_write(target, data)
        self.mouse_binding_store.save(self.hotkeys.mouse_bindings, self.hotkeys.mouse_keys)
        self.mouse_proxy_keys = dict(self.hotkeys.mouse_keys)
        self.applied_mouse_proxy_keys = dict(self.hotkeys.mouse_keys)
        for button, key in self.mouse_proxy_keys.items():
            self.settings.setValue(f"mouseProxy{button}", key)
        self._sync_mouse_remapper()
        self.hotkeys.pending.clear()
        self.hotkeys.undo_stack.clear()
        self.hotkeys.redo_stack.clear()
        return backup

    def restore_latest(self) -> None:
        latest = self.backups.latest()
        if not latest:
            QMessageBox.information(self, tr("restore"), tr("no_backup"))
            return
        try:
            target = self.game_dir / "Data/English/generals.csf"
            self.backups.create(target, self.source_csf)
            self.backups.restore(latest, target)
            if self.hotkeys:
                self.hotkeys.mouse_bindings.clear()
                self.mouse_binding_store.save({}, self.applied_mouse_proxy_keys)
                self._sync_mouse_remapper()
            QMessageBox.information(self, tr("restored"), tr("latest_restored"))
        except Exception as exc:
            QMessageBox.critical(self, tr("restore_failed"), str(exc))

    def restore_original(self) -> None:
        target = self.game_dir / "Data/English/generals.csf"
        if not target.exists():
            QMessageBox.information(self, tr("restore_original"), tr("already_original"))
            return
        try:
            self.backups.create(target)
            target.unlink()
            if self.hotkeys:
                self.hotkeys.mouse_bindings.clear()
                self.mouse_binding_store.save({}, self.applied_mouse_proxy_keys)
                self._sync_mouse_remapper()
            QMessageBox.information(self, tr("restored"), tr("original_restored"))
        except Exception as exc:
            QMessageBox.critical(self, tr("restore_failed"), str(exc))

    def save_profile(self) -> None:
        if not self.hotkeys or not self.db:
            return
        name, ok = QInputDialog.getText(self, tr("save_profile"), tr("profile_name"))
        if not ok or not name.strip():
            return
        bindings = {c.button.text_label: self.hotkeys.get_hotkey(c) for c in self.db.contexts if c.button.text_label}
        try:
            path = self.profiles.save(Profile(name.strip(), bindings))
            self.statusBar().showMessage(tr("profile_saved", name=path.name), 5000)
        except Exception as exc:
            QMessageBox.warning(self, tr("profile"), str(exc))

    def load_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("load_profile"), str(self.profiles.directory), tr("json_profiles"))
        if not path or not self.hotkeys or not self.db:
            return
        try:
            profile = self.profiles.load(path)
            by_label = {}
            for context in self.db.contexts:
                by_label.setdefault(context.button.text_label.casefold(), context)
            for label, key in profile.bindings.items():
                context = by_label.get(label.casefold())
                if context and self.hotkeys.get_hotkey(context) != key:
                    try:
                        self.hotkeys.set_hotkey(context, key)
                    except ValueError:
                        logging.warning("Profile key %r cannot be represented in label %s", key, label)
            self._refresh_after_change()
        except Exception as exc:
            QMessageBox.warning(self, tr("profile"), str(exc))

    def manage_profiles(self) -> None:
        dialog = ProfileDialog(self.profiles, self)
        if dialog.exec() and dialog.selected_path:
            self._apply_profile_path(dialog.selected_path)

    def _apply_profile_path(self, path: Path) -> None:
        if not self.hotkeys or not self.db:
            return
        try:
            profile = self.profiles.load(path)
            by_label = {}
            for context in self.db.contexts:
                by_label.setdefault(context.button.text_label.casefold(), context)
            for label, key in profile.bindings.items():
                context = by_label.get(label.casefold())
                if context and self.hotkeys.get_hotkey(context) != key:
                    try:
                        self.hotkeys.set_hotkey(context, key)
                    except ValueError:
                        logging.warning("Profile key %r cannot be represented in label %s", key, label)
            self._refresh_after_change()
        except Exception as exc:
            QMessageBox.warning(self, tr("profile"), str(exc))

    def show_settings(self) -> None:
        dialog = SettingsDialog(str(self.game_dir), self.developer, self.language, self.theme_name,
                                self.mouse_remapping_enabled, self.mouse_proxy_keys, self)
        if dialog.exec():
            proxy_keys = dialog.proxy_keys()
            if len(set(proxy_keys.values())) != len(proxy_keys):
                QMessageBox.warning(self, tr("mouse_remapping"), tr("mouse_proxy_duplicate"))
                return
            self.developer = dialog.developer.isChecked()
            self.language = dialog.language.currentData()
            self.theme_name = dialog.theme.currentData()
            self.mouse_remapping_enabled = dialog.mouse_remapping.isChecked()
            self.mouse_proxy_keys = proxy_keys
            if self.hotkeys:
                self.hotkeys.set_mouse_proxy_keys(proxy_keys)
            self.settings.setValue("developerMode", self.developer)
            self.settings.setValue("language", self.language)
            self.settings.setValue("theme", self.theme_name)
            self.settings.setValue("mouseRemapping", self.mouse_remapping_enabled)
            if not self.hotkeys or not self.hotkeys.pending:
                self.applied_mouse_proxy_keys = dict(proxy_keys)
                self.mouse_binding_store.save(
                    self.hotkeys.mouse_bindings if self.hotkeys else {}, proxy_keys
                )
                for button, key in proxy_keys.items():
                    self.settings.setValue(f"mouseProxy{button}", key)
            self._refresh_after_change()
            self._sync_mouse_remapper()
            set_language(self.language)
            QApplication.instance().setStyleSheet(style_for(self.theme_name, self.faction))
            current_faction = self.faction
            current_general = self._current_general()
            self._retranslate()
            self.select_faction(current_faction)
            index = self.general.findData(current_general)
            if index >= 0:
                self.general.setCurrentIndex(index)
            current_item = self.producer_list.currentItem()
            self._producer_selected((current_item.data(Qt.ItemDataRole.UserRole) or current_item.text())
                                    if current_item else "")

    def _sync_mouse_remapper(self) -> None:
        if not self.hotkeys:
            return
        used = {
            binding for context in self.hotkeys.contexts
            if (binding := self.hotkeys.get_hotkey(context)) in MOUSE_BUTTONS
        }
        mapping = {
            button: proxy for button, proxy in self.applied_mouse_proxy_keys.items()
            if button in used
        }
        self.mouse_remapper.update(mapping, self.mouse_remapping_enabled)

    def closeEvent(self, event) -> None:
        self.mouse_remapper.stop()
        super().closeEvent(event)

    def show_global_hotkeys(self) -> None:
        if not self.command_map_source or not self.csf or not self.assets:
            return
        source = (self.command_map.to_text().encode("utf-8")
                  if self.command_map and self.command_map_pending else self.command_map_source)
        dialog = GlobalHotkeysDialog(source, self.csf, self.assets, self.db, self.hotkeys,
                                     self.game_dir, self.app_root, self._apply_csf_changes, self)
        dialog.exec()
        loose = self.game_dir / "Data/English/CommandMap.ini"
        if dialog.applied and loose.is_file():
            self.command_map_source = loose.read_bytes()
            self.command_map = CommandMapFile.parse(
                self.command_map_source.decode("utf-8-sig", errors="replace")
            )
            self.command_map_pending.clear()
        self._refresh_after_change()

    def _retranslate(self) -> None:
        self.search.setPlaceholderText(tr("search"))
        self.capture_label.setText(tr("select_command"))
        self.unsaved.setText(tr("unsaved", count=len(self.hotkeys.pending) if self.hotkeys else 0))
        self.apply_action.setText(tr("apply"))
        self.undo_action.setText(tr("undo"))
        self.redo_action.setText(tr("redo"))
        self.clear_all_action.setText(tr("clear_all_bindings"))
        self.profile_action.setText(tr("save_profile"))
        self.load_profile_action.setText(tr("manage_profiles"))
        self.settings_action.setText(tr("settings"))
        self.global_action.setText(tr("global_hotkeys"))
        self.file_menu.setTitle(tr("file"))
        self.profile_menu.setTitle(tr("profiles"))
        self.restore_latest_action.setText(tr("restore_latest"))
        self.restore_original_action.setText(tr("restore_original"))
        self.open_backup_action.setText(tr("open_backup"))

    def _update_search(self, query: str) -> None:
        if not self.db:
            return
        query = query.strip().casefold()
        self.search_results.clear()
        self.context_by_search_row = []
        if not query:
            self.search_results.hide()
            return
        seen = set()
        for context in self.db.contexts:
            haystack = f"{context.display_name} {context.producer_name} {context.button.id} {context.button.object_id}".casefold()
            if query in haystack and context.identity not in seen:
                key = self.hotkeys.get_hotkey(context) if self.hotkeys else None
                self.search_results.addItem(f"{context.faction} • {context.general} • {context.producer_name} • {context.display_name} [{key or '—'}]")
                self.context_by_search_row.append(context)
                seen.add(context.identity)
                if len(self.context_by_search_row) >= 40:
                    break
        self.search_results.setVisible(bool(self.context_by_search_row))

    def _open_search_result(self, item) -> None:
        row = self.search_results.row(item)
        if row < 0 or row >= len(self.context_by_search_row):
            return
        context = self.context_by_search_row[row]
        self.select_faction(context.faction)
        self.general.setCurrentText(context.general)
        self.producer_list.setCurrentItem(next((self.producer_list.item(i) for i in range(self.producer_list.count())
                                                if (self.producer_list.item(i).data(Qt.ItemDataRole.UserRole)
                                                    or self.producer_list.item(i).text()) == context.producer_name), None))
        self._producer_selected(context.producer_name)
        self.grid.select(context.identity)
        self.search.clear()
