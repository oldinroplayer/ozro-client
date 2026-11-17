# Ragexe internals / patch manifest — OzRo

Last verified: 2026-11-17
Audience: agents/RE work. Compact, offsets are authoritative.
Scope: `OzRo.exe` (PE32 i386, Ragexe 2019-06-05, patched build).

## Artifacts

| Artifact | Path | SHA-256 |
|---|---|---|
| live client | `/mnt/games/OzRo/OzRo.exe` | `d4335d1ef9d565c23ee6236e286a1272715ac9d76aa5e08c8133be4fa204e5be` |
| base + timestamp | `/mnt/games/OzRo (experiments)/OzRo.exe` | `4ef074a628551e6f7cd6e65e52be285823fed31c99f8ad798b7bb31a9ce00669` |
| + nav button hide | `/mnt/games/OzRo (experiments)/OzRo-navihide.exe` | `e2d88fb73dc81c7833040f8e831de604e8a21642ff43aa1070b40ea4277392c2` |
| + nav window/guards (final) | `/mnt/games/OzRo (experiments)/OzRo-navihide-nonav.exe` | `19d81cac4684ff267cab558b7abebd3a126483ac028e5e7060a1911d1c7cce24` |
| committed copy | `patch/OzRo.exe` | same as final |

Size: `9,216,000` bytes.

## PE layout

```
e_lfanew = 0x138
TimeDateStamp file off = e_lfanew + 8 = 0x140
ImageBase = 0x400000
AddressOfEntryPoint = 0x5DC9AD
CheckSum = 0
```

| Section | VA | VSize | Raw | RawSize | Notes |
|---|---|---|---|---|---|
| .text | 0x00401000 | 0x006BE9B1 | 0x00000400 | 0x006BEA00 | main code |
| .rdata | 0x00AC0000 | 0x0011C42A | 0x006BEE00 | 0x0011C600 | strings, vtables/RTTI |
| .data | 0x00BDD000 | 0x002B45C0 | 0x007DB400 | 0x0003A200 | globals |
| .rsrc | 0x00E92000 | 0x00024F48 | 0x00815600 | 0x00025000 | |
| .reloc | 0x00EB7000 | 0x00075E3C | 0x0083A600 | 0x00076000 | |
| .xdiff | 0x00F2D000 | 0x0001A000 | 0x008B0600 | 0x00019A00 | RWX-ish code cave area; entropy ~7.99 |

Code cave tail: file `0x8C9FB0..0x8C9FFF` / VA `0xF469B0..0xF469FF`. Used by patches below. End = file `0x8CA000`, VA `0xF46A00`.

Protection indicators: strings `CThemidaMgr`, `nProtect KeyCrypt`; `.xdiff` high entropy. Entry point is normal code (`0x5DC9AD`), main `.text` not virtualized. Static analysis worked.

## PE timestamp / WARP gate

WARP `NewButtonVis.validate` needs `Exe.BuildDate > 20170000`.
Live exe timestamp = `0` -> WARP skipped patches silently.

Patch:

```
file 0x140, 4 bytes: 00 00 00 00 -> C0 AE F7 5C
value = 0x5CF7AEC0 = 2019-06-05 12:00:00 UTC
```

The noon time avoids date-boundary off-by-one in WARP's local-time conversion. WARP then reports 2019-06-05 and applies patches.

## WARP usage (console under wine)

WARP path: `/home/oz/Descargas/WARP-rock_win32/win32/WARP_console.exe`
Run from its own `win32` dir:

```bash
cd /home/oz/Descargas/WARP-rock_win32/win32
wine WARP_console.exe -using Z:/tmp/session.yml
```

Session format:

```yaml
from: "Z:/path/in.exe"
to: "Z:/path/out.exe"
patches:
  - HideNewButtons
  - HideGameWindows
```

Important:

- Console cannot answer `Exe.GetUserInput`. To automate, copy WARP to `/tmp` and hardcode inputs in `Scripts/Patches/*.qjs`.
- All desired WARP patches must be in **one session**. Running a second WARP session strips/undoes prior WARP tag patches. Observed: `HideGameWindows` alone reverted `HideNewButtons`.
- `HideNewButtons` temp edit in `NewButtonVisibility.qjs`:
  - replace the `Exe.GetUserInput(... D_MultiChoice ...)` block with
    `const selection = (_ === 'HideNewButtons') ? ["Navigation"] : [];`
