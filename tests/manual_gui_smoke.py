"""Optional real-install GUI smoke check; not collected by pytest."""
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from app.i18n import set_language, tr
from app.main_window import MainWindow
import app.main_window as main_window_module
from app.theme import style_for
from ui.global_hotkeys_dialog import GlobalHotkeysDialog


def run(game_dir: str) -> int:
    app = QApplication([])
    set_language("uk")
    app.setStyleSheet(style_for("zero_hour"))
    settings = QSettings(str(Path(".build-temp/qa-settings.ini")), QSettings.Format.IniFormat)
    window = MainWindow(Path(game_dir), Path("."), settings)
    window.show()
    result = {"ok": False}

    def check(*_args) -> None:
        logos = []
        for faction in ("USA", "China", "GLA"):
            window.select_faction(faction)
            logos.append((faction, not window.faction_logo.pixmap().isNull()))
        result["ok"] = all(loaded for _, loaded in logos)
        print(f"ukrainian_language={tr('settings') == 'Налаштування'}")
        print(f"logos={logos}")
        print(f"contexts={len(window.db.contexts)}")
        window.select_faction("USA")
        producer_icons = sum(not window.producer_list.item(i).icon().isNull() for i in range(window.producer_list.count()))
        dialog = GlobalHotkeysDialog(window.command_map_source, window.csf, window.assets, window.db, window.hotkeys,
                                     window.game_dir, window.app_root, window.apply_changes, window)
        print(f"producer_icons={producer_icons}/{window.producer_list.count()}")
        print(f"global_rows={dialog.tree.topLevelItemCount()}")
        pairs = []
        for target in window.db.contexts:
            for occupied in window.db.contexts:
                if (target.command_set_id == occupied.command_set_id and target.identity != occupied.identity
                        and window.hotkeys.get_hotkey(occupied) and
                        window.hotkeys.get_hotkey(target) != window.hotkeys.get_hotkey(occupied)):
                    pairs = [target, occupied]
                    break
            if pairs:
                break
        main_window_module.ask_conflict = lambda *_args: "replace"
        target, occupied = pairs
        key = window.hotkeys.get_hotkey(occupied)
        window._begin_capture(target)
        QTest.keyClick(window.search, Qt.Key(ord(key)))
        physical_capture = window.hotkeys.get_hotkey(target) == key and window.hotkeys.get_hotkey(occupied) is None
        print(f"physical_capture_replace={physical_capture}")
        result["ok"] = result["ok"] and producer_icons > 0 and dialog.tree.topLevelItemCount() >= 90 and physical_capture
        app.quit()

    poll = QTimer()
    poll.timeout.connect(lambda: check() if window.db is not None else None)
    poll.start(100)
    QTimer.singleShot(20_000, app.quit)
    app.exec()
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(run(r"E:\SteamLibrary\steamapps\common\Command & Conquer Generals - Zero Hour"))
