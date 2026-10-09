# --- RENDER LADDER ---------------------------------------------------------
# Лестница рендер-пресетов RS_draft / RS_tex / RS_keys / RS_final (c4d-core §4)
# + apply_preset(rd, имя) — пресеты из rs_presets.py (обоснование: render-presets.md).
# Подключается раннером: run.py --ladder. Идемпотентно: повторный вызов обновляет
# существующие пресеты, а не плодит копии.
# Создаёт режим `сцена` (Шаг 1) числами из scene.json.output; режим `рендер`
# не пересоздаёт лестницу, а дотюнивает RS_final и меряет время кадра.
# RS_keys — НЕ самостоятельные настройки, а клон RS_final ступенью ниже
# (sync_keys): лист ключевых кадров всегда показывает свет/материалы/движок финала.
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
                  gi=False, path=None, mb=False, dof=False, preset=None):
    """Создать/обновить всю лестницу. engine/res/gi/mb/dof/path/preset — из scene.json.output.
    preset (имя из rs_presets.py) применяется к RS_final поверх базовых настроек.
    Вызывать ПОСЛЕ timing(): fps берётся из документа. Активный пресет не меняет —
    после вызова включи рабочий: use_rs("RS_draft")."""
    fps = doc.GetFps()
    eng = ENG.get(str(engine).lower(), ENG["standard"])
    sizes = {"RS_draft": (960, 540), "RS_tex": (960, 540),
             "RS_final": (int(res[0]), int(res[1]))}

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
    # отражения ВКЛ: у стандартных материалов с GGX-слоями (после прохода материалов) при выкл
    # отражениях Standard рендерит объекты чёрными — черновик перестаёт показывать что-либо
    _opt(d, "RDATA_OPTION_REFLECTION", True)
    _opt(d, "RDATA_OPTION_TRANSPARENCY", False)
    _vp_drop(d, GI_VP)

    t = _rs_find("RS_tex")              # текстуры и материалы: фактура без светотени
    t[c4d.RDATA_RENDERENGINE] = ENG["standard"]
    _opt(t, "RDATA_ANTIALIASING", AA_BEST)
    _opt(t, "RDATA_OPTION_SHADOW", False)
    _opt(t, "RDATA_OPTION_REFLECTION", True)
    _opt(t, "RDATA_OPTION_TRANSPARENCY", True)
    _vp_drop(t, GI_VP)

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

    if gi:
        if _vp_ensure(f, GI_VP) is None:
            _MISS.append("VPglobalillumination(create)")
    else:
        _vp_drop(f, GI_VP)

    if eng == ENG["physical"]:
        pf = _vp_ensure(f, ENG["physical"])
        if pf is not None:
            _set_first(pf, ["VP_XMB_MOTIONBLUR"], bool(mb))
            _set_first(pf, ["VP_XMB_DOF", "VP_XMB_DEPTHOFFIELD"], bool(dof))
    else:
        _vp_drop(f, ENG["physical"])
        if mb or dof:
            # Standard: MB и DOF — отдельные VideoPost, включает /c4d-look вручную
            _MISS.append("standard:mb/dof — включить VideoPost вручную")

    if preset:
        apply_preset(f, preset, out_res=res)
        sizes["RS_final"] = (int(f[c4d.RDATA_XRES]), int(f[c4d.RDATA_YRES]))
    keys = sync_keys()
    sizes["RS_keys"] = keys
    print(json.dumps({"ladder": {k: list(v) for k, v in sizes.items()},
                      "engine": str(engine).lower(), "gi": bool(gi),
                      "fps": fps, "range": [f0, f1], "path": path,
                      "active": doc.GetActiveRenderData().GetName(),
                      "missing": _MISS}))
    return _MISS


