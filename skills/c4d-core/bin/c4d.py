#!/usr/bin/env python3
"""Тонкий CLI-клиент к мосту Cinema 4D (cinema4d_mcp_bridge).

Использование:
    c4d.py <command> ['{json params}' | @params.json] [--out FILE] [--raw]

Примеры:
    c4d.py ping
    c4d.py get_document_state
    c4d.py preview_render '{"width": 800, "height": 450}'
    c4d.py get_mesh '{"entity": "/Cube"}' --out /tmp/mesh.json

Поведение:
  - Протокол: TCP, одна JSON-строка запроса + "\n", одна JSON-строка ответа.
  - Любое строковое поле *_base64 в результате декодируется в файл
    (PNG/бинарь) рядом в IMG_DIR, а в выводе заменяется на путь — чтобы
    мегабайты base64 не попадали в контекст агента.
  - --out FILE: полный result пишется в файл, на stdout — краткая сводка.
  - status=error → сообщение в stderr, exit 1.

Env: C4D_MCP_HOST (127.0.0.1), C4D_MCP_PORT (18710), C4D_MCP_TOKEN (нет),
     C4D_MCP_TIMEOUT (600 сек — рендер может быть долгим), C4D_MCP_IMG_DIR.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import sys
import time

HOST = os.environ.get("C4D_MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("C4D_MCP_PORT", "18710"))
TOKEN = os.environ.get("C4D_MCP_TOKEN", "").strip()
TIMEOUT = float(os.environ.get("C4D_MCP_TIMEOUT", "600"))
IMG_DIR = os.environ.get("C4D_MCP_IMG_DIR") or os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "c4d-mcp-images"
)

# Выше этого порога строка *_base64 всегда уходит в файл, не в stdout.
_B64_INLINE_LIMIT = 256


def _fail(msg: str) -> "NoReturn":  # noqa: F821 - py3.9-совместимый хинт не нужен
    print(f"c4d: {msg}", file=sys.stderr)
    sys.exit(1)


def _call(command: str, params: dict) -> dict:
    req = {"id": f"cli-{int(time.time() * 1000)}", "command": command, "params": params}
    if TOKEN:
        req["token"] = TOKEN
    try:
        s = socket.create_connection((HOST, PORT), timeout=10)
    except OSError as exc:
        _fail(
            f"мост C4D недоступен на {HOST}:{PORT} ({exc}). "
            f"Cinema 4D запущена? Плагин cinema4d_mcp_bridge загружен?"
        )
    s.settimeout(TIMEOUT)
    try:
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            try:
                chunk = s.recv(1 << 20)
            except socket.timeout:
                _fail(f"таймаут {TIMEOUT:.0f}с в ожидании ответа на '{command}'")
            if not chunk:
                _fail("мост закрыл соединение, не прислав ответ")
            buf += chunk
    finally:
        s.close()
    line = buf.split(b"\n", 1)[0]
    try:
        return json.loads(line.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        _fail(f"не смог разобрать ответ моста: {exc}")


def _extract_base64(node, stem: str):
    """Рекурсивно заменяет длинные строки *_base64 на записанные файлы."""
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if (
                isinstance(k, str)
                and k.endswith("_base64")
                and isinstance(v, str)
                and len(v) > _B64_INLINE_LIMIT
            ):
                os.makedirs(IMG_DIR, exist_ok=True)
                raw = base64.b64decode(v)
                ext = ".png" if raw[:8] == b"\x89PNG\r\n\x1a\n" else ".bin"
                path = os.path.join(
                    IMG_DIR, f"{stem}-{int(time.time() * 1000)}-{k[:-7]}{ext}"
                )
                with open(path, "wb") as fh:
                    fh.write(raw)
                out[k[:-7] + "_file"] = path
                out[k[:-7] + "_bytes"] = len(raw)
            else:
                out[k] = _extract_base64(v, stem)
        return out
    if isinstance(node, list):
        return [_extract_base64(v, stem) for v in node]
    return node


def _summary(value, depth=0):
    """Однострочная сводка формы результата для --out."""
    if isinstance(value, dict):
        parts = []
        for k, v in list(value.items())[:12]:
            if isinstance(v, list):
                parts.append(f"{k}[{len(v)}]")
            elif isinstance(v, dict):
                parts.append(f"{k}{{{len(v)}}}")
            elif isinstance(v, str) and len(v) > 40:
                parts.append(f"{k}=str({len(v)})")
            else:
                parts.append(f"{k}={v!r}")
        more = "" if len(value) <= 12 else f" …+{len(value) - 12}"
        return "{" + ", ".join(parts) + more + "}"
    if isinstance(value, list):
        return f"[{len(value)} items]"
    return repr(value)


def main(argv: list[str]) -> int:
    args = [a for a in argv]
    raw_mode = "--raw" in args
    if raw_mode:
        args.remove("--raw")
    out_path = None
    if "--out" in args:
        i = args.index("--out")
        try:
            out_path = args[i + 1]
        except IndexError:
            _fail("--out требует путь к файлу")
        del args[i : i + 2]

    if not args:
        _fail("использование: c4d.py <command> ['{json}' | @file] [--out FILE] [--raw]")
    command = args[0]
    params: dict = {}
    if len(args) > 1:
        blob = args[1]
        if blob.startswith("@"):
            with open(blob[1:], "r", encoding="utf-8") as fh:
                blob = fh.read()
        try:
            params = json.loads(blob)
        except json.JSONDecodeError as exc:
            _fail(f"params — не валидный JSON: {exc}")
        if not isinstance(params, dict):
            _fail("params должен быть JSON-объектом")

    resp = _call(command, params)
    status = resp.get("status")
    if status != "ok":
        err = resp.get("error", "<нет текста ошибки>")
        print(f"c4d: {command} → error: {err}", file=sys.stderr)
        return 1

    result = resp.get("result")
    if not raw_mode:
        result = _extract_base64(result, command)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=1)
        print(f"ok → {out_path} ({os.path.getsize(out_path)} bytes)")
        print(_summary(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
