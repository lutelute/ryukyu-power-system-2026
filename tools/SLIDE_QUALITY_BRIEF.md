# スライド品質の統一基準（第8回を見本にする）

対象: `コード/fig_chNN.py` と `スライド/chNN.md`
見本: `コード/fig_ch08.py` と `スライド/ch08.md`（この 2 つを先に読むこと）

## 背景 — 何が起きていたか

図は 9〜12 inch のキャンバスに 13〜14 pt で描かれていた。それを
`figure-story` のスライドに貼ると、図は本文領域の 58%（約 7.1 inch）まで縮む。
結果、図の中の文字が投影して読めない大きさになっていた。

これを次の 2 つで直した。すでに全回に適用済みなので、作り直す必要はない。

1. `コード/pws_common.py` の `savefig()` が、`コード/fig_scale.json`
   （`tools/fig-scale.py` が スライド/*.md から自動生成）を見て、
   **スライド上での図の箱に合わせてキャンバスを縮めてから保存する**。
   フォントの pt は変わらないので、スライド上での文字の見かけの大きさが 1:1 に揃う。
2. 縦横比 2.1 以上の横長の図は `figure-story` に収まらないので、
   `tools/widen-figs.py` が `figure-full` のスライドへ移した。
   このとき h2（読み方）と fs-conclusion はキャプションへ、
   fs-points は講師ノートへ移してある。

## あなたの仕事

キャンバスが縮んだぶん、**図の中の注記・凡例・ラベルが重なる**ようになった。
また figure-full へ移したスライドは、キャプションが機械的な連結のままになっている。
担当する回について、これを人が見て直す。

### 手順

```bash
BASE="…/講義資料_claude版"          # このファイルのある tools/ の親
cd "$BASE/コード" && /usr/bin/python3 fig_chNN.py      # 図を作り直す
cd "$BASE" && export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
bash tools/build-decks.sh chNN                         # PPTX を作る（error 0 が必須）
# PNG にして全ページを目で見る
soffice --headless --convert-to pdf --outdir /tmp/qNN "$BASE/スライド/chNN.pptx"
pdftoppm -png -r 100 /tmp/qNN/chNN.pdf /tmp/qNN/p
```
`/tmp/qNN/p-XX.png` を **Read ツールで 1 枚ずつ実際に見る**（4 枚ずつ 1 枚に
並べた接触シートを作ってもよい）。図単体は `図/chNN_*.png` を直接見る。

### 直すもの（優先度順）

0. **図の中の文字が小さすぎる** — 図はスライド上で「描いたときの pt のまま」表示される
   （savefig がキャンバスを縮めるため）。`fontsize=9` と書けば投影しても 9 pt にしかならず、
   後ろの席から読めない。11 pt を下限にする。

   ```bash
   python3 tools/lift-fontsize.py --check chNN   # 何箇所変わるか見る
   python3 tools/lift-fontsize.py chNN           # 11 pt 下限で +1.5 pt
   ```
   **底上げすると必ず新しい重なりが出る。** 図を作り直したあと、スライドのページだけでなく
   `図/chNN_*.png` を 1 枚ずつ Read で直接見て、下の 1. の要領で配置を直す。
   ch03 では底上げ後の見直しを飛ばしたため、注記が箱に食い込んだまま残っていた。

1. **図の中の重なり** — 凡例が曲線に重なる、注記が箱に食い込む、
   帯のラベル同士がぶつかる。
   - 凡例が邪魔なら消して、線の右端に直接ラベルを置く（`fig_ch08.py` の
     `fig_dfdp` が見本。`fig.subplots_adjust(right=0.70)` で場所を作る）
   - 2 枚のパネルに共通の凡例は図の上へ出す（`fig_compare`。
     `fig.legend(..., loc="upper center", bbox_to_anchor=(0.5, 1.0))`）
   - 帯や区間のラベルは軸の上端（データ範囲の外）に一列に並べ、`set_ylim` で場所を作る（`fig_stages`）
   - 注記は `transform=ax.transAxes` の座標で、空いている場所へ移す
2. **豆腐（□ になる文字）** — ヒラギノのボールドには下付き数字（₀ ₁ ₂）、
   上付きマイナス、≤ ≠ が無い。`f₀ → f_0`、`x₁ → x_1`、`≤ → 以下` に置き換える。
   図のテキストとスライドの本文の両方を確認する。
3. **図のタイトルとスライドの見出しの重複** — `ax.set_title(...)` が
   スライドの `# 見出し` と同じことを言っているなら、`set_title` を削る。
   スライド側にしか無い情報を持っているなら残す。
4. **figure-full へ移したスライドのキャプション** — 「読み方…　結論…」の
   機械的な連結になっている。1〜2 文の日本語として自然に書き直す。
   同じことを図の中にも書いてあるなら、キャプションからは落とす。
5. **たとえ話と「よくある誤解」のスライド** — 全15回とも cols-2 / zone-compare の
   文字だけで、投影すると余白だらけになる。`pws_eqfig.analogy_figure()` を使って
   figure-full の 1 枚図にする。

   ```python
   from pws_eqfig import analogy_figure
   analogy_figure("chNN_analogy.png",
       left_title="天秤（たとえ）", right_title="電力系統（実物）",
       pairs=[("左の皿に「発電」、右の皿に「消費」を載せる",
               "皿の重さの差＝需給アンバランス ΔP [MW]"), ...],   # 4〜5 組
       note="下に置く 1 文（任意）")
   ```
   誤解のほうは `left_title="× よくある誤解"`, `right_title="○ 正しい理解"` で **3 組**。
   日本語の折り返しは自動。見本は `fig_ch08.py` の `fig_analogy()` / `fig_myth()`。
   ヒラギノに `✓ ✗` は無いので `○ ×` を使う。

6. **文字だけのスライド** — `doctor` が `[info] text-only slide` と言う。
   title / divider / agenda / end / takeaway はそのままでよい。
   それ以外で中身が薄いページは、数値・事例・具体例を足すか、隣と統合する。

### 重なりを直すときの落とし穴

**figsize を広げて余白を作ろうとすると、逆に重なりが増える。**
`savefig()` はキャンバスをスライド上の箱に合わせて縮めるので、キャンバスを広げるほど
縮小率が上がり、**文字が図に対して相対的に大きくなる**。余白は増えない。
重なりは「既存の余白の中で配置し直す」ことでしか解けない。

ただし**縦は別**。縮小率が幅で決まっている図（`k = box_w / w` のとき）は、
figsize の**高さ**を足すと縦方向の余白が実際に増える。段が縦に詰まっている図は
高さを伸ばして間隔を取るのが効く（`fig_ch03.py` の `fig_per_unit` がその例）。

### やってはいけないこと

- `pws_common.py` / `pws_eqfig.py` / `tools/` を書き換えない（全回で共有している）
- 図の数値を手で書き換えない。数値は必ず計算結果から出す
- 図を小さくして重なりを避けない。**文字は大きいまま、配置で解く**
- `figsize` を広げて解決しようとしない（上記のとおり逆効果）
- `fig_scale.json` を手で編集しない（`.md` を変えたら `python3 tools/fig-scale.py` で作り直す）

### 完了条件

- `bash tools/build-decks.sh chNN` が `✓ chNN: NN slides, warn 0`
- 全ページを実際に見て、図の中に重なり・豆腐・見切れが無い
- 最後に「直した箇所」を箇条書きで報告する
