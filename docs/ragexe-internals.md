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
| + nav window/guards | `/mnt/games/OzRo (experiments)/OzRo-navihide-nonav.exe` | `19d81cac4684ff267cab558b7abebd3a126483ac028e5e7060a1911d1c7cce24` |
| + StartNavigation kill | `/mnt/games/OzRo (experiments)/OzRo-navihide-nonav-noarrows.exe` | `0cfa7681a5dd00eee8a2beb38e4e9b9209ab0a602fa7ca90f7e1542f7b015ee8` |
| + login window cleanup | `/mnt/games/OzRo (experiments)/OzRo.exe` | `39f49643f85ed354e7da1cba288504583b7f835f48679133ce95e7be7ff5b20a` |
| + bank menu button hide | `/mnt/games/OzRo (experiments)/OzRo-nobankbutton2.exe` | `7f3e62096ca9b4e38eaf05f4dd24127c92ff2b1f34581e8aa2793d2b4aef4692` |
| + hide menu icons: keyboard/tip/shop/attendance/achievement/rec | `/mnt/games/OzRo (experiments)/OzRo.exe` | `8e81d4db75b8d603819d6ead778a5bb60636c583df662d7d56cc3073863525a3` |
| + hide menu icon battle/battlegrounds | `/mnt/games/OzRo (experiments)/OzRo.exe` | `a7d4cd97a96ed5d484848f8b452320bde936302c44fbc67612ccc1c99997fd41` |
| + menu window height 197 -> 111 (final) | `/mnt/games/OzRo (experiments)/OzRo.exe` | `84938b455345c8ca9384800a0949d4a12d08f3c8d2822d4feceadf0f4edf4d65` |
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

## Minimap icon navigation (StartNavigation kill)

Minimap town/quest buttons call `CNavigationManager::StartNavigation`, which draws the route arrows. Blocking window 203 does **not** stop these icons.

`CNavigationManager::StartNavigation`:
- Entry VA `0x7B3C30`, stdcall/thiscall cleanup `ret 0x30`.
- Normal early-return path at `0x7B3CF3`: sets `[ebp-0x231]=0`, `[ebp-4]=-1`, destroys the by-value `std::string` at `[ebp+8]` via `call 0x46B690`, then epilogue.
- Patching at `0x7B3C5D` (after prologue/SEH setup) to jump to `0x7B3CF3` returns `false` and still runs the string destructor.

Patch:

```
file 0x3B305D / VA 0x7B3C5D, 5 bytes:
  8B F9 8B 45 20  ->  E9 91 00 00 00    ; jmp 0x7B3CF3
```

Effect: all `StartNavigation` calls return false. Minimap town/quest icon clicks and quest links no longer set a route; no arrows. Icons and the magnifier toggle remain functional. No leak from the by-value string because the destructor path is preserved.

Minimap UI source: `/home/oz/Descargas/rodecomp/Source/UI/Dialogs/UIEditctrlWnd.cpp` (`UIMiniMapWnd::SendMsg`, IDs 1000..1999 towns, >2000 quest marks, both call `StartNavigation`).

## Login window cleanup

`UILoginWnd::OnCreate` is at VA `0x5D6C00` in this build; confirmed by `EnsureWindow(0x145)` = `WID_RPIMAGEWND2` (325). It creates the account-type combo and two bottom buttons.

Object layout observed (actual build, differs from newer decomp headers):
- Combo pointer: `[this+0xC8]`, allocated with `new(0xB8)` at `0x5D736F`.
- Combo `Move(13,10)` at `0x5D73EE`.
- Bottom button id `285` `Move(13,104)` at `0x5D6DDB`.
- Bottom button `ID_MAKEACCOUNT` `Move(87,104)` at `0x5D6F47`.

Patches (move offscreen to `-100,-100`; keep objects/logic intact):

