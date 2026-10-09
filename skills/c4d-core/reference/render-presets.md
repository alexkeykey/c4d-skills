# Рендер-пресеты C4D 2024 (Physical / Standard)

Справочник для `renderladder.py` и /c4d-look. Redshift не используем.
Метки: **[П]** — подтверждено замером в проектах пользователя; **[Д]** — из документации Maxon,
нужен замер; **[?]** — оценка. Имена констант сверены со стабами C4D 2024
(`resource/modules/python/libs/python311/c4d/__init__.py`).

## 0. Что уже известно (замеры пользователя)

| Конфиг | Разрешение | с/кадр | Проект |
|---|---|---|---|
| Standard, AA Geometry, без теней (глина) | 960×540 | 0.5–0.7 | lego-flip, blueprint [П] |
| Physical PREVIEW, без MB | 960×540 | 3.3 | lego-flip [П] |
| Physical без GI, шейдинг 2 / размытый шейдинг 2 / размытый свет 1 / AO 4, MB 1/60 | 1920×1080 | 3–4 | blueprint v43, простая сцена [П] |
| Physical 2/1/2/AO2, без MB | 1280×720 | 12–13 | lego-flip v9, LDraw-геометрия [П] |
| Physical 2/2/2/AO4, без MB | 1280×720 | 21–27 | lego-flip [П] |
| Physical 2/2/2/AO4 + MB 1/60 | 1920×1080 | 23–70 | lego-flip, intro v34-hq [П] |
| Standard AA Best + AO | 1920×1080 | > 60 | lego-flip [П] |
| Physical 4/3/2/AO4 | 3840×2160 | ≈29 | blueprint 4K v55 [П] |
| Матовое стекло (размытое преломление) | 960×540 | 212 вместо 19 | intro v30 [П]: ×11 |
| + GI QMC 16 + AO 6 к черновому Physical | 960×540 | 19.6 вместо 17.6 | odysseus [П], зерно |
| GI (IC, глубина 2) | 1080p | 48 | blueprint [П], пересвет |

Выводы: время съедает **сэмплирование Physical**, а не GI или AO. При AO-подразбиении 1 светлые
поверхности зернят, 4 дают чистую картинку [П]. Motion blur и 1080p вместе дают ×2–5.

## 1. Пресеты

Цена указана относительно PRODUCT_FAST (= 1×) при одинаковом разрешении.
Подразбиения Physical: `n` → 2ⁿ (0=1, 1=2, 2=4, 3=8). Сэмплов на пиксель (2ⁿ)²: 2 → 16, 3 → 64 [П: intro].
Каждая ступень примерно удваивает время [Д].

| Пресет | Когда | Движок / сэмплер | Ш / РШ / РС / AO | GI | MB | Цена |
|---|---|---|---|---|---|---|
| DRAFT | блокинг, тайминг, плейбласт | Standard, AA Geometry | — | нет | нет | ≈0.1× [П] |
| KEYS | лист ключевых кадров движком финала | Physical PREVIEW, 50% | пресет | нет | нет | ≈0.3× [П] |
| PRODUCT_FAST | пластик, металл, студия, MG; дефолтный финал | Physical Adaptive 2 | 2 / 2 / 1 / 4 | нет, AO + небо для отражений | нет | **1×** [П] |
| FINAL_MB | то же, с движением, выдержка 1/60 | Physical Adaptive 2 | 2 / 2 / 1 / 4 | нет | 1/60, подразб. 2 | ×1.5–3 [П/?] |
| PRODUCT_GLASS | стекло, вода, прозрачный корпус | Physical Adaptive 2 | 1 / 1 / 1 / 2 | нет | по задаче | ×1.5–3 [П/?] |
| CHAR_OUTDOOR | персонаж или сцена под небом и солнцем | Physical Adaptive 2 | 2 / 1 / 2 / 3 | нет: sky-AO (вариант B — QMC 16) | 1/60 | ×1.2 (B: ×2–4) [?] |
| INTERIOR_GI | интерьер, свет через окна, отскоки | Physical Adaptive 2 | 2 / 1 / 2 / 2 | QMC + Light Mapping | по задаче | ×4–10 [Д, замер] |
| NIGHT_EMISSION | ночь, неон, светящиеся элементы | Physical Adaptive 2 | 2 / 1 / 3 / 3 | нет: реальные источники в эмиттерах | по задаче | ×1.3–2 [?] |
| HQ_4K | 4K-сдача | Physical Adaptive **1** | 4 / 3 / 2 / 4 | нет | по задаче | ≈29 с/кадр 4K [П] |

