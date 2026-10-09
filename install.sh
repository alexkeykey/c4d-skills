#!/bin/bash
# Устанавливает C4D-скиллы в ~/.claude/skills (симлинками на этот репозиторий).
# Повторный запуск безопасен: обновляет ссылки. Существующие папки (не симлинки)
# бэкапит в <name>.bak, чтобы ничего не потерять.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills"
mkdir -p "$TARGET"

# убрать ссылки на скиллы, которых в репо больше нет (c4d-layout/animator/look/asset → /c4d)
for l in "$TARGET"/*; do
  if [ -L "$l" ]; then
    t="$(readlink "$l")"
    case "$t" in "$REPO_DIR"/*) [ -e "$t" ] || { rm "$l"; echo "✗ убрана устаревшая ссылка $(basename "$l")"; };; esac
  fi
done

for src in "$REPO_DIR"/skills/*/; do
  name="$(basename "$src")"
  dst="$TARGET/$name"
  if [ -L "$dst" ]; then
    rm "$dst"
  elif [ -d "$dst" ]; then
    echo "⚠️  $dst существует как обычная папка — переношу в $name.bak"
    rm -rf "$dst.bak"
    mv "$dst" "$dst.bak"
  fi
  ln -s "${src%/}" "$dst"
  echo "✓ $name → $dst"
done

echo
echo "Готово. Скиллы: /c4d-plan (план), /c4d (исполнитель с режимами), c4d-core (база)."
echo "Обновление в будущем: git pull в $REPO_DIR (симлинки подхватят изменения сами)."
