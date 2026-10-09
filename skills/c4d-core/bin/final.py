#!/usr/bin/env python3
"""Чистовой рендер: замер → запуск в Picture Viewer (асинхронно) → ожидание → сборка.

    final.py estimate [--frames 48,96] [--range 0-179]
        RS_final, полное разрешение, по кадру на вызов; экстраполяция на диапазон,
        сверка с scene.json output.time_budget_min. Кадр > 50 с упрётся в лимит
        моста — это уже ответ: понижать пресет (render-presets.md).

    final.py launch --accepted keys-vN [--range 0-179 | --missing] [--dir renders/final-v{v}]
                    [--alpha] [--cam CAM]
        ГЕЙТ: --accepted — лист ключевых кадров, который пользователь принял ПОСЛЕ
        последней правки камеры/света/материалов. Без него запуск запрещён.
        --missing: продолжить незаконченный прогон с первого недостающего кадра
        (по умолчанию — последний каталог renders/final-v*).
        Пишет строку в pipeline.md. Сразу после запуска — `final.py watch` в фоне.

    final.py watch [--dir …] [--audio wav] [--prores] [--bg '#163B9A'] [--stage final]
        Ждёт все кадры диапазона (по scene.json / последнему запуску), собирает
        mp4 (и ProRes 4444 + превью на цвете при --prores/--bg), проверяет пересвет
        на трёх кадрах, открывает видео. Запускать через Bash run_in_background.
"""
import argparse, glob, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import c4dlib as L

ap = argparse.ArgumentParser()
ap.add_argument("op", choices=["estimate", "launch", "watch"])
ap.add_argument("--proj"); ap.add_argument("--frames"); ap.add_argument("--range")
ap.add_argument("--accepted"); ap.add_argument("--missing", action="store_true")
ap.add_argument("--dir"); ap.add_argument("--alpha", action="store_true"); ap.add_argument("--cam")
ap.add_argument("--audio"); ap.add_argument("--prores", action="store_true"); ap.add_argument("--bg")
ap.add_argument("--stage"); ap.add_argument("--no-open", action="store_true")
a = ap.parse_args()

slug, proj = L.project(a.proj)
sj = L.scene_json(proj)
fps = sj.get("fps", 24)
fr = sj.get("frame_range") or [0, sj.get("length", 120)]
rng = L.parse_frames(a.range) if a.range else list(range(fr[0], fr[1] + 1))
state_p = os.path.join(proj, "renders/.final-state.json")


def frames_in(d):
    got = {}
    for p in glob.glob(os.path.join(d, slug + "_*.png")):
        m = re.search(r"_(\d+)\.png$", p)
        if m and os.path.getsize(p) > 0:
            got[int(m.group(1))] = p
    return got


def latest_dir():
    ds = sorted(glob.glob(os.path.join(proj, "renders/final-v*/")),
                key=lambda p: int(re.search(r"v(\d+)", p).group(1)))
    return ds[-1] if ds else None


