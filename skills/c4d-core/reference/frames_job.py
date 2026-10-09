# frames_job.py — рендер пачки кадров в PNG внутри C4D (зовут bin/playblast.py и bin/keysheet.py).
# JOB = {"frames": [...], "out": "/abs/dir/", "rs": "RS_draft", "cam": "CAM_x"|None,
#        "w": 640, "h": 360, "clay": False, "simplify": True, "prefix": "f", "pad": 4}
# simplify — временные упрощения ТОЛЬКО на время пачки (возвращаются в finally):
#   источники не видны в отражениях, шероховатость отражений → 0, дисперсия прозрачности → 0.
#   Без них стекло/матовые отражения делают черновой кадр 2–3 мин и мост висит.
# clay — серый материал на всё, кроме объектов/материалов с префиксом SET_ или из JOB["keep"].
restore = []
_t0 = time.time()
if JOB.get("simplify", True):
    for o in W(doc.GetFirstObject()):
        if o.GetType() == c4d.Olight:
            pid = getattr(c4d, "LIGHT_AREADETAILS_SHOWINREFLECTION", None)
            if pid is not None and o[pid]:
                restore.append((o, pid, o[pid])); o[pid] = False
    RG = getattr(c4d, "REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS", None)
    m = doc.GetFirstMaterial()
    while m:
        if m.GetType() == c4d.Mmaterial:
            if m[c4d.MATERIAL_USE_TRANSPARENCY] and m[c4d.MATERIAL_TRANSPARENCY_DISPERSION]:
                restore.append((m, c4d.MATERIAL_TRANSPARENCY_DISPERSION, m[c4d.MATERIAL_TRANSPARENCY_DISPERSION]))
                m[c4d.MATERIAL_TRANSPARENCY_DISPERSION] = 0.0
            if RG is not None:
                for i in range(m.GetReflectionLayerCount()):
                    lid = m.GetReflectionLayerIndex(i).GetDataID()
                    if m[lid + RG]:
                        restore.append((m, lid + RG, m[lid + RG])); m[lid + RG] = 0.0
        m = m.GetNext()
tag_restore = []
if JOB.get("clay"):
    keep = set(JOB.get("keep", []))
    clay = doc.SearchMaterial("MAT_tmp_clay")
    if clay is None:
        clay = c4d.BaseMaterial(c4d.Mmaterial); clay.SetName("MAT_tmp_clay"); doc.InsertMaterial(clay)
    clay[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(0.5, 0.5, 0.49)
    for o in W(doc.GetFirstObject()):
        if o.GetName().startswith("SET_") or o.GetName() in keep:
            continue
        for t in o.GetTags():
            if t.GetType() == c4d.Ttexture:
                mm = t[c4d.TEXTURETAG_MATERIAL]
                if mm and mm.GetName() not in keep:
                    tag_restore.append((t, mm)); t[c4d.TEXTURETAG_MATERIAL] = clay
prev_rs = doc.GetActiveRenderData().GetName()
prev_cam = doc.GetActiveBaseDraw().GetSceneCamera(doc)
prev_t = doc.GetTime()
use_rs(JOB.get("rs", "RS_draft"))
if JOB.get("cam"):
    activate(JOB["cam"])
done_frames, failed = [], []
try:
    for f in JOB["frames"]:
        p = JOB["out"] + "%s%0*d.png" % (JOB.get("prefix", "f"), JOB.get("pad", 4), f)
        if render_to(p, f, JOB["w"], JOB["h"]):
            done_frames.append(f)
        else:
            failed.append(f)
        if time.time() - _t0 > JOB.get("budget", 48):      # не упираться в 60 с моста
            break
finally:
    for obj, pid, val in restore:
        obj[pid] = val
    for t, mm in tag_restore:
        t[c4d.TEXTURETAG_MATERIAL] = mm
    cl = doc.SearchMaterial("MAT_tmp_clay")
    if cl:
        cl.Remove()
    use_rs(prev_rs)
    if prev_cam:
        activate(prev_cam)
    doc.SetTime(prev_t)
dt = time.time() - _t0
print(json.dumps({"done": done_frames, "failed": failed, "sec": round(dt, 1),
                  "per_frame": round(dt / max(1, len(done_frames)), 2)}))
