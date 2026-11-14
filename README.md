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

`itemInfo_EN.lua` es un archivo de **encoding mixto**:

- **Texto visible** (`*DisplayName` y `*DescriptionName`): **ISO-8859-1**. Así se renderizan bien tildes y `ñ` con `langtype 12`.
- **`ResourceName`**: **CP949** si es un nombre vanilla coreano (ej. `영혼의조각`), o ASCII si es custom (ej. `ozro_platinum_coin`).

No guardes el archivo completo como Latin-1 ni como CP949: romperías la otra mitad. Tampoco lo abras y lo guardes con un editor que re-codifique todo el archivo. Si editas a mano, cambia solo el texto entre comillas y conserva los bytes de los `ResourceName` coreanos.

Consecuencia práctica: decodificar el archivo entero como CP949 o como Latin-1 falla o corrompe nombres. Cualquier script que lo procese debe trabajar por campo.

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
