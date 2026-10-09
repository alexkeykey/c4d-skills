#!/usr/bin/env python3
"""Отправить скрипт(ы) проекта в C4D через мост 18710: прелюдия [+ лестница] [+ JOB] + тела.

    run.py [--ladder] [--lib FILE ...] [--job '{json}' | --job @job.json] [--doc NAME]
           [--timeout S] script.py [script2.py ...]
    run.py --wait [S]        ждать, пока мост ответит на ping (после таймаута / рестарта)
    run.py --code 'print(doc.GetDocumentName())'      разовый код без файла

Что делает сам, чтобы скрипты проекта этого не повторяли:
  * склеивает `import c4d, math, random, time, json` + prelude.py [+ renderladder.py]
    [+ --lib файлы, например c4d-core/reference/lib_solids.py] + JOB = {...} + скрипты;
  * определяет проект по пути скрипта (~/c4d-projects/<slug>/scripts/…) и подставляет
    PROJ = "/abs/…/<slug>/", SLUG и SCENE = scene.json словарём (open() в C4D — ASCII); активирует открытый документ <slug>.c4d (или --doc),
    чтобы правка не ушла в чужую открытую сцену;
  * печатает stdout/stderr скрипта и result; код выхода ≠ 0 при ошибке;
  * при таймауте моста (60 с главного потока C4D) объясняет, что делать: C4D ещё
    выполняет — следующий вызов встанет в очередь; `run.py --wait`, потом дробить.
"""
import json, os, re, socket, sys, time

