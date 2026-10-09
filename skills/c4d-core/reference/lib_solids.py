# lib_solids.py — проверка проникновений: (1) вершина внутри замкнутого тела (GeRayCollider, чётность
# пересечений, 3 луча) + (2) ребро пересекает чужую поверхность (ловит тонкие стенки, сквозь которые
# прошли без вершин внутри).
# Для вложенных деталей (кейкап над корпусом, пружина в штоке), где AABB из collision.py пересекаются
# всегда и ничего не говорят. Вклеивать после прелюдии.
#   groups = {"CAP": ["KEY_cap", ...], ...}  — имена объектов (берутся видимые, с кэшами генераторов)
#   check_solids(groups, pairs=None, max_pts=900) → {"pairs": [...], "violations": N}
_RAYS = [c4d.Vector(0.3127, 0.9411, 0.1289), c4d.Vector(-0.7071, 0.1, 0.6997), c4d.Vector(0.15, -0.35, -0.92)]

def _visible(o):
    while o:
        if o[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] == 1:
            return False
        o = o.GetUp()
    return True

def _meshes(o, out):
    """Полигональные меши объекта (без детей-объектов): реальный меш или кэш генератора, с мировой матрицей."""
    def walk(c, mgp):
        while c:
            mg = mgp * c.GetMl()
            dc = c.GetDeformCache()
            src = dc if dc is not None else c
            if isinstance(src, c4d.PolygonObject) and src.GetPolygonCount():
                out.append((src, mg))
            walk(c.GetDown(), mg)
            c = c.GetNext()
    cache = o.GetDeformCache() or o.GetCache()
    if cache is not None:
        mgp = o.GetMg()
        cc = cache
        # корень кэша — в пространстве генератора
        while cc:
            mg = mgp * cc.GetMl()
            dc = cc.GetDeformCache()
            src = dc if dc is not None else cc
            if isinstance(src, c4d.PolygonObject) and src.GetPolygonCount():
                out.append((src, mg))
            walk(cc.GetDown(), mg)
            cc = cc.GetNext()
    elif isinstance(o, c4d.PolygonObject) and o.GetPolygonCount():
        out.append((o, o.GetMg()))
    return out

def _group_meshes(names, root=None):
    res = []
    for n in names:
        objs = []
        def rec(x):
            while x:
                if x.GetName() == n:
                    objs.append(x)
                rec(x.GetDown())
                x = x.GetNext()
        rec(root.GetDown() if root is not None else doc.GetFirstObject())
        for o in objs:
            if _visible(o):
                _meshes(o, res)
    return res

def _inside(pw, rc, mi):
    lp = mi * pw
    votes = 0
    for d in _RAYS:
        dl = mi.MulV(d)
        dl.Normalize()
        rc.Intersect(lp, dl, 1.0e4, False)
        if rc.GetIntersectionCount() % 2 == 1:
            votes += 1
    return votes >= 2

def _edges(poly, mg, max_edges):
    """Уникальные рёбра меша в мировых координатах (подвыборка до max_edges)."""
    pts = poly.GetAllPoints(); seen = set(); out = []
    for pl in poly.GetAllPolygons():
        ids = [pl.a, pl.b, pl.c] if pl.c == pl.d else [pl.a, pl.b, pl.c, pl.d]
        for i in range(len(ids)):
            a, b = ids[i], ids[(i + 1) % len(ids)]
            k = (a, b) if a < b else (b, a)
            if k not in seen:
                seen.add(k); out.append((mg * pts[a], mg * pts[b]))
    step = max(1, len(out) // max_edges)
    return out[::step]

def _crosses(p0, p1, rc, mi):
    """Ребро p0→p1 пересекает поверхность меша (концы не считаются — касание допустимо)."""
    a = mi * p0; b = mi * p1; d = b - a; L = d.GetLength()
    if L < 1e-6:
        return False
    d.Normalize()
    eps = min(1e-4, L * 0.01)
    if not rc.Intersect(a + d * eps, d, L - 2 * eps, False):
        return False
    return rc.GetIntersectionCount() > 0

def check_solids(groups, pairs=None, max_pts=900, root=None, frame=None, max_edges=1500):
    G = {k: _group_meshes(v, root) for k, v in groups.items()}
    keys = sorted(G)
    if pairs is None:
        pairs = [(a, b) for i, a in enumerate(keys) for b in keys[i + 1:]]
    cols = {}
    for k in keys:
        lst = []
        for poly, mg in G[k]:
            rc = c4d.utils.GeRayCollider()
            rc.Init(poly, True)
            lst.append((rc, ~mg))
        cols[k] = lst
    rep = {"frame": frame, "pairs": [], "violations": 0,
           "meshes": {k: len(v) for k, v in G.items()}}
    for a, b in pairs:
        for A, B in ((a, b), (b, a)):
            pts = []
            for poly, mg in G[A]:
                pp = poly.GetAllPoints()
                step = max(1, len(pp) // max(1, max_pts // max(1, len(G[A]))))
                pts.extend(mg * p for p in pp[::step])
            hits = 0; ex = None
            for pw in pts:
                for rc, mi in cols[B]:
                    if _inside(pw, rc, mi):
                        hits += 1
                        if ex is None:
                            ex = [round(pw.x, 3), round(pw.y, 3), round(pw.z, 3)]
                        break
            eh = 0; eex = None
            for poly, mg in G[A]:
                for p0, p1 in _edges(poly, mg, max(1, max_edges // max(1, len(G[A])))):
                    for rc, mi in cols[B]:
                        if _crosses(p0, p1, rc, mi):
                            eh += 1
                            if eex is None:
                                eex = [round(p0.x, 3), round(p0.y, 3), round(p0.z, 3)]
                            break
            if hits or eh:
                rep["pairs"].append({"a_in_b": [A, B], "points_inside": hits, "of": len(pts),
                                     "edges_crossing": eh, "example_world": ex or eex})
    rep["violations"] = len(rep["pairs"])
    return rep
