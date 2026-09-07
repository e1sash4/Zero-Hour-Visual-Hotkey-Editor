from models import CommandButton, CommandContext
from core.csf_parser import CsfFile, CsfLabel, CsfValue
from core.hotkey_manager import HotkeyManager


def context(name, label, command_set, slot):
    return CommandContext("USA", "Vanilla", "Factory", "War Factory", command_set, slot,
                          CommandButton(name, text_label=label), display_name=name)


def test_conflicts_are_scoped_to_command_set_and_shared_labels_are_linked():
    first = context("Humvee", "HUMVEE", "WarFactory", 1)
    conflict = context("Crusader", "CRUSADER", "WarFactory", 2)
    safe = context("Ranger", "RANGER", "Barracks", 1)
    linked = context("AirF Humvee", "HUMVEE", "AirFFactory", 1)
    csf = CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("&Humvee")]),
                          CsfLabel("CRUSADER", [CsfValue("&Crusader")]),
                          CsfLabel("RANGER", [CsfValue("&Ranger")])])
    manager = HotkeyManager(csf, [first, conflict, safe, linked])
    manager.set_hotkey(conflict, "H")
    assert manager.get_conflicts(first, "H") == [conflict]
    assert safe not in manager.get_conflicts(first, "R")
    assert manager.get_linked_commands(first) == [first, linked]


def test_undo_redo():
    item = context("Humvee", "HUMVEE", "Factory", 1)
    manager = HotkeyManager(CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("Hum&vee")])]), [item])
    manager.set_hotkey(item, "H")
    assert manager.get_hotkey(item) == "H"
    assert manager.undo() and manager.get_hotkey(item) == "V"
    assert manager.redo() and manager.get_hotkey(item) == "H"


def test_mouse_binding_uses_proxy_key_and_survives_reload():
    item = context("Humvee", "HUMVEE", "Factory", 1)
    csf = CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("Humvee")])])
    manager = HotkeyManager(csf, [item])

    manager.set_hotkey(item, "M4")
    assert manager.get_hotkey(item) == "M4"
    data = manager.materialize().to_bytes()
    assert manager.mouse_bindings == {"humvee": "M4"}

    restored = HotkeyManager(CsfFile.from_bytes(data), [item], manager.mouse_bindings)
    assert restored.get_hotkey(item) == "M4"


def test_mouse_proxy_conflicts_with_its_underlying_keyboard_key():
    mouse = context("Humvee", "HUMVEE", "Factory", 1)
    keyboard = context("Ranger", "RANGER", "Factory", 2)
    manager = HotkeyManager(
        CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("Humvee")]),
                        CsfLabel("RANGER", [CsfValue("Ranger (&8)")])]),
        [mouse, keyboard],
    )

    assert manager.get_conflicts(mouse, "M4") == [keyboard]


def test_mouse_proxy_keys_can_be_changed_and_are_rewritten():
    item = context("Humvee", "HUMVEE", "Factory", 1)
    csf = CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("Humvee (&8)")])])
    manager = HotkeyManager(csf, [item], {"humvee": "M4"})

    manager.set_mouse_proxy_keys({"M3": "4", "M4": "5", "M5": "6"})

    assert manager.get_hotkey(item) == "M4"
    manager.materialize()
    assert manager.csf.get("HUMVEE").endswith("(&5)")


def test_clear_all_is_one_undoable_action_and_deduplicates_shared_labels():
    humvee = context("Humvee", "HUMVEE", "Factory", 1)
    linked_humvee = context("AirF Humvee", "HUMVEE", "AirFFactory", 1)
    ranger = context("Ranger", "RANGER", "Barracks", 1)
    manager = HotkeyManager(
        CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("&Humvee")]),
                        CsfLabel("RANGER", [CsfValue("&Ranger")])]),
        [humvee, linked_humvee, ranger],
    )

    assert manager.clear_all() == 2
    assert manager.get_hotkey(humvee) is None
    assert manager.get_hotkey(linked_humvee) is None
    assert manager.get_hotkey(ranger) is None
    assert manager.undo()
    assert manager.get_hotkey(humvee) == "H"
    assert manager.get_hotkey(ranger) == "R"
    assert manager.redo()
    assert manager.get_hotkey(humvee) is None
    assert manager.get_hotkey(ranger) is None


def test_clear_key_only_clears_matching_key_as_one_action():
    humvee = context("Humvee", "HUMVEE", "Factory", 1)
    crusader = context("Crusader", "CRUSADER", "Factory", 2)
    ranger = context("Ranger", "RANGER", "Barracks", 1)
    manager = HotkeyManager(
        CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue("&Humvee")]),
                        CsfLabel("CRUSADER", [CsfValue("&Heavy tank")]),
                        CsfLabel("RANGER", [CsfValue("&Ranger")])]),
        [humvee, crusader, ranger],
    )

    assert manager.clear_key("H") == 2
    assert manager.get_hotkey(humvee) is None
    assert manager.get_hotkey(crusader) is None
    assert manager.get_hotkey(ranger) == "R"
    assert manager.undo()
    assert manager.get_hotkey(humvee) == "H"
    assert manager.get_hotkey(crusader) == "H"
