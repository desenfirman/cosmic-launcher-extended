# ADR 0003: Unified runtime launcher modes

Status: Accepted
Date: 2026-08-26

## Context

The split `windows` and `combi` binaries introduced separate compile-time
features and binaries to isolate singleton state. That avoided cross-mode state,
but created needless operational complexity: two installed binaries and two
build variants for one launcher feature set.

## Decision

Use one binary and one singleton identity:

```text
cosmic-launcher-extended windows
cosmic-launcher-extended combi
```

The binary uses `APP_ID = com.mis.CosmicLauncherExtended`. Mode is runtime state:

- `windows` / `window-search` sets `window_search = true` and retains results
  with a window handle.
- `combi` sets `window_search = false` and retains non-window results from
  persistent desktop-entry and PATH-command plugins.
- `alt-tab` also retains window results.

Every mode activation resets query and focus before requesting a fresh search.
The existing `hide()` path resets mode state when the launcher closes.

Shortcuts use the unified binary:

- `Super+Y`: `cosmic-launcher-extended windows`
- `Super+Space`: `cosmic-launcher-extended combi`

The installer builds one release binary and installs it at
`~/.local/bin/cosmic-launcher-extended`. It still installs local pop-launcher
plugin manifests and restarts the old unified process after replacement.

## Consequences

- One executable and one build command replace split binaries.
- One singleton can switch modes safely because each activation explicitly sets
  mode state and resets query state.
- Stock `/usr/bin/cosmic-launcher` remains separate through its own APP_ID.
- Combi result limit remains `max_open: 5000`; window mode shares same service
  client but filters results at the frontend.
- `0002-split-window-and-combi-launchers.md` records the previous interim design;
  this ADR supersedes its split-binary decision.

## Verification

- Unified release build completed with `cargo build --release --locked
  --no-default-features`.
- CLI help exposes both `windows` and `combi` subcommands.
- PATH plugin protocol and controlled command activation smoke checks pass.
