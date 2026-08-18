# --- LIGHT / MATERIAL / RENDER TOOLKIT -------------------------------------
# Вклеивать ПОСЛЕ прелюдии c4d-core. Требует find/N/render_to.

def light(name, kind="distant", rot=(0, 0, 0), pos=(0, 0, 0),
          color=(1.0, 1.0, 1.0), power=1.0, shadow="soft", size=None):
    """kind: distant | area | omni | spot. shadow: none | soft | hard | area."""
    TYPES = {"distant": c4d.LIGHT_TYPE_DISTANT, "area": c4d.LIGHT_TYPE_AREA,
             "omni": c4d.LIGHT_TYPE_OMNI, "spot": c4d.LIGHT_TYPE_SPOT}
    SH = {"none": c4d.LIGHT_SHADOWTYPE_NONE, "soft": c4d.LIGHT_SHADOWTYPE_SOFT,
          "hard": c4d.LIGHT_SHADOWTYPE_HARD, "area": c4d.LIGHT_SHADOWTYPE_AREA}
    grp = N("GRP_lights", c4d.Onull)
    l = N(name, c4d.Olight, grp, pos=pos, rot=rot)
    l[c4d.LIGHT_TYPE] = TYPES[kind]
    l[c4d.LIGHT_COLOR] = c4d.Vector(*color)
    l[c4d.LIGHT_BRIGHTNESS] = float(power)
    l[c4d.LIGHT_SHADOWTYPE] = SH[shadow]
    if kind == "area" and size:
        l[c4d.LIGHT_AREADETAILS_SIZEX] = float(size[0])
        l[c4d.LIGHT_AREADETAILS_SIZEY] = float(size[1])
    return l


def three_point(sun_rot=(-40, -35, 0), rim_rot=(150, -20, 0),
                warm=(1.0, 0.93, 0.80), cool=(0.62, 0.72, 1.0),
                key_power=1.1, fill_power=0.35, rim_power=1.4):
    """Дневная раскладка для погони. Контровой — не украшение: без него
    силуэты персонажей сливаются с фоном."""
    k = light("LGT_key", "distant", rot=sun_rot, color=warm,
              power=key_power, shadow="soft")
    f = light("LGT_fill", "area", rot=(-90, -90, 0), pos=(0, 900, 0),
              color=cool, power=fill_power, shadow="none", size=(4000, 4000))
    r = light("LGT_rim", "distant", rot=rim_rot, color=(1.0, 0.98, 0.92),
              power=rim_power, shadow="none")
    return k, f, r


def mat(name, color=(0.5, 0.5, 0.5), lum=None):
    """Матовый материал: цвет + опциональное свечение. Для прокси этого хватает."""
    m = None
    for x in doc.GetMaterials():
        if x.GetName() == name:
            m = x
            break
    if m is None:
        m = c4d.BaseMaterial(c4d.Mmaterial)
        m.SetName(name)
        doc.InsertMaterial(m)
    m[c4d.MATERIAL_USE_COLOR] = True
    m[c4d.MATERIAL_COLOR_COLOR] = c4d.Vector(*color)
    m[c4d.MATERIAL_USE_REFLECTION] = False
    if lum is not None:
        m[c4d.MATERIAL_USE_LUMINANCE] = True
        m[c4d.MATERIAL_LUMINANCE_COLOR] = c4d.Vector(*lum)
    m.Update(True, True)
    return m


def assign(m, target, recursive=True):
    """Повесить материал на объект (и на всех потомков)."""
    if isinstance(target, str):
        target = find(target)
    if target is None:
        return 0
    n = 0
    stack = [target]
    while stack:
        o = stack.pop()
        tag = None
        for t in o.GetTags():
            if t.GetType() == c4d.Ttexture:
                tag = t
                break
        if tag is None:
            tag = o.MakeTag(c4d.Ttexture)
        tag[c4d.TEXTURETAG_MATERIAL] = m
        n += 1
        if recursive:
            c = o.GetDown()
            while c:
                stack.append(c)
                c = c.GetNext()
    return n


def render_settings(w=1280, h=720, f0=0, f1=100, path=None, png=True):
    """Настройка финального прогона. Сам прогон запускает пользователь:
    Render → Render to Picture Viewer (мост отвалится по таймауту)."""
    fps = doc.GetFps()
    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_XRES] = float(w)
    rd[c4d.RDATA_YRES] = float(h)
    rd[c4d.RDATA_FRAMERATE] = float(fps)
    rd[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL
    rd[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(f0, fps)
    rd[c4d.RDATA_FRAMETO] = c4d.BaseTime(f1, fps)
    if path:
        rd[c4d.RDATA_SAVEIMAGE] = True
        rd[c4d.RDATA_PATH] = path
        if png:
            rd[c4d.RDATA_FORMAT] = c4d.FILTER_PNG
    print(json.dumps({"res": [w, h], "frames": [f0, f1], "fps": fps,
                      "path": path, "engine": rd[c4d.RDATA_RENDERENGINE]}))
    return rd


def contact_sheet(folder, frames, cam=None, w=800, h=450, tag="look"):
    """Отрендерить набор кадров по одному. ВНИМАНИЕ: 30 с на скрипт —
    больше 3–4 кадров за один вызов не запрашивай, режь на несколько скриптов."""
    if cam:
        activate(cam)
    out = []
    for f in frames:
        p = "%s/%s-f%03d.png" % (folder, tag, f)
        if render_to(p, f, w, h):
            out.append(p)
    print(json.dumps(out))
    return out
# --- END TOOLKIT -----------------------------------------------------------
