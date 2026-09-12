import errno

from core.csf_parser import CsfFile, CsfLabel, CsfValue
from core.write_recovery import (
    create_recovery_package, install_recovery_package, is_access_error,
    manual_copy_instructions, take_install_argument,
)


def csf_bytes() -> bytes:
    return CsfFile(labels=[CsfLabel("CONTROLBAR:Test", [CsfValue("&Test")])]).to_bytes()


def test_access_errors_are_recognized_through_exception_chain():
    wrapped = RuntimeError("write failed")
    wrapped.__cause__ = OSError(errno.EACCES, "denied")

    assert is_access_error(wrapped)
    assert not is_access_error(ValueError("bad config"))


def test_recovery_package_can_be_installed_or_copied_manually(tmp_path):
    app_root = tmp_path / "app-data"
    game = tmp_path / "game"
    package = create_recovery_package(
        app_root, game,
        {"generals.csf": csf_bytes(), "CommandMap.ini": b"MapKey TEST\n  Key = KEY_A\nEnd\n"},
    )

    installed_game, installed = install_recovery_package(package)

    assert installed_game == game.resolve()
    assert (game / "Data/English/generals.csf").read_bytes() == csf_bytes()
    assert (game / "Data/English/CommandMap.ini").read_bytes().startswith(b"MapKey TEST")
    assert len(installed) == 2
    instructions = manual_copy_instructions(package)
    assert "generals.csf" in instructions
    assert str(game / "Data/English/generals.csf") in instructions


def test_install_argument_is_removed_before_qt_sees_it(tmp_path):
    package, remaining = take_install_argument(["--style", "fusion", "--install-config", str(tmp_path)])

    assert package == tmp_path
    assert remaining == ["--style", "fusion"]
