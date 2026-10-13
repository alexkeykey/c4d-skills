# c4d-skills

**English** | [Русский](README.ru.md) | [中文](README.zh-CN.md)

Skills for [Claude Code](https://claude.com/claude-code) that let Claude work in Cinema 4D on its own:
it sets up the scene, models with placeholders and real assets, animates, places the camera,
lights, shades and renders. You describe what you want to see, not which buttons to press.

> The skill instructions are written in Russian. Claude reads them fine and answers in
> whatever language you write to it.

## How it works

The skill works like a small animation studio: every stage has its own role, and the next
stage starts only after you have approved the previous one.

| Stage | What happens |
|---|---|
| **Director** (`/c4d-plan`) | Asks about the scene: duration, mood, camera, what matters. Writes the plan (`shotplan.md`, `scene.json` with key frames) and ready-made prompts for the next stages. Cinema 4D is not needed. |
| **Blocking** (`/c4d сцена`) | The scene in simple shapes: only poses and timing are checked, no lights or materials. |
| **Animator** (`/c4d анимация`) | Turns poses into motion: anticipation, impact, recoil, flips. |
| **Camera operator** | Camera angle and movement, so the action reads clearly. |
| **Assets** (`/c4d ассеты`) | Placeholders are swapped for real models without breaking the animation. |
| **Lights and materials** (`/c4d свет`, `/c4d материалы`) | Several lighting options in a couple of minutes: studio, drama, sunset, neon. |
| **Render** (`/c4d рендер`) | A ladder of presets: quick previews → key-frame sheet → final render in the background. |

Between stages Claude shows a draft video (playblast) or a sheet of key frames.

Mode names after `/c4d` are Russian words (`сцена` = scene, `анимация` = animation,
`ассеты` = assets, `свет` = lighting, `материалы` = materials, `рендер` = render).
You can also just describe the task in your own language: `/c4d set up the lighting`.

## What's inside

| Skill | What it does |
|---|---|
| `/c4d-plan` | Planner: interviews you about the idea, writes `shotplan.md`, `scene.json` (key frames, render preset) and prompts for each pass. |
| `/c4d` | Executor with modes: scene, assets, animation, materials, lighting, render, iterations, free-form work. Chapters live in `skills/c4d/modes/*.md`. |
| `c4d-core` | The base: bridge and script runner, connection check and C4D restart, prelude, render preset ladder, quality gates, tools and references. |

Tools (`skills/c4d-core/bin`):

| | |
|---|---|
| `preflight.sh` / `restart.sh` | connection check / restart C4D with `exec_python` enabled |
| `run.py` | run a project script inside C4D (prelude, project folder, active document) |
| `playblast.py` | draft video in batches that fit the bridge time limit, with sound |
| `keysheet.py` | key-frame sheet rendered with the final engine + % of clipped pixels — a gate before the final render |
| `final.py` | `estimate` → `launch` (Picture Viewer, in the background) → `watch` (builds mp4/ProRes) |
| `clipcheck.py`, `c4d.py` | clipped pixels in a PNG; low-level bridge client |

References (`skills/c4d-core/reference`): `traps.md` (C4D and bridge pitfalls), `motion.md`
(animation and camera principles), `render-presets.md` + `rs_presets.py` (render presets),
`model-sources.md` (where to get models), `bridge.md` (bridge commands).

## Requirements

- **Claude Code** — CLI or app.
- **Cinema 4D 2024 or newer.** Tested on 2024.
- **The `cinema4d_mcp_bridge` plugin** from
  [kumoproductions/mcp-cinema4d](https://github.com/kumoproductions/mcp-cinema4d) (MIT).
  The skills only need the plugin inside C4D; the MCP server from that project is optional.
  Bridge [v0.4.2](https://github.com/kumoproductions/mcp-cinema4d/releases/tag/v0.4.2) is tested
  on C4D 2024; newer versions target C4D 2026.
- `python3` with Pillow and `ffmpeg` — for playblasts and key-frame sheets.
- macOS. The C4D launch scripts (`restart.sh`, `preflight.sh`) are written for macOS.

## Installation

**1. The bridge plugin.** Download the `cinema4d_mcp_bridge` archive from the
[releases page](https://github.com/kumoproductions/mcp-cinema4d/releases) and extract the
`cinema4d_mcp_bridge/` folder into the Cinema 4D plugins folder
(macOS: `~/Library/Preferences/Maxon/Maxon Cinema 4D <version>/plugins/`).

**2. The skills.**

```bash
git clone https://github.com/alexkeykey/c4d-skills ~/c4d-skills
~/c4d-skills/install.sh
```

`install.sh` creates symlinks from `~/.claude/skills/` to the repository folders, so
`git pull` updates the skills right away. Running it again is safe.

**3. Start C4D with the bridge.**

```bash
bash ~/.claude/skills/c4d-core/bin/restart.sh
```

The script launches Cinema 4D with `C4D_MCP_ENABLE_EXEC_PYTHON=1` and waits for the bridge.
By default it looks for `/Applications/Maxon Cinema 4D 2024/Cinema 4D.app`; for another version set the path:
`C4D_APP="/Applications/Maxon Cinema 4D 2026/Cinema 4D.app" bash …/restart.sh`.
Connection check: `bash ~/.claude/skills/c4d-core/bin/preflight.sh`.

## First run

In Claude Code:

```
/c4d-plan podcast intro: a mechanical keyboard switch floating in the air,
pressed a few times with a punchy impact, the word "press" on the keycap
```

The planner asks its questions and hands you prompts for the next stages. Then, in order:
`/c4d сцена` → `/c4d анимация` → `/c4d ассеты` → `/c4d свет` → `/c4d рендер`.

You can skip the plan too: `/c4d what is in the scene right now?` or
`/c4d move the camera lower and render a preview`.

## Security

The skills run Python code inside Cinema 4D (`exec_python`). That code has the same rights as
C4D itself: files, network, launching programs. So:

- work on a copy of the scene or with version control;
- keep action approvals in Claude Code turned on unless you are sure;
- the bridge listens on `127.0.0.1` only. If other people use the computer, set a
  `C4D_MCP_TOKEN` — see the
  [bridge README](https://github.com/kumoproductions/mcp-cinema4d#security).

Cinema 4D 2026.4 and later ship a built-in MCP server from Maxon. The skills in this repository
work through the `cinema4d_mcp_bridge` bridge; do not enable both servers in the same client.

## License

[MIT](LICENSE) © 2026 Alexey Kurbatov. The bridge plugin is a separate project with its own
MIT license: [kumoproductions/mcp-cinema4d](https://github.com/kumoproductions/mcp-cinema4d).
