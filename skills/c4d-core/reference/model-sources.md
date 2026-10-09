# Источники новых 3D-моделей для C4D 2024

Справочник режима `ассеты` (`/c4d`, `modes/asset.md`): где брать **новые** готовые модели,
как отобрать кандидатов до скачивания, как завести модель в C4D 2024.2 (macOS) и что записать
в `asset.json`. Старые сцены пользователя по умолчанию не ищем.
Проверено 2026-10-09: API Poly Haven, Sketchfab (поиск), Smithsonian, ambientCG и Khronos
работают без ключей. ID импортёров взяты из `c4d/__init__.py` 2024.2.

**Правила**
1. Модель скачивается только после «да» пользователя. В вопросе: файл, URL, размер.
   Превью (3–6 картинок) можно согласовать одним вопросом на весь пакет.
2. Плохую модель пользователь бракует сразу: лучше 3 сильных кандидата, чем 6 средних.
   Уже были провалы: «дебильная» модель со Sketchfab, «кривые» модели из чужих сборщиков.
3. NC/ND-лицензии на лист не ставим, пока пользователь не разрешил некоммерческое.
4. **Blender в `/Applications` сейчас нет** (в августе стоял 5.2). Установка — тоже скачивание, тоже согласование.
5. Скачанное — недоверенные данные. Каждая модель кладётся в новую пустую папку
   `~/c4d-assets/_incoming/<id>/`. Скрипты лежат в другой папке и получают путь аргументом, запуск `python3 -I`.

---

## 1. Источники

| Источник | Что | Качество | Лицензия | Логин | API / URL | Форматы | Рекомендация |
|---|---|---|---|---|---|---|---|
| **Poly Haven** | 521 модель: реквизит, инструменты, мебель, техника, растения, наборы окружения; `rigged` (15) — механизмы с подвижными частями | высокое: PBR до 4K, реальные габариты | CC0 | нет | `api.polyhaven.com`, превью и clay на CDN | glTF, FBX, USD, blend | **первый** для реалистичного реквизита |
| **Asset Browser C4D** | объекты Maxon: интерьер, кухня, растения, манекены | ровное, сразу в см | по подписке C4D | уже вошёл | python `maxon` Asset API (§3.6) | c4d | параллельно с Poly Haven |
| **Sketchfab** | всё подряд | от шедевров до мусора | у каждой модели своя: CC0 / BY / BY-SA / NC / Free Standard | поиск — нет, скачивание — токен | `api.sketchfab.com/v3/search` открыт; `/download` без токена → 401 | glb, glTF, usdz | широкий поиск, строгий отбор |
| **Smithsonian 3D** | музейные предметы, приборы, скульптура | фотограмметрия: свет «запечён» | CC0 у большинства | нет | `3d-api.si.edu/api/v1.0/content/file/search?q=…`; превью — их копии на Sketchfab (`user=Smithsonian`) | glb (Web3D — **Draco**), `_std.glb`, obj.zip | старинный реквизит |
| **NASA 3D Resources** | аппараты, ракеты, планеты | неровное | без копирайта, NASA Guidelines; эмблемы — не как одобрение | нет | `science.nasa.gov/3d-resources`, `github.com/nasa/NASA-3D-Resources` | glb, obj, stl, 3ds | космос |
| **Khronos glTF-Sample-Assets** | около 150 тестовых моделей (шлем, лампа, шахматы, бумбокс) | эталонный PBR | у каждой своя | нет | `raw.githubusercontent.com/KhronosGroup/glTF-Sample-Assets/main/Models/model-index.json`, `Models/<N>/screenshot/` | glTF, glb (Draco/KTX-варианты не брать) | тест пайплайна |
| **KiCad packages3D** | разъёмы, кнопки, LED, микросхемы, свитчи | точный CAD без текстур | CC-BY-SA 4.0 с исключением для проектов | нет | `gitlab.com/kicad/libraries/kicad-packages3D` | STEP, WRL | электроника в продукт-шоте |
| **McMaster-Carr** | крепёж, подшипники, пружины, профили | точный CAD | для проектирования, без перераспространения | нет | только браузер (антибот), качает пользователь | STEP, IGES | метизы |
| **GrabCAD** | инженерные сборки, моторы | от точного до любительского | по автору + ToS | да | нет | STEP, SLDPRT, STL | механизмы, вручную |
| **Printables / Thingiverse** | корпуса, игрушки | печатный меш: без UV, мм, Z-up | у каждой своя (часто BY / NC) | обычно нет | нет стабильного | STL, 3MF | только ради уникальной формы |
| **LDraw** | все детали LEGO | эталон | CC BY 4.0, часть деталей CC BY 2.0 (`0 !LICENSE` в .dat) | нет | `library.ldraw.org/library/updates/complete.zip` | .dat | **единственный** для LEGO |
| **Kenney / Quaternius** | low-poly; у Quaternius персонажи с ригом и анимациями | чисто, игровой стиль | CC0 | нет (зеркало Poly Pizza — ключ) | zip; Drive/itch | FBX, glTF | только мультяшный стиль |
| **Mixamo** | персонажи с ригом + анимации | среднее–хорошее | бесплатно и для коммерции, сырые файлы не раздавать | Adobe ID | только браузер, бывают сбои | FBX | персонаж с циклом; качает пользователь |
| **Fab / Megascans** | сканы окружения, паки | Megascans — высшее | Fab Standard / CC-BY; с 2025 в основном платно | Epic | нет | FBX, glTF | окружение, вручную |
| **TurboSquid / CGTrader / Free3D (free)** | всё | free в основном слабое | royalty-free | да | нет | FBX, OBJ, c4d | последний резерв |
| **BlenderKit** | модели, материалы | разное | RF / CC0 | да | только аддон Blender | blend | без Blender мимо |
| **Objaverse(++)** (HF) | около 800K моделей со Sketchfab | в основном низкое | у каждой своя | нет | HF `allenai/objaverse` | glb | разве что CC0-фон |
| **ambientCG** | PBR-материалы, HDRI | высокое | CC0 | нет | `ambientcg.com/api/v2/full_json?type=Material&q=…&include=downloadData,imageData` | zip | материалы |

