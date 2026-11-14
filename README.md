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