```
file 0x1D61DB / VA 0x5D6DDB: 6A 68 6A 0D -> 6A 9C 6A 9C  ; button 285 Move(13,104)
file 0x1D6347 / VA 0x5D6F47: 6A 68 6A 57 -> 6A 9C 6A 9C  ; ID_MAKEACCOUNT Move(87,104)
file 0x1D67EE / VA 0x5D73EE: 6A 0A 6A 0D -> 6A 9C 6A 9C  ; loginTypeCombo Move(13,10)
```

The combo still initializes and sets `loginExtra = "G000"`. Login/exit buttons are untouched.

### Empty dropdown background

The white dropdown box + arrow is **baked into** `bg_login.tga`; moving the combo only removes its label. The login background is 301x132 32-bit TGA.
- Client TGA loader requires **uncompressed type 2**; an RLE type 10 file is ignored/falls back to GRF. PIL save must use `rle=False`.
- Edit area used: `x=12..173, y=9..32` filled with white (panel color).
- `data/` folder does **not** override existing GRF entries by default (`DataFolderFirst` not active). `data.ini` order: **key 1 is highest priority** (first wins).
- Shipped inside `ozro.grf` at key 1.

## GRF layout (current)

`patch/data.ini`:

```
1=ozro.grf             # base custom: data/ + System/ (highest) - 91 entries
2=gefenia.grf          # custom gefenia maps
3=renewal2021.grf
4=resources2021.grf
5=rdata.grf            # renewal patch data; overrides some data.grf entries
6=data.grf
```

`ozro.grf` is the single custom base. It flattens the former `ozro_data.grf`, `ozro_ui.grf`, `ozro_maps.grf`, `ozro_fixes.grf`, and the loose `patch/System/` files: `msgstringtable.txt`, item/collection/cashshop textures, custom ground sprites, loading/background illustrations, map overrides, `clientinfo.xml`, `etcinfo.txt`, `System/itemInfo_EN.lua`, `System/OngoingQuestInfoList_True_EN.lub`, and `System/Towninfo*.lub`. No loose `data/` or `System/` remains in `patch/`.

The distribution is a clean client: base GRFs + `ozro.grf` + `gefenia.grf` + `data.ini`. `rdata.grf` goes before `data.grf` because it is renewal data and overrides some entries. Future fixes go in a new GRF at key 1 (first wins); the `.exe` is only touched in extreme cases. `tools/grf_pack.py` normalizes each path component from UTF-8-encoded mojibake to CP949.

## NPC signboards

- Source: `data/luafiles514/lua files/signboardlist.lub`, global `SignBoardList` (`IT_SIGNBOARD`), 49294 B in `data.grf`; older 39682 B copy in `rdata.grf`. `ozro.grf` wins (key 1); without it, `rdata.grf` wins over `data.grf`.
- Loader: `data/luafiles514/lua files/signboardlist_f.lub`, function `GetSignBoardListTable(index)`.
- Access pattern: `SignBoardList[index][field]`; returns 8 values:
  `MAPNAME, CELLX, CELLY, HEIGHT, ICONID, FILEPATH, CONTENTS, CHARCOLOR`.
- Renders world NPC head icons/nameplates. Icons:
  `information\over_guide.bmp`, `information\over_store.bmp`, `information\over_kafra.bmp`,
  `information\over_inn.bmp`, `information\over_warp.bmp`-style paths; custom entries carry `CONTENTS` text.
- Empty `SignBoardList = {}` -> `SignBoardList_F.lua:30: attempt to index field '?' (a nil value)`.
- Disable without error: one dummy entry:
  `MAPNAME="disabled", CELLX=0, CELLY=0, HEIGHT=0, ICONID=0, FILEPATH="", CONTENTS="", CHARCOLOR=0`.
- Override via `ozro.grf` (data.ini key 1, first wins). `data/` does not override GRF entries without `DataFolderFirst`.

## Towninfo load path

- Client opens `System/Towninfo_EN.lub`; `System/Towninfo.lub` is not opened (Wine `strace`, openat).
- Towninfo feeds minimap town icons only, not world NPC head icons.
- Empty `mapNPCInfoTable = {}` removes minimap town icons; restore original files to recover them.
- `MINIMAPWNDINFO.WHOWNPC` (registry `Software\Wow6432Node\Gravity Soft\Ragnarok\UIRectInfo`; default `1`) = minimap "show towns", not head icons.
- `.xdiff` begins with ASCII override list: `System/Towninfo_EN.lub`, `system\OngoingQuestInfoList_True_EN`, `system\RecommendedQuestInfoList_True_EN`, `DATA.INI`, etc.