**Генерация (text/image-to-3D):**
- **Meshy** — аккаунт. Free: CC BY 4.0 с указанием Meshy, около 10 загрузок в месяц.
- **Tripo** — аккаунт. Free: права у Tripo, считать NC.
- **Rodin (Hyper3D)** — аккаунт, оплата за каждое скачивание.
- **Hunyuan3D 2.1** — открытые веса, на Mac только community-форки с MPS (около 12 ГБ весов).
  Лицензия Tencent не действует в ЕС, UK и Южной Корее.

Для крупного плана продукта генерация **не годится**: фаски мыльные, плоскости кривые,
свет «запечён», сетка-каша, детали не разделить. Годится для фона, еды и органики, фигурок,
болванки формы. Помечать `"source": "generated:<сервис>"`.

---

## 2. Поиск

### 2.1 Порядок источников по типу объекта

- **Персонаж.** Mixamo (риг и цикл, качает пользователь) → Quaternius, если стиль мультяшный →
  Sketchfab `rigged=true`. Генерацию не предлагать: персонаж будет без рига.
- **Продукт или механизм.** Сначала решить, не собрать ли процедурно в `build.py`, как
  `mx_switch_clear_blue`: для крупного плана это часто лучше. Иначе: CAD производителя,
  KiCad, McMaster (в STEP детали отдельные, фаски точные) → Poly Haven `c=rigged` /
  `c=electronics` → GrabCAD → Sketchfab `staffpicked=true`.
- **Реквизит.** Poly Haven → Asset Browser C4D → Sketchfab (`cc0`/`by`, staffpicked) →
  Smithsonian (старинное) → генерация (фон).
- **Окружение.** Коллекции Poly Haven (`the_shed`, `hidden_alley`, `smugglers_cove`,
  `pine_forest`, `moon`, `project_lighthouse`) + ambientCG + HDRI Poly Haven → Fab (вручную) → Sketchfab.
- **LEGO.** Только LDraw `.dat` через свой конвертер. Образцы: `~/c4d-assets/<деталь>.obj` + `.json`
  (1 LDU = 2 юнита, лицо в +X, Y вверх). LEGO со Sketchfab не брать.

### 2.2 Кандидаты → лист → выбор → скачивание

1. Из плана выписать: объект, стиль, крупность в кадре, риг или подвижные части, коммерция ли это.
2. Опросить 2–3 источника по API, отсеять по метаданным (§2.3), оставить 3–6.
3. Согласовать превью («6 картинок ≈1–2 МБ во временную папку»), собрать лист (скрипт ниже),
   посмотреть самому (Read), показать пользователю (`open sheet.png`).
4. Под листом — таблица: №, название, URL, автор, лицензия, полигоны, текстуры,
   **размер скачивания**, риски (Draco, нет UV, Z-up).
5. Пользователь выбирает → отдельный вопрос на скачивание (файл, URL, размер) → `_incoming/<id>/`.

