from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from core.game_detector import detect_game, is_game_directory
from .i18n import set_language, tr
from .main_window import MainWindow
from .paths import data_root, resource_path
from .theme import style_for


def _configure_logging(root: Path) -> None:
    folder = root / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=folder / "app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s", encoding="utf-8")


def run() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("ZeroHourTools")
    app.setApplicationName("Zero Hour Visual Hotkey Editor")
    app.setWindowIcon(QIcon(str(resource_path("assets/app_icon.png"))))
    root = data_root()
    _configure_logging(root)
    settings = QSettings()
    set_language(settings.value("language", "uk", str))
    app.setStyleSheet(style_for(settings.value("theme", "dark", str)))
    configured = settings.value("gamePath", "", str)
    game = detect_game(configured or None)
    if not game:
        selected = QFileDialog.getExistingDirectory(None, tr("select_game"))
        if not selected or not is_game_directory(Path(selected)):
            QMessageBox.critical(None, tr("game_not_found"), tr("game_not_found_text"))
            return 1
        game = Path(selected)
    settings.setValue("gamePath", str(game))
    logging.info("Detected game directory: %s", game)
    window = MainWindow(game, root, settings)
    window.show()
    return app.exec()
