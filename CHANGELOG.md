# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- New target writers for `iTerm2`, `tmux`, and `btop`.
- New target writers for `WezTerm`, `Alacritty`, and `Ghostty`.
- Improved Yazi flavor handling with safer theme selector behavior.
- One-time setup helper: `configs/wallpaper-colors/setup-targets.sh`.
- Governance docs: `CODE_OF_CONDUCT.md` and `SECURITY.md`.
- GitHub contribution templates: issue forms and pull request template.
- Path/name overrides for borders, Yazi, WezTerm, Alacritty, Ghostty, iTerm2, tmux, and btop.
- Unit tests for writer path overrides and tmux reload behavior.
- CI shell syntax checks and Python unit test workflow.

### Changed
- `tmux` target now hot-reloads automatically when a tmux server is running.
- Installer supports `--setup-targets` for one-time `tmux`/`btop`/`iTerm2` wiring.
- Launchd templates and install flow are now prefix-configurable for public reuse.
- Borders now use a stronger active accent and a muted inactive color derived from wallpaper.

### Security
- Path overrides in setup/install flows are validated and constrained to the current user home.
