# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

## [1.1.0] - 2026-07-15

### Highlights
- Added opt-in VS Code token-color syncing without replacing existing TextMate rules.
- Wallpaper colors now reapply after display changes and resync when configuration changes.
- Require Pillow 12.3.0 and escape LaunchAgent install paths before plist rendering.

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
- Raised the minimum Pillow version to `12.3.0` to exclude releases affected by [CVE-2026-54059](https://osv.dev/vulnerability/PYSEC-2026-2253), [CVE-2026-54060](https://osv.dev/vulnerability/PYSEC-2026-2254), [CVE-2026-55379](https://osv.dev/vulnerability/PYSEC-2026-2255), [CVE-2026-55380](https://osv.dev/vulnerability/PYSEC-2026-2256), and [CVE-2026-55798](https://osv.dev/vulnerability/PYSEC-2026-2257).
- LaunchAgent plist rendering now XML-escapes substituted install paths.
