#!/bin/bash
# tools/make-dist.sh — 学生配布用 zip を作る（試験問題・解答、作業用ファイルは含めない）
#   bash tools/make-dist.sh            → ../講義資料_配布用_YYYYMMDD.zip
# 配布物は index.html をダブルクリックするだけで動く（file:// で完結。サーバー不要）。
set -e
BASE="$(cd "$(dirname "$0")/.." && pwd)"
NAME="電力エネルギーシステム解析_講義資料_$(date +%Y%m%d)"
STAGE="$(mktemp -d)/$NAME"
mkdir -p "$STAGE"
# 含める: index / notes / viz / ex / ノート(原稿) / コード / 図 / README / 記号表 / 教科書対応
for d in index.html notes viz ex スライド ノート コード 図 README.md 記号表.md 教科書対応.md; do
  [ -e "$BASE/$d" ] && cp -R "$BASE/$d" "$STAGE/"
done
# 除外: 試験/（問題・解答）, tools/, .claude/, .playwright-mcp, __pycache__, .DS_Store
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -name '.DS_Store' -delete 2>/dev/null || true
cat > "$STAGE/はじめに.txt" <<'TXT'
電力エネルギーシステム解析の基礎と応用（ 集中講義）配布資料

開き方
  1. この zip を展開する（展開せずに中を開くと動きません）
  2. index.html をダブルクリック（Chrome / Edge / Safari / Firefox いずれでも可）
  3. 各回は「📖 ノート」「🖥 動く図」「✍ 演習」の 3 つ。上から順に進む

メモ
  - インターネット接続は不要です。すべてブラウザの中で計算します
  - 演習の採点結果は、この PC のブラウザにだけ保存されます（他人には見えません）
  - ノートの原稿（Markdown）は ノート/、Python コードは コード/ にあります
TXT
OUT="$BASE/../$NAME.zip"
rm -f "$OUT"
(cd "$(dirname "$STAGE")" && zip -qr "$OUT" "$NAME" -x '*.DS_Store')
rm -rf "$(dirname "$STAGE")"
echo "作成: $OUT ($(du -h "$OUT" | cut -f1))"
