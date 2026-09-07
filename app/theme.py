from __future__ import annotations

THEMES = {"dark": "Modern Dark", "zero_hour": "Zero Hour", "light": "Light"}
_BASE = '''
QMainWindow, QDialog, QWidget { font-family: "Segoe UI"; font-size: 10pt; }
QToolBar { border: none; padding: 6px; spacing: 6px; }
QPushButton, QToolButton, QComboBox, QLineEdit { border-radius: 6px; padding: 7px 10px; }
QPushButton:disabled { color: #77818a; }
QListWidget { border-radius: 8px; padding: 4px; }
QListWidget::item { padding: 9px; border-radius: 5px; }
QScrollArea { border: none; }
QProgressBar { border-radius: 6px; text-align: center; }
QFrame#commandCard[selected="true"] { border: 2px solid #e7bd5d; }
QLabel { background: transparent; }
QLabel#commandHotkey { font-size: 15pt; font-weight: 700; }
QLabel#commandFallbackIcon { font-size: 30pt; }
'''
DARK_STYLE = _BASE + '''
QMainWindow, QDialog, QWidget { background: #121820; color: #e8edf2; }
QToolBar, QStatusBar { background: #18212b; color: #aebdca; }
QPushButton, QToolButton, QComboBox, QLineEdit { background: #202b36; border: 1px solid #344353; }
QPushButton:hover, QToolButton:hover { border-color: #6f8ca8; background: #263544; }
QPushButton:checked { background: #315574; border-color: #72a7d2; }
QLineEdit:focus, QComboBox:focus { border-color: #75a7ce; }
QListWidget { background: #151d26; border: 1px solid #293746; }
QListWidget::item:selected { background: #29465e; }
QProgressBar { border: 1px solid #344353; background: #1a222c; }
QProgressBar::chunk { background: #4f88b3; border-radius: 5px; }
QFrame#commandCard { background:#1b2530; border:2px solid #344353; border-radius:9px; }
QLabel#commandHotkey { color: #f1c76a; }
QLabel#commandFallbackIcon, QLabel#captureHint { color: #aebdca; }
QLabel#linkedHint { color: #d9bd78; }
'''
LIGHT_STYLE = _BASE + '''
QMainWindow, QDialog, QWidget { background: #f3f6f8; color: #18242e; }
QToolBar, QStatusBar { background: #dfe7ec; color: #263946; border-bottom: 1px solid #aab9c4; }
QPushButton, QToolButton, QComboBox, QLineEdit {
    background: #ffffff; color: #18242e; border: 1px solid #879aa8;
}
QPushButton:hover, QToolButton:hover { background: #eaf3f8; border-color: #466f8b; }
QPushButton:checked { background: #b9d9ed; color: #102f43; border: 2px solid #3f779c; }
QPushButton:disabled { background: #e5eaee; color: #687985; border-color: #bac5cc; }
QLineEdit:focus, QComboBox:focus { border: 2px solid #477d9f; }
QComboBox QAbstractItemView { background: #ffffff; color: #18242e; selection-background-color: #b9d9ed; }
QListWidget { background: #ffffff; color: #18242e; border: 1px solid #9cabb6; }
QListWidget::item:hover { background: #edf4f8; }
QListWidget::item:selected { background: #b9d9ed; color: #102f43; }
QProgressBar { border: 1px solid #879aa8; background: #ffffff; color: #18242e; }
QProgressBar::chunk { background: #518caf; }
QFrame#commandCard { background:#ffffff; border:2px solid #9cabb6; border-radius:9px; }
QFrame#commandCard:hover { border-color: #477d9f; background: #f7fbfd; }
QFrame#commandCard[selected="true"] { border-color: #b07814; background: #fff5d9; }
QLabel#commandHotkey { color: #795000; }
QLabel#commandFallbackIcon, QLabel#captureHint { color: #526979; }
QLabel#linkedHint { color: #76520b; }
'''
STYLES = {"dark": DARK_STYLE, "light": LIGHT_STYLE}
FACTION_ACCENTS = {"USA": "#4d86b8", "China": "#a84d4d", "GLA": "#6f8e55"}

_ZERO_HOUR_PALETTES = {
    "USA": {
        "background": "#061116", "panel": "#071d25", "panel_alt": "#0b2b35",
        "metal": "#82969b", "metal_dark": "#344b50", "accent": "#d7a53e",
        "hover": "#124653", "selected": "#16566a", "text": "#edf4ee",
    },
    "China": {
        "background": "#160907", "panel": "#2a100c", "panel_alt": "#42170f",
        "metal": "#89745e", "metal_dark": "#4c392d", "accent": "#d73a27",
        "hover": "#5b2116", "selected": "#76281b", "text": "#f3e7d7",
    },
    "GLA": {
        "background": "#071008", "panel": "#0b1b0d", "panel_alt": "#142b16",
        "metal": "#82765f", "metal_dark": "#463f31", "accent": "#c98d34",
        "hover": "#234324", "selected": "#315932", "text": "#eee7cf",
    },
}


