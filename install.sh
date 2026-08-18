#!/bin/bash
# Устанавливает C4D-скиллы в ~/.claude/skills (симлинками на этот репозиторий).
# Повторный запуск безопасен: обновляет ссылки. Существующие папки (не симлинки)
# бэкапит в <name>.bak, чтобы ничего не потерять.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/.claude/skills"
mkdir -p "$TARGET"

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
echo "Готово. Скиллы доступны как /c4d-plan, /c4d-layout, /c4d-animator, /c4d-look, /c4d-asset."
echo "Обновление в будущем: git pull в $REPO_DIR (симлинки подхватят изменения сами)."