**Poly Haven** (нужен осмысленный User-Agent):
```bash
UA="c4d-skills/1.0"
curl -s -A "$UA" "https://api.polyhaven.com/assets?t=models&c=electronics"
# поля: name, polycount, dimensions (мм в осях Blender X, Y, Z = высота), max_resolution, authors
curl -s -A "$UA" "https://api.polyhaven.com/files/<id>"   # gltf|fbx|usd|blend → 1k|2k|4k → url, size, include{}
```
Размер скачивания = `size` + сумма `size` из `include` (текстуры идут отдельными файлами).
Превью: `https://cdn.polyhaven.com/asset_img/thumbs/<id>.png?width=512&height=512`,
`…/asset_img/primary/<id>.png?height=780` (beauty), `…/asset_img/renders/<id>/clay.png?height=780` (форма без текстур).

**Sketchfab**:
```bash
curl -s "https://api.sketchfab.com/v3/search?type=models&q=espresso%20machine&downloadable=true\
&license=by&staffpicked=true&max_face_count=200000&sort_by=-likeCount&count=24"
# license: cc0|by|by-sa|free-st (одна на запрос); rigged=true; user=Smithsonian
# поля: faceCount, license.label, user.username, viewerUrl, thumbnails.images[],
#       archives.glb.{size,textureCount,textureMaxResolution}, animationCount, staffpickedAt
```
Скачивание: `GET /v3/models/<uid>/download` с заголовком `Authorization: Token $SKETCHFAB_API_TOKEN`
(личный токен пользователя). Возвращает короткоживущие ссылки на glb, glTF и usdz; FBX через API нет.
Если 401/403 (по некоторым данным, нужен OAuth), пользователь скачивает сам по `viewerUrl`.

**Smithsonian.** `…/file/search?q=<что>&rows=40`. Брать `usage=Download3D`: `*_std.glb` или
`*-obj_std.zip`. `Web3D` и `*_draco.glb` пропускать.

**Лист** — запуск `python3 -P sheet.py items.json sheet.png`. Флаг `-P`, а не `-I`:
PIL стоит в user-site, а `-I` его отключает.
```python
import sys, json
from PIL import Image, ImageDraw, ImageFont
items = json.load(open(sys.argv[1]))  # [{"img": "a.png", "label": "1 · Poly Haven · Drill_01 | 2.9k tris · 4K · CC0"}]
T, CAP, COLS = 480, 64, 3
sheet = Image.new("RGB", (COLS * T, -(-len(items) // COLS) * (T + CAP)), "white")
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 20)
d = ImageDraw.Draw(sheet)
for i, it in enumerate(items):
    x, y = (i % COLS) * T, (i // COLS) * (T + CAP)
    im = Image.open(it["img"]).convert("RGBA")
    im = Image.alpha_composite(Image.new("RGBA", im.size, (232, 232, 232, 255)), im).convert("RGB")
    im.thumbnail((T, T))
    sheet.paste(im, (x + (T - im.width) // 2, y + (T - im.height) // 2))
    for k, line in enumerate(it["label"].split(" | ")[:2]):
        d.text((x + 8, y + T + 6 + k * 26), line, fill="black", font=font)
sheet.save(sys.argv[2])
```

### 2.3 Качество до скачивания

| Критерий | Где смотреть | Норма (герой / фон) |
|---|---|---|
| Полигоны | `polycount`, `faceCount` | 10K–300K / 1K–50K. Миллионы — скан без ретопологии |
| Форма | clay Poly Haven; wireframe во вьюере Sketchfab (открывает пользователь) | ровные плоскости, есть фаски, нет «оплавленности» |
| Текстуры | `files`, `textureCount`, `textureMaxResolution` | PBR (color, roughness, normal, metal), 2K–4K. Diffuse с тенями — минус |
| Масштаб | только Poly Haven `dimensions` | после импорта мерить всегда |
| Риг | `animationCount`, описание | скелет без skin-весов — брак |
| Части | описание, дерево во вьюере | у механизма детали — отдельными объектами |
| Сигналы | staff pick, лайки, портфолио автора | повышают шанс, но не гарантируют |
| Лицензия | `license` | CC0 / BY / Free Standard; NC и ND — только с разрешения |

---

## 3. Импорт в C4D 2024.2

### 3.1 Формат → импортёр

