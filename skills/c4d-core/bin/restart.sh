#!/usr/bin/env bash
# Перезапуск Cinema 4D с включённым exec_python и ожидание моста.
#   restart.sh [сцена.c4d] [--force]
# Без --force: если C4D отвечает — просит сохранить и закрыть руками (несохранённое пропадёт).
# --force — только когда C4D висит намертво (ping не отвечает, CPU ~0) или пользователь разрешил.
# Запускать в фоне не нужно: ждёт мост до 4 минут и печатает итог.
BIN="$(cd "$(dirname "$0")" && pwd)"
APP="${C4D_APP:-/Applications/Maxon Cinema 4D 2024/Cinema 4D.app}"   # другая версия: C4D_APP="/Applications/Maxon Cinema 4D 2026/Cinema 4D.app"
SCENE=""; FORCE=0
for a in "$@"; do
  case "$a" in --force) FORCE=1;; *) SCENE="$a";; esac
done

if pgrep -f "Cinema 4D.app/Contents/MacOS" >/dev/null; then
  if python3 "$BIN/run.py" --timeout 10 --code 'print("alive")' 2>/dev/null | grep -q alive && [ $FORCE -eq 0 ]; then
    echo "C4D жива и отвечает. Перезапуск потеряет несохранённое."
    echo "Сохрани сцену (или попроси пользователя) и повтори с --force."
    exit 2
  fi
  echo "закрываю C4D…"
  osascript -e 'tell application "Cinema 4D" to quit' >/dev/null 2>&1
  for i in $(seq 1 15); do pgrep -f "Cinema 4D.app/Contents/MacOS" >/dev/null || break; sleep 1; done
  pkill -f "Cinema 4D.app/Contents/MacOS"; sleep 2
  pkill -9 -f "Cinema 4D.app/Contents/MacOS" 2>/dev/null; sleep 1
fi

launchctl setenv C4D_MCP_ENABLE_EXEC_PYTHON 1
if [ -n "$SCENE" ]; then open -a "$APP" "$SCENE"; else open -a "$APP"; fi
echo "C4D запускается${SCENE:+ со сценой $(basename "$SCENE")}; жду мост…"
for i in $(seq 1 80); do
  if nc -z -G 2 127.0.0.1 "${C4D_MCP_PORT:-18710}" >/dev/null 2>&1; then
    sleep 3
    exec bash "$BIN/preflight.sh"
  fi
  sleep 3
done
echo "Мост не поднялся за 4 мин. Возможна модалка в C4D (лицензия, восстановление сцены) — попроси пользователя глянуть на экран."
exit 1
