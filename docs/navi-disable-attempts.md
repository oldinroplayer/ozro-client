# Navigation disable attempts (OzRo client)

Date: 2026-11-16
Scope: only the in-game navigation button/window for `OzRo.exe`.
Status: unresolved. The navigation button is still visible. Do not retry the approaches below.

## Current state

- Live client: `/mnt/games/OzRo/OzRo.exe` — untouched.
- Experimental: `/mnt/games/OzRo/OzRo_experimental.exe` — based on the live `OzRo.exe`.
  - It has a 34-byte patch for `HideNewButtons` and `HideGameWindows`.
  - It launches and reads the data folder correctly.
  - The navigation button is still visible.
- `2019-06-05fRagexe_patched.exe` is the old historical base. It does **not** have the live client's patch set and does not read the data folder correctly. Do not use it as the live base.
- No download was completed. The NEMO mirrors returned `403 Forbidden` / timeouts and the machine became blacklisted. Do not retry downloads from this machine.

## What was tried and why it failed

### 1. Server-side questinfo guard

`DISABLE_QUESTINFO_MARKERS` and the `questinfo` early return only affect packet `0x446` (quest marks/minimap marks).

They do **not** affect the client navigation UI. Unrelated to this problem.

### 2. WARP `HideNewButtons` on the old f base

A copy of WARP-rock was used with `HideNewButtons`.

The old f base accepted the patch (29 bytes changed), but that client does not have the live client's data-folder/GRF patch set. It could not even read the data folder before login. Discarded.

### 3. WARP `HideNewButtons` on the live `OzRo.exe`

Result: 0 bytes changed. The navigation button remained.

Reason: `OzRo.exe` has PE timestamp `0`, so WARP reads `Exe.BuildDate` as `0`. `NewButtonVis.validate` requires `Exe.BuildDate > 20170000`, so the patch is skipped.

The WARP scripts were bypassed in a **temporary copy** at `/tmp/kilo/warp_bypass`:

- `NewButtonVisibility.qjs`: `validate` forced to `true`, selection hardcoded to `['navigation']`.
- The original WARP install was not modified.

Even with the bypass, `HideNewButtons` on the live `OzRo.exe` changed 0 bytes.

### 4. WARP `HideGameWindows` with navigation window IDs

The 2025 reference IDs `203, 229, 306, 314` were hardcoded in the temporary WARP copy and applied to a copy of the live `OzRo.exe`.

Result: 34 bytes changed. The `.epi` listed `HideNewButtons` and `HideGameWindows`. The client launches, but the navigation button is still visible.

Problems with this approach:

- `306` and `314` are outside the 256-byte `idxTbl` used by `HideGameWindows`; writing them modifies adjacent data. Do **not** repeat this.
- The 2025 reference IDs are not the right target for the 2019 client's visible navigation button.

### 5. Binary analysis of the live `OzRo.exe`

The real `UIWindowMgr::MakeWindow` switch was located:

- `203` maps to `UINavigationV4Wnd`.
- `229` maps to `UINavigationHelpWnd`.

Those IDs were already patched by `HideGameWindows`, and the button is still visible. Therefore the visible navigation button is not removed by hiding the `UINavigationV4Wnd`/`UINavigationHelpWnd` windows. It is likely a separate UI control, a legacy `UINavigationWnd` path, or a directly created overlay.

Do not continue guessing window IDs.

## Do not retry

- Downloading `2019-06-05hRagexeRE` from the NEMO mirrors. The mirrors are blocked from this machine.
- `HideNewButtons` on `OzRo.exe`. It produces 0 bytes of change.
- `HideGameWindows` with `203, 229, 306, 314`. It produces no visible effect and `306`/`314` are out of bounds.
- NEMO `HideNavButton` / `Disable specified Windows`. Not the chosen tool; `Disable specified Windows` also failed in the reference patch lists.
- Server-side `DISABLE_QUESTINFO_MARKERS`. It only affects `0x446`, not navigation.
- Using `2019-06-05fRagexe_patched.exe` as an experimental base. It lacks the live client's data/GRF patch set.

## If this is ever revisited

The remaining work would be to identify the actual navigation **button control** in the client UI, not the `MakeWindow` window switch. That is a different patch target. Removing the navigation Lua data only disables route calculation; it does not remove the button.

Until then: leave navigation enabled.