## Bank menu button

`UIMenuIconWnd::OnCreate` creates the menu icons; the bank button is the basic-info/menu entry id **`0x1BB`** (443), not `MENUICON_BANK` (`0x1CD` / 461, which is a different menu icon).

Visibility table for the basic window buttons: VA `0x57F5C4`, normalized id = `id - 0x169`.

Patch (hide bank button):

```
file 0x17EA16 / VA 0x57F616 (0x57F5C4 + 0x52): 01 -> 00
```

`0x1CD` (file `0x17EA28`) was tested first and did **not** hide the basic bank button; it is the `MENUICON_BANK` menu icon id, not the button the NPC replaced. The bank UI itself is opened by the NPC via `openbank` (`OUT_UI_BANK`); do not block `WID_BANK_NEWWND`.

## Main menu icons (hide options)

`UIMenuIconWnd::OnCreate` (VA `0x57E680`) builds the menu from two parallel 22-entry local arrays constructed from `.rdata` constants:

- ids array (`ids[0..21]`), loaded via `movaps` from VA `0xADCB90`, `0xADCBA0`, `0xADCB80`, `0xADCBB0`, `0xADCBC0`, plus two immediates.
- names array: `status, equip, item, skill, booking, party, guild, battle, quest, map, navigation, option, bank, rec, mail, achievement, tip, shop, keyboard, sns, attendance, adventurerAgency`.

| name | id | notes |
|---|---|---|
| keyboard | `0x160` | Shortcut Description (opens `UIHotkeyGuideWnd`) |
| battle | `0x166` | Battlegrounds (crossed swords); **not** Battle Mode (`/bm`) |
| rec | `0x17D` | replay/record |
| achievement | `0x1C7` | menu id; `MENUICON_ACHIEVEMENT` differs |
| tip | `0x1ED` | |
| shop | `0x1EE` | cash shop |
| attendance | `0x20A` | |
| booking | `0x169` | already skipped by default |
| sns | `0x1F4` | already skipped by default |
| adventurerAgency | `0x20E` | already skipped by default |

Hide mechanism: the create switch at VA `0x57ED00` computes `eax = id - 0x169`, rejects `eax > 0xB5`, then indexes the byte table at VA `0x57F5C4` and jumps through `0x57F5BC`. Table value `00` -> `0x57F303` (skip, no icon, no position slot); value `01` -> `0x57ED1A` (create).

- **id in `0x169..0x21E`**: patch the table byte at file `0x17E9C4 + (id - 0x169)` from `01` to `00`.
- **id below `0x169`**: not addressable by that table; rewrite the ids constant instead:
  - `keyboard` (`ids[18]`, file `0x6DB9C8`): `0x160` -> `0x169`
  - `battle` (`ids[7]`, file `0x6DB9AC`): `0x166` -> `0x169`

Applied hides (all one-byte writes except the two dwords):

```
file 0x17E9D8 / id rec 0x17D:          01 -> 00
file 0x17EA22 / id achievement 0x1C7:  01 -> 00
file 0x17EA48 / id tip 0x1ED:          01 -> 00
file 0x17EA49 / id shop 0x1EE:         01 -> 00
file 0x17EA65 / id attendance 0x20A:   01 -> 00
file 0x6DB9C8 / keyboard 0x160:  60 01 00 00 -> 69 01 00 00
file 0x6DB9AC / battle 0x166:    66 01 00 00 -> 69 01 00 00
```

Skipping does not increment the icon position, so the remaining icons reflow without a gap. This removes the Battlegrounds menu icon only; Battle Mode (`/bm`, checkbox in Shortcut Settings) and the Esc-menu `Shortcut Settings` are untouched.

### Menu window height

