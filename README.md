# c4d-skills

Скиллы Claude Code для работы в Cinema 4D 2024: план → исполнение → итерации → финал.

## Состав

| Скилл | Что делает |
|---|---|
| `/c4d-plan` | Планировщик: допрос по идее, `shotplan.md`, `scene.json` (с ключевыми кадрами и пресетом рендера), промты проходов. C4D не нужна. |
| `/c4d` | Исполнитель с режимами: `сцена`, `ассеты`, `анимация`, `материалы`, `свет`, `рендер`, `итерации`, свободная работа. Главы — `skills/c4d/modes/*.md`. |
| `c4d-core` | База: мост и раннер, preflight/рестарт, прелюдия, лестница пресетов, гейты, инструменты и справочники. |

## Инструменты (`skills/c4d-core/bin`)

| | |
|---|---|
| `preflight.sh` / `restart.sh` | проверка связи / перезапуск C4D с exec_python |
| `run.py` | выполнить скрипт проекта в C4D (прелюдия, PROJ, активный документ) |
| `playblast.py` | черновое видео пачками под лимит моста, со звуком |
| `keysheet.py` | лист ключевых кадров движком финала + % пересвета — гейт перед финалом и после правок камеры |
| `final.py` | `estimate` → `launch --accepted keys-vN` (Picture Viewer, асинхронно) → `watch` (сборка mp4/ProRes) |
| `clipcheck.py`, `c4d.py` | пересвет PNG; низкоуровневый клиент моста |

Справочники (`skills/c4d-core/reference`): `traps.md` (ловушки C4D), `motion.md`
(принципы анимации и камеры), `render-presets.md` + `rs_presets.py` (пресеты рендера),
`model-sources.md` (новые модели), `bridge.md` (команды моста).

## Установка

```bash
git clone https://github.com/alexkeykey/c4d-skills ~/c4d-skills
~/c4d-skills/install.sh
```

Симлинки из `~/.claude/skills/` на папки репо: `git pull` обновляет скиллы.

## Требования

- Cinema 4D 2024 с плагином `cinema4d_mcp_bridge` (мост 127.0.0.1:18710) и
  `C4D_MCP_ENABLE_EXEC_PYTHON=1` в окружении запуска (`restart.sh` ставит сам).
- `python3` с Pillow, `ffmpeg`.
