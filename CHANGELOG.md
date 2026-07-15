# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- GitHub Pages project site.
- Opt-in VS Code token-color syncing that preserves existing user TextMate rules.
- CI coverage for sandboxed macOS installs and Swift runtime startup.

### Changed
- CI now uses the current stable major releases of `actions/checkout` and `actions/setup-python`.
- Wallpaper colors now reapply after display configuration changes.
- Wallpaper sync cache now invalidates when config or `WALLPAPER_*` overrides change.
- Theme watcher startup and wallpaper cycling now avoid first-run double-cycle races.
- Target App path policy, output writes, fallbacks, failure reporting, and Sync Run orchestration now use shared modules.

### Security
- Raised the minimum Pillow version to `12.2.0` to exclude vulnerable releases.
- LaunchAgent plist rendering now XML-escapes substituted install paths.