def zero_hour_style(faction: str) -> str:
    p = _ZERO_HOUR_PALETTES.get(faction, _ZERO_HOUR_PALETTES["USA"])
    return _BASE + f'''
QMainWindow, QDialog {{
    background: {p["background"]}; color: {p["text"]};
}}
QWidget {{ background: {p["background"]}; color: {p["text"]}; }}
QLabel {{ background: transparent; }}
QToolBar, QStatusBar, QMenuBar {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {p["metal"]}, stop:0.12 {p["metal_dark"]}, stop:0.22 {p["panel"]}, stop:1 {p["background"]});
    border-top: 1px solid {p["metal"]}; border-bottom: 2px solid {p["metal_dark"]};
    color: {p["text"]}; padding: 5px;
}}
QPushButton, QToolButton, QComboBox, QLineEdit {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {p["panel_alt"]}, stop:0.48 {p["panel"]}, stop:1 {p["background"]});
    color: {p["text"]}; border: 2px solid {p["metal_dark"]};
    border-top-color: {p["metal"]}; border-left-color: {p["metal"]};
    border-radius: 1px; padding: 7px 10px;
}}
QPushButton:hover, QToolButton:hover, QComboBox:hover {{
    background: {p["hover"]}; border-color: {p["accent"]};
}}
QPushButton:pressed, QToolButton:pressed {{ border-top-color: {p["metal_dark"]}; border-left-color: {p["metal_dark"]}; }}
QPushButton:checked {{ background: {p["selected"]}; border: 2px solid {p["accent"]}; color: #ffffff; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {p["accent"]}; }}
QComboBox::drop-down {{ border-left: 1px solid {p["metal_dark"]}; width: 25px; }}
QComboBox QAbstractItemView {{ background: {p["panel"]}; border: 2px solid {p["metal"]}; selection-background-color: {p["selected"]}; }}
QListWidget, QTreeWidget, QScrollArea {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {p["panel_alt"]}, stop:0.03 {p["panel"]}, stop:1 {p["background"]});
    border: 2px solid {p["metal_dark"]}; border-top-color: {p["metal"]}; border-left-color: {p["metal"]}; border-radius: 1px;
}}
QListWidget::item {{ border: 1px solid transparent; padding: 8px; }}
QListWidget::item:hover {{ background: {p["hover"]}; border-color: {p["metal_dark"]}; }}
QListWidget::item:selected {{ background: {p["selected"]}; border: 1px solid {p["accent"]}; color: #ffffff; }}
QFrame#commandCard {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {p["panel_alt"]}, stop:0.12 {p["panel"]}, stop:1 {p["background"]});
    border: 2px solid {p["metal_dark"]}; border-top-color: {p["metal"]}; border-left-color: {p["metal"]}; border-radius: 1px;
}}
QFrame#commandCard:hover {{ border-color: {p["accent"]}; background: {p["hover"]}; }}
QFrame#commandCard[selected="true"] {{ border: 3px solid {p["accent"]}; background: {p["selected"]}; }}
QLabel#commandHotkey, QLabel#linkedHint {{ color: {p["accent"]}; }}
QLabel#commandFallbackIcon, QLabel#captureHint {{ color: {p["metal"]}; }}
QMenu {{ background: {p["panel"]}; color: {p["text"]}; border: 2px solid {p["metal"]}; padding: 3px; }}
QMenu::item {{ padding: 6px 24px 6px 10px; border: 1px solid transparent; }}
QMenu::item:selected {{ background: {p["selected"]}; border-color: {p["accent"]}; }}
QMenu::separator {{ height: 1px; background: {p["metal_dark"]}; margin: 4px; }}
QProgressBar {{ border: 2px solid {p["metal_dark"]}; background: {p["background"]}; border-radius: 1px; text-align: center; }}
QProgressBar::chunk {{ background: {p["accent"]}; }}
QSplitter::handle {{ background: {p["metal_dark"]}; width: 2px; }}
QScrollBar:vertical {{ background: {p["background"]}; width: 14px; }}
QScrollBar::handle:vertical {{ background: {p["metal_dark"]}; border: 1px solid {p["metal"]}; min-height: 24px; }}
'''


def style_for(name: str, faction: str = "USA") -> str:
    if name == "zero_hour":
        return zero_hour_style(faction)
    return STYLES.get(name, DARK_STYLE)
