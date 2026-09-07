from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit

from app.i18n import LANGUAGES, tr
from core.hotkey_manager import MOUSE_BUTTONS, VALID_KEYS
from app.theme import THEMES


class SettingsDialog(QDialog):
    def __init__(self, game_path: str, developer: bool, language: str, theme: str,
                 mouse_remapping: bool, mouse_proxy_keys: dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings"))
        layout = QFormLayout(self)
        self.path = QLineEdit(game_path)
        self.path.setReadOnly(True)
        self.developer = QCheckBox(tr("developer_hint"))
        self.developer.setChecked(developer)
        self.mouse_remapping = QCheckBox(tr("mouse_remapping_hint"))
        self.mouse_remapping.setChecked(mouse_remapping)
        self.mouse_note = QLabel(tr("mouse_extra_buttons_hint"))
        self.mouse_note.setWordWrap(True)
        self.mouse_proxies = {}
        key_order = "7890ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        for button in MOUSE_BUTTONS:
            combo = QComboBox()
            for key in key_order:
                if key in VALID_KEYS:
                    combo.addItem(key, key)
            combo.setCurrentIndex(max(0, combo.findData(mouse_proxy_keys[button])))
            self.mouse_proxies[button] = combo
        self.language = QComboBox()
        for code, label in LANGUAGES.items():
            self.language.addItem(label, code)
        self.language.setCurrentIndex(max(0, self.language.findData(language)))
        self.theme = QComboBox()
        for code, label in THEMES.items():
            self.theme.addItem(label, code)
        self.theme.setCurrentIndex(max(0, self.theme.findData(theme)))
        layout.addRow(tr("game_folder"), self.path)
        layout.addRow(tr("language"), self.language)
        layout.addRow(tr("theme"), self.theme)
        layout.addRow(tr("mouse_remapping"), self.mouse_remapping)
        for button, combo in self.mouse_proxies.items():
            layout.addRow(tr("mouse_proxy", button=button), combo)
        layout.addRow("", self.mouse_note)
        layout.addRow(tr("developer_mode"), self.developer)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def proxy_keys(self) -> dict[str, str]:
        return {button: combo.currentData() for button, combo in self.mouse_proxies.items()}
