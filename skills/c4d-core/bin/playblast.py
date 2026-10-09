#!/usr/bin/env python3
"""Черновое видео (плейбласт) — главный инструмент итераций.

    playblast.py [--proj SLUG] [--range 0-179] [--cam CAM_sh010] [--rs RS_draft]
                 [--size 640x360] [--clay] [--no-simplify] [--audio sound.wav]
                 [--out renders/preview/draft-v{v}.mp4] [--stage NAME] [--no-open]

* Кадры — пачками под лимит моста 60 с; размер пачки подбирается по замеру первой;
  после таймаута ждёт мост и дорендеривает дыры. Повторный запуск с тем же --frames-dir
  дорендеривает только недостающее.
* По умолчанию RS_draft 640×360, временные упрощения стекла/отражений (возвращаются).
* Звук: --audio или <проект>/sound/current.wav, если есть. Видео открывается само.
* --stage NAME — копия в making-of-stages/ (материал для мейкинга).
* Запускать через Bash run_in_background, если кадров > ~60: чат не должен стоять.
"""
import argparse, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import c4dlib as L

ap = argparse.ArgumentParser()
ap.add_argument("--proj"); ap.add_argument("--range"); ap.add_argument("--cam")
ap.add_argument("--rs", default="RS_draft"); ap.add_argument("--size", default="640x360")
ap.add_argument("--clay", action="store_true"); ap.add_argument("--no-simplify", action="store_true")
ap.add_argument("--audio"); ap.add_argument("--out"); ap.add_argument("--stage")
ap.add_argument("--frames-dir"); ap.add_argument("--no-open", action="store_true")
ap.add_argument("--batch", type=int)
a = ap.parse_args()

slug, proj = L.project(a.proj)
sj = L.scene_json(proj)
fps = sj.get("fps", 24)
if a.range:
    frames = L.parse_frames(a.range)
else:
    fr = sj.get("frame_range") or [0, sj.get("length", 120)]
    frames = list(range(fr[0], fr[1] + 1))
cam = a.cam          # None → активная камера сцены (или Stage-объект, если он переключает шоты)
w, h = [int(x) for x in a.size.lower().split("x")]
out = a.out or os.path.join(proj, "renders/preview/draft-v{v}.mp4")
if "{v}" in out:
    out, v = L.next_version(out if os.path.isabs(out) else os.path.join(proj, out))
elif not os.path.isabs(out):
    out = os.path.join(proj, out)
fdir = a.frames_dir or os.path.join(proj, "renders/pb-" + os.path.splitext(os.path.basename(out))[0]) + "/"

print("playblast %s: %d кадров %s→%s, %s, %dx%d" % (slug, len(frames), frames[0], frames[-1], a.rs, w, h))
ok = L.render_frames(proj, frames, fdir, a.rs, w, h, cam=cam, clay=a.clay,
                     simplify=not a.no_simplify, batch=a.batch)
if not ok:
    sys.exit(1)
audio = a.audio or (os.path.join(proj, "sound/current.wav") if os.path.exists(os.path.join(proj, "sound/current.wav")) else None)
if L.assemble(fdir + "f%04d.png", frames[0], fps, out, audio=audio):
    print("VIDEO", out)
    if a.stage:
        print("STAGE", L.stage(proj, out, a.stage))
    if not a.no_open:
        L.open_file(out)
