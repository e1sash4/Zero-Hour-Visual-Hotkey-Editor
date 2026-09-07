# Zero Hour Visual Hotkey Editor

A working Windows desktop editor for **Command & Conquer: Generals — Zero Hour** hotkeys. It replaces raw `CONTROLBAR:` identifiers with the game's own locally extracted command icons, the producer/building, localized name, and current key.

> This project does **not** contain Electronic Arts images, audio, text tables, or other game resources. Every cameo is read from the user's installed game and cached locally. Deleting `cache/icons` is safe; the editor rebuilds it.

## MVP status

The current build can:

- auto-detect the Steam/EA installation or let the user select it;
- read validated BIG4/BIGF archives without FinalBIG;
- parse MappedImage, CommandButton, CommandSet and Object/ChildObject INI data;
- resolve the chain `faction/general → producer → CommandSet slot → CommandButton → ButtonImage/TextLabel`;
- crop real TGA cameos with Pillow and cache only referenced images;
- read and byte-for-byte round-trip the real `generals.csf` string table;
- show USA, China and GLA plus all nine standard generals;
- capture A–Z/0–9 from the active editor window or its virtual keyboard;
- detect conflicts only inside the same CommandSet;
- identify shared CSF labels and explain that one edit affects all linked commands;
- queue edits in memory, show an unsaved count, and support Ctrl+Z/Ctrl+Y;
- safely Apply through a validated temporary file and automatic backup;
- restore the latest backup or remove the override to return to the archive original;
- create, import, export, duplicate, rename, delete and apply logical JSON profiles;
- search commands and jump to their producer;
- expose technical IDs in Developer Mode;
- switch the interface live between English, Ukrainian and Russian;
- switch between Modern Dark, Zero Hour-styled and Light themes;
- extract and display the original USA, China and GLA faction emblems from the local game;
- index on a background Qt thread with progress and diagnostics;
- produce a reliable one-folder Windows build with PyInstaller.

## Screenshot

Screenshot placeholder — run the app against a local Zero Hour installation so copyrighted game cameos are never committed to this repository.

## Requirements

- Windows 10/11
- Python 3.12 or newer for development
- A legal local installation of Command & Conquer: Generals — Zero Hour

Runtime packages are listed in `requirements.txt`: PySide6, Pillow, pytest and PyInstaller.

