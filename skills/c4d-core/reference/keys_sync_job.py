# keys_sync_job.py — RS_keys ← RS_final (зовёт bin/keysheet.py; нужен renderladder.py).
# JOB = {"scale": 0.5, "mb": False}
size = sync_keys(JOB.get("scale", 0.5), JOB.get("mb", False))
f = _rs_find("RS_final")
eng = {v: k for k, v in ENG.items()}.get(f[c4d.RDATA_RENDERENGINE], str(f[c4d.RDATA_RENDERENGINE])) if f else None
print(json.dumps({"size": list(size) if size else None, "engine": eng}))
