# --- RENDER LADDER ---------------------------------------------------------
# Лестница рендер-пресетов RS_draft / RS_tex / RS_light / RS_final (c4d-core §5b).
# Вклеивать ПОСЛЕ прелюдии (нужны use_rs / render_to). Идемпотентно: повторный
# вызов обновляет существующие пресеты, а не плодит копии.
# Создаёт лейаут (его Шаг 1) числами из scene.json.output; /c4d-look в режиме
# `рендер` не пересоздаёт лестницу, а дотюнивает RS_final и меряет время кадра.
# Константы новее прелюдии защищены getattr: чего нет в этой версии C4D —
# попадает в "missing" итогового JSON (и в selftest.py), а не роняет скрипт.

_MISS = []


def _rs_find(name):
    rd = doc.GetFirstRenderData()
    while rd:
        if rd.GetName() == name:
            return rd
        rd = rd.GetNext()
    return None


def _rs_get(name):
    rd = _rs_find(name)
    if rd is None:
        rd = c4d.documents.RenderData()
        rd.SetName(name)
        if hasattr(doc, "InsertRenderDataLast"):
            doc.InsertRenderDataLast(rd)
        else:
            doc.InsertRenderData(rd)
    return rd


def _opt(bl, cname, val):
    """Поставить параметр по имени константы; нет константы — записать в _MISS."""
    cid = getattr(c4d, cname, None)
    if cid is None:
        if cname not in _MISS:
            _MISS.append(cname)
        return False
    bl[cid] = val
    return True


def _set_first(bl, names, val):
    """Первая существующая константа из списка кандидатов (версии C4D разнятся)."""
    for n in names:
        cid = getattr(c4d, n, None)
        if cid is not None:
            bl[cid] = val
            return n
    _MISS.append("|".join(names))
    return None


def _vp_ensure(rd, plugin_id):
    vp = rd.GetFirstVideoPost()
    while vp:
        if vp.GetType() == plugin_id:
            return vp
        vp = vp.GetNext()
    vp = c4d.documents.BaseVideoPost(plugin_id)
    if vp is not None:
        rd.InsertVideoPost(vp)
    return vp


def _vp_drop(rd, plugin_id):
    vp = rd.GetFirstVideoPost()
    while vp:
        nxt = vp.GetNext()
        if vp.GetType() == plugin_id:
            vp.Remove()
        vp = nxt


ENG = {"standard": getattr(c4d, "RDATA_RENDERENGINE_STANDARD", 0),
       "physical": getattr(c4d, "RDATA_RENDERENGINE_PHYSICAL", 1023342)}
AA_GEO = getattr(c4d, "RDATA_ANTIALIASING_GEOMETRY", 1)
AA_BEST = getattr(c4d, "RDATA_ANTIALIASING_BEST", 2)
GI_VP = getattr(c4d, "VPglobalillumination", 1021096)


