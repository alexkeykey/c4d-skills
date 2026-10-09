"""Общая часть драйверов c4d-core/bin: проект, пачки кадров через мост, сборка видео,
версии файлов, материалы мейкинга. Импортируется playblast.py / keysheet.py / final.py."""
import glob, json, os, re, shutil, subprocess, sys, tempfile, time

BIN = os.path.dirname(os.path.realpath(__file__))
REF = os.path.join(os.path.dirname(BIN), "reference")
RUN = os.path.join(BIN, "run.py")
PROJ_ROOT = os.path.realpath(os.path.expanduser(os.environ.get("C4D_PROJECTS", "~/c4d-projects")))


def project(slug=None):
    """(slug, abs_dir/) — по аргументу, иначе по cwd, иначе последний изменённый проект."""
    if slug:
        d = os.path.join(PROJ_ROOT, slug)
    else:
        cwd = os.path.realpath(os.getcwd())
        if cwd.startswith(PROJ_ROOT + os.sep):
            d = os.path.join(PROJ_ROOT, cwd[len(PROJ_ROOT) + 1:].split(os.sep)[0])
        else:
            ds = [p for p in glob.glob(PROJ_ROOT + "/*") if os.path.isdir(p)]
            if not ds:
                sys.exit("нет проектов в " + PROJ_ROOT)
            d = max(ds, key=lambda p: os.path.getmtime(os.path.join(p, "pipeline.md"))
                    if os.path.exists(os.path.join(p, "pipeline.md")) else 0)
    if not os.path.isdir(d):
        sys.exit("нет проекта " + d)
    return os.path.basename(d), d + os.sep


def scene_json(proj):
    p = os.path.join(proj, "scene.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def parse_frames(spec):
    """'0-179', '16,32,48', '0-100:5' → [кадры]."""
    out = []
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        step = 1
        if ":" in part:
            part, st = part.split(":"); step = int(st)
        if "-" in part[1:]:
            a, b = part.split("-", 1) if not part.startswith("-") else (part, part)
            out += list(range(int(a), int(b) + 1, step))
        else:
            out.append(int(part))
    return sorted(set(out))


def next_version(pattern):
    """pattern с {v}: 'renders/preview/draft-v{v}.mp4' → первый свободный v (с 1)."""
    v = 1
    while os.path.exists(pattern.format(v=v)):
        v += 1
    return pattern.format(v=v), v


def run_job(job, script, proj_dir, timeout=75):
    """Один вызов моста: JOB + script (в reference/). Возвращает dict из последней JSON-строки."""
    tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(job, tf); tf.close()
    cmd = [sys.executable, RUN, "--ladder", "--job", "@" + tf.name, "--timeout", str(timeout),
           os.path.join(REF, script)]
    # cwd = проект: раннер найдёт slug и активирует <slug>.c4d
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=proj_dir)
    os.unlink(tf.name)
    last = None
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                last = json.loads(line)
            except ValueError:
                pass
    if r.returncode != 0 or last is None:
        return {"error": (r.stderr or r.stdout)[-600:], "rc": r.returncode}
    return last


def wait_bridge(max_s=600):
    return subprocess.run([sys.executable, RUN, "--wait", str(max_s)]).returncode == 0


