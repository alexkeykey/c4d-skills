# final_job.py — операции с RS_final (зовёт bin/final.py; нужен renderladder.py).
# JOB = {"op": "time", "frame": 96, "path": "/abs/x.png"}            — замер кадра (1 кадр на вызов!)
# JOB = {"op": "launch", "f0": 0, "f1": 179, "path": "/abs/dir/slug_", "alpha": False, "cam": None}
#   launch: асинхронный рендер в Picture Viewer (CallCommand 12099) — мост сразу свободен.
#   PV рендерит КОПИЮ сцены на момент запуска: правки после старта в прогон не попадут.
#   Остановить PV из скрипта нельзя (StopExternalRenderer через мост вешает C4D) — просить пользователя.
op = JOB["op"]
if op == "time":
    dt = time_frame(JOB["frame"], JOB["path"])
    print(json.dumps({"frame": JOB["frame"], "sec": round(dt or -1, 1)}))
elif op == "launch":
    rd = use_rs("RS_final")
    if JOB.get("cam"):
        activate(JOB["cam"])
    rd[c4d.RDATA_SAVEIMAGE] = True
    rd[c4d.RDATA_PATH] = JOB["path"]
    rd[c4d.RDATA_FORMAT] = c4d.FILTER_PNG
    if JOB.get("alpha"):
        rd[c4d.RDATA_ALPHACHANNEL] = True
        sa = getattr(c4d, "RDATA_STRAIGHTALPHA", None)
        if sa is not None:
            rd[sa] = True                  # straight: PNG по стандарту straight; PV показывает её «грязной» — норма
    rd[c4d.RDATA_FRAMESEQUENCE] = c4d.RDATA_FRAMESEQUENCE_MANUAL
    rd[c4d.RDATA_FRAMEFROM] = c4d.BaseTime(JOB["f0"], FPS)
    rd[c4d.RDATA_FRAMETO] = c4d.BaseTime(JOB["f1"], FPS)
    # сохранить сцену: прогон должен быть воспроизводим из файла
    sp = doc.GetDocumentPath() + "/" + doc.GetDocumentName() if doc.GetDocumentPath() else None
    saved = bool(sp) and c4d.documents.SaveDocument(doc, sp, c4d.SAVEDOCUMENTFLAGS_NONE, c4d.FORMAT_C4DEXPORT)
    doc.SetTime(c4d.BaseTime(JOB["f0"], FPS))
    c4d.EventAdd()
    c4d.CallCommand(12099)                 # Render to Picture Viewer — асинхронно
    print(json.dumps({"launched": True, "range": [JOB["f0"], JOB["f1"]], "path": JOB["path"],
                      "res": [int(rd[c4d.RDATA_XRES]), int(rd[c4d.RDATA_YRES])], "saved": saved}))
