#!/usr/bin/env bash
# Проверка моста Claude ↔ Cinema 4D. Запускать перед любой работой со сценой.
PORT="${C4D_MCP_PORT:-5555}"

if pgrep -f "Cinema 4D.app" >/dev/null 2>&1; then
  echo "C4D_APP: running"
else
  echo "C4D_APP: not running"
  echo "FIX: запусти Cinema 4D"
fi

if nc -z -G 2 127.0.0.1 "$PORT" >/dev/null 2>&1; then
  echo "C4D_BRIDGE: up (127.0.0.1:$PORT)"
else
  echo "C4D_BRIDGE: down"
  echo "FIX: в Cinema 4D — меню Extensions → Socket Server Plugin → Start Server"
fi

PROJ="${C4D_PROJECTS:-$HOME/c4d-projects}"
if [ -d "$PROJ" ]; then
  echo "PROJECTS: $(ls -1 "$PROJ" 2>/dev/null | tr '\n' ' ')"
else
  echo "PROJECTS: (нет ещё ни одного)"
fi
