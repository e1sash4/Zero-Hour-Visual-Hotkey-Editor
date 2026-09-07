from core.command_map import CommandMapFile


SOURCE = """CommandMap SELECT_ALL
  Key = KEY_Q
  Transition = DOWN
  Modifiers = NONE
  UseableIn = GAME
  Category = SELECTION
  DisplayName = GUI:SelectAll
  Description = GUI:SelectAllDescription
End

CommandMap OTHER
  Key = KEY_Q
  Transition = DOWN
  Modifiers = CTRL
  UseableIn = GAME
End
"""


def test_command_map_parse_edit_roundtrip_and_conflicts():
    parsed = CommandMapFile.parse(SOURCE)
    assert [item.shortcut for item in parsed.bindings] == ["Q", "Ctrl+Q"]
    first, second = parsed.bindings
    assert parsed.conflicts(first, "KEY_Q", "NONE") == []
    second.modifiers = "NONE"
    assert parsed.conflicts(first, "KEY_Q", "NONE") == [second]
    first.key = "KEY_W"
    reparsed = CommandMapFile.parse(parsed.to_text())
    assert reparsed.bindings[0].shortcut == "W"