| Формат | ID `c4d.FORMAT_*` | Опции и замечания |
|---|---|---|
| FBX (SDK 2020.3.4) | `FBX_IMPORT` 1026369 | лучший путь для рига и анимации; `FBXIMPORT_SCALE`, `_UP_AXIS*`, `_MATERIALS` |
| glTF / glb | `GLTFIMPORT` 1060210 | **Draco, meshopt и KTX2 не читает**; `GLTFIMPORTER_UNITSCALE`, `_MATERIALS`, `_ANIMATION_*` |
| OBJ + MTL | `OBJ2IMPORT` 1030177 | `OBJIMPORTOPTIONS_SCALE`, `_MATERIAL_MTLFILE`, `_POINTTRANSFORM_SWAPYZ` |
| Alembic | `ABCIMPORT` 1028081 | кэши, без материалов |
| USD / usdz | `USDIMPORT` 1055178 | материалы приходят только в Redshift |
| STEP / IGES / JT / SolidWorks / CATIA V5 | `STEPIMPORT` 1039777, `IGESIMPORT` 1039779, `JTIMPORT` 1039780, `SOLIDWORKSIMPORT` 1039781, `CATIAIMPORT` 1039778 | встроенный CAD Exchange: `CADIMPORT_DETAILING_*`, `_ORIGINAL_UNITS`, `_SCALE` |
| STL | `STL_IMPORT` 1001020 | `STLIMPORTFILTER_SCALE`; обычно мм и Z-up |
| 3DS, DAE, SKP, VRML | `3DSIMPORT`, `DAE15IMPORT`, `SKPIMPORT`… | — |
| blend, 3MF, PLY, glb с Draco/meshopt | нет | через Blender (§3.4) |

### 3.2 Проверка glb/glTF без зависимостей (`python3 -I glbinfo.py <файл>`)

```python
import json, struct, sys
b = open(sys.argv[1], "rb").read()
j = json.loads(b[20:20 + struct.unpack_from("<I", b, 12)[0]]) if b[:4] == b"glTF" else json.loads(b)
acc = j.get("accessors", [])
tris = sum(acc[p["indices"] if "indices" in p else p["attributes"]["POSITION"]]["count"] // 3
           for m in j.get("meshes", []) for p in m["primitives"])
print({"required": j.get("extensionsRequired", []), "tris": tris, "materials": len(j.get("materials", [])),
       "images": len(j.get("images", [])), "skins": len(j.get("skins", [])), "anims": len(j.get("animations", []))})
```
`KHR_draco_mesh_compression`, `EXT_meshopt_compression` или `KHR_texture_basisu` в `required` означают:
нужен другой вариант файла или Blender.

### 3.3 Импорт с опциями (через `bin/run.py`; вживую не прогонялось — первый раз проверить на мелкой модели)

```python
def import_model(path, fmt_id, opts=None, materials=True):
    plug = c4d.plugins.FindPlugin(fmt_id, c4d.PLUGINTYPE_SCENELOADER)
    data = {}
    if opts and plug and plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, data):
        for k, v in opts.items():
            data["imexporter"][k] = v
    flt = c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MERGESCENE   # без DIALOGSALLOWED — без диалогов
    if materials:
        flt |= c4d.SCENEFILTER_MATERIALS
    ok = c4d.documents.MergeDocument(doc, path, flt, None)
    c4d.EventAdd()
    return ok

us = c4d.UnitScaleData(); us.SetUnitScale(1.0, c4d.DOCUMENT_UNIT_M)   # glTF всегда в метрах
import_model(src, c4d.FORMAT_GLTFIMPORT, {c4d.GLTFIMPORTER_UNITSCALE: us})
```
`asset_merge()` из `assetlib.py` грузит **без** `SCENEFILTER_MATERIALS`. Для процедурных ассетов
так и задумано, но у импортной модели пропадут PBR-текстуры. Для импорта — `import_model`.

### 3.4 Конвертация через Blender headless (после установки)

Лучший вариант — glb с Draco → чистый glb, потом нативный импорт: PBR сохраняется.
```bash
B=/Applications/Blender.app/Contents/MacOS/Blender
"$B" -b --factory-startup --python-expr '
import bpy, sys
src, dst = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_draco_mesh_compression_enable=False)
' -- in.glb out_clean.glb
```
glb или blend → FBX (для рига и анимации; Y-up, единицы — см):
```bash
"$B" -b --factory-startup --python-expr '
import bpy, sys
src, dst = sys.argv[sys.argv.index("--") + 1:]
if src.endswith(".blend"): bpy.ops.wm.open_mainfile(filepath=src)
else: bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.export_scene.fbx(filepath=dst, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
    axis_forward="-Z", axis_up="Y", add_leaf_bones=False, mesh_smooth_type="FACE",
    path_mode="COPY", embed_textures=True, bake_anim=True)
' -- in.glb out.fbx
```
`--factory-startup` обязателен: без него автостартует MCP-аддон и блокирует `-b`-процесс
(memory: reference-blender-mcp). Габарит после конвертации всё равно мерить.