HERE = os.path.dirname(os.path.realpath(__file__))
REF = os.path.join(os.path.dirname(HERE), "reference")
HOST = os.environ.get("C4D_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("C4D_MCP_PORT", "18710"))
TIMEOUT = float(os.environ.get("C4D_MCP_TIMEOUT", "600"))
PROJ_ROOT = os.path.expanduser(os.environ.get("C4D_PROJECTS", "~/c4d-projects"))


def call(command, params, timeout=TIMEOUT):
    req = {"id": "run-%d" % int(time.time() * 1000), "command": command, "params": params}
    tok = os.environ.get("C4D_MCP_TOKEN", "").strip()
    if tok:
        req["token"] = tok
    s = socket.create_connection((HOST, PORT), timeout=5)
    s.settimeout(timeout)
    try:
        s.sendall((json.dumps(req) + "\n").encode())
        buf = b""
        while b"\n" not in buf:
            ch = s.recv(1 << 20)
            if not ch:
                raise ConnectionError("мост закрыл соединение без ответа")
            buf += ch
    finally:
        s.close()
    return json.loads(buf.split(b"\n", 1)[0].decode())


def ping(timeout=5.0):
    try:
        r = call("ping", {}, timeout=timeout)
        return r.get("status") == "ok"
    except Exception:
        return False


def wait(max_s=600):
    t0 = time.time()
    while time.time() - t0 < max_s:
        if ping():
            print("bridge: up (%.0f s)" % (time.time() - t0))
            return True
        time.sleep(3)
    print("bridge: НЕ ответил за %d с — C4D висит? см. c4d-core §0 (restart.sh)" % max_s)
    return False


def project_of(path):
    p = os.path.realpath(path)
    root = os.path.realpath(PROJ_ROOT) + os.sep
    if p.startswith(root):
        slug = p[len(root):].split(os.sep)[0]
        return slug, root + slug + os.sep
    return None, None


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "--wait":
        return 0 if wait(float(argv[1]) if len(argv) > 1 else 600) else 1

    ladder, libs, job, docname, files, code_inline = False, [], None, None, [], None
    timeout = TIMEOUT
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--ladder":
            ladder = True
        elif a == "--lib":
            i += 1; libs.append(argv[i])
        elif a == "--job":
            i += 1; v = argv[i]
            job = json.load(open(v[1:])) if v.startswith("@") else json.loads(v)
        elif a == "--doc":
            i += 1; docname = argv[i]
        elif a == "--timeout":
            i += 1; timeout = float(argv[i])
        elif a == "--code":
            i += 1; code_inline = argv[i]
        else:
            files.append(a)
        i += 1

    slug, proj = (None, None)
    for f in files:
        slug, proj = project_of(f)
        if slug:
            break
    if slug is None:
        slug, proj = project_of(os.getcwd())
    if docname is None and slug:
        docname = slug + ".c4d"

    parts = ["import c4d, math, random, time, json"]
    if docname:
        # активировать документ проекта ДО прелюдии: прелюдия берёт doc/FPS из активного
        parts.append(
            "_d = c4d.documents.GetFirstDocument()\n_hit = False\n"
            "while _d:\n"
            "    if _d.GetDocumentName() == %r:\n"
            "        c4d.documents.SetActiveDocument(_d); _hit = True\n"
            "    _d = _d.GetNext()\n"
            "doc = c4d.documents.GetActiveDocument()\n"
            "if not _hit: print('WARN: документ %%s не открыт — работаю в активном %%s' %% (%r, doc.GetDocumentName()))"
            % (docname, docname))
    if proj:
        parts.append("PROJ = %r\nSLUG = %r" % (proj, slug))
        sj = os.path.join(proj, "scene.json")
        if os.path.exists(sj):
            # open() внутри C4D читает в ASCII — кириллица в scene.json роняет json.load;
            # раннер читает сам (utf-8) и передаёт словарём
            parts.append("SCENE = " + repr(json.load(open(sj, encoding="utf-8"))))
    parts.append(open(os.path.join(REF, "prelude.py")).read())
    if ladder:
        parts.append(open(os.path.join(REF, "rs_presets.py")).read())
        parts.append(open(os.path.join(REF, "renderladder.py")).read())
    for l in libs:
        p = l if os.path.exists(l) else os.path.join(REF, l)
        parts.append(open(p).read())
    if job is not None:
        parts.append("JOB = " + repr(job))      # repr, не json: True/False/None — питоновские
    for f in files:
        parts.append("# ---- %s\n" % os.path.basename(f) + open(f).read())
    if code_inline:
        parts.append(code_inline)
    code = "\n".join(parts) + "\n"

    t0 = time.time()
    try:
        r = call("exec_python", {"code": code}, timeout=timeout)
    except (ConnectionRefusedError, OSError) as e:
        if isinstance(e, socket.timeout) or "timed out" in str(e):
            print("TIMEOUT клиента %.0f с. C4D, вероятно, ещё считает — `run.py --wait`." % timeout,
                  file=sys.stderr)
        else:
            print("bridge down (%s): bash ~/.claude/skills/c4d-core/bin/preflight.sh" % e, file=sys.stderr)
        return 3
    dt = time.time() - t0
    if r.get("status") != "ok":
        err = str(r.get("error"))
        print("ERROR: " + err, file=sys.stderr)
        if "timed out" in err:
            print("HINT: лимит 60 с главного потока. Работа в C4D могла продолжиться — "
                  "`run.py --wait`, затем дроби (меньше кадров/объектов на вызов).", file=sys.stderr)
        if "disabled" in err.lower() or "exec_python" in err.lower():
            print("HINT: exec_python выключен — c4d-core §0: restart.sh", file=sys.stderr)
        return 1
    d = r.get("result") or {}
    if d.get("stdout"):
        sys.stdout.write(d["stdout"])
    if d.get("stderr"):
        sys.stderr.write(d["stderr"])
    if d.get("error"):
        sys.stderr.write("ERROR: %s\n" % d["error"])
        return 1
    if d.get("result") is not None:
        print("result:", json.dumps(d["result"], ensure_ascii=False))
    if dt > 40:
        print("NOTE: вызов шёл %.0f с — близко к лимиту 60 с, дроби следующий." % dt, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
