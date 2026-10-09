#!/usr/bin/env python3
"""Лист ключевых кадров — гейт перед чистовым рендером и проверка света после правок камеры.

    keysheet.py [--proj SLUG] [--frames 16,32,48,64,80,96] [--cam CAM] [--scale 0.5]
                [--mb] [--rs RS_keys] [--stage NAME] [--no-open] [--title TEXT]

* Перед рендером синхронизирует RS_keys с текущим RS_final (sync_keys): тот же движок,
  свет, GI/AO, материалы, разрешение × scale, сэмплер на preview, MB выкл (--mb — вкл).
* Кадры: --frames или scene.json "key_frames" (опорные кадры плана: удары, вершины,
  смены состояний, первый/последний кадр каждого шота).
* По одному кадру на вызов моста (Physical легко > 20 с/кадр). Повторный запуск
  с тем же листом дорендеривает только недостающие кадры.
* Каждый кадр проверяется на пересвет (% пикселей ≥ 250); > 0.5 % — красная подпись
  и строка WARN. Итог — один PNG renders/keys/keys-vN.png, открывается сам; Read его.
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import c4dlib as L

ap = argparse.ArgumentParser()
ap.add_argument("--proj"); ap.add_argument("--frames"); ap.add_argument("--cam")
ap.add_argument("--scale", type=float, default=0.5); ap.add_argument("--mb", action="store_true")
ap.add_argument("--rs", default="RS_keys"); ap.add_argument("--stage"); ap.add_argument("--title")
ap.add_argument("--no-open", action="store_true"); ap.add_argument("--dir")
a = ap.parse_args()

slug, proj = L.project(a.proj)
sj = L.scene_json(proj)
frames = L.parse_frames(a.frames) if a.frames else sorted(set(sj.get("key_frames", [])))
if not frames:
    sys.exit("нет кадров: --frames или scene.json key_frames")

if a.rs == "RS_keys":
    r = L.run_job({"scale": a.scale, "mb": a.mb}, "keys_sync_job.py", proj)
    if "error" in r:
        sys.exit("sync_keys: " + r["error"])
    w, h = r["size"]
    print("RS_keys ← RS_final: %dx%d (%s), MB %s" % (w, h, r.get("engine"), "вкл" if a.mb else "выкл"))
else:
    w, h = 960, 540

sheet, v = L.next_version(os.path.join(proj, "renders/keys/keys-v{v}.png"))
fdir = a.dir or os.path.join(proj, "renders/keys/v%d/" % v)
t0 = time.time()
ok = L.render_frames(proj, frames, fdir, a.rs, w, h, cam=a.cam, simplify=False, batch=1)
if not ok:
    sys.exit(1)
pngs = [os.path.join(fdir, "f%04d.png" % f) for f in frames]
clip = [L.clip_pct(p) for p in pngs]
labels = ["f%d · пересвет %.1f%%" % (f, c) for f, c in zip(frames, clip)]
title = a.title or "%s · ключевые кадры v%d · %s %dx%d" % (slug, v, a.rs, w, h)
L.contact_sheet(pngs, labels, sheet, title=title, clip=clip)
per = (time.time() - t0) / len(frames)
print("SHEET", sheet)
print("per_frame_keys %.1f s" % per)
for f, c in zip(frames, clip):
    if c > 0.5:
        print("WARN пересвет f%d: %.1f%% пикселей ≥ 250" % (f, c))
if a.stage:
    print("STAGE", L.stage(proj, sheet, a.stage))
if not a.no_open:
    L.open_file(sheet)
