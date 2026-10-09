#!/usr/bin/env bash
# Проверка связи Claude ↔ Cinema 4D (мост cinema4d_mcp_bridge, 127.0.0.1:18710).
# Печатает строки KEY: value и FIX: что делать. Код выхода 0 — можно работать.
BIN="$(cd "$(dirname "$0")" && pwd)"
PORT="${C4D_MCP_PORT:-18710}"
ok=0

if pgrep -f "Cinema 4D.app/Contents/MacOS" >/dev/null 2>&1; then
  echo "C4D_APP: running"
else
  echo "C4D_APP: not running"
  echo "FIX: bash $BIN/restart.sh [сцена.c4d]  (запустит C4D с включённым exec_python)"
  ok=1
fi

ENVV="$(launchctl getenv C4D_MCP_ENABLE_EXEC_PYTHON)"
echo "LAUNCHCTL_EXEC_PYTHON: ${ENVV:-unset}"
[ "$ENVV" = "1" ] || echo "FIX: после перезагрузки мака переменная слетает — restart.sh выставит её сам"

if [ $ok -eq 0 ]; then
  if nc -z -G 2 127.0.0.1 "$PORT" >/dev/null 2>&1; then
    echo "C4D_BRIDGE: up (127.0.0.1:$PORT)"
    out="$(python3 "$BIN/run.py" --timeout 15 --code 'print("EXEC_OK", doc.GetDocumentName(), doc.GetFps(), c4d.GetC4DVersion())' 2>&1)"
    case "$out" in
      *EXEC_OK*) echo "EXEC_PYTHON: on — $(echo "$out" | grep EXEC_OK | sed 's/EXEC_OK //')";;
      *TIMEOUT*|*timed\ out*) echo "EXEC_PYTHON: мост занят (идёт долгая операция или модальное окно в C4D)"
                              echo "FIX: python3 $BIN/run.py --wait 300; не ответил — C4D висит → restart.sh (с согласия пользователя)"; ok=1;;
      *) echo "EXEC_PYTHON: off/error — $(echo "$out" | head -2 | tr '\n' ' ')"
         echo "FIX: bash $BIN/restart.sh (C4D закроется — сначала сохранить сцену)"; ok=1;;
    esac
  else
    echo "C4D_BRIDGE: down (C4D запущена, порт $PORT закрыт)"
    echo "FIX: C4D ещё грузится — подожди 30 с; после суток работы порт закрывается сам → restart.sh"
    ok=1
  fi
fi

PROJ="${C4D_PROJECTS:-$HOME/c4d-projects}"
echo "PROJECTS: $(ls -1t "$PROJ" 2>/dev/null | tr '\n' ' ')"
exit $ok
