from core import game_detector


def make_game(path):
    path.mkdir(parents=True)
    (path / "INIZH.big").write_bytes(b"ini")
    (path / "TexturesZH.big").write_bytes(b"textures")


def test_reads_custom_steam_library_and_detects_unknown_folder_name(tmp_path, monkeypatch):
    steam = tmp_path / "Steam"
    library = tmp_path / "A Custom Library"
    vdf = steam / "steamapps/libraryfolders.vdf"
    vdf.parent.mkdir(parents=True)
    escaped = str(library).replace("\\", "\\\\")
    vdf.write_text(
        f'"libraryfolders"\n{{\n  "1"\n  {{\n    "path" "{escaped}"\n  }}\n}}',
        encoding="utf-8",
    )
    game = library / "steamapps/common/Unexpected Steam Folder Name"
    make_game(game)
    monkeypatch.setattr(game_detector, "_steam_roots", lambda: [steam])
    monkeypatch.setattr(game_detector, "_registry_candidates", lambda: [])
    monkeypatch.setattr(game_detector, "_non_steam_candidates", lambda: [])

    assert game_detector.detect_game() == game.resolve()


def test_invalid_remembered_path_does_not_block_non_steam_detection(tmp_path, monkeypatch):
    game = tmp_path / "Games/Zero Hour Custom Install"
    make_game(game)
    monkeypatch.setattr(game_detector, "_steam_candidates", lambda: [])
    monkeypatch.setattr(game_detector, "_registry_candidates", lambda: [])
    monkeypatch.setattr(game_detector, "_non_steam_candidates", lambda: [game])

    assert game_detector.detect_game(tmp_path / "removed-old-install") == game.resolve()