def render_frames(proj_dir, frames, out_dir, rs, w, h, cam=None, clay=False,
                  simplify=True, prefix="f", pad=4, batch=None, keep=(), log=print):
    """Рендер кадров пачками под лимит моста. Размер пачки подстраивается по замеру
    первой; после таймаута — ждём мост и продолжаем с недостающих. Уже готовые PNG
    не перерендериваются (повторный запуск = дорендер дыр)."""
    os.makedirs(out_dir, exist_ok=True)
    path = lambda f: os.path.join(out_dir, "%s%0*d.png" % (prefix, pad, f))
    todo = [f for f in frames if not (os.path.exists(path(f)) and os.path.getsize(path(f)) > 0)]
    b = batch or 3
    t_start, fails = time.time(), 0
    while todo:
        chunk = todo[:b]
        job = {"frames": chunk, "out": out_dir.rstrip("/") + "/", "rs": rs, "cam": cam,
               "w": w, "h": h, "clay": clay, "simplify": simplify, "prefix": prefix,
               "pad": pad, "keep": list(keep), "budget": 45}
        res = run_job(job, "frames_job.py", proj_dir)
        if "error" in res:
            fails += 1
            log("пачка %s…: ошибка/таймаут → жду мост (%s)" % (chunk[0], res["error"][-160:].strip()))
            if fails > 4 or not wait_bridge(600):
                log("СТОП: мост не восстановился / слишком много ошибок")
                return False
            b = max(1, b // 2)
        else:
            fails = 0
            pf = res.get("per_frame") or 1
            if not batch:
                b = max(1, min(60, int(40 / max(pf, 0.05))))
            log("кадры %s–%s: %.1f с/кадр, пачка→%d" % (chunk[0], chunk[-1], pf, b))
        todo = [f for f in todo if not (os.path.exists(path(f)) and os.path.getsize(path(f)) > 0)]
    log("готово: %d кадров за %.0f с" % (len(frames), time.time() - t_start))
    return True


def assemble(frames_glob_pattern, start, fps, out, audio=None, prores=False, bg=None,
             scale=None, crf=18):
    """PNG-секвенция → видео. pattern в стиле ffmpeg: /dir/f%04d.png.
    prores=True → ProRes 4444 с альфой (.mov); bg='#163B9A' → подложка цветом (превью альфы)."""
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
           "-start_number", str(start), "-i", frames_glob_pattern]
    if bg:
        from PIL import Image
        first = frames_glob_pattern % start
        W_, H_ = Image.open(first).size
        cmd += ["-f", "lavfi", "-i", "color=c=%s:s=%dx%d:r=%s" % (bg.replace("#", "0x"), W_, H_, fps)]
    if audio:
        cmd += ["-i", audio]
    vf = []
    if bg:
        fc = "[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[o]"
        cmd += ["-filter_complex", fc, "-map", "[o]"]
    else:
        if scale:
            vf.append("scale=%s:flags=lanczos" % scale)
        if vf:
            cmd += ["-vf", ",".join(vf)]
        cmd += ["-map", "0:v"]
    if audio:
        cmd += ["-map", "%d:a" % (2 if bg else 1), "-c:a", "aac", "-b:a", "192k", "-shortest"]
    if prores:
        cmd += ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le"]
    else:
        # all-intra-подобный GOP: H.264 с B-кадрами дёргается в AE (traps.md)
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-bf", "0", "-g", "12"]
    cmd += ["-r", str(fps), out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("ffmpeg: " + r.stderr[-500:])
        return False
    return True


def contact_sheet(pngs, labels, out, cols=None, title=None, clip=None):
    """Лист: картинки сеткой с подписями (номер кадра, % пересвета). PIL."""
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(p).convert("RGB") for p in pngs]
    w, h = ims[0].size
    n = len(ims)
    cols = cols or (n if n <= 4 else (3 if n in (5, 6, 9) else 4))
    rows = (n + cols - 1) // cols
    pad, lab = 8, 26
    top = 34 if title else 0
    sheet = Image.new("RGB", (cols * (w + pad) + pad, top + rows * (h + lab + pad) + pad), (24, 24, 26))
    dr = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
        tfont = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 18)
    except Exception:
        font = tfont = ImageFont.load_default()
    if title:
        dr.text((pad, 8), title, fill=(235, 235, 235), font=tfont)
    for i, (im, lb) in enumerate(zip(ims, labels)):
        x = pad + (i % cols) * (w + pad)
        y = top + pad + (i // cols) * (h + lab + pad)
        sheet.paste(im, (x, y + lab))
        warn = clip and clip[i] > 0.5
        dr.text((x + 2, y + 4), lb, fill=(255, 120, 90) if warn else (220, 220, 220), font=font)
    sheet.save(out)
    return out


def clip_pct(png, thr=250):
    """Доля пересвеченных пикселей (любой канал ≥ thr), %."""
    from PIL import Image
    im = Image.open(png).convert("RGB")
    px = im.getdata()
    n = len(px)
    c = sum(1 for r, g, b in px if r >= thr or g >= thr or b >= thr)
    return 100.0 * c / max(1, n)


def stage(proj_dir, src, name, note=None):
    """Материал этапа для мейкинга: копия в making-of-stages/NN-name.ext + строка в stages.md."""
    d = os.path.join(proj_dir, "making-of-stages")
    os.makedirs(d, exist_ok=True)
    n = len([p for p in os.listdir(d) if re.match(r"\d\d-", p)]) + 1
    ext = os.path.splitext(src)[1]
    dst = os.path.join(d, "%02d-%s%s" % (n, name, ext))
    shutil.copy2(src, dst)
    with open(os.path.join(d, "stages.md"), "a") as fh:
        fh.write("- %s · %s · `%s`%s\n" % (time.strftime("%Y-%m-%d %H:%M"), name,
                                            os.path.basename(dst), (" — " + note) if note else ""))
    return dst


def open_file(p):
    subprocess.run(["open", p])
