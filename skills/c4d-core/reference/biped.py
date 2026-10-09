# --- BIPED PROXY BUILDER ---------------------------------------------------
# Вклеивать ПОСЛЕ прелюдии c4d-core. Требует find/N из неё.
# Все размеры считаются от роста h, поэтому великан = тот же вызов с h=630.
# Персонаж смотрит в +X. Мах конечностей вперёд-назад = канал "rb".
#
# ЗНАК "rb" РАЗНЫЙ ДЛЯ КОРПУСА И ДЛЯ КОНЕЧНОСТЕЙ — проверено в C4D 2024:
#   root.rb = +16°  → голова уходит ВПЕРЁД (+X). Наклон вперёд = плюс.
#   arm/leg_piv.rb = +125° → кисть/стопа уходит НАЗАД (−X).
# Причина: конечность свисает ВНИЗ от пивота, поэтому её конец движется
# в сторону, противоположную «верху» корпуса. Для циклической ходьбы это
# неважно (обе ноги в противофазе), но замах, бросок и любое одиночное
# движение рукой ставится с ОБРАТНЫМ знаком. Не угадывай — считай позицию
# конца конечности через GetMg() и сравнивай с позицией CTRL.

def biped(cid, h=180.0, pos=(0, 0, 0), build=0.11, parent=None):
    """Прокси-двуногий на нулевых контроллерах.

    cid    — id персонажа ("odysseus"), даёт префикс CHAR_<cid>_
    h      — рост в юнитах (см)
    pos    — стартовая позиция CTRL на земле
    build  — сложение: 0.09 худой, 0.11 обычный, 0.15 массивный
    Возвращает dict с ключевыми нулями.
    """
    p = "CHAR_%s_" % cid
    ctrl = N(p + "CTRL", c4d.Onull, parent, pos=pos)
    hip = 0.53 * h
    root = N(p + "root", c4d.Onull, ctrl, pos=(0, hip, 0))

    torso = N(p + "torso", c4d.Ocapsule, root, pos=(0, 0.17 * h, 0))
    torso[c4d.PRIM_CAPSULE_RADIUS] = build * h
    torso[c4d.PRIM_CAPSULE_HEIGHT] = 0.40 * h

    head = N(p + "head", c4d.Osphere, root, pos=(0, 0.40 * h, 0))
    head[c4d.PRIM_SPHERE_RAD] = 0.075 * h

    out = {"ctrl": ctrl, "root": root, "torso": torso, "head": head}

    for side, sgn in (("L", 1.0), ("R", -1.0)):
        # рука: пивот в плече, капсула свисает вниз
        ap = N(p + "arm%s_piv" % side, c4d.Onull, root,
               pos=(0, 0.29 * h, sgn * (build * h + 0.035 * h)))
        arm = N(p + "arm%s" % side, c4d.Ocapsule, ap, pos=(0, -0.16 * h, 0))
        arm[c4d.PRIM_CAPSULE_RADIUS] = 0.40 * build * h
        arm[c4d.PRIM_CAPSULE_HEIGHT] = 0.32 * h

        # нога: пивот в бедре
        lp = N(p + "leg%s_piv" % side, c4d.Onull, root,
               pos=(0, 0.0, sgn * 0.055 * h))
        leg = N(p + "leg%s" % side, c4d.Ocapsule, lp, pos=(0, -0.25 * h, 0))
        leg[c4d.PRIM_CAPSULE_RADIUS] = 0.55 * build * h
        leg[c4d.PRIM_CAPSULE_HEIGHT] = 0.50 * h

        out["arm" + side] = ap
        out["leg" + side] = lp

    return out


def ground(name="SET_ground", size=(12000, 12000), y=0.0):
    g = N(name, c4d.Oplane, None, pos=(0, y, 0))
    g[c4d.PRIM_PLANE_WIDTH] = float(size[0])
    g[c4d.PRIM_PLANE_HEIGHT] = float(size[1])
    g[c4d.PRIM_PLANE_SUBW] = 1
    g[c4d.PRIM_PLANE_SUBH] = 1
    return g


def scatter(name, count=14, x_range=(-2500, 2000), z_range=(-450, 450),
            scale=(80, 260), seed=7, parent=None, shape="cube", avoid_z=None):
    """Полоса объектов вдоль трассы — главный носитель скорости.

    shape   — "cube" (валуны) или "cylinder" (стволы/колонны)
    avoid_z — (z0, z1): коридор, который надо держать пустым. Нужен, когда камера
              летит вдоль трассы: объект в её коридоре просто влетит в объектив.
              Попавшие внутрь выталкиваются наружу, а не выбрасываются, — иначе
              при узком z_range половина объектов молча пропадает.
    Сид фиксирован: повторный прогон даёт ту же расстановку."""
    random.seed(seed)
    grp = N(parent or "GRP_set", c4d.Onull, None)
    made = []
    pushed = 0
    for i in range(count):
        s = random.uniform(scale[0], scale[1])
        x = random.uniform(x_range[0], x_range[1])
        z = random.uniform(z_range[0], z_range[1])
        if avoid_z and avoid_z[0] < z < avoid_z[1]:
            half = 0.5 * (avoid_z[0] + avoid_z[1])
            edge = avoid_z[1] if z >= half else avoid_z[0]
            span = max(1.0, (z_range[1] - z_range[0]) * 0.25)
            z = edge + (span * random.uniform(0.15, 1.0)) * (1 if z >= half else -1)
            pushed += 1
        if shape == "cone":
            # горы/скалы: конус, ширина основания больше высоты — иначе читается
            # как ёлка, а не как гора
            o = N("%s_%02d" % (name, i), c4d.Ocone, grp,
                  pos=(x, s * 0.5, z), rot=(random.uniform(0, 360), 0,
                                            random.uniform(-4, 4)))
            o[c4d.PRIM_CONE_BRAD] = s * random.uniform(0.55, 0.95)
            o[c4d.PRIM_CONE_TRAD] = s * random.uniform(0.0, 0.10)
            o[c4d.PRIM_CONE_HEIGHT] = s
        elif shape == "cylinder":
            o = N("%s_%02d" % (name, i), c4d.Ocylinder, grp,
                  pos=(x, s * 0.5, z), rot=(0, 0, random.uniform(-3, 3)))
            o[c4d.PRIM_CYLINDER_RADIUS] = s * random.uniform(0.045, 0.085)
            o[c4d.PRIM_CYLINDER_HEIGHT] = s
        else:
            o = N("%s_%02d" % (name, i), c4d.Ocube, grp,
                  pos=(x, s * 0.35, z),
                  rot=(random.uniform(0, 360), 0, random.uniform(-12, 12)))
            o[c4d.PRIM_CUBE_LEN] = c4d.Vector(s, s * 0.7, s * 0.9)
        made.append(o)
    if avoid_z:
        print("scatter %s: %d шт, вытолкнуто из коридора %s: %d"
              % (name, len(made), avoid_z, pushed))
    return made
# --- END BIPED BUILDER -----------------------------------------------------
