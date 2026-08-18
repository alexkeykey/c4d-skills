# --- COLLISION CHECK -------------------------------------------------------
# Вклеивать ПОСЛЕ прелюдии c4d-core И assetlib.py (нужны find / WD / bbox).
#
# Проверка проникновений на уровне мировых AABB поддеревьев:
#   - под землю: низ габарита корня ниже ground_y - tol
#   - пары корней: их AABB пересекаются глубже tol по ВСЕМ трём осям
#
# AABB — грубая оболочка вокруг геометрии, поэтому:
#   - молчание проверки при честном зазоре надёжно (оболочка больше геометрии);
#   - срабатывание — КАНДИДАТ, а не приговор: подтверждай рендером этого кадра.
# SET_ground в roots не передавать — контакт с землёй проверяет ground-тест.

def at_frame(f):
    doc.SetTime(c4d.BaseTime(f, FPS))
    bf = getattr(c4d, "BUILDFLAGS_NONE", 0)
    doc.ExecutePasses(None, True, True, True, bf)


def _overlap(a, b):
    """Глубина пересечения двух AABB по осям или None, если не пересекаются."""
    d = []
    for lo_a, hi_a, lo_b, hi_b in (
        (a[0].x, a[1].x, b[0].x, b[1].x),
        (a[0].y, a[1].y, b[0].y, b[1].y),
        (a[0].z, a[1].z, b[0].z, b[1].z),
    ):
        v = min(hi_a, hi_b) - max(lo_a, lo_b)
        if v <= 0:
            return None
        d.append(v)
    return d


def check_penetration(roots, frames=(0,), tol=1.0, ground_y=0.0, ignore=()):
    """Критерий приёмки подмены прокси: в отчёте "violations": 0.

    roots  — имена корней, между которыми ищем пересечения
             (CHAR_*_CTRL, PROP_*, крупные SET_* кроме земли)
    frames — сэмпл кадров; для статики (0,), для анимации 6-10 кадров
             равномерно по диапазону плюс кадры контактов из shotplan
    tol    — допуск в юнитах: мелкие касания не считаются
    ignore — пары имён, которым пересекаться положено по постановке,
             например (("CHAR_hero_CTRL", "PROP_sword"),)
    """
    rep = {"frames": list(frames), "tol": tol,
           "ground": [], "pairs": [], "violations": 0}
    for f in frames:
        at_frame(f)
        bb = {}
        for n in roots:
            r = bbox(n)
            if r is None:
                continue
            bb[n] = r
            depth = (ground_y - r[0].y)
            if depth > tol:
                rep["ground"].append(
                    {"frame": f, "obj": n, "depth": round(depth, 1)})
        names = sorted(bb)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if (a, b) in ignore or (b, a) in ignore:
                    continue
                d = _overlap(bb[a], bb[b])
                if d and min(d) > tol:
                    rep["pairs"].append(
                        {"frame": f, "a": a, "b": b,
                         "depth": [round(x, 1) for x in d]})
    rep["violations"] = len(rep["ground"]) + len(rep["pairs"])
    print(json.dumps(rep, ensure_ascii=False))
    return rep
# --- END COLLISION CHECK ---------------------------------------------------