Ш — `VP_XMB_RAYTRACING_SAMPLES_SHADING_MAX`, РШ — `..._BLURRY_SHADING` (размытые отражения
и преломления), РС — `..._BLURRY_LIGHT` (мягкие тени, UI «Shadow Subdivision»), AO — `..._BLURRY_AO`.

Поверх любого пресета: **ALPHA** — прозрачный фон (§2.9).

## 2. Подробности по пресетам

**2.1 DRAFT** = RS_draft. Отражения не выключать: GGX-материалы в Standard без них чёрные [П].

**2.2 KEYS.** Свет и экспозиция — движком финала, `QUALITY_PREVIEW`, 50%, без MB/DOF; ≤15–20 кадров на вызов моста [П].

**2.3 PRODUCT_FAST** — главный рабочий финал. GI выключен. Объём дают две вещи:
- небо-градиент, которое видят только отражения: Compositing — камера, прозрачность,
  преломление и GI выкл, отражения вкл [П];
- AO-видеопост; при Physical качество AO задаёт только `BLURRY_AO`.

Если зернит:
- на светлых плоскостях — поднять AO до 4;
- в мягких тенях — поднять РС до 2;
- на матовых бликах — поднять РШ.

`RDATA_RAYDEPTH` 6 [П]. «Блестит как лак» — шероховатость в материале, не сэмплы [П].

**2.4 FINAL_MB.** Physical берёт **выдержку**, а не угол затвора. Ставь
`CAMERAOBJECT_SHUTTER_SPEED_PRESET = _CUSTOM` и `CAMERAOBJECT_SHUTTER_SPEED_VALUE = 1/60`.
Пресет `_1_60` значение не меняет: остаётся 1/30, смаз на весь кадр [П].

Шум motion blur лечится `VP_XMB_RAYTRACING_SAMPLES`, то есть начальными сэмплами пикселя, а не
шейдингом. 2 (16 spp) достаточно, а 3 (64 spp) стоили ×5: 49 → 10 с [П: intro v32].
`VP_XMB_MOTION_SAMPLES_MOTION` (1..6; 1 = 0 промежуточных, 2 = 1, 3 = 3): 2 — для вращений
и сальто, 1 — для прямолинейного движения [Д].

Ловушки: смены видимости — ступенькой на f−0.5, иначе «призрак» [П]; частичную видимость Display-тега
Physical не рендерит [П]; динамику и Cloth запекать [Д].

**2.5 PRODUCT_GLASS.** Главная статья расхода — **размытое преломление**
(`MATERIAL_TRANSPARENCY_DISPERSION` > 0, «матовое стекло»): ×11 [П].
- Материал стекла: Dispersion **0**, шероховатость 0; матовость — текстурой/Bump, не размытием.
- `RDATA_RAYDEPTH` 6 (было 8; у CAD-корпуса много прозрачных стенок) [П].
  `RDATA_REFLECTIONDEPTH` 3, `RDATA_SHADOWDEPTH` 3 [Д, замер].