The menu panel is the **window geometry**, not an image. `EnsureWindow` creates `UIMenuIconWnd` with `SetSize(220, 197)` then `Move(0, 225)`:

```
VA 0x6F6BE0 / file 0x2F5FE0:
  68 C5 00 00 00   push 197   ; height -> byte at file 0x2F5FE3
  68 DC 00 00 00   push 220   ; width
  call SetSize
  68 E1 00 00 00   push 225   ; Move(0, 225); UIMenuIconWnd::Move sets y = 225 - 4
```

`CUIFrameWnd::Paint` fills `geometry.width × geometry.height` and draws the rounded outline, so the height controls the visible panel. `menu_icon/bg_menu.tga` is **only a translucent overlay** (220×225, black alpha 128, white right edge) drawn at `(0,13)` and clipped to the window; cropping/scaling it would not shrink the panel.

Icons are 32×34 at `x = (position % 5) * 42 + 9`, `y = (position / 5) * 43 + 23`. With 10 visible icons (2 rows) the last icon ends at `y=100`; the original 197 was sized for 4 rows (`y=186` + 11 px). Patch height to 111 to match:

```
file 0x2F5FE3: C5 -> 6F   ; 197 -> 111
```

Height is fixed, so if enough icons are re-enabled to reach a 3rd row (`y=109`, bottom 143), use ~155 instead.

## Complete reproducible patch list

Base: live `OzRo.exe` (timestamp 0). Applying these bytes in order produces the final hash `84938b45...` exactly.

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
 (0x3B305D, bytes.fromhex("e991000000")),  # StartNavigation -> return false
 (0x1D61DB, bytes.fromhex("6a9c6a9c")),  # login button id 285 -> offscreen
 (0x1D6347, bytes.fromhex("6a9c6a9c")),  # login ID_MAKEACCOUNT -> offscreen
 (0x1D67EE, bytes.fromhex("6a9c6a9c")),  # loginTypeCombo -> offscreen
 (0x17EA16, bytes.fromhex("00")),  # basic bank button id 0x1BB -> hidden
 (0x17E9D8, bytes.fromhex("00")),  # menu icon rec 0x17D -> hidden
 (0x17EA22, bytes.fromhex("00")),  # menu icon achievement 0x1C7 -> hidden
 (0x17EA48, bytes.fromhex("00")),  # menu icon tip 0x1ED -> hidden
 (0x17EA49, bytes.fromhex("00")),  # menu icon shop 0x1EE -> hidden
 (0x17EA65, bytes.fromhex("00")),  # menu icon attendance 0x20A -> hidden
 (0x6DB9C8, bytes.fromhex("69010000")),  # menu icon keyboard 0x160 -> 0x169 (skipped)
 (0x6DB9AC, bytes.fromhex("69010000")),  # menu icon battle 0x166 -> 0x169 (skipped)
 (0x2F5FE3, bytes.fromhex("6f")),  # menu window height 197 -> 111
]
```

Validation: SHA-256 of the result must be `84938b455345c8ca9384800a0949d4a12d08f3c8d2822d4feceadf0f4edf4d65`.

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
- `StartNavigation` kill is global: it also disables quest-link navigation. Intentional for OzRo; do not use if navigation should remain partially available.
- Do not use `2019-06-05fRagexe_patched.exe` as base; lacks live data/GRF patch set.
- Do not write patches beyond `.xdiff` tail `0xF46A00`; section ends there.
- Do not mark new experimental exes executable if Wine double-click is desired; mode `664`.
- Do not save UI TGA overrides as RLE (type 10); use uncompressed type 2 (`rle=False`).
- Do not expect `data/` to override a file that already exists in a GRF without `DataFolderFirst`. Use a high-priority GRF (`data.ini` key 1 wins).
- Do not remove world NPC head icons by editing `Towninfo*`; those are signboards (`signboardlist.lub`).
- Do not empty `SignBoardList` to `{}`; keep one dummy entry or `GetSignBoardListTable` errors on `SignBoardList[1]`.
- Do not trust `MINIMAPWNDINFO.WHOWNPC` for head icons; it only toggles minimap town marks.
