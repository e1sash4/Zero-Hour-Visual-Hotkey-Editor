from core.csf_parser import CsfFile, CsfLabel, CsfValue, extract_hotkey, set_hotkey_marker


def fixture_csf():
    return CsfFile(labels=[
        CsfLabel("CONTROLBAR:Humvee", [CsfValue("Hum&vee")]),
        CsfLabel("EXTRA", [CsfValue("Text", b"metadata")]),
        CsfLabel("EMPTY", []),
    ])


def test_csf_round_trip_is_lossless():
    data = fixture_csf().to_bytes()
    assert CsfFile.from_bytes(data).to_bytes() == data


def test_hotkey_marker_manipulation():
    assert extract_hotkey("Hum&vee") == "V"
    assert set_hotkey_marker("Hum&vee", "H") == "&Humvee"
    assert set_hotkey_marker("Rock && Roll", None) == "Rock && Roll"
    assert set_hotkey_marker("Humvee", "F") == "Humvee (&F)"
    assert set_hotkey_marker("Humvee (&F)", "V") == "Hum&vee"


def test_csf_writer_changes_only_selected_text():
    csf = CsfFile.from_bytes(fixture_csf().to_bytes())
    csf.by_name()["controlbar:humvee"].values[0].text = set_hotkey_marker(csf.get("CONTROLBAR:Humvee"), "H")
    reread = CsfFile.from_bytes(csf.to_bytes())
    assert reread.get("CONTROLBAR:Humvee") == "&Humvee"
    assert reread.get("EXTRA") == "Text"