- `MATERIAL_TRANSPARENCY_EXITREFLECTIONS` = False на внутренних стенках [Д].
- Небу-фону Compositing `SEENBYTRANSPARENCY`/`SEENBYREFRACTION` выкл, иначе стекло «молочное» [П].
- `RDATA_ENABLEBLURRY` = False гасит ВСЕ размытые эффекты [Д]; шероховатые блики могут стать
  зеркальными — только с замером.
- `SAMPLES_SHADING_TRANS` не включать: он только против артефактов альфа+MB и дорогой [Д].

**2.6 CHAR_OUTDOOR.** Вариант A без GI (по умолчанию): небо (фон и отражения), солнце Infinite/Area с мягкой тенью, AO с `VPAMBIENTOCCLUSION_ENVIRONMENT`
= True (затенение цвета неба — дешёвый «небесный» свет), слабая заливка без теней.

Вариант B, если нужен честный отскок от земли: GI primary QMC, secondary Off (`GI_SETUP_METHOD_NONE`),
`DIFFUSE_DEPTH` 1, QMC 16 (небо 16). QMC считается попиксельно и не кэшируется, поэтому
не мерцает, только шумит [Д]. Это «почти бесплатно» по odysseus [П], но там же отмечено зерно:
поднимать QMC до 32 или AO-подразбиение.

Irradiance Cache в анимации мерцает на низкой плотности — не брать [Д, П].

**2.7 INTERIOR_GI.** Комбинация Maxon «Fast Complete Diffuse»: primary QMC +
secondary Light Mapping (`GI_SETUP_PRESET_PROGRESSIVE_PREPASS`) [Д].

Для анимации, где движется только камера:
- `LIGHT_MAPPING_PATH_CAMERA` = True + масштаб World: один стабильный кэш, без мерцания [Д].
- анимированы объекты или свет — `LIGHT_MAPPING_ANIMATION` (Full Animation Mode) [Д].
- Prefilter вкл (6–8) уменьшает мерцание [Д].
- Direct Lights вкл: заметно быстрее при реальных источниках [Д].
- Diffuse Depth 3: глубже уже в основном просто осветляет [Д].

Light Map проверять в режиме Visualize, финал — в Normal [Д]. Пересвет — `PRIMARY/SECONDARY_INTENSITY` < 1 [?].

**2.8 NIGHT_EMISSION.** Светящиеся материалы (Luminance) без GI сцену не освещают.
Самый дешёвый и стабильный путь [?]:
- материал-эмиттер (Luminance) плюс реальный Area-свет той же формы внутри или рядом;
  у света выключить «Show in Specular», если блик дублируется;
- тёмные зоны освещены мягкими тенями от Area, поэтому РС 3 и AO 3;
- `RDATA_FORMATDEPTH_16` против бандинга градиентов в темноте;
- bloom — в посте (`hq/10-grade.py`), а не постэффектом Glow: Glow пользователь выключал [П].

**2.9 ALPHA (накладка)** [П: lego v9, blueprint v41]:
- `RDATA_ALPHACHANNEL` = True и `RDATA_STRAIGHTALPHA` = True, формат PNG. Picture Viewer
  показывает straight-RGB «грязным» — это нормально.
- Фоновым объектам — Compositing: `SEENBYCAMERA`, `SEENBYTRANSPARENCY` и `SEENBYREFRACTION` выкл.
  Отражения и AO от них остаются. Тень на полу пропадает вместе с полом; ловец теней
  пользователь отверг.
- Сборка: `ffmpeg -framerate 30 -i hk_%04d.png -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le out.mov`
  (12-битная версия — `yuva444p12le`).

**2.10 HQ_4K.** Сэмплы на **площадь экрана**: в 4K пикселей ×4, поэтому `VP_XMB_RAYTRACING_SAMPLES`
можно опустить на ступень (2 → 1). Шум на экранный сантиметр сохраняется, а время ≈ как у 1080p
с подразбиением 2 [?, замер]. Подтверждено: 4/3/2/AO4 — ≈29 с/кадр 4K, 2/2/1/AO4 — ≈19 с/кадр [П].

