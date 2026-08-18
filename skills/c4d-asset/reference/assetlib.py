# --- ASSET LIBRARY TOOLKIT -------------------------------------------------
# Вклеивать ПОСЛЕ прелюдии c4d-core. Требует find/N/W/render_to.
# ВАЖНО: пути передавать АБСОЛЮТНЫМИ. Тильда внутри C4D не раскрывается,
# модуля os в песочнице нет — подставляй /Users/<user>/... сам.

def WD(o):
    """Обход поддерева (в отличие от W из прелюдии — без соседей)."""
    if isinstance(o, str):
        o = find(o)
    if o is None:
        return
    yield o
    c = o.GetDown()
    while c:
        for x in WD(c):
            yield x
        c = c.GetNext()


SKIP_TYPES = (c4d.Ojoint,)

def bbox(o):
    """Глобальный габарит поддерева → (min, max) или None, если геометрии нет.

    ДЖОЙНТЫ ИСКЛЮЧЕНЫ НАМЕРЕННО. У Ojoint есть собственный GetRad() — это длина
    кости для отрисовки, а не геометрия. На риге из Mixamo/C4D шея и голова дают
    габарит втрое выше самой модели, и fit_height молча подгоняет не то:
    просишь рост 180 — получаешь 530.
    """
    if isinstance(o, str):
        o = find(o)
    lo = [1e20, 1e20, 1e20]
    hi = [-1e20, -1e20, -1e20]
    got = False
    for x in WD(o):
        if x.GetType() in SKIP_TYPES:
            continue
        r = x.GetRad()
        if r.x == 0 and r.y == 0 and r.z == 0:
            continue
        m = x.GetMg()
        c = m * x.GetMp()
        for i in (-1, 1):
            for j in (-1, 1):
                for k in (-1, 1):
                    p = c + m.v1 * (r.x * i) + m.v2 * (r.y * j) + m.v3 * (r.z * k)
                    lo = [min(lo[0], p.x), min(lo[1], p.y), min(lo[2], p.z)]
                    hi = [max(hi[0], p.x), max(hi[1], p.y), max(hi[2], p.z)]
                    got = True
    if not got:
        return None
    return c4d.Vector(*lo), c4d.Vector(*hi)


def bbox_size(o):
    b = bbox(o)
    if b is None:
        print("bbox: геометрии не найдено")
        return None
    s = b[1] - b[0]
    print("bbox %s: %.1f x %.1f x %.1f (низ y=%.1f)"
          % (o if isinstance(o, str) else o.GetName(), s.x, s.y, s.z, b[0].y))
    return s


def fit_height(o, target):
    """Вписать поддерево в целевой рост. Масштаб ложится на переданный объект —
    поэтому применяй к импорт-нулю ВНУТРИ контракта, а не к CHAR_*_CTRL:
    у CTRL масштаб обязан остаться 1,1,1."""
    if isinstance(o, str):
        o = find(o)
    b = bbox(o)
    if b is None:
        return None
    h = b[1].y - b[0].y
    if h <= 0:
        print("fit_height: нулевая высота")
        return None
    f = float(target) / h
    o[c4d.ID_BASEOBJECT_REL_SCALE] = o[c4d.ID_BASEOBJECT_REL_SCALE] * f
    c4d.EventAdd()
    print("fit_height: %.2f → %.2f (коэффициент %.4f)" % (h, target, f))
    return f


