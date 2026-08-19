# --- C4D PRELUDE v2 --------------------------------------------------------
# Приклеивай целиком в начало КАЖДОГО execute_python_script.
# Песочница уже даёт: c4d, math, random, time, json, doc.
# Углы везде в ГРАДУСАХ — конвертация в радианы внутри.
FPS = doc.GetFps()

def W(o):
    while o:
        yield o
        for c in W(o.GetDown()):
            yield c
        o = o.GetNext()

def find(n):
    for o in W(doc.GetFirstObject()):
        if o.GetName() == n:
            return o
    return None

def N(name, otype=c4d.Onull, parent=None, pos=None, rot=None, scl=None):
    """Идемпотентно: вернуть объект с этим именем, иначе создать."""
    o = find(name)
    if o is None:
        o = c4d.BaseObject(otype)
        o.SetName(name)
        p = find(parent) if isinstance(parent, str) else parent
        doc.InsertObject(o, parent=p)
    if pos is not None:
        o[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(*pos)
    if rot is not None:
        o[c4d.ID_BASEOBJECT_REL_ROTATION] = c4d.Vector(*[math.radians(a) for a in rot])
    if scl is not None:
        o[c4d.ID_BASEOBJECT_REL_SCALE] = c4d.Vector(*scl)
    return o

CH = {
    "px": (c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_X),
    "py": (c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Y),
    "pz": (c4d.ID_BASEOBJECT_REL_POSITION, c4d.VECTOR_Z),
    "rh": (c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_X),
    "rp": (c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Y),
    "rb": (c4d.ID_BASEOBJECT_REL_ROTATION, c4d.VECTOR_Z),
    "sx": (c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_X),
    "sy": (c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Y),
    "sz": (c4d.ID_BASEOBJECT_REL_SCALE, c4d.VECTOR_Z),
}
INT = {
    "spline": c4d.CINTERPOLATION_SPLINE,
    "linear": c4d.CINTERPOLATION_LINEAR,
    "step": c4d.CINTERPOLATION_STEP,
}

def key(o, ch, frame, val, interp="spline"):
    """Ключ на канал. ch: px py pz rh rp rb sx sy sz. Замена сломанному MCP set_keyframe."""
    if isinstance(o, str):
        o = find(o)
    if o is None:
        raise ValueError("key(): object not found")
    vid, sub = CH[ch]
    did = c4d.DescID(c4d.DescLevel(vid, c4d.DTYPE_VECTOR, 0),
                     c4d.DescLevel(sub, c4d.DTYPE_REAL, 0))
    tr = o.FindCTrack(did)
    if tr is None:
        tr = c4d.CTrack(o, did)
        o.InsertTrackSorted(tr)
    cu = tr.GetCurve()
    t = c4d.BaseTime(frame, FPS)
    ex = cu.FindKey(t)
    if ex:
        k = ex["key"]
    else:
        r = cu.AddKey(t)
        k = r["key"]
        cu.SetKeyDefault(doc, r["nidx"])
    k.SetValue(cu, math.radians(val) if ch[0] == "r" else val)
    k.SetInterpolation(cu, INT[interp])
    return k

def key_vis(o, frame, on):
    """Ключ видимости (editor+render разом), интерполяция step. Механизм смены
    состояний ассетов (__<состояние>, c4d-core §5): на кадре смены —
    key_vis(старый, f, False) + key_vis(новый, f, True)."""
    if isinstance(o, str):
        o = find(o)
    if o is None:
        raise ValueError("key_vis(): object not found")
    v = 0 if on else 1          # 0 = вкл, 1 = выкл
    for pid in (c4d.ID_BASEOBJECT_VISIBILITY_EDITOR,
                c4d.ID_BASEOBJECT_VISIBILITY_RENDER):
        did = c4d.DescID(c4d.DescLevel(pid, c4d.DTYPE_LONG, 0))
        tr = o.FindCTrack(did)
        if tr is None:
            tr = c4d.CTrack(o, did)
            o.InsertTrackSorted(tr)
        cu = tr.GetCurve()
        t = c4d.BaseTime(frame, FPS)
        ex = cu.FindKey(t)
        if ex:
            k = ex["key"]
        else:
            k = cu.AddKey(t)["key"]
        k.SetValue(cu, v)
        k.SetInterpolation(cu, c4d.CINTERPOLATION_STEP)
    return o

def clear_keys(o, ch=None):
    """Снести треки объекта (все или один канал) — для перезаливки анимации.
    Трек удаляется через tr.Remove(): метода KillCTrack у объекта НЕТ."""
    if isinstance(o, str):
        o = find(o)
    n = 0
    for tr in list(o.GetCTracks()):
        if ch is None:
            tr.Remove()
            n += 1
        else:
            vid, sub = CH[ch]
            d = tr.GetDescriptionID()
            if d[0].id == vid and d[1].id == sub:
                tr.Remove()
                n += 1
    return n

def timing(fps=24, length=120):
    """Кадровая база документа: fps и диапазон 0..length."""
    doc.SetFps(fps)
    doc[c4d.DOCUMENT_MINTIME] = c4d.BaseTime(0, fps)
    doc[c4d.DOCUMENT_MAXTIME] = c4d.BaseTime(length, fps)
    doc[c4d.DOCUMENT_LOOPMINTIME] = c4d.BaseTime(0, fps)
    doc[c4d.DOCUMENT_LOOPMAXTIME] = c4d.BaseTime(length, fps)

def look(cam, target):
    """Повесить на камеру Target-таг — камера всегда смотрит на объект."""
    if isinstance(cam, str):
        cam = find(cam)
    if isinstance(target, str):
        target = find(target)
    for t in cam.GetTags():
        if t.GetType() == c4d.Ttargetexpression:
            t[c4d.TARGETEXPRESSIONTAG_LINK] = target
            return t
    tag = cam.MakeTag(c4d.Ttargetexpression)
    tag[c4d.TARGETEXPRESSIONTAG_LINK] = target
    return tag

def activate(cam):
    """Сделать камеру активной во вьюпорте и в рендере."""
    if isinstance(cam, str):
        cam = find(cam)
    doc.GetActiveBaseDraw().SetSceneCamera(cam)
    return cam

def use_rs(name):
    """Активировать рендер-пресет лестницы по имени (RS_draft/RS_tex/RS_light/RS_final).
    Роль включает свой пресет первой строкой рендер-фазы — c4d-core §5b."""
    rd = doc.GetFirstRenderData()
    while rd:
        if rd.GetName() == name:
            doc.SetActiveRenderData(rd)
            return rd
        rd = rd.GetNext()
    print("NO RENDER PRESET %s — вклей renderladder.py и создай лестницу" % name)
    return None

def render_to(path, frame=None, w=960, h=540, show=True):
    """Рендер кадра в PNG (через активный рендер-пресет) + показ в Picture Viewer,
    чтобы пользователь видел, что идёт рендер, а не «всё зависло». Потом Read файла."""
    if frame is not None:
        doc.SetTime(c4d.BaseTime(frame, FPS))
        bf = getattr(c4d, "BUILDFLAGS_NONE", 0)
        doc.ExecutePasses(None, True, True, True, bf)
    if hasattr(c4d, "StatusSetText"):
        c4d.StatusSetText("render f%s → %s" % (frame, path.split("/")[-1]))
    rd = doc.GetActiveRenderData().GetClone()
    rd[c4d.RDATA_XRES] = float(w)
    rd[c4d.RDATA_YRES] = float(h)
    rd[c4d.RDATA_SAVEIMAGE] = False
    bmp = c4d.bitmaps.BaseBitmap()
    bmp.Init(int(w), int(h), 24)
    res = c4d.documents.RenderDocument(doc, rd.GetData(), bmp,
                                       c4d.RENDERFLAGS_EXTERNAL)
    if hasattr(c4d, "StatusClear"):
        c4d.StatusClear()
    if res != c4d.RENDERRESULT_OK:
        print("RENDER FAILED code=%s" % res)
        return False
    bmp.Save(path, c4d.FILTER_PNG)
    if show and hasattr(c4d.bitmaps, "ShowBitmap"):
        c4d.bitmaps.ShowBitmap(bmp)
    print("RENDERED %s (frame=%s)" % (path, frame))
    return True

def tree():
    """Печать иерархии сцены с отступами — дешёвая замена list_objects."""
    def rec(o, d):
        while o:
            print("%s%s  [%s]" % ("  " * d, o.GetName(), o.GetTypeName()))
            rec(o.GetDown(), d + 1)
            o = o.GetNext()
    rec(doc.GetFirstObject(), 0)

def done(msg="ok"):
    c4d.EventAdd()
    print(msg)
# --- END PRELUDE -----------------------------------------------------------
