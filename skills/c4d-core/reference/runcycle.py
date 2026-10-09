# --- RUN CYCLE / TIMING TOOLKIT --------------------------------------------
# Вклеивать ПОСЛЕ прелюдии c4d-core. Требует find/key/clear_keys/FPS.
# Персонаж смотрит в +X, мах конечностей — канал "rb".
# Если на первом рендере мах идёт назад — передай sign=-1.0 (и запиши это в pipeline.md).

def travel(cid, f0, f1, x0, x1, y=0.0, z=0.0):
    """Траектория CTRL по +X. Линейная интерполяция: сплайн даёт замедление
    на концах, а замедление при неизменном цикле ног = скольжение."""
    c = find("CHAR_%s_CTRL" % cid)
    clear_keys(c, "px")
    c[c4d.ID_BASEOBJECT_REL_POSITION] = c4d.Vector(x0, y, z)
    key(c, "px", f0, x0, "linear")
    key(c, "px", f1, x1, "linear")
    v = (x1 - x0) / float(f1 - f0)
    print("travel %s: v=%.1f юнитов/кадр (%.0f юнитов/с)" % (cid, v, v * FPS))
    return v


def cycle_for(h, base=16.0, base_h=180.0):
    """Период шага ∝ √(длина ноги). Великан 630 см → ~30 кадров при 25 fps."""
    return max(6.0, base * math.sqrt(float(h) / base_h))


def run_cycle(cid, f0, f1, h=180.0, v=None, cyc=None, phase=0.0,
              lean_deg=14.0, arm_ratio=0.8, amp=None, bob=None, sign=1.0):
    """Цикл бега на нулевых пивотах. Ключи ставятся по четвертям цикла.

    v    — скорость в юнитах/кадр (из travel()); по ней считается амплитуда
    cyc  — длина полного цикла (два шага) в кадрах; по умолчанию из роста
    Возвращает (cyc, amp).
    """
    p = "CHAR_%s_" % cid
    if cyc is None:
        cyc = cycle_for(h)
    L = 0.5 * h                      # длина ноги
    if amp is None:
        if v is None:
            amp = 32.0
        else:
            d = abs(v) * (cyc / 2.0)     # путь тела за один шаг
            r = d / (2.0 * L)            # требуемый sin амплитуды
            if r > 0.8:
                print("WARN %s: цикл слишком длинный для скорости "
                      "(ratio=%.2f). Укороти cyc, а не задирай амплитуду." % (cid, r))
                r = 0.8
            amp = math.degrees(math.asin(r))
    if bob is None:
        bob = 0.025 * h

    legL = find(p + "legL_piv"); legR = find(p + "legR_piv")
    armL = find(p + "armL_piv"); armR = find(p + "armR_piv")
    root = find(p + "root")
    for o in (legL, legR, armL, armR):
        clear_keys(o, "rb")
    clear_keys(root, "py")
    hip = root[c4d.ID_BASEOBJECT_REL_POSITION].y

    n = 0
    f = float(f0)
    stp = cyc / 4.0
    while f <= f1 + 1e-6:
        fi = int(round(f))
        t = 2.0 * math.pi * ((f - f0) / cyc + phase)
        s = math.cos(t)
        key(legL, "rb", fi,  sign * amp * s)
        key(legR, "rb", fi, -sign * amp * s)
        key(armL, "rb", fi, -sign * amp * arm_ratio * s)
        key(armR, "rb", fi,  sign * amp * arm_ratio * s)
        # покачивание корпуса — двойная частота: низшая точка в опоре
        key(root, "py", fi, hip - bob * math.cos(2.0 * t))
        f += stp
        n += 1

    key(root, "rb", f0, sign * lean_deg)   # наклон корпуса вперёд, постоянный
    print("run_cycle %s: cyc=%.1f amp=%.1f° bob=%.1f ключей/канал=%d"
          % (cid, cyc, amp, bob, n))
    return cyc, amp


def footfalls(f0, f1, cyc, phase=0.0):
    """Кадры контакта ноги с землёй — под тряску камеры и звук."""
    out = []
    f = float(f0) + phase * cyc
    while f <= f1:
        out.append(int(round(f)))
        f += cyc / 2.0
    return out


def cam_shake(cam, frames, amp=1.5, dur=3):
    """Микро-толчок камеры на каждый шаг великана. Самый дешёвый сигнал массы.
    Внимание: пишет в canal py камеры — не сочетать с анимацией высоты камеры."""
    if isinstance(cam, str):
        cam = find(cam)
    base = cam[c4d.ID_BASEOBJECT_REL_POSITION].y
    for f in frames:
        key(cam, "py", f, base)
        key(cam, "py", f + 1, base - amp)
        key(cam, "py", f + dur, base)
    print("cam_shake: %d толчков" % len(frames))


def glance_back(cid, f, hold=6, ang=55.0, ramp=4):
    """Взгляд назад через плечо — пауза-акцент в погоне."""
    r = find("CHAR_%s_root" % cid)
    key(r, "rh", f - ramp, 0.0)
    key(r, "rh", f, ang)
    key(r, "rh", f + hold, ang)
    key(r, "rh", f + hold + ramp + 1, 0.0)


def anticipate(cid, f, dip=0.06, frames=4, h=180.0):
    """Подготовка перед стартом: корпус оседает вниз, потом выстреливает."""
    r = find("CHAR_%s_root" % cid)
    hip = r[c4d.ID_BASEOBJECT_REL_POSITION].y
    key(r, "py", f - frames, hip)
    key(r, "py", f, hip - dip * h)
    key(r, "py", f + frames, hip + dip * h * 0.4)
    key(r, "py", f + frames * 2, hip)
# --- END TOOLKIT -----------------------------------------------------------
