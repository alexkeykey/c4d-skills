# Прогони один раз на новой машине / новой версии C4D:
# отправь этот файл целиком в mcp__cinema4d__execute_python_script.
# Он проверяет, что все константы и вызовы, на которых стоит прелюдия, существуют.
NAMES = [
    "Onull", "Ocube", "Osphere", "Ocylinder", "Ocapsule", "Oplane", "Ofloor",
    "Ocamera", "Olight", "Mmaterial", "Ttexture", "Ttargetexpression",
    "ID_BASEOBJECT_REL_POSITION", "ID_BASEOBJECT_REL_ROTATION",
    "ID_BASEOBJECT_REL_SCALE", "VECTOR_X", "VECTOR_Y", "VECTOR_Z",
    "DTYPE_VECTOR", "DTYPE_REAL",
    "CINTERPOLATION_SPLINE", "CINTERPOLATION_LINEAR", "CINTERPOLATION_STEP",
    "DOCUMENT_MINTIME", "DOCUMENT_MAXTIME",
    "DOCUMENT_LOOPMINTIME", "DOCUMENT_LOOPMAXTIME",
    "RDATA_XRES", "RDATA_YRES", "RDATA_SAVEIMAGE",
    "RENDERFLAGS_EXTERNAL", "RENDERRESULT_OK", "FILTER_PNG",
    "PRIM_CUBE_LEN", "PRIM_SPHERE_RAD", "PRIM_CYLINDER_RADIUS",
    "PRIM_CYLINDER_HEIGHT", "PRIM_CAPSULE_RADIUS", "PRIM_CAPSULE_HEIGHT",
    "PRIM_PLANE_WIDTH", "PRIM_PLANE_HEIGHT",
    "CAMERA_FOCUS", "TARGETEXPRESSIONTAG_LINK", "TEXTURETAG_MATERIAL",
    "LIGHT_TYPE", "LIGHT_TYPE_AREA", "LIGHT_COLOR", "LIGHT_BRIGHTNESS",
    "LIGHT_SHADOWTYPE", "LIGHT_SHADOWTYPE_SOFT",
    "MATERIAL_COLOR_COLOR", "MATERIAL_USE_REFLECTION", "MATERIAL_USE_COLOR",
]
missing = [n for n in NAMES if not hasattr(c4d, n)]

# живая проверка ключевого механизма: трек + кривая + ключ на временном объекте
probe = "ZZ_selftest_probe"
o = c4d.BaseObject(c4d.Onull)
o.SetName(probe)
doc.InsertObject(o)
ok_key = False
try:
    did = c4d.DescID(
        c4d.DescLevel(c4d.ID_BASEOBJECT_REL_POSITION, c4d.DTYPE_VECTOR, 0),
        c4d.DescLevel(c4d.VECTOR_X, c4d.DTYPE_REAL, 0))
    tr = c4d.CTrack(o, did)
    o.InsertTrackSorted(tr)
    cu = tr.GetCurve()
    r = cu.AddKey(c4d.BaseTime(10, doc.GetFps()))
    cu.SetKeyDefault(doc, r["nidx"])
    r["key"].SetValue(cu, 100.0)
    r["key"].SetInterpolation(cu, c4d.CINTERPOLATION_SPLINE)
    ok_key = cu.GetKeyCount() == 1
finally:
    o.Remove()

print(json.dumps({
    "c4d_version": c4d.GetC4DVersion(),
    "fps": doc.GetFps(),
    "missing_constants": missing,
    "keyframe_mechanism_ok": ok_key,
}, indent=2))
c4d.EventAdd()
