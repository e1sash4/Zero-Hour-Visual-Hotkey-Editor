# Changelog

All notable changes to Zero Hour Visual Hotkey Editor are documented here.

## [0.2.0] - 2026-09-12

### Added

- Dedicated Unit Actions, Building Actions, and Infantry Actions pages for all
  twelve official factions and generals.
- Mouse hotkeys for the standard M3, M4, and M5 buttons, enabled by default on
  first launch and active only while Zero Hour is in the foreground.
- Global hotkey editing, reusable profiles, backups, multilingual UI, and
  selectable application themes.
- Independent, configurable action layouts for every general, including
  support for additional grid rows.
- Automatic discovery of configured active abilities while preserving their
  real CommandButton, localized label, and game icon.
- Recovery flow for Windows write-access failures in protected game folders.
- One-click restart with administrator privileges while preserving pending
  `generals.csf` and `CommandMap.ini` changes.
- Manual-copy fallback with prepared configuration files and exact destination
  paths when elevated installation is still unavailable.
- Windows executable version metadata and a versioned GitHub release archive.

### Changed

- `layouts.json` is now authoritative for both visibility and placement of
  configured Active Actions.
- Active Action positions are reloaded instead of remaining stale in memory.
- Per-general action layout identifiers replace legacy faction-wide fallback
  identifiers.
- README documentation now covers the new action pages and access-recovery
  behavior.

### Fixed

- Added Active Actions not appearing unless they were also hardcoded in the
  indexer.
- Edited Active Action coordinates not taking effect because of layout caching.
- Valid fourth and later grid rows being rejected by configuration tests.
- Failed writes to protected game installations losing a straightforward path
  to applying the generated configuration.
