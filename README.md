# OzRo Client

Parche de cliente de Ragnarok Online para **OzRagnarok** (3 jugadores). Se mantiene a mano, sin updater ni servicios web. Se edita `patch/`, se comprime en `dist/patch.zip` y se reparte por USB o link; cada jugador lo descomprime en la raíz de su cliente. Sitio informativo: `https://ro.ozkr.net/`.

## Estructura

```
patch/
  OzRo.exe
  data.ini
  data/                    overlay que pisa los GRF (clientinfo, texturas...)
  System/itemInfo_EN.lua   fuente de verdad de nombres y descripciones de items
  gefenia.grf, OzRo.ico    referencias locales
dist/patch.zip             paquete manual para repartir
tools/grf.py               lector/extractor GRF v2
tmp/                       pruebas y GRFs locales (ignorado por git)
```

`OzRo.exe` lee `data.ini` y `data/`; `data/` tiene prioridad sobre los GRF. No hay `ozro.grf`.

## Items

- Editar `patch/System/itemInfo_EN.lua` dentro de `tbl`. Es la única fuente; no hay archivo de staging.
- Encoding mixto: texto visible en **ISO-8859-1/CP1252**; `ResourceName` vanilla en **CP949**; custom en ASCII (`ozro_*`).
- Abrir y guardar el archivo como **ISO-8859-1 estricto** (no UTF-8 ni autodetectado). Los `ResourceName` coreanos se ven como mojibake y no se tocan. Guardar sin cambios debe dejar `git diff` vacío; si aparece un diff masivo, `git checkout -- patch/System/itemInfo_EN.lua`.
- Para añadir un item: entrada en `itemInfo_EN.lua`, icono y collection en `patch/data/texture/<carpeta coreana>/item|collection/<resource>.bmp`, alta en `rathena/db/import/item_db.yml` (fuera de este repo), probar con `@reloaditemdb` y `@item`, y repackear.
- Si el `ResourceName` es custom y falta el BMP de item o collection, el cliente muestra `Resource File Loading fail`.

## Quests y CTRL+U

- El server define las quests en `rathena/db/import/quest_db.yml` y en los scripts (`setquest`/`setquestinfo`).
- El cliente muestra la ventana CTRL+U desde `System/OngoingQuestInfoList_True_EN.lub` (y variantes `_EN`/`_True`) en la carpeta del cliente; si se overridea, va en `patch/System/`. **Cada QuestID debe existir en ambos lados**: si falta en el cliente, la quest aparece vacía/rota aunque el server la tenga.
- Bounty boards: `F_Bounty_Board` recibe cuartetos `MonsterID, QuestID, BaseExp, JobExp`; cada `QuestID` tiene que estar en `quest_db.yml` y en la lista del cliente.
- Estado actual: los 188 IDs custom de `quest_db.yml` y los 181 IDs usados por las bounty boards están presentes en la lista del cliente.
- `npc/custom/ozro/hunting_missions.txt` (Hunting Missions, Euphy) está deshabilitado en `scripts_custom.conf`. Usa variables de personaje (`Mission0`, `#Mission_Delay`), **no** el sistema de quests, así que no afecta CTRL+U.
- En `npc/custom/ozro/bounty/Geffen.txt` están comentados `FAKE_ANGEL` (1371/62691) y `MINI_DEMON` (1292/62693). Ambos IDs existen hoy en `quest_db.yml` y en la lista del cliente; se pueden reactivar y probar.
- Al crear una quest custom: alta en `quest_db.yml`, entrada en la lista del cliente, y prueba en CTRL+U. `DISABLE_QUESTINFO_MARKERS` solo oculta el icono de questinfo sobre el NPC, no la ventana de quests.

## Mapas sin árboles de navidad

El `data.grf` actual trae versiones de evento en varias ciudades. En `patch/data/` hay overrides `.rsw` no-event para quitar los árboles y la decoración de modelos:

| Mapa | Origen |
|---|---|
| `prontera.rsw` | `pprontera.rsw` del mismo `data.grf` |
| `geffen.rsw`, `izlude.rsw`, `aldebaran.rsw`, `alberta.rsw`, `hugel.rsw` | kRO 2020 (`kro_20200306_data.grf`) |

- Solo se reemplaza el `.rsw`. Los `.gnd`/`.gat` siguen saliendo de `data.grf`, así que la colisión y el `map_cache` del server no cambian. Si queda decoración en el piso, habría que reemplazar también el `.gnd`.
- Para revertir un mapa: borrar `patch/data/<mapa>.rsw`.
- Izlude 2020 conserva 4 modelos pequeños de pan navideño, no árboles; el resto de las ciudades quedó sin referencias navideñas.
- Otras ciudades: Rachel/Malangdo/Lasagna tienen referencias menores; Payon, Lighthalzen, Einbroch, Veins, Umbala, etc. tienen el RSW cifrado y no se escanearon.
- Si el cliente muestra modelos faltantes o NPCs desalineados, probar el set GND/RSW completo de la misma fuente o revertir ese mapa puntual.

## Imágenes (genkit, externo)

Herramienta: `/home/oz/Code/genkit` (perfiles YAML + Replicate/RunPod). Perfiles RO:

- `ro-item-icon`: RD+ `skill_icon`, genera 96×96 y deja BMP **24×24, 8bpp, fondo magenta**.
- `ro-item-illustration`: RunPod Flux Schnell, genera 512×688 y deja BMP **75×100, 24bpp, fondo blanco**.

Flujo recomendado: **3 variantes de icono y 3 de ilustración por item, con seed random**, armar una overview y que el usuario elija. No elegir automáticamente.

```bash
cd /home/oz/Code/genkit
./run.sh image --profile ro-item-icon --prompt "..." --out /ruta/item/<resource>.bmp
./run.sh image --profile ro-item-illustration --prompt "..." --out /ruta/collection/<resource>.bmp
```

Preferencias de estilo:

- Iconos: pixel art RO, silueta clara, 1px de outline, sin texto.
- Ilustraciones: acuarela/lápiz de color, ligera inclinación en tres cuartos, sombra suave separada del objeto, fondo blanco.
- Los perfiles hacen el postproceso local con Pillow; `--out` debe terminar en `.bmp`.

## GRF

`tools/grf.py` lee GRF v2 (rdata.grf), lista y extrae. No escribe ni repackea todavía.

```bash
python3 tools/grf.py info tmp/rdata.grf
python3 tools/grf.py list tmp/rdata.grf --filter collection --limit 20
python3 tools/grf.py extract tmp/rdata.grf "data/texture/.../collection/amber.bmp" --out /tmp/amber.bmp
python3 tools/grf.py extract-matching tmp/rdata.grf --filter .gat --out-dir /tmp/gat --limit 3
```

Los mapas `.gat`/`.rsw`/`.gnd` de rdata son plaintext. La única entrada DES se reporta como no soportada.

## Enviar cambios

1. Editar y probar en `patch/`.
2. Comprimir el contenido de `patch/` en `dist/patch.zip`.
3. Repartir por USB o link; descomprimir en la raíz del cliente.