def render_ladder(engine="standard", res=(1280, 720), f0=0, f1=100,
                  gi=False, path=None, mb=False, dof=False):
    """Создать/обновить всю лестницу. engine/res/gi/mb/dof/path — из scene.json.output.
    Вызывать ПОСЛЕ timing(): fps берётся из документа. Активный пресет не меняет —
    после вызова включи рабочий: use_rs("RS_draft")."""
    fps = doc.GetFps()
    eng = ENG.get(str(engine).lower(), ENG["standard"])
    lw, lh = max(2, int(res[0]) // 2), max(2, int(res[1]) // 2)
    sizes = {"RS_draft": (960, 540), "RS_tex": (960, 540),
             "RS_light": (lw, lh), "RS_final": (int(res[0]), int(res[1]))}

    for name, (w, h) in sizes.items():
        rd = _rs_get(name)
        rd[c4d.RDATA_XRES] = float(w)
        rd[c4d.RDATA_YRES] = float(h)
        rd[c4d.RDATA_FRAMERATE] = float(fps)
        rd[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL
        rd[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(f0, fps)
        rd[c4d.RDATA_FRAMETO] = c4d.BaseTime(f1, fps)
        rd[c4d.RDATA_SAVEIMAGE] = False

    d = _rs_find("RS_draft")            # геометрия, блокинг, тайминг
    d[c4d.RDATA_RENDERENGINE] = ENG["standard"]
    _opt(d, "RDATA_ANTIALIASING", AA_GEO)
    _opt(d, "RDATA_OPTION_SHADOW", False)
    _opt(d, "RDATA_OPTION_REFLECTION", False)
    _opt(d, "RDATA_OPTION_TRANSPARENCY", False)
    _vp_drop(d, GI_VP)

    t = _rs_find("RS_tex")              # текстуры и материалы: фактура без светотени
    t[c4d.RDATA_RENDERENGINE] = ENG["standard"]
    _opt(t, "RDATA_ANTIALIASING", AA_BEST)
    _opt(t, "RDATA_OPTION_SHADOW", False)
    _opt(t, "RDATA_OPTION_REFLECTION", True)
    _opt(t, "RDATA_OPTION_TRANSPARENCY", True)
    _vp_drop(t, GI_VP)

    l = _rs_find("RS_light")            # свет: движок финала, preview-качество
    l[c4d.RDATA_RENDERENGINE] = eng
    _opt(l, "RDATA_ANTIALIASING", AA_GEO)
    _opt(l, "RDATA_OPTION_SHADOW", True)
    _opt(l, "RDATA_OPTION_REFLECTION", True)
    _opt(l, "RDATA_OPTION_TRANSPARENCY", True)

    f = _rs_find("RS_final")            # вывод
    f[c4d.RDATA_RENDERENGINE] = eng
    _opt(f, "RDATA_ANTIALIASING", AA_BEST)
    _opt(f, "RDATA_OPTION_SHADOW", True)
    _opt(f, "RDATA_OPTION_REFLECTION", True)
    _opt(f, "RDATA_OPTION_TRANSPARENCY", True)
    if path:
        f[c4d.RDATA_SAVEIMAGE] = True
        f[c4d.RDATA_PATH] = path
        f[c4d.RDATA_FORMAT] = c4d.FILTER_PNG

    for rd, final in ((l, False), (f, True)):
        if gi:
            vp = _vp_ensure(rd, GI_VP)
            if vp is None:
                _MISS.append("VPglobalillumination(create)")
            elif not final:
                # качество GI вниз, метод не трогаем: «тот же свет, но грубее»
                pid = getattr(c4d, "GI_SETUP_DATA_IR_DENSITY_QUALITY", None)
                pval = getattr(c4d, "GI_SETUP_QUALITY_PREVIEW", None)
                if pid is not None and pval is not None:
                    vp[pid] = pval
                else:
                    _MISS.append("GI_SETUP_DATA_IR_DENSITY_QUALITY/GI_SETUP_QUALITY_PREVIEW")
        else:
            _vp_drop(rd, GI_VP)

    if eng == ENG["physical"]:
        pl = _vp_ensure(l, ENG["physical"])   # качество сэмплера вниз на свет-тесте
        if pl is not None:
            q = getattr(c4d, "VP_XMB_RAYTRACING_QUALITY", None)
            qv = getattr(c4d, "VP_XMB_RAYTRACING_QUALITY_PREVIEW", None)
            if q is not None and qv is not None:
                pl[q] = qv
            else:
                _MISS.append("VP_XMB_RAYTRACING_QUALITY(_PREVIEW)")
        pf = _vp_ensure(f, ENG["physical"])
        if pf is not None:
            _set_first(pf, ["VP_XMB_MOTIONBLUR"], bool(mb))
            _set_first(pf, ["VP_XMB_DOF", "VP_XMB_DEPTHOFFIELD"], bool(dof))
    else:
        _vp_drop(l, ENG["physical"])
        _vp_drop(f, ENG["physical"])
        if mb or dof:
            # Standard: MB и DOF — отдельные VideoPost, включает /c4d-look вручную
            _MISS.append("standard:mb/dof — включить VideoPost вручную")

    print(json.dumps({"ladder": {k: list(v) for k, v in sizes.items()},
                      "engine": str(engine).lower(), "gi": bool(gi),
                      "fps": fps, "range": [f0, f1], "path": path,
                      "active": doc.GetActiveRenderData().GetName(),
                      "missing": _MISS}))
    return _MISS


def time_frame(frame, path):
    """Честный замер времени кадра на RS_final (полное разрешение, полные настройки).
    По одному кадру на вызов: кадр дольше ~25 с упрётся в 30-секундный таймаут
    моста — и сам таймаут уже ответ: время кадра больше лимита, жми на понижение."""
    rd = _rs_find("RS_final")
    if rd is None:
        print(json.dumps({"error": "нет RS_final — сначала render_ladder()"}))
        return None
    w, h = int(rd[c4d.RDATA_XRES]), int(rd[c4d.RDATA_YRES])
    use_rs("RS_final")
    t0 = time.time()
    ok = render_to(path, frame, w, h)
    dt = time.time() - t0
    print(json.dumps({"frame": frame, "sec": round(dt, 1),
                      "res": [w, h], "ok": bool(ok)}))
    return dt
# --- END RENDER LADDER -----------------------------------------------------
