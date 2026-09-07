#!/bin/bash
# tools/build-decks.sh — スライド/chNN.md → スライド/chNN.pptx（terracotta）。doctor で error があれば失敗にする
#   bash tools/build-decks.sh            # 全部
#   bash tools/build-decks.sh ch08       # 1 回分
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH
BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE/スライド" || exit 1
fail=0
for md in ${1:+$1.md} ${1:-ch*.md}; do
  [ -f "$md" ] || continue
  name="${md%.md}"
  out=$(marp-pptx convert "$md" -o "$name.pptx" -p terracotta 2>&1) || { echo "✗ $name: convert 失敗"; echo "$out" | tail -3; fail=1; continue; }
  n=$(echo "$out" | grep -o '[0-9]* slides' | head -1)
  doc=$(marp-pptx doctor "$name.pptx" 2>&1)   # keynote 密度で作った実物を測る
  errs=$(echo "$doc" | grep -c '^\[error\]'); warns=$(echo "$doc" | grep -c '^\[warn\]')
  if [ "$errs" -gt 0 ]; then echo "✗ $name: $n, error $errs"; echo "$doc" | grep -A1 '^\[error\]' | head -12; fail=1
  else echo "✓ $name: $n, warn $warns"; [ "$warns" -gt 0 ] && echo "$doc" | grep -A1 '^\[warn\]' | head -8; fi
done
exit $fail
