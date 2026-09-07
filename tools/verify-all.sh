#!/bin/bash
# tools/verify-all.sh — 図からスライド・ノート・演習まで作り直して全部検証する
#   bash tools/verify-all.sh          # 図の再生成から全部
#   bash tools/verify-all.sh --quick  # 図の再生成を飛ばす
export PATH=/opt/homebrew/bin:$HOME/.local/bin:$PATH
BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE" || exit 1
PY=/usr/bin/python3
fail=0
line() { printf '\n\033[1m%s\033[0m\n' "── $1 ─────────────────────────────"; }

if [ "$1" != "--quick" ]; then
  line "1. 図を作り直す"
  $PY tools/fig-scale.py || fail=1
  cd コード || exit 1
  for f in fig_ch*.py; do
    if out=$($PY "$f" 2>&1); then
      n=$(echo "$out" | grep -c '\[図を保存\]')
      w=$(echo "$out" | grep -ci 'Glyph .* missing')       # 豆腐になる文字
      if [ "$w" -gt 0 ]; then
        echo "△ $f: $n 枚（フォントに無い文字が $w 件）"
        echo "$out" | grep -i 'Glyph .* missing' | sed 's/^/    /' | sort -u | head -3
        fail=1
      else
        echo "✓ $f: $n 枚"
      fi
    else
      echo "✗ $f: 失敗"; echo "$out" | tail -3; fail=1
    fi
  done
  cd "$BASE" || exit 1
else
  $PY tools/fig-scale.py || fail=1
fi

line "2. 図の参照切れ"
$PY - <<'PYEOF' || fail=1
import re, glob, os, sys
miss = [(md, img) for md in sorted(glob.glob("スライド/ch*.md")) + sorted(glob.glob("ノート/*.md"))
        for img in re.findall(r"!\[[^\]]*\]\(\.\./図/([^)]+)\)", open(md, encoding="utf-8").read())
        if not os.path.exists(os.path.join("図", img))]
print(f"✓ 参照切れなし（図 {len(glob.glob('図/*.png'))} 枚）" if not miss else "✗ 参照切れ:")
for m in miss[:10]:
    print("   ", m)
sys.exit(1 if miss else 0)
PYEOF

line "3. 図の中の文字の大きさ / キャプションの書き残し"
$PY tools/lift-fontsize.py --check
$PY - <<'PYEOF2'
import glob, os
tot = 0
for md in sorted(glob.glob("スライド/ch*.md")):
    n = sum(1 for l in open(md, encoding="utf-8")
            if 'class="caption"' in l and "\u3000" in l)
    if n:
        print(f"  {os.path.basename(md)}: {n} 件")
        tot += n
print(f"{'△' if tot else '✓'} 機械的に連結されたままのキャプション {tot} 件"
      + ("（figure-full へ移したときの自動生成。日本語として書き直す）" if tot else ""))
PYEOF2

line "4. スライド（PPTX）"
bash tools/build-decks.sh || fail=1

line "5. ノート（HTML・KaTeX）"
node tools/build-notes.mjs 2>&1 | tail -3 || fail=1

line "6. ページの検査"
node tools/check-pages.mjs 2>&1 | tail -5 || fail=1

line "7. 演習"
node tools/test-ex.mjs 2>&1 | tail -5 || fail=1

line "結果"
[ $fail -eq 0 ] && echo "✓ すべて通った" || echo "✗ 直すところが残っている"
exit $fail