## Development setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python main.py
```

The detector checks registry entries, common EA/Steam folders, all Windows drive letters, and `ZERO_HOUR_PATH`. The selected path is remembered by Qt settings.

## Build the EXE

Run:

```bat
build.bat
```

The script installs dependencies into `.venv`, runs all tests, and creates:

```text
dist\ZeroHourHotkeyEditor\ZeroHourHotkeyEditor.exe
```

One-folder packaging is intentional: Qt plugins and Pillow image codecs are more reliable and easier to diagnose this way than in a single self-extracting executable.

## Architecture

The UI contains no binary/INI parsing logic:

```text
app/       application startup, paths, theme, main window and background indexing
ui/        command cards/grid, virtual keyboard, settings/conflict/profile dialogs
core/      detection, BIG/INI/CSF parsers, indexing, assets, hotkeys, profiles, backups
models/    parser-independent dataclasses
tests/     small synthetic fixtures only
data/      user-created logical profiles
cache/     regenerated local icon cache (gitignored)
logs/      diagnostic logs (gitignored)
backups/   timestamped validated CSF backups (gitignored)
```

This differs slightly from the initial suggested tree by grouping small related models in `models/entities.py` and keeping orchestration in `core/indexer.py`. It avoids one-class files while preserving strict separation between GUI and game-data logic.

## BIG indexing

`core.big_reader.BigArchive` supports BIGF and BIG4 read-only archives. It validates the signature, table boundary, filename termination, count, offsets and payload sizes. It provides enumeration, case-insensitive lookup, substring search and extraction of one member to memory.

Overlay priority is currently `PatchINI.big`, `PatchZH.big`, `INIZH.big`, `EnglishZH.big`, `TexturesZH.big`, then `WindowZH.big`. Loose files win when directly requested. Repacking is deliberately unsupported and unnecessary for this editor.

## Icon extraction and MappedImage cropping

MappedImage INIs under `Data\INI\MappedImages` provide an ID, atlas filename, atlas dimensions and a `Left/Top/Right/Bottom` rectangle. The Asset Manager finds the referenced atlas by basename across indexed archives, decodes its TGA orientation through Pillow, crops with the top-left coordinate box, converts to RGBA PNG, and atomically places it in `cache/icons`.

Only `ButtonImage` IDs used by indexed command contexts are requested. Missing mappings, textures or invalid images become placeholders and warnings instead of crashes. In the tested English Steam installation, UI atlases such as `SAUserInterface512_005.tga` are inside `EnglishZH.big`.

The header faction emblems use the stock MappedImages `SAFactionLogo144_US`, `SNFactionLogo144_China` and `SUFactionLogo144_GLA`. They are cropped at runtime from `SCLogosUserInterface512_001.tga` and cached like command cameos; no EA logo is packaged with the editor.

## Interface language and themes

Settings can switch the interface immediately between English, Ukrainian and Russian. The selected language and theme are stored in Qt settings and restored on the next launch. Localized game command names still come from the selected game's `generals.csf`; the application translation never modifies that file.

Three themes are included: Modern Dark, a muted olive-and-gold Zero Hour style, and Light. Themes affect only the editor UI and do not modify the game.

## Building the logical command database

1. `CommandButton.ini` supplies command behavior, object/upgrade/special power, `ButtonImage`, `TextLabel`, and description label.
2. `CommandSet.ini` supplies command-bar slot → CommandButton.
3. Object INIs supply producer Object → CommandSet, side and localized producer label.
4. Known stock prefixes (`AirF_`, `Lazr_`, `SupW_`, `Tank_`, `Infa_`, `Nuke_`, `Chem_`, `Slth_`, `Demo_`) classify the twelve user-facing faction/general variants.
5. `generals.csf` resolves user-facing names and current mnemonic keys.

Unused/debug sides are excluded because only the three stock factions and the explicit general-prefix map are accepted.

## CSF editing

`core.csf_parser` is a clean-room implementation based on published format documentation and validation against the user's real file. It supports labels with zero or multiple values, plain ` RTS` and extended `WRTS` records, inverted UTF-16LE text, extra metadata, and exact serialization. The real 928,775-byte English CSF currently round-trips byte-for-byte when unmodified.

Zero Hour treats the character after `&` as the mnemonic. The editor removes the old marker and inserts it before the chosen character. If the character is absent (for example assigning **F** to **Humvee**), it appends the conventional localized suffix `(&F)`, which gives SAGE a valid mnemonic while keeping the visual editor label clean.

The shipped language archive is never repacked. Apply writes a loose override to:

```text
<Zero Hour>\Data\English\generals.csf
```

Before writing, the current loose file—or the untouched CSF extracted from `EnglishZH.big` on first Apply—is copied to a timestamped backup. The new file is serialized to a sibling temporary file, parsed again, flushed to disk, then atomically replaced. Restore Original removes only this generated loose override after backing it up; the game then falls back to its original archive.

## User data

Development mode stores data beside the repository:

- `backups/YYYY-MM-DD_HHMMSS_microseconds/generals.csf`
- `data/profiles/*.json`
- `cache/icons/*.png`
- `logs/app.log`

The packaged app uses `%LOCALAPPDATA%\ZeroHourHotkeyEditor` for the same folders, while the applied CSF override stays in the selected game directory.

`Game Default` is created on first successful index and is read-only. Profiles contain only `TextLabel → key`, never a copyrighted CSF copy.

## Tests and real-install verification

Synthetic tests cover BIG boundaries/extraction, generic INI blocks, MappedImages, CommandButtons/Sets, CSF read/write, mnemonic manipulation, context-aware conflicts, shared labels, undo/redo, profiles and atomic backup/restore. No fixture comes from the game.

The implementation was also read-only tested against a real Steam installation at `E:\SteamLibrary\steamapps\common\Command & Conquer Generals - Zero Hour`: all stock faction/general variants indexed, the real CSF parsed, and the Humvee cameo was cropped successfully. Integration checks never write the installed game's CSF.

## Known limitations / post-MVP work

- English (`EnglishZH.big` and `Data\English`) is the fully tested language. Automatic selection among every localized language archive is next.
- A configurable automatic Grid Layout preset is architecturally possible through profiles but does not yet have a scheme editor.
- F1–F12 are intentionally not offered: CSF mnemonics are character-based, and no safe stock Zero Hour representation was verified.
- Global command-map shortcuts are displayed only when they are normal CommandButtons; editing engine-level `CommandMap.ini` bindings is not included.
- Mod-specific faction classification may require a small override JSON in a future version.
- The full parsed database is rebuilt at startup; expensive PNG crops are hash-keyed and reused. A serialized metadata index can further shorten startup for very large mods.

## Format references

- [OpenSAGE BIG format documentation](https://github.com/OpenSAGE/Docs/blob/master/file-formats/big/index.rst)
- [TheAssemblyArmada/Thyme CSF format documentation](https://github.com/TheAssemblyArmada/Thyme/wiki/Compiled-String-File-Format)
- [GenHotkeys reference project](https://github.com/MahBoiDeveloper/GenHotkeys) — consulted for behavior only; no GPL source was copied.

Electronic Arts does not endorse this project. Command & Conquer and Zero Hour are trademarks of Electronic Arts Inc.