if a.op == "estimate":
    kf = L.parse_frames(a.frames) if a.frames else (sj.get("key_frames") or [rng[len(rng) // 2]])[-2:]
    secs = []
    for f in kf:
        r = L.run_job({"op": "time", "frame": f, "path": os.path.join(proj, "renders/time-f%04d.png" % f)},
                      "final_job.py", proj, timeout=70)
        if "error" in r:
            print("f%d: > лимита моста (таймаут) — кадр дороже ~55 с. Понижать пресет." % f)
            L.wait_bridge(600)
            sys.exit(2)
        secs.append(r["sec"]); print("f%d: %.1f с" % (f, r["sec"]))
    worst = max(secs)
    total_min = worst * len(rng) / 60
    budget = (sj.get("output") or {}).get("time_budget_min")
    print("ОЦЕНКА: худший кадр %.1f с × %d кадров ≈ %.0f мин%s" % (
        worst, len(rng), total_min, (" (бюджет %s мин%s)" % (budget, " — ПРЕВЫШЕН" if budget and total_min > budget else "")) if budget else ""))

elif a.op == "launch":
    if not a.accepted:
        sys.exit("ГЕЙТ: нужен --accepted keys-vN — лист ключевых кадров, принятый пользователем "
                 "после последней правки камеры/света/материалов (keysheet.py).")
    if a.missing:
        d = a.dir and os.path.join(proj, a.dir) or latest_dir()
        if not d:
            sys.exit("нет прошлых прогонов renders/final-v*")
        st = json.load(open(state_p)) if os.path.exists(state_p) else {}
        want = list(range(st.get("f0", rng[0]), st.get("f1", rng[-1]) + 1))
        have = frames_in(d)
        miss = [f for f in want if f not in have]
        if not miss:
            sys.exit("все кадры на месте: " + d)
        f0, f1 = miss[0], miss[-1]
        print("дорендер %d кадров: %d–%d (в диапазоне могут быть и готовые — PV их перезапишет)" % (len(miss), f0, f1))
    else:
        d = a.dir and os.path.join(proj, a.dir) or None
        if not d or "{v}" in d:
            d, _ = L.next_version(os.path.join(proj, (a.dir or "renders/final-v{v}").rstrip("/")))
        f0, f1 = rng[0], rng[-1]
    d = d.rstrip("/") + "/"
    os.makedirs(d, exist_ok=True)
    r = L.run_job({"op": "launch", "f0": f0, "f1": f1, "path": d + slug + "_", "alpha": a.alpha,
                   "cam": a.cam}, "final_job.py", proj)
    if "error" in r:
        sys.exit("launch: " + r["error"])
    st = {"dir": d, "f0": f0 if not a.missing else json.load(open(state_p)).get("f0", f0),
          "f1": f1 if not a.missing else json.load(open(state_p)).get("f1", f1),
          "alpha": a.alpha, "accepted": a.accepted, "launched": time.strftime("%Y-%m-%d %H:%M")}
    json.dump(st, open(state_p, "w"), ensure_ascii=False)
    with open(os.path.join(proj, "pipeline.md"), "a") as fh:
        fh.write("\n- %s финал запущен в Picture Viewer: кадры %d–%d → `%s`, принят лист %s%s\n" % (
            st["launched"], f0, f1, os.path.relpath(d, proj), a.accepted, ", альфа" if a.alpha else ""))
    print("LAUNCHED %s %d–%d %s" % (d, f0, f1, r.get("res")))
    print("Дальше: final.py watch (run_in_background). Правки сцены до конца прогона в него не попадут.")

elif a.op == "watch":
    st = json.load(open(state_p)) if os.path.exists(state_p) else {}
    d = (a.dir and os.path.join(proj, a.dir)) or st.get("dir") or latest_dir()
    d = d.rstrip("/") + "/"
    f0, f1 = st.get("f0", rng[0]), st.get("f1", rng[-1])
    want = list(range(f0, f1 + 1))
    last_n, stall = -1, 0
    while True:
        have = frames_in(d)
        n = sum(1 for f in want if f in have)
        if n == len(want):
            break
        if n == last_n:
            stall += 1
            if stall * 20 > 1800:
                print("30 мин без новых кадров (%d/%d) — PV остановлен или C4D висит. "
                      "Дорендер: final.py launch --missing --accepted %s" % (n, len(want), st.get("accepted", "keys-vN")))
                sys.exit(3)
        else:
            stall, last_n = 0, n
        time.sleep(20)
    time.sleep(5)
    pat = d + slug + "_%04d.png"
    base = os.path.join(proj, "renders", os.path.basename(d.rstrip("/")))
    audio = a.audio or (os.path.join(proj, "sound/current.wav") if os.path.exists(os.path.join(proj, "sound/current.wav")) else None)
    outs = []
    if L.assemble(pat, f0, fps, base + ".mp4", audio=audio, crf=16, bg=a.bg if st.get("alpha") else None):
        outs.append(base + ".mp4")
    if a.prores or st.get("alpha"):
        if L.assemble(pat, f0, fps, base + "-alpha.mov", audio=audio, prores=True):
            outs.append(base + "-alpha.mov")
    for f in (want[len(want) // 4], want[len(want) // 2], want[-1]):
        c = L.clip_pct(have[f]) if f in have else L.clip_pct(pat % f)
        print("пересвет f%d: %.2f%%%s" % (f, c, "  WARN" if c > 0.5 else ""))
    for o in outs:
        print("VIDEO", o)
    if a.stage and outs:
        print("STAGE", L.stage(proj, outs[0], a.stage))
    if outs and not a.no_open:
        L.open_file(outs[0])