def sync_keys(scale=0.5, mb=False):
    """RS_keys = клон RS_final ступенью ниже: тот же движок, свет, GI/AO, материалы;
    разрешение × scale, сэмплер/GI на preview-качестве, MB выкл (mb=True — оставить).
    Звать перед КАЖДЫМ листом ключевых кадров (keysheet.py делает это сам): после
    дотюна RS_final ключевые кадры обязаны показывать уже новые настройки.
    Старый RS_light (лестница v2) удаляется."""
    f = _rs_find("RS_final")
    if f is None:
        print(json.dumps({"error": "нет RS_final — сначала render_ladder()"}))
        return None
    active = doc.GetActiveRenderData().GetName()
    for old in ("RS_keys", "RS_light"):
        o = _rs_find(old)
        if o is not None:
            o.Remove()
    k = f.GetClone()
    k.SetName("RS_keys")
    if hasattr(doc, "InsertRenderDataLast"):
        doc.InsertRenderDataLast(k)
    else:
        doc.InsertRenderData(k)
    w = max(2, int(round(f[c4d.RDATA_XRES] * scale)) // 2 * 2)
    h = max(2, int(round(f[c4d.RDATA_YRES] * scale)) // 2 * 2)
    k[c4d.RDATA_XRES] = float(w)
    k[c4d.RDATA_YRES] = float(h)
    k[c4d.RDATA_SAVEIMAGE] = False
    k[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_CURRENTFRAME
    vp = k.GetFirstVideoPost()
    while vp:
        if vp.GetType() == GI_VP:
            # качество GI вниз, метод не трогаем: IC2/legacy IC — preview, QMC/LM — половина лучей
            pval = getattr(c4d, "GI_SETUP_QUALITY_PREVIEW", None)
            for qn in ("GI_SETUP_DATA_IC2_QUALITY", "GI_SETUP_DATA_IR_DENSITY_QUALITY"):
                qid = getattr(c4d, qn, None)
                if qid is not None and pval is not None:
                    vp[qid] = pval
            for cn, lo in (("GI_SETUP_DATA_QMC_COUNT", 8), ("GI_SETUP_DATA_LIGHT_MAPPING_PATH_COUNT", 50)):
                cid = getattr(c4d, cn, None)
                if cid is not None and vp[cid]:
                    vp[cid] = max(lo, int(vp[cid]) // 2)
        if vp.GetType() == ENG["physical"]:
            q = getattr(c4d, "VP_XMB_RAYTRACING_QUALITY", None)
            qv = getattr(c4d, "VP_XMB_RAYTRACING_QUALITY_PREVIEW", None)
            if q is not None and qv is not None:
                vp[q] = qv
            if not mb:
                _set_first(vp, ["VP_XMB_MOTIONBLUR"], False)
        vp = vp.GetNext()
    use_rs(active if _rs_find(active) else "RS_draft")
    return (w, h)


AO_VP = getattr(c4d, "VPambientocclusion", 300001045)


def _cval(v):
    """Строка-имя константы → значение c4d; прочее как есть."""
    if isinstance(v, str) and v.isupper() and hasattr(c4d, v):
        return getattr(c4d, v)
    if isinstance(v, str) and v.isupper():
        _MISS.append(v)
        return None
    return v


def _apply_group(bl, d):
    for k, v in (d or {}).items():
        cid = getattr(c4d, k, None)
        val = _cval(v)
        if cid is None:
            if k not in _MISS:
                _MISS.append(k)
            continue
        if val is None:
            continue
        try:
            bl[cid] = val
        except Exception as e:
            _MISS.append("%s=%r (%s)" % (k, v, e))


def _resolve(name):
    p = RS_PRESETS[name]
    if "base" not in p:
        return {k: (dict(v) if isinstance(v, dict) else v) for k, v in p.items()}
    out = _resolve(p["base"])
    for k, v in p.items():
        if k == "base":
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def _vp_toggle(rd, pid, data):
    """data=None → видеопост выкл (BIT_VPDISABLED); dict → включить и выставить."""
    vp = rd.GetFirstVideoPost()
    while vp and vp.GetType() != pid:
        vp = vp.GetNext()
    if data is None:
        if vp is not None:
            vp.SetBit(c4d.BIT_VPDISABLED)
        return vp
    if vp is None:
        vp = _vp_ensure(rd, pid)
    if vp is not None:
        vp.DelBit(c4d.BIT_VPDISABLED)
        _apply_group(vp, data)
    return vp


def apply_preset(rd, name, out_res=None, cameras=True):
    """Применить пресет из rs_presets.py к RenderData rd (обычно RS_final).
    out_res — scene.json.output.res (для долевого res). ALPHA — накладка поверх
    уже применённого пресета: apply_preset(rd, "ALPHA") вторым вызовом.
    Возвращает список промахов констант (пусто — всё встало)."""
    if isinstance(rd, str):
        rd = _rs_find(rd)
    p = _resolve(name)
    _apply_group(rd, p.get("rd"))
    r = p.get("res")
    if r is not None and not p.get("overlay"):
        if isinstance(r, (tuple, list)):
            w, h = r
        else:
            bw, bh = out_res or (rd[c4d.RDATA_XRES], rd[c4d.RDATA_YRES])
            w, h = int(bw * r) // 2 * 2, int(bh * r) // 2 * 2
        rd[c4d.RDATA_XRES], rd[c4d.RDATA_YRES] = float(w), float(h)
    if not p.get("overlay"):
        phys = rd[c4d.RDATA_RENDERENGINE] == ENG["physical"]
        if phys:
            _vp_toggle(rd, ENG["physical"], p.get("phys") or {})
        _vp_toggle(rd, GI_VP, p.get("gi"))
        _vp_toggle(rd, AO_VP, p.get("ao"))
    if cameras and p.get("cam"):
        for o in W(doc.GetFirstObject()):
            if o.GetType() == c4d.Ocamera:
                _apply_group(o, p["cam"])
    if p.get("mat_glass"):
        m = doc.GetFirstMaterial()
        while m:
            if m.GetType() == c4d.Mmaterial and m[c4d.MATERIAL_USE_TRANSPARENCY]:
                _apply_group(m, p["mat_glass"])
            m = m.GetNext()
    if p.get("comp_bg"):
        for o in W(doc.GetFirstObject()):
            if o.GetType() in (c4d.Osky, c4d.Obackground):
                t = o.GetTag(c4d.Tcompositing) or o.MakeTag(c4d.Tcompositing)
                _apply_group(t, p["comp_bg"])
    print(json.dumps({"preset": name, "rd": rd.GetName(),
                      "res": [int(rd[c4d.RDATA_XRES]), int(rd[c4d.RDATA_YRES])], "missing": _MISS}))
    return _MISS


def ladder_state():
    """Какие пресеты есть, их движок/разрешение, активный, выдержка камер."""
    out, rd = {}, doc.GetFirstRenderData()
    while rd:
        out[rd.GetName()] = {"engine": {v: k for k, v in ENG.items()}.get(rd[c4d.RDATA_RENDERENGINE], rd[c4d.RDATA_RENDERENGINE]),
                             "res": [int(rd[c4d.RDATA_XRES]), int(rd[c4d.RDATA_YRES])]}
        rd = rd.GetNext()
    sh = getattr(c4d, "CAMERAOBJECT_SHUTTER_SPEED_VALUE", None)
    cams = {o.GetName(): (round(1.0 / o[sh]) if sh and o[sh] else None)
            for o in W(doc.GetFirstObject()) if o.GetType() == c4d.Ocamera}
    print(json.dumps({"presets": out, "active": doc.GetActiveRenderData().GetName(),
                      "fps": doc.GetFps(), "shutter_1_over": cams}, ensure_ascii=False))


def time_frame(frame, path):
    """Честный замер времени кадра на RS_final (полное разрешение, полные настройки).
    По одному кадру на вызов: кадр дольше ~50 с упрётся в 60-секундный лимит
    моста — и сам таймаут уже ответ: время кадра больше лимита, жми на понижение
    (пресеты render-presets.md), а не «запущу, посмотрим»."""
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
