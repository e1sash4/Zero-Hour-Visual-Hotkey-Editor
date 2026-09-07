from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit

from app.i18n import LANGUAGES, tr
from app.theme import THEMES


class SettingsDialog(QDialog):
    def __init__(self, game_path: str, developer: bool, language: str, theme: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings"))
        layout = QFormLayout(self)
        self.path = QLineEdit(game_path)
        self.path.setReadOnly(True)
        self.developer = QCheckBox(tr("developer_hint"))
        self.developer.setChecked(developer)
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
        layout.addRow(tr("developer_mode"), self.developer)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
