import pytest

from core.backup_manager import BackupManager
from core.csf_parser import CsfFile, CsfLabel, CsfValue
from core.profile_manager import Profile, ProfileManager


def csf_bytes(text="&Humvee"):
    return CsfFile(labels=[CsfLabel("HUMVEE", [CsfValue(text)])]).to_bytes()


def test_profile_export_import(tmp_path):
    manager = ProfileManager(tmp_path)
    path = manager.save(Profile("My Grid", {"CONTROLBAR:Humvee": "H", "OTHER": None}))
    loaded = manager.load(path)
    assert loaded.name == "My Grid"
    assert loaded.bindings["CONTROLBAR:Humvee"] == "H"


def test_game_default_is_refreshed_but_cannot_be_overwritten_by_user(tmp_path):
    manager = ProfileManager(tmp_path)
    path = manager.save_game_default({"HUMVEE": "H"})
    manager.save_game_default({"HUMVEE": "V"})

    assert manager.load(path).bindings == {"HUMVEE": "V"}
    with pytest.raises(PermissionError):
        manager.save(Profile("Game Default", {"HUMVEE": "Z"}))


def test_existing_game_settings_are_captured_only_on_initial_scan(tmp_path):
    manager = ProfileManager(tmp_path)
    path, created = manager.capture_initial_game_settings({"HUMVEE": "H"})
    no_path, created_again = manager.capture_initial_game_settings({"HUMVEE": "V"})

    assert created is True
    assert created_again is False
    assert no_path is None
    assert manager.load(path).bindings == {"HUMVEE": "H"}


def test_initial_scan_without_override_prevents_later_duplicate(tmp_path):
    manager = ProfileManager(tmp_path)
    assert manager.capture_initial_game_settings(None) == (None, False)

    manager.save(Profile("My Profile", {"HUMVEE": "H"}))
    assert manager.capture_initial_game_settings({"HUMVEE": "H"}) == (None, False)
    assert [path.name for path in manager.list()] == ["My Profile.json"]


def test_initial_scan_does_not_duplicate_matching_profile(tmp_path):
    manager = ProfileManager(tmp_path)
    existing = manager.save(Profile("My Profile", {"HUMVEE": "H"}))

    matched, created = manager.capture_initial_game_settings({"HUMVEE": "H"})

    assert matched == existing
    assert created is False
    assert [path.name for path in manager.list()] == ["My Profile.json"]


def test_backup_and_atomic_restore(tmp_path):
    target = tmp_path / "Data/English/generals.csf"
    target.parent.mkdir(parents=True)
    target.write_bytes(csf_bytes())
    manager = BackupManager(tmp_path / "backups")
    backup = manager.create(target)
    manager.atomic_write(target, csf_bytes("H&umvee"))
    assert CsfFile.read(target).get("HUMVEE") == "H&umvee"
    manager.restore(backup, target)
    assert CsfFile.read(target).get("HUMVEE") == "&Humvee"
