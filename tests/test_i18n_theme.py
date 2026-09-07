from app.i18n import set_language, tr
from app.main_window import FACTION_LOGOS, GENERAL_ICONS
from app.theme import style_for


def test_ukrainian_and_russian_translations():
    set_language("uk")
    assert tr("settings") == "Налаштування"
    assert tr("unsaved", count=3) == "Незбережені зміни: 3"
    set_language("ru")
    assert tr("settings") == "Настройки"
    assert tr("unsaved", count=3) == "Несохранённые изменения: 3"
    set_language("en")


def test_themes_and_faction_logo_mappings_are_complete():
    usa = style_for("zero_hour", "USA")
    china = style_for("zero_hour", "China")
    gla = style_for("zero_hour", "GLA")
    assert len({usa, china, gla}) == 3
    assert "#061116" in usa
    assert "#160907" in china
    assert "#071008" in gla
    assert "#eef1f4" in style_for("light")
    assert FACTION_LOGOS == {
        "USA": "SAFactionLogo144_US",
        "China": "SNFactionLogo144_China",
        "GLA": "SUFactionLogo144_GLA",
    }
    assert {faction: set(generals) for faction, generals in GENERAL_ICONS.items()} == {
        "USA": {"Vanilla", "Air Force", "Laser", "Superweapon"},
        "China": {"Vanilla", "Tank", "Infantry", "Nuclear"},
        "GLA": {"Vanilla", "Toxin", "Stealth", "Demolition"},
    }


def test_global_hotkey_translation_exists():
    set_language("uk")
    assert tr("global_hotkeys") == "Глобальні хоткеї…"
    set_language("en")
