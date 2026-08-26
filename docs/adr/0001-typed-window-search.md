# ADR 0001: Typed window-search mode

Status: Accepted
Date: 2026-08-26

## Context

Upstream `cosmic-launcher` (COSMIC's app launcher/window-switcher, `com.system76.CosmicLauncher`)
supports `alt-tab` (visual, non-typed window cycling) but has no mode to type a
window title and jump straight to a match. We wanted a `rofi -show window`-style
keybinding: `Super+Y` opens the launcher restricted to open windows, typed
filtering, `Enter` activates the match.

Rather than patch a separate launcher (wofi/rofi don't see COSMIC's Wayland
toplevel list), we forked `cosmic-launcher` and added a new mode so it reuses
the existing window list plumbing (`pop_launcher` window results) already
wired into the app.

## Decision

Add a `window-search` CLI subcommand / `LauncherTasks::WindowSearch` action
(`src/app.rs`) that:

- Sets a new `window_search: bool` field on `CosmicLauncher`.
- On activation, clears the query and filters results to
  `item.window.is_some()` only (reuses the normal search pipeline, just
  post-filtered to windows).
- Behaves like `alt_tab` for closing: selecting a result or losing focus
  hides the launcher and resets `window_search = false`.

Installed as a separate binary (`~/.local/bin/cosmic-launcher-typed`) bound to
`Super+Y`, alongside the unmodified `alt-tab` binding (`Super+Shift+X`) and
`drun`/`run` bindings kept on rofi. The fork is built with
`CARGO_TARGET_DIR` pointed at `/opt/...` (not `~`, which is a small/quota'd
partition) via `~/dotfiles_setup/install_cosmic_launcher_extended.sh`.

## Consequences

- New commits (`0a36812`, `c6360fe`, `8f21cfb`, `1e00a40`, `4f09e0b`) diverge
  from upstream `cosmic-launcher`; `APP_ID` was changed to
  `com.mis.CosmicLauncherTyped` to avoid colliding with the system launcher's
  D-Bus identity/singleton.
- Because it's a separate binary/APP_ID, it runs as its own long-lived
  singleton process (COSMIC launchers stay resident between invocations
  rather than exiting after each use). **Any binary rebuild must kill the
  running process** (`pkill -x cosmic-launcher-typed`) or the old in-memory
  state (including stale typed query) keeps serving the keybinding. The
  install script now does this automatically after `install -Dm755`.
- Follow-up bugs, in order found and fixed:
  1. `c6360fe` - selecting a window in `window-search` mode didn't close the
     launcher/reset state (only `alt_tab` was checked, not `window_search`).
  2. `8f21cfb` - reopening after a normal close still showed the last typed
     query, because clearing happened on hide but activation didn't always
     route through the same hide path in every case.
  3. `1e00a40` - explicit query clear added directly in the `Activate`
     handler, before request dispatch.
  4. `4f09e0b` - that clear sent `Request::Search("")` to the backend
     immediately before `Request::Activate(item.id)`; the backend reset the
     result list before activation resolved, so `Enter` silently failed to
     switch windows. Fixed by clearing only local UI state
     (`input_value`, `focused`) and dropping the backend search call - no
     round-trip needed since the launcher closes right after.
- Net effect: query resets locally on activation with no backend race;
  window switching confirmed working after the process restart.

## Alternatives considered

- **wofi/rofi window mode**: no Wayland toplevel access on COSMIC's
  compositor (`cosmic-comp`); rejected up front, see the earlier
  investigation in commit history / session notes.
- **Patch `alt_tab` itself to accept typed input**: would change existing
  keybinding behavior for `Super+Shift+X`; rejected to keep the visual
  alt-tab flow untouched.