## 3. Словарь для билдера

Ключи и строковые значения — имена констант `c4d` (`getattr`, промах → `_MISS`); `gi`/`ao` = None —
видеопост выкл (`BIT_VPDISABLED`); `res` — пиксели или доля `output.res`; `cam` — к камере рендера.

Словарь `RS_PRESETS` живёт в `rs_presets.py` (рядом); применяется `apply_preset(rd, имя)` из
`renderladder.py`. Правишь пресет — правь словарь там и обоснование здесь.


**[П]** подразбиения 2/2/1/4, 2/1/2/2, 4/3/2/4; `SAMPLES` 2; `SHADING_ERROR` 0.1; `RAYDEPTH` 6; выдержка; MB; ALPHA;
DISPERSION 0; QMC 16. **[Д]** `SHADING_MIN`, `MOTION_SAMPLES`, глубины 3, `EXITREFLECTIONS`, GI в INTERIOR_GI,
AO ENVIRONMENT. **[?]** `AO MAXLENGTH` (масштаб сцены), `SAMPLES` 1 в 4K, цены OUTDOOR/NIGHT/INTERIOR.

## 4. Найденные ошибки в текущих скриптах

1. **`RENDERSETTING_AO_*` в C4D 2024 не существует.** В `lego-flip/20-render-hq.py`,
   `blueprint/07-realism.py` и `intro/hq/01-hq-settings.py` эти строки защищены `hasattr`
   и молча пропускались. AO шёл с дефолтной длиной луча, и дистанции 60 и 0.35 из логов
   не применялись. Правильные имена: `VPAMBIENTOCCLUSION_MAXLENGTH`, `_MINLENGTH`, `_DISPERSION`,
   `_MINSAMPLES`, `_MAXSAMPLES`, `_ACCURACY`. При Physical сэмплы AO задаёт `BLURRY_AO`.
2. **`renderladder.py` понижает GI через `GI_SETUP_DATA_IR_DENSITY_QUALITY`.** Это плотность
   *Legacy* Irradiance Cache (`GI_SETUP_METHOD_IRRADIANCE_CACHE`). В 2024 «Irradiance Cache» —
   это `GI_SETUP_METHOD_IC2`, и его плотность — `GI_SETUP_DATA_IC2_QUALITY` (значения те же:
   `GI_SETUP_QUALITY_PREVIEW`…). Ставить оба или выбирать по `GI_SETUP_DATA_PRIMARY_METHOD`.
3. `CAMERAOBJECT_SHUTTER_SPEED_PRESET_1_60` выдержку не меняет. Ставить `_CUSTOM` (0)
   и затем `SHUTTER_SPEED_VALUE` [П].
4. Подразбиения `VP_XMB_*` — float (по стабам). Сэмплер `Interactive` в Python называется
   `VP_XMB_RAYTRACING_SAMPLER_INTERACTIVE` (в UI — Progressive).

## 5. Порядок выбора

```
двигается? ─ нет → PRODUCT_FAST (стекло → PRODUCT_GLASS)
           └ да  → FINAL_MB (стекло → GLASS + MB)
снаружи под небом → CHAR_OUTDOOR (отскок нужен → CHAR_OUTDOOR_GI)
интерьер / окна → INTERIOR_GI    ночь / неон → NIGHT_EMISSION
4K → HQ_4K    прозрачный фон → + ALPHA
```

Каждый новый пресет — сначала `time_frame()` на 2–3 опорных кадрах: самом тяжёлом (стекло,
крупный план) и типичном. Время пишется в `pipeline.md`. Бюджет по умолчанию — ≤15 с/кадр 1080p;
больше — заявка с вариантами (разрешение, MB, подразбиения).

Источники: help.maxon.net/c4d/2024 (Physical Renderer, GI General/Caches/Light Mapping), developers.maxon.net Py 2024.2, стабы и `.res` C4D 2024.