- `HideGameWindows` temp edit in `HideGameWindows.qjs`:
  - replace the `GetUserInput`/`LoadYaml` block with `const WinIDs = [203];`
- Original WARP install was not modified.

### WARP `HideGameWindows` is broken on this build

`HideGameWindows.qjs` computes an index-table base from `Exe.GetInt32(addr+3)` and writes `SetInt8(idxTblAddr + id, dfCase)`.
On this build it wrote to file `0x6F77C0` / VA `0xAF89C0` (inside a CP949 `.rdata` string), not to the real table at file `0x2F6AF4`.
Do **not** use WARP `HideGameWindows` here. Patch the table directly (below).

## Navigation button hide (HideNewButtons)

WARP-produced hook. The visible basic-info navigation button is handled by the switch at `0x57ED00`.

Original:

```
57ED00: 05 97 FE FF FF    add eax, 0xFFFFFE97   ; eax = menu/button id
57ED05: 3D B5 00 00 00    cmp eax, 0xB5
57ED0A: 77 0E             ja  0x57ED1A
57ED0C: ...               movzbl/jmp switch table
```

Patched:

```
file 0x17E100 / VA 0x57ED00, 5 bytes:
  E9 AB 7C 9C 00        jmp 0xF469B0
```

Cave at file `0x8C9FB0` / VA `0xF469B0`, 33 bytes:

```
3D 9C 01 00 00          cmp eax, 0x19C
0F 84 48 89 63 FF       je  0x57F303
8D 80 97 FE FF FF       lea eax, [eax-0x169]
3D B5 00 00 00          cmp eax, 0xB5
0F 87 4E 83 63 FF       ja  0x57ED1A
E9 3B 83 63 FF          jmp 0x57ED0C
```

Logic: if button id == `0x19C`, jump to loop continuation `0x57F303` (skip creating that button). Otherwise restore the original `add` and rejoin the switch.
Note: decompiled source (different build) has `MENUICON_NAVIGATION = 430`; the live build uses `0x19C` here.

## Navigation window block

`UIWindowMgr::EnsureWindow` switch at VA `0x6EFF50`:

```
6EFFD4: 81 FE 4F 01 00 00    cmp esi, 0x14F
6EFFDA: 0F 87 81 73 00 00    ja  0x6F7361             ; default
6EFFE0: 0F B6 86 F4 76 6F 00 movzbl 0x6F76F4(esi),eax ; index table
6EFFE7: FF 24 85 84 73 6F 00 jmp *0x6F7384(,eax,4)    ; jump table
```

Index table:
- VA `0x6F76F4`, file `0x2F6AF4`, length `0x150` (IDs 0..0x14F).
- Default index = `0xDB` (entries 54 and 67).
- Entry `203` (`WID_NAVIGATIONV4WND`) = `0x92`.

Patch:

```
file 0x2F6BBF (0x2F6AF4 + 203): 92 -> DB
```

Effect: `EnsureWindow(203)` goes to default; navigation window is never created from world map, menu icon, or hotkey.
IDs from decompiled source: `WID_ROMAPWND=140`, `WID_NAVIGATIONV4WND=203`, `WID_NAVIGATIONHELPWND=229`, `WID_NAVIGATIONROADICONWND=306`, `WID_NAVIGATIONRUIDEWND=314`. Direct table patch valid for any id <= `0x14F`.

## Crash after blocking 203, and null guards

Blocking 203 leaves `g_navigationManager` (global pointer at `0xCE8F98`) null. World-map click still calls navigation methods.

Crash log:

```
Exception 0xC0000005
EIP 0x0049EAA5
esi = 0
stack: 0x0049EAA5 -> 0x0064A8C3 -> 0x006FA82D -> 0x008D51FF -> 0x008D3A6A -> 0x008D3968 -> 0x009DA3C4 -> 0x009DC8E6
```

Fault:

```
49EAA5: 8B 8E D0 00 00 00    mov ecx, [esi+0xD0]   ; esi=0
```

Functions:
- `sub_49EA70` — deref `[this+0xD0]` at `0x49EAA5`; epilogue `0x49ED5E`.
- `sub_49F340` — deref `[this+0xD0]` at `0x49F375`; epilogue `0x49F3A7`.
- Call sites: `0x49A147`, `0x49D84D` -> `0x49EA70`; `0x49D8F2` -> `0x49F340`; `0x64A8BE`/`0x64A8CB` (world-map click); `0x652332`/`0x65233F`.

Patch both derefs to return early when `esi == 0`:

