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

