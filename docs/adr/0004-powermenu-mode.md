# ADR 0004: Powermenu mode

Status: Accepted
Date: 2026-08-26

## Context

`Super+Shift+E` ran a rofi/`walker`-based power menu script
(`~/.config/rofi/powermenu/type-3/powermenu.sh`) listing Lock, Suspend,
Logout, Reboot, Shutdown with an uptime header and a Confirm/Cancel step.
The unified launcher (`cosmic-launcher-extended`, ADR 0003) already owns the
`windows`/`combi` keybindings; adding a third mode keeps power actions on the
same visual surface and process instead of a separate rofi theme/script.

## Decision

Add `LauncherTasks::Powermenu` (`cosmic-launcher-extended powermenu`) as a
fourth runtime mode alongside `windows`/`combi`/`alt-tab`:

- On activation, `power_menu = true` and `launcher_items` is populated
  directly in-process via `power_items()` — no pop-launcher backend request.
  The first entry is a disabled `Uptime: <value>` label (from `uptime -p`);
  the sizeable ones are `Lock`, `Suspend`, `Logout`, `Reboot`, `Shutdown`.
- The text input is replaced with a static header showing the uptime line
  when `power_menu` is true, so the surface can't be typed into.
- `pop_launcher::Response::Update` is short-circuited when `power_menu` is
  set, so no in-flight backend search can overwrite the power-menu list.
- Selecting `Lock` runs `loginctl lock-session self` immediately (Lock is
  non-destructive, no confirmation needed — mirrors the rofi script).
- Selecting `Suspend`/`Logout`/`Reboot`/`Shutdown` replaces `launcher_items`
  with a `Confirm`/`Cancel` step (`power_confirmation` holds the pending
  action) before executing — mirrors the rofi script's confirm step.
- `Confirm` dispatches directly via `std::process::Command`:
  `systemctl suspend|reboot|poweroff`, `loginctl terminate-session
  $XDG_SESSION_ID`. No shell interpolation of user input; only fixed
  argv per branch.
- `hide()` always resets `power_menu`/`power_confirmation`, so reopening any
  mode starts clean.

`Super+Shift+E` now runs `cosmic-launcher-extended powermenu`, replacing the
rofi/walker script for that binding.

## Consequences

- One fewer external script/theme dependency for this specific keybinding;
  the rofi powermenu script itself remains on disk (unused by this binding)
  in case other bindings or manual invocation still reference it.
- Power actions run as direct child processes of the launcher, not through a
  confirmation subprocess/dmenu roundtrip — action list changes must stay
  reviewed carefully, since there's no separate confirmation UI process.
- Powermenu items are locally constructed `SearchResult`s (no `icon`,
  `category_icon`, `window`); button icons render as text-only for this mode,
  same as the visual style already used when items lack icons.
- Verified: unified build succeeds, CLI exposes `powermenu`, process starts
  and stays resident without crashing, and the pop-launcher backend is never
  invoked for this mode (confirmed via process list — no child `pop-launcher`
  spawned). Full on-screen click-through of Lock/Suspend/Logout/Reboot/
  Shutdown could not be verified in this session: the layer-shell surface is
  not visible to the available accessibility/window inspection tooling
  (same limitation as ADR 0002/0003).