def ground_it(o):
    """Посадить низ габарита на y=0."""
    if isinstance(o, str):
        o = find(o)
    b = bbox(o)
    if b is None:
        return None
    p = o[c4d.ID_BASEOBJECT_REL_POSITION]
    o[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(p.x, p.y - b[0].y, p.z)
    c4d.EventAdd()
    print("ground_it: сдвиг по y на %.2f" % (-b[0].y))
    return -b[0].y


def wrap_contract(model, cid, hip_ratio=0.53, height=None):
    """Обернуть импортированную модель в контракт CHAR_biped_v1.
    Возвращает dict нулей. Лимб-пивоты НЕ создаются: у произвольной модели
    определить суставы нечем — см. случай «модель без скелета» в SKILL.md."""
    if isinstance(model, str):
        model = find(model)
    p = "CHAR_%s_" % cid
    ctrl = N(p + "CTRL", c4d.Onull, None, pos=(0, 0, 0), scl=(1, 1, 1))
    if height is None:
        b = bbox(model)
        height = (b[1].y - b[0].y) if b else 180.0
    root = N(p + "root", c4d.Onull, ctrl, pos=(0, hip_ratio * height, 0))
    model.Remove()
    doc.InsertObject(model, parent=root)
    model.SetName(p + "geo")
    # компенсировать подъём root, чтобы модель осталась стоять на земле
    model[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(0, -hip_ratio * height, 0)
    c4d.EventAdd()
    print("wrap_contract: %s, рост %.1f" % (cid, height))
    return {"ctrl": ctrl, "root": root, "geo": model}


def check_contract(ctrl_name, height=None, need_limbs=True, tol_pct=2.0):
    """Проверка контракта CHAR_biped_v1. Печатает и возвращает список расхождений."""
    issues = []
    c = find(ctrl_name)
    if c is None:
        print(json.dumps(["нет объекта " + ctrl_name], ensure_ascii=False))
        return ["нет объекта " + ctrl_name]
    base = ctrl_name[:-5] if ctrl_name.endswith("_CTRL") else ctrl_name

    s = c[c4d.ID_BASEOBJECT_REL_SCALE]
    if abs(s.x - 1) > 1e-3 or abs(s.y - 1) > 1e-3 or abs(s.z - 1) > 1e-3:
        issues.append("масштаб CTRL %.3f/%.3f/%.3f вместо 1,1,1" % (s.x, s.y, s.z))

    if find(base + "_root") is None:
        issues.append("нет " + base + "_root")
    if need_limbs:
        for n in ("armL_piv", "armR_piv", "legL_piv", "legR_piv"):
            if find(base + "_" + n) is None:
                issues.append("нет " + base + "_" + n)

    b = bbox(c)
    if b is None:
        issues.append("под CTRL нет геометрии")
    else:
        h = b[1].y - b[0].y
        if height and abs(h - height) > height * tol_pct / 100.0:
            issues.append("рост %.1f вместо %.1f" % (h, height))
        foot = b[0].y - c.GetMg().off.y
        if abs(foot) > max(1.0, h * 0.01):
            issues.append("ноги не на y=0: низ габарита на %.1f от CTRL" % foot)

    print(json.dumps(issues if issues else ["контракт ок"], ensure_ascii=False, indent=2))
    return issues


def strip_empty_texture_tags(root):
    """OBJ-импорт без .mtl вешает на каждый меш ПУСТОЙ Texture-тег (материал = None).
    Он идёт последним и перекрывает назначенный материал — объект рендерится белым,
    хотя тег с материалом на месте. Вызывать после каждого импорта OBJ."""
    if isinstance(root, str):
        root = find(root)
    n = 0
    for o in WD(root):
        for t in list(o.GetTags()):
            if t.GetType() == c4d.Ttexture and t[c4d.TEXTURETAG_MATERIAL] is None:
                t.Remove()
                n += 1
    return n


def align_to(src, ref, scale):
    """Совместить центр геометрии src с центром ref (обе — меши).
    Нужно, когда деталь из LDraw центрирована иначе, чем уже стоящая в сцене:
    у нашей головы центр был +0.56 от точки крепления, у импортной −0.4,
    и она молча висела на высоту головы ниже, внутри шеи."""
    if isinstance(src, str):
        src = find(src)
    if isinstance(ref, str):
        ref = find(ref)
    return ref.GetMp().y - src.GetMp().y * scale


def asset_import(path):
    """Загрузить внешний файл (fbx/obj/c4d) в текущий документ.
    Возвращает список новых объектов верхнего уровня."""
    return asset_merge(path)


def asset_merge(path):
    before = []
    o = doc.GetFirstObject()
    while o:
        before.append(o)
        o = o.GetNext()
    ok = c4d.documents.MergeDocument(
        doc, path, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MERGESCENE, None)
    if not ok:
        print("MERGE FAILED: %s (нет импортёра под формат или файл битый)" % path)
        return []
    new = []
    o = doc.GetFirstObject()
    while o:
        if o not in before:
            new.append(o)
        o = o.GetNext()
    c4d.EventAdd()
    print("merged %s → %s" % (path, [x.GetName() for x in new]))
    return new


def asset_save(root, path):
    """Выгрузить поддерево в отдельный .c4d. Материалы НЕ сохраняются намеренно:
    их раздаёт /c4d-look на уровне сцены."""
    if isinstance(root, str):
        root = find(root)
    if root is None:
        print("asset_save: объект не найден")
        return False
    tmp = c4d.documents.BaseDocument()
    tmp.InsertObject(root.GetClone())
    ok = c4d.documents.SaveDocument(
        tmp, path, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, c4d.FORMAT_C4DEXPORT)
    print("asset_save %s: %s" % (path, "ok" if ok else "FAILED"))
    return ok


def swap_proxy(ctrl_name, new_root, parts=None):
    """Подменить геометрию прокси на геометрию ассета, сохранив нули и ключи.

    По умолчанию: удаляет всю НЕ-нулевую геометрию под старым CTRL и вкладывает
    содержимое ассета под <base>_root. Анимация живёт на нулях и не трогается.
    parts — словарь {"имя_нуля_прокси": "имя_объекта_в_ассете"} для поштучной
    привязки, когда у ассета есть свои конечности.
    """
    old = find(ctrl_name)
    if isinstance(new_root, str):
        new_root = find(new_root)
    if old is None or new_root is None:
        print("swap_proxy: не найден CTRL или ассет")
        return False
    base = ctrl_name[:-5] if ctrl_name.endswith("_CTRL") else ctrl_name

    killed = 0
    for x in list(WD(old)):
        if x is old:
            continue
        if x.GetType() != c4d.Onull:
            x.Remove()
            killed += 1

    if parts:
        moved = 0
        for null_name, src_name in parts.items():
            tgt = find(null_name)
            src = find(src_name)
            if tgt and src:
                src.Remove()
                doc.InsertObject(src, parent=tgt)
                src[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(0, 0, 0)
                moved += 1
        new_root.Remove()
        print("swap_proxy: удалено %d, привязано частей %d" % (killed, moved))
    else:
        root = find(base + "_root") or old
        for c in list(WD(new_root)):
            if c is new_root:
                continue
            if c.GetUp() is not new_root:
                continue
            c.Remove()
            doc.InsertObject(c, parent=root)
        new_root.Remove()
        print("swap_proxy: удалено %d объектов прокси, геометрия ассета вложена в %s"
              % (killed, root.GetName()))
    c4d.EventAdd()
    return True
# --- END TOOLKIT -----------------------------------------------------------
