# c4d-skills

[English](README.md) | [Русский](README.ru.md) | **中文**

适用于 [Claude Code](https://claude.com/claude-code) 的技能包，让 Claude 自己在 Cinema 4D 中工作：
搭建场景、用占位体和真实资产建模、制作动画、布置摄像机、灯光和材质，并完成渲染。
你只需描述想看到的画面，而不是该按哪些按钮。

> 技能说明是用俄语写的。Claude 可以正常理解，并会用你使用的语言回复。

## 工作方式

这个技能像一个小型动画工作室：每个阶段都有自己的角色，只有在你确认上一阶段后，
下一阶段才会开始。

| 阶段 | 内容 |
|---|---|
| **导演**（`/c4d-plan`） | 询问场景细节：时长、氛围、镜头、重点。编写计划（`shotplan.md`、带关键帧的 `scene.json`）以及后续阶段可直接使用的提示词。不需要打开 Cinema 4D。 |
| **布局预演**（`/c4d сцена`） | 用简单几何体搭建场景：只检查姿势和节奏，不涉及灯光和材质。 |
| **动画师**（`/c4d анимация`） | 把姿势变成运动：预备动作、撞击、回弹、翻转。 |
| **摄像师** | 设计机位和运镜，让动作清晰易读。 |
| **资产**（`/c4d ассеты`） | 把占位体替换成真实模型，动画不会被破坏。 |
| **灯光与材质**（`/c4d свет`、`/c4d материалы`） | 几分钟内给出多种灯光方案：影棚、戏剧、日落、霓虹。 |
| **渲染**（`/c4d рендер`） | 渲染预设阶梯：快速预览 → 关键帧拼图 → 后台最终渲染。 |

在各阶段之间，Claude 会展示预览视频（playblast）或关键帧拼图。

`/c4d` 后面的模式名称是俄语单词（`сцена` = 场景，`анимация` = 动画，`ассеты` = 资产，
`свет` = 灯光，`материалы` = 材质，`рендер` = 渲染）。你也可以直接用自己的语言描述任务：
`/c4d 设置灯光`。

## 包含内容

| 技能 | 作用 |
|---|---|
| `/c4d-plan` | 规划器：就创意向你提问，编写 `shotplan.md`、`scene.json`（关键帧、渲染预设）以及每一步的提示词。 |
| `/c4d` | 带模式的执行器：场景、资产、动画、材质、灯光、渲染、迭代、自由操作。各章节位于 `skills/c4d/modes/*.md`。 |
| `c4d-core` | 基础层：桥接与脚本运行器、连接检查与 C4D 重启、预置代码、渲染预设阶梯、质量关卡、工具和参考资料。 |

工具（`skills/c4d-core/bin`）：

| | |
|---|---|
| `preflight.sh` / `restart.sh` | 检查连接 / 以启用 `exec_python` 的方式重启 C4D |
| `run.py` | 在 C4D 中运行项目脚本（预置代码、项目文件夹、当前文档） |
| `playblast.py` | 分批生成带声音的预览视频，避开桥接的时间限制 |
| `keysheet.py` | 用最终渲染引擎输出关键帧拼图 + 过曝像素百分比，作为最终渲染前的关卡 |
| `final.py` | `estimate` → `launch`（图片查看器，后台运行）→ `watch`（合成 mp4/ProRes） |
| `clipcheck.py`、`c4d.py` | PNG 过曝检查；底层桥接客户端 |

参考资料（`skills/c4d-core/reference`）：`traps.md`（C4D 与桥接的常见陷阱）、`motion.md`
（动画与镜头原则）、`render-presets.md` + `rs_presets.py`（渲染预设）、
`model-sources.md`（模型来源）、`bridge.md`（桥接命令）。

## 环境要求

- **Claude Code**：命令行或应用程序。
- **Cinema 4D 2024 或更新版本。** 已在 2024 上测试。
- **`cinema4d_mcp_bridge` 插件**，来自
  [kumoproductions/mcp-cinema4d](https://github.com/kumoproductions/mcp-cinema4d)（MIT）。
  技能只需要 C4D 内的插件，该项目的 MCP 服务器可以不装。
  桥接 [v0.4.2](https://github.com/kumoproductions/mcp-cinema4d/releases/tag/v0.4.2) 已在 C4D 2024 上测试；
  较新版本面向 C4D 2026。
- 带 Pillow 的 `python3` 和 `ffmpeg`：用于预览视频和关键帧拼图。
- macOS。C4D 启动脚本（`restart.sh`、`preflight.sh`）是为 macOS 编写的。

## 安装

**1. 桥接插件。** 从[发布页面](https://github.com/kumoproductions/mcp-cinema4d/releases)下载
`cinema4d_mcp_bridge` 压缩包，把 `cinema4d_mcp_bridge/` 文件夹解压到 Cinema 4D 的插件目录
（macOS：`~/Library/Preferences/Maxon/Maxon Cinema 4D <版本>/plugins/`）。

**2. 技能。**

```bash
git clone https://github.com/alexkeykey/c4d-skills ~/c4d-skills
~/c4d-skills/install.sh
```

`install.sh` 会在 `~/.claude/skills/` 中创建指向仓库文件夹的符号链接，因此
`git pull` 后技能会立即更新。重复运行是安全的。

**3. 启动带桥接的 C4D。**

```bash
bash ~/.claude/skills/c4d-core/bin/restart.sh
```

脚本会以 `C4D_MCP_ENABLE_EXEC_PYTHON=1` 启动 Cinema 4D，并等待桥接就绪。
默认查找 `/Applications/Maxon Cinema 4D 2024/Cinema 4D.app`；其他版本请指定路径：
`C4D_APP="/Applications/Maxon Cinema 4D 2026/Cinema 4D.app" bash …/restart.sh`。
连接检查：`bash ~/.claude/skills/c4d-core/bin/preflight.sh`。

## 首次使用

在 Claude Code 中输入：

```
/c4d-plan 播客片头：一个悬浮在空中的机械键盘轴，
带着有力的撞击感被按下几次，键帽上写着"按下"
```

规划器会提出问题，并给出后续阶段的提示词。之后依次执行：
`/c4d сцена` → `/c4d анимация` → `/c4d ассеты` → `/c4d свет` → `/c4d рендер`。

也可以不做计划直接使用：`/c4d 场景里现在有什么？` 或 `/c4d 把摄像机放低一点并渲染预览`。

## 安全

这些技能会在 Cinema 4D 中执行 Python 代码（`exec_python`）。这些代码拥有与 C4D 本身相同的权限：
文件、网络、启动程序。因此：

- 请在场景副本上工作，或启用版本控制；
- 如果不确定，请保持 Claude Code 中的操作确认开启；
- 桥接只监听 `127.0.0.1`。如果这台电脑还有其他人使用，请设置
  `C4D_MCP_TOKEN`，详见[桥接 README](https://github.com/kumoproductions/mcp-cinema4d#security)。

从 Cinema 4D 2026.4 起，Maxon 内置了 MCP 服务器。本仓库的技能通过 `cinema4d_mcp_bridge`
桥接工作；请不要在同一个客户端中同时启用两个服务器。

## 许可证

[MIT](LICENSE) © 2026 Alexey Kurbatov。桥接插件是独立项目，拥有自己的 MIT 许可证：
[kumoproductions/mcp-cinema4d](https://github.com/kumoproductions/mcp-cinema4d)。
