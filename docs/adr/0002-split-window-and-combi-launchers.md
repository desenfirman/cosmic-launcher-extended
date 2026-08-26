# ADR 0002: Split window and combi launchers

Status: Accepted
Date: 2026-08-26

## Context

Window search and application/command search originally shared one long-lived
COSMIC launcher singleton. `window_search` was mutable process state. Reusing
that process across shortcuts allowed mode state and stale result behavior to
cross boundaries; replacing the binary also left old state alive until the
singleton exited.

Rofi's `combi` combines application and command sources. pop-launcher already
provides the application source (`desktop_entries`) but no source that lists
executables from `$PATH`.

## Decision

Build two launcher variants from one source tree:

- `cosmic-launcher-extended-windows windows`, feature `windows-mode`,
  `APP_ID = com.mis.CosmicLauncherWindows`; retains only results with a
  window handle.
- `cosmic-launcher-extended-combi combi`, default features,
  `APP_ID = com.mis.CosmicLauncherCombi`; retains non-window results from the
  persistent desktop-entry source and local PATH command source.

Bind `Super+Y` to windows and `Super+Space` to combi. Each variant has its
own D-Bus singleton identity and cannot overwrite the other's mode state.

The local pop-launcher plugin setup contains:

- `desktop_entries/plugin.ron` with `query: (persistent: true)` so apps appear
  on empty query.
- `path_commands/plugin.ron` with `query: (persistent: true)`.
- `path_commands.py`, which enumerates unique executable names from `$PATH`,
  filters by typed substring, and activates the selected executable directly
  with `subprocess.Popen` (no shell interpolation).

The rebuild script builds both feature variants into `/opt/...`, installs both
binaries, installs plugin files, and stops old variant processes after install.

## Consequences

- Window switching and combi search have isolated UI/service processes and
  independent D-Bus activation routes.
- Combi empty-query result count uses `max_open: 5000` instead of the upstream
  default 8, preventing the combined app/command inventory from being cut off
  at the first eight results.
- PATH commands are executable files only, de-duplicated by command name using
  first-directory-wins PATH precedence. They launch without a terminal wrapper;
  commands needing a terminal remain available through existing `run `, `:`,
  and `t:` terminal plugin prefixes.
- Plugin manifests currently refer to the system desktop-entry executable and
  are installed by the rebuild script, preserving relocatable plugin directory
  layout for the custom PATH plugin.
- Existing stock `cosmic-launcher` remains untouched.

## Verification

- PATH plugin protocol smoke test returned filtered `Append` responses and a
  `Finished` response.
- PATH activation smoke test launched a controlled executable and returned
  `Close`.
- Both `windows-mode` and default release builds completed successfully.
- CLI help exposes `combi`, `windows`, and existing launcher commands.