```
file 0x9DEA5 / VA 0x49EAA5, 6 bytes:
  E9 2E 7F AA 00 90      jmp 0xF469D8 ; nop

file 0x8C9FD8 / VA 0xF469D8, 19 bytes:
  85 F6                  test esi, esi
  0F 84 7E 83 55 FF      je   0x49ED5E
  8B 8E D0 00 00 00      mov  ecx, [esi+0xD0]
  E9 C0 80 55 FF         jmp  0x49EAAB

file 0x9E775 / VA 0x49F375, 6 bytes:
  E9 71 76 AA 00 90      jmp 0xF469EB ; nop

file 0x8C9FEB / VA 0xF469EB, 19 bytes:
  85 F6                  test esi, esi
  0F 84 B4 89 55 FF      je   0x49F3A7
  8B 8E D0 00 00 00      mov  ecx, [esi+0xD0]
  E9 7D 89 55 FF         jmp  0x49F37B
```

Empty `.xdiff` tail is used: `0x8C9FB0..0x8C9FFF`. Navi hook cave ends at `0x8C9FD0`; guards start at `0x8C9FD8` and `0x8C9FEB`.

## Complete reproducible patch list

Base: live `OzRo.exe` (timestamp 0). Applying these bytes in order produces the final hash `19d81cac...` exactly.

```python
patches = [
 (0x140,    bytes.fromhex("c0aef75c")),  # TimeDateStamp 2019-06-05 12:00 UTC
 (0x17E100, bytes.fromhex("e9ab7c9c00")),  # nav button hook
 (0x8C9FB0, bytes.fromhex("3d9c0100000f84488963ff8d8097feffff3db50000000f874e8363ffe93b8363ff")),  # nav button cave
 (0x2F6BBF, bytes.fromhex("db")),  # WID_NAVIGATIONV4WND 203 -> default
 (0x9DEA5,  bytes.fromhex("e92e7faa0090")),  # guard 49EA70
 (0x8C9FD8, bytes.fromhex("85f60f847e8355ff8b8ed0000000e9c08055ff")),  # guard cave A
 (0x9E775,  bytes.fromhex("e97176aa0090")),  # guard 49F340
 (0x8C9FEB, bytes.fromhex("85f60f84b48955ff8b8ed0000000e97d8955ff")),  # guard cave B
]
```

Validation: SHA-256 of the result must be `19d81cac4684ff267cab558b7abebd3a126483ac028e5e7060a1911d1c7cce24`.

## Decompiled source (reference, offsets differ slightly)

`/home/oz/Descargas/rodecomp/Source/`

Relevant:
- `UI/Window/WindowId.h` — window IDs.
- `UI/Window/UIWindowMgr.cpp` — `EnsureWindow` switch, `WID_NAVIGATIONV4WND` case at ~6397, hotkey at ~4507.
- `UI/Navigation/UIRoMapWnd.cpp` — world map `SendMsg` ~722; `ID_BASE` calls `EnsureWindow(203)`; `ID_SEARCH` calls `g_navigationManager.SearchNavigation` without null check.
- `UI/Navigation/UINavigationV4Wnd.cpp` / `UINavigationWnd.cpp`.
- `UI/Menu/UIMenuIconWnd.cpp` — menu icon navigation `EnsureWindow(203)`.
- `UI/Shortcuts/UIShortCutWnd.cpp` — hotkey path.

RTTI class names present in binary: `UINavigationV4Wnd`, `UINavigationWnd`, `UINavigationHelpWnd`, `UINavigationroadiconWnd`, `UINavigationRuideWnd`, `UIRoMapWnd`, `UIMiniMapWnd`.

Embedded: Lua 5.1.4; `CDClient.dll`, `cps.dll` external.

## Do not repeat

- Do not use WARP `HideGameWindows` on this build; wrong table base corrupts `.rdata` text.
- Do not apply WARP patches in separate sessions; include all in one session or previous tags are stripped.
- Do not assume PE timestamp from filename; check `0x140`.
- Do not set timestamp to raw `20190605`; use a real Unix timestamp. Noon UTC avoids date-boundary issues.
- Do not block window 203 without the two null guards; world-map click crashes at `0x49EAA5`.
- Do not use `2019-06-05fRagexe_patched.exe` as base; lacks live data/GRF patch set.
- Do not write patches beyond `.xdiff` tail `0xF46A00`; section ends there.
- Do not mark new experimental exes executable if Wine double-click is desired; mode `664`.
