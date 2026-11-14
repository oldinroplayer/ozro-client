# Staging de mapas faltantes

Mapas que el server conoce pero cuyo `.gat/.rsw/.gnd` no está en el cliente
desplegado. Se extraen aquí, se prueban **de a uno** y, si cargan bien, recién
después pasan a `patch/data/`.

Prioridad actual: **mapas de job quest**. Las instancias se pueden desactivar.

## Estado

- Server: 1295 mapas (`db/map_index.txt`).
- Cliente desplegado: 912 mapas.
- Faltan: 386.
  - Presentes en el `data.grf` 2025: **136** (casi todas instancias nuevas).
  - Presentes en el `data.grf` 2021: **0**.
  - En ninguno de los dos GRF parciales: **250**.
- Los donantes de `Descargas` solo traen `data.grf` (2021) y `data.grf`+`en.grf`
  (2025). Es probable que los clientes kRO completos (20210406/20220721/20230404)
  sí tengan los mapas que faltan, sobre todo los de job quest.

## Job quests afectados

Ver `manifest.tsv`. Por ahora ninguno está disponible en los GRF parciales:

- `npc/re/jobs/novice/academy.txt` → `new_1-1` … `new_5-4`
- `npc/re/jobs/3-1/warlock.txt` → `job3_war02`
- `npc/re/jobs/3-1/mechanic.txt` → `jupe_core2`
- `npc/re/jobs/3-2/sura.txt` → `sword_1-1`, `sword_2-1`

El `map_cache.dat` del server ya tiene la colisión de esos mapas; lo que falta
es el asset visual del cliente.

## Resultado con el cliente 2023 (libgrf)

- `libgrf` abre el cliente 2023 (probado extrayendo `airplane.gat`).
- Los mapas de job quest (`job3_war02`, `jupe_core2`, `sword_1-1`, `sword_2-1`,
  `new_*`) **no están** en `2023/client/data.grf` ni `rdata.grf`, ni en
  `ro2021/data.grf`, ni en el cliente desplegado (`data.grf`/`rdata.grf`).
- Solo existen como `.mcache` en `/home/oz/Code/ozro/maps/re/` (cache del server),
  sin `.gat/.rsw/.gnd` visuales.
- Por ahora no hay fuente de assets para estos mapas; las opciones son conseguir
  un cliente antiguo que los tenga o desactivar las job quests afectadas.

## Uso

Extraer un mapa desde un GRF a `staging/maps/<map>/data/`:

```bash
python3 tools/extract_map.py --grf /ruta/data.grf --map jupe_core2
```

Instalar directo en el cliente para probar (copiar a `/mnt/games/OzRo/data/`):

```bash
python3 tools/extract_map.py --grf /ruta/data.grf --map jupe_core2 --install
```

Luego, en el juego: warp al mapa / hacer la job quest y revisar que no haya
modelos faltantes ni crash. Si falla, borrar los archivos de `data/` (no están
en git) y volver a intentar con otra fuente.

## Limitaciones

- El extractor saca solo `.gat`, `.rsw` y `.gnd`. No sigue las referencias del
  `.rsw` a modelos/texturas; si faltan, hay que extraerlos aparte.
- Algunos GRF tienen los mapas cifrados (DES, type `0x05`): el `data.grf` 2021 y
  el del cliente desplegado. `tools/grf.py` no los extrae. Usar un GRF plaintext
  (el `data.grf` 2025 sí lo es) o una herramienta con soporte DES.
- Si el `.rsw/.gnd` es de una versión más nueva que el exe 2019, puede no
  cargar. Probar uno por uno antes de agregar más.
- Los archivos extraídos quedan ignorados por git (ver `.gitignore` en esta
  carpeta); solo se versionan el manifiesto y esta documentación.
