# OzRo Client

Parche de cliente de Ragnarok Online para **OzRagnarok**. Proyecto pequeño (3 jugadores), mantenido por una persona, sin updater ni servicios web para el cliente: se edita `patch/`, se comprime en `dist/patch.zip` y se reparte por USB o link. Cada jugador descomprime en la raíz de su cliente y juega. El sitio público es solo informativo: `https://ro.ozkr.net/`.

El cliente actual lee directamente la carpeta `data/` del disco. **`ozro.grf` ya no se usa.** No hay que empaquetar GRF propio ni mantener versiones del parche.

## Cómo carga el cliente

- `OzRo.exe` es un Ragexe parcheado con WARP. No se toca salvo cambio de PACKETVER.
- `data.ini` lista los GRF base (gefenia, renewal2021, resources2021, data, rdata).
- `data/` en disco tiene prioridad sobre esos GRF. Ahí van los assets del cliente.
- `patch/` es el overlay listo para comprimir.

## Estructura

```
patch/
  OzRo.exe
  data.ini
  data/                     overlay: clientinfo, texturas...
    texture/<carpeta coreana>/item/         iconos 24x24 de items custom
    texture/<carpeta coreana>/collection/   imágenes grandes de items custom
  System/itemInfo_EN.lua    FUENTE DE VERDAD de nombres y descripciones
  gefenia.grf               referencia local, NO va en el zip
  OzRo.ico                  referencia local, NO va en el zip

dist/
  patch.zip                 zip manual para repartir
```

## Items: fuente de verdad

El cliente usa **solo** `patch/System/itemInfo_EN.lua`. No hay archivo de staging aparte: la entrada se edita directamente ahí, dentro de `tbl`.

### Codificación (importante)

El archivo contiene bytes de dos mundos:

- **Texto visible** (`*DisplayName` y `*DescriptionName`): **ISO-8859-1 / Windows-1252**. Así se renderizan bien tildes y `ñ` con `langtype 12`.
- **`ResourceName` vanilla**: bytes **CP949** (coreano). Los custom usan ASCII (`ozro_platinum_coin`).

A nivel de archivo todos son bytes `0x00-0xFF`, así que **puedes abrirlo y guardarlo entero como ISO-8859-1**: el round-trip es exacto. Los `ResourceName` coreanos se verán como mojibake (`¿µÈ¥ÀÇÁ¶°¢`), pero conservan sus bytes.

Reglas para que sea seguro:

1. Abre el archivo explícitamente como **ISO-8859-1**, no como UTF-8 ni en autodetectado. En VS Code: *Reopen with Encoding* → *Western (ISO 8859-1)*.
2. Guarda con la misma codificación. No uses *Save with Encoding: UTF-8*.
3. No toques los `ResourceName` coreanos: no los retipees ni los pegues desde una fuente Unicode.
4. Para items custom usa `ResourceName` ASCII (`ozro_*`); así no dependes de los bytes coreanos.
5. No pegues caracteres fuera de ISO-8859-1 (coreano, comillas curvas, `€`, em dash). Tildes, `ñ`, `¿` y `¡` están bien.

Riesgo:

- **Bajo** si el editor abre y guarda ISO-8859-1 de forma estricta.
- **Medio** si el editor interpreta Windows-1252 o autodetecta: puede cambiar bytes en `0x80-0x9F` (hay unos pocos, dentro de nombres coreanos y un apóstrofo curvo) al guardar como ISO-8859-1.
- **Alto** si abre como UTF-8 o convierte a UTF-8: rompe los `ResourceName`.

Comprobación rápida: abre y guarda sin cambiar nada; `git diff --stat patch/System/itemInfo_EN.lua` debe quedar vacío. Si aparecen miles de líneas, el editor reconvirtió el archivo: `git checkout -- patch/System/itemInfo_EN.lua`.

### Añadir un item custom

1. Añade la entrada directamente en `patch/System/itemInfo_EN.lua`, dentro de `tbl`, respetando el encoding: texto Latin-1, `ResourceName` tal cual. El `identifiedResourceName` debe coincidir con el BMP sin extensión.
2. Copia el icono a `patch/data/texture/<carpeta coreana existente>/item/<resource>.bmp` y la imagen grande a `.../collection/<resource>.bmp`. Usa la misma carpeta coreana que ya contiene `loading00.jpg`; no crees otra.
3. Alta en el servidor: `rathena/db/import/item_db.yml` (fuera de este repo).
4. Comprime el contenido de `patch/` (sin `gefenia.grf` ni `OzRo.ico`) en `dist/patch.zip`.
5. Prueba: `@reloaditemdb`, `@item <AegisName>`, y revisa nombre, descripción, icono e imagen grande.

**Nota:** si un item usa un `ResourceName` vanilla (ej. `백금화`), el icono y la imagen grande salen del GRF base y no necesitan BMP en `data/`. Si usa un nombre custom (`ozro_*`), ambos BMP tienen que existir en `data/texture/.../item/` y `data/texture/.../collection/` o el cliente mostrará `Resource File Loading fail`. Antes las monedas custom parecían tener icono porque sus entradas usaban resource names vanilla, no los BMP custom.

Items de prueba actuales:

| ID | AegisName | Uso |
|----|-----------|-----|
| 35001 | Ozro_Platinum_Coin | Moneda premium |
| 35002 | Ozro_Gold_Coin | Moneda alta |
| 35003 | Ozro_Silver_Coin | Moneda media |
| 35004 | Ozro_Bronze_Coin | Moneda baja |
| 35005 | MVP_Soul | Invocaciones; buen test de encoding con resource name coreano |
| 35010 | Ozro_Apple | Test; requiere alta en el server para poder usarlo |

## Flujo de trabajo

1. Edita en `patch/`.
2. Prueba en el cliente/servidor.
3. Comprime el contenido de `patch/` en `dist/patch.zip` (excluye `gefenia.grf` y `OzRo.ico`).
4. Reparte el zip por USB o link. Sin updater ni servicios web para el cliente.