### 3.5 Масштаб и оси

В C4D единицы — см, ось Y вверх. Витринная ориентация: лицо в **+X**, низ на `y = 0`.

| Вход | Единицы и оси | Что делать |
|---|---|---|
| glTF / glb | м, Y-up | `UNITSCALE` = 1 м |
| FBX из Blender | см, Y-up | обычно сразу верно |
| FBX Mixamo | рост около 100 вместо 180 | `fit_height` |
| OBJ | что угодно, от 0.01 до 1000 | мерить; при Z-up — `SWAPYZ` |
| STL | мм, Z-up | `STLIMPORTFILTER_SCALE` 0.1, поднять P ±90° |
| STEP | единицы файла (обычно мм) | `CADIMPORT_ORIGINAL_UNITS` вкл. → пересчёт в см |

Дальше — Шаг 3 `modes/asset.md`: `bbox_size` → сверка с реальным размером (Poly Haven:
мм ÷ 10, Blender-Z = C4D-Y) → `fit_height` → `ground_it` → разворот лица в +X (проверка рендером
сверху) → масштаб на импорт-нуль, не на `*_CTRL` → удалить чужие камеры, свет, пустые нули.

### 3.6 Asset Browser C4D (не проверено)

Путь: `maxon.AssetInterface.GetUserPrefsRepository().FindAssets(...)` → `maxon.AssetManagerInterface.LoadAssets`.
Не сработает — пользователь выбирает ассет в Asset Browser сам и называет его.

### 3.7 Гейт приёмки: витрина до лейаута

В сцену модель попадает только после принятия на витрине.
1. Чистый документ или `kit.c4d` (Шаг 3b `modes/asset.md`), модель приведена по §3.5.
2. Четыре камеры примерно на 2.5 габарита, `look()` на центр bbox: 3/4 спереди
   (H 35°, P −15°), профиль, 3/4 сзади, сверху (P −60°). Светлый пол-циклорама, мягкий ключ (`lighting.py`).
3. `use_rs("RS_tex")`, `render_to(...)` 960×540 — по кадру на вызов →
   `<проект>/renders/asset_<id>_{a,b,c,d}.png`. Плюс clay-кадр (на всё один серый материал): видны сетка и фаски.
4. Проверить самому (Read): масштаб рядом с эталоном (кубик 10 см или биппед 180 см), нет дыр,
   вывернутых нормалей, чёрных или розовых текстур, потерянных частей; пивот на месте.
5. Показать пользователю лист кадров. «Да» → `asset_save` + `thumb.png` → лейаут.
   «Нет» → следующий кандидат с листа, бракованную модель не чиним.

---

## 4. Лицензия и происхождение в `asset.json`

К манифесту (`modes/asset.md`, Шаг 1) для импортной модели добавить:

```json
{
  "source": "import",
  "origin": {
    "site": "polyhaven",
    "url": "https://polyhaven.com/a/Drill_01",
    "download_url": "https://dl.polyhaven.org/file/ph-assets/Models/gltf/2k/Drill_01/Drill_01_2k.gltf",
    "original_id": "Drill_01",
    "author": "Fernando Quinn",
    "license": "CC0-1.0",
    "attribution": null,
    "commercial_ok": true,
    "downloaded": "2026-10-09",
    "original_file": "_incoming/Drill_01/Drill_01_2k.gltf",
    "converted": "нет",
    "modified": "масштаб, разворот в +X, удалены камеры"
  },
  "real_size_cm": [18.3, 18.5, 5.2]
}
```
- `license`: `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`, `Sketchfab-Free-Standard`, `Mixamo`,
  `Fab-Standard`, `NASA-guidelines`, `generated:meshy-CC-BY-4.0`. Значение берётся из поля самой модели,
  а не со страницы сайта: у Sketchfab, Objaverse, Khronos и LDraw лицензия у каждой модели своя.
- `attribution` для BY, BY-SA и Meshy free — **готовая строка титра**:
  «"Название" by Автор (URL), CC BY 4.0, modified». Пользователя предупредить при выборе:
  ролик потребует титра.
- BY-SA: ассет, сделанный из такой модели, распространяется только на тех же условиях.
- Оригинал хранить в `_incoming/<id>/`: он доказывает происхождение.
