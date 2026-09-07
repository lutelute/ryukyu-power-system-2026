# 回別スライド作り直し — 作業仕様書（サブエージェント用）

目標: 各回を **教科書並みの丁寧さ** に引き上げる。文字だけのスライドを、実計算の図・段階開示の導出・図つき例題で作り直す。
見本は **第1回**（`コード/fig_ch01.py`、`スライド/ch01.md`、`スライド/ch01.figs.json`）。構造・密度・文体をそのまま踏襲する。

## 0. 先に読むもの（順番どおり）
1. `スライド/ch01.md` — 36 枚の骨格。型の使い方、`<!-- build -->` の導出、figure-story の書き方、講師ノート `<!-- note: -->` の書き方
2. `コード/fig_ch01.py` — 図の作り方。先頭のスタイル定数（C_MAIN 等、rcParams）をそのまま使う。`pws_common.setup_japanese_font / savefig` を使う
3. `スライド/ch01.figs.json` と `tools/place-figs.mjs` — ノートに図を置く仕組み
4. 担当回のノート `ノート/chNN_*.md`（全文）と動く図 `viz/<slug>.html` の先頭〜定数定義（数値感を合わせる）
5. `/Users/shigenoburyuto/.claude/skills/marp-pptx/SKILL.md` の「文字数の目安」「デザイン原則」、`references/type-skeletons.md` の figure-story / sections / steps / graphical-abstract / blocks / table-slide

## 1. 成果物（担当回 chNN について）
- `コード/fig_chNN.py` → `図/chNN_*.png` を **8〜10 枚**。すべて実計算（数式・シミュレーション）から描く。手描き風の模式図（回路図・系統図・フロー）は matplotlib の patches で描いてよい
- `スライド/chNN.md` を全面書き換え（30〜36 枚）。**骨格は ch01 と同じ**:
  title → statement（一言）→ graphical-abstract（問い・課題（図）・道具（図）・到達点 KPI）→ sections 事例 2 件 → cols-2 たとえ話 → agenda →
  Ⅰ〜Ⅳ の各章: divider → figure-story（1〜3 枚）→ sections `<!-- build -->` の導出（少なくとも 2 章に 1 つ）→ steps の例題（数値）→ kpi →
  figure（`図/chNN_viz.png`、動く図で試すこと 3 つ）→ blocks（なぜそう考えるか 3 つ、最後は alert）→ zone-compare（誤解）→ takeaway → end
  - 既存の `スライド/chNN.md` にある **事例・たとえ話・なぜそう考えるか・誤解・持ち帰る 3 点** は活かしてよい（内容が薄ければ深める）
  - **全内容スライドに講師ノート** `<!-- note: … -->`（何を強調するか、学生に何を計算させるか、よくある質問）
- `スライド/chNN.figs.json`（各図をノートのどの節に置くか。`after` はノートの実在する見出し行の先頭文字列）
- 実行して確認: 
  1. `cd コード && /usr/bin/python3 fig_chNN.py`（警告以外のエラー 0。図の数値を print して、スライドの数値はその出力から取る）
  2. `bash tools/build-decks.sh chNN` → `✓ … warn 0` になるまで直す（error は溢れ。文字を削る／分割する）
  3. `node tools/place-figs.mjs chNN` → 全図が配置されること
  4. `node tools/sync-intuition.mjs chNN` → `node tools/build-notes.mjs --only chNN` → KaTeX エラー 0
  5. PNG で目視: `mkdir -p /tmp/deckNN && cd /tmp/deckNN && /opt/homebrew/bin/soffice --headless --convert-to pdf "<絶対パス>/スライド/chNN.pptx" --outdir /tmp/deckNN && /opt/homebrew/bin/pdftoppm -png -r 55 chNN.pdf s` → 少なくとも graphical-abstract・figure-story 3 枚・build の最終枚・steps を Read で見て、ラベル重なり・図の潰れ・はみ出しを直す（図側は fig_chNN.py を直して再生成）

## 2. 守ること（過去に失敗した点）
- marp: H1 は 25 字以内。`df-term`（定義の見出し行）は折り返さないので短く。KPI 値は 6 字以内。数式に `\text{日本語}` や `\%` を入れない（記号だけにし説明は eq-desc へ）。画像は `![w:600](../図/chNN_xxx.png)`（w は 520〜700）。figure-story は `## 読み方｜…` と `<div class="fs-points">`（4 行、各 24 字以内）と `<div class="fs-conclusion">` を必ず持つ。`<!-- build -->` は sections にだけ
- 図: 日本語フォントは setup_japanese_font()。タイトルは 1 行（figsize 幅 8〜10 in、フォント 11 pt 前後）。凡例は frameon=False。ラベルの重なりを PNG で確認して offset を調整。色は C_MAIN/C_SEC/C_ACC/C_WARM/C_BLUE/C_GREY/C_LIGHT のみ
- 数値: **スライドに書く数値は fig_chNN.py が print した値**か、ノートに既にある値。実世界の事例の数字は「約」を付け、確信のない数値は書かない。出典 URL や架空の引用を書かない
- 用語・記号は `記号表.md` と教科書（加藤・田岡）に合わせる（同期化力 K_s、慣性 H と M=2H/ω0、%K は %MW/0.1Hz、発電余剰を正、ΔP_T は A→B 正）
- 触らないもの: 他の回のファイル、`ex/`、`viz/`、`index.html`、`tools/`、`README.md`、`講義資料_codex版/`。ノートは place-figs / sync-intuition 経由でだけ変わる（本文を手で直す必要があれば、既存の文を消さず追記のみ）
- サブエージェントをさらに起動しない。`node tools/build-notes.mjs`（引数なしの全体ビルド）と `build-decks.sh`（引数なし）は実行しない

## 3. 回別の仕様（図・導出・例題）

### ch02 電力システムの構成（viz/grid.html）
図: ①系統の階層図（発電 10〜25 kV → 昇圧 275〜500 kV → 送電 → 一次変電 154/66 kV → 配電 6.6 kV → 100/200 V、箱と矢印）②損失率 vs 電圧（P=100 MW, 100 km, R=0.1 Ω/km, 力率 0.9。66/154/275/500 kV に印）③損失 vs 力率（1/cos²φ）④単線結線図の例（3 母線: 母線＝太線、遮断器＝□、変圧器＝◎、線路）⑤並列 2 回線の分流（インピーダンス逆比、数値例）⑥沖縄本島の簡略系統図（`pws_common.OKINAWA_BUSES/LINES/LOADS` を描く）⑦供給予備率と N-1（需要・供給力・最大機脱落後の棒）⑧放射状 vs ループの停電範囲（模式図）
導出（build）: (a) I = P/(√3 V cosφ) → P_loss = 3I²R = RP²/(V² cos²φ)、(b) 並列線路の分流 I₁/I₂ = Z₂/Z₁ と、1 本開放後に残りが全電流を負う
例題: 66/275/500 kV の損失（28.3 / 1.63 / 0.49 MW）、275→66 kV 変圧器の巻数比と電流、需要 1,500 MW・供給力 1,650 MW・最大機 250 MW の N-1 予備率
### ch03 基本量と等価回路（viz/acpower.html）
図: ①瞬時電力 p(t) = P(1 − cos2ωt) − Q sin2ωt の分解（力率 0.8）②電力三角形 S, P, Q, φ ③力率改善のベクトル図（Q_C）④π 型等価回路（R, X, B/2 の回路図）⑤P–δ 曲線と Q–V 曲線（V_s=V_r=1, X=0.3）⑥単位法：変圧器両側で Z_pu が同じになる図 ⑦損失 vs 力率 ⑧フェランチ効果：無負荷の V_r/V_s = 1/cos(βl)、β=√(xb)、x=0.4 Ω/km, b=3 µS/km、0〜400 km
導出（build）: (a) v(t)i(t) の積から S = VI* = P + jQ、(b) 2 母線の送電電力式 P = V_sV_r sinδ/X, Q_r = (V_sV_r cosδ − V_r²)/X
例題: 80 MW・力率 0.8→1.0 の Q_C = 60 Mvar、Z_pu = 10 Ω × 100 MVA / 66 kV² = 0.230、δ=15° の P と P_max
### ch04 潮流計算の理論(1)（viz/ybus.html）
図: ①3 母線系統図と Y_bus の数値（x12=0.2, x13=0.25, x23=0.1 → 行列を図中に）②線路 1 本追加で 4 か所更新の図 ③IEEE 14 母線と 118 母線の Y_bus の spy 図（`pandapower.networks.case14/case118`、`pp.runpp` 後の `net._ppc['internal']['Ybus']` か自前で組む。密度 % をタイトルに）④母線種別の表図（既知・未知）⑤直流法潮流の 3 母線例（角度と線路潮流を図上に）⑥P_i の非線形性（V₁V₂ と sinθ）⑦未知数の数 vs 母線数 ⑧case14 で交流法 vs 直流法の線路潮流の散布（pp.runpp と pp.rundcpp）
導出（build）: (a) KCL → I = Y_bus V → S_i = V_i I_i* → P_i, Q_i の式、(b) 直流法の 3 近似で P = B'θ
例題: 3 母線 Y_bus、12 母線（PV 3, PQ 8）の未知数 19、直流法 3 母線の θ と潮流
### ch05 潮流計算の理論(2)（viz/newton.html）
図: ①1 変数 NR の接線の図（f(θ)=5 sinθ − 0.8、θ₀=0 → 0.160 → 0.16069）②GS vs NR のミスマッチ履歴（片対数。`pws_common.newton_raphson` と自前 GS で同じ系統）③ヤコビアンの H N M L ブロック（case14 のヒートマップ）④‖N‖,‖M‖/‖H‖,‖L‖ vs X/R ⑤高速デカップル法のフロー ⑥収束判定閾値と反復回数 ⑦PV 母線の Q 限界（Q–V 曲線で上限に当たる）⑧初期値の良し悪しと収束
導出（build）: (a) テイラー展開 → J Δx = −f → 2 次収束、(b) H, N, M, L の要素（対角は P_i, Q_i で書ける）
例題: 1 変数の 2 反復、GS 29 回 vs NR 4 回、B′ の要素
### ch06 潮流計算の実践（viz/voltage.html）
図: ①4 母線系統の電圧プロファイル（pandapower）②PV カーブ（2 母線、鼻先 P_max=V²/2X と pandapower の負荷増加で収束しなくなる点）③電圧感度 ΔV/ΔQ vs 短絡容量 ④太陽光導入量 vs 末端電圧（力率 1 と 0.95、`pws_common.build_okinawa(pv_mw, pv_pf)`）⑤ΔV ≈ (RP+XQ)/V の近似と厳密解 ⑥LTC タップと電圧 ⑦case14 の線路 loading の棒 ⑧pandapower のデータ構造図（bus/line/load/gen の表の絵）
導出（build）: (a) ΔV ≈ (RP + XQ)/V、(b) PV カーブの鼻先 P_max = V_s²/2X（力率 1、R=0）
例題: R=0.1, X=0.3 で 0.90 / 1.04 / 1.00 p.u.、P_max、感度 ρ
### ch07 電力系統の安定度（viz/swing.html）
図: ①発電機–無限大母線の系統図（E′, X, V）②P–δ 曲線と等面積 A₁/A₂（P_m=0.8, P_max=2.0, δ_cr=89.4°）③δ(t) の RK4 積分 t_c=240 ms（振れ戻り）vs 260 ms（脱調）④t_cr vs H（√H）⑤事故前・事故中・事故後の 3 本の P–δ 曲線（1 回線開放）⑥安定度 3 分類の時間スケール（対数）⑦H の典型値（火力・水力・原子力・インバータ）⑧除去時間 sweep → 最大相差角
導出（build）: (a) Jθ̈ = T_m − T_e → (2H/ω₀)δ̈ = P_m − P_e、(b) 等面積 A₁=A₂ → cos δ_cr の式 → t_cr = √(4H(δ_cr−δ₀)/(ω₀P_m))
例題: δ₀=23.6°, δ_cr=89.4°, t_cr=247 ms（H=4）、H=2 で 175 ms、1 回線開放
### ch08 受給バランスと周波数制御（viz/freq.html）
図: ①周波数応答の時間波形 沖縄（1,500 MW, H 4.5, K 150）vs 九州（16,000 MW）250 MW 脱落（慣性→ガバナ（ε=5%）→LFC（PI））②速度調定率の直線（F–P 図）③発電特性と負荷特性の交点＝系統定数 ④ΔF vs 脱落量（K 別）⑤RoCoF vs H ⑥連系 2 系統の模式図と ΔP_T ⑦制御の階層と時間分担（慣性・ガバナ・LFC・ELD）⑧LFC ゲイン α 大小の応答（教科書 例題7.3）
導出（build）: (a) ΔP = (K_G + K_L)ΔF = KΔF、(b) 連系系統 ΔP_A = K_AΔF + ΔP_T, ΔP_B = K_BΔF − ΔP_T → ΔF と ΔP_T
例題: 沖縄 −1.67 Hz / 九州 −0.16 Hz、連系（300+500 MW, 50 MW 負荷増）、AR
### ch09 インバータと系統連系（viz/inverter.html）
図: ①PWM 波形（変調波・搬送波・パルス、m=0.9, m_f=21）②DFT スペクトル m_f=21 vs 99 と THD ③基本波振幅 vs m（線形領域と過変調）④dq 変換のベクトル図（abc → αβ → dq）⑤Volt-Var の折れ線 ⑥合成慣性あり/なしの周波数応答（第8回のモデルに ΔP = −2H_v S/f₀·df/dt を追加）⑦フォロイング（電流源）とフォーミング（電圧源）の等価回路 ⑧LCL フィルタの周波数特性
導出（build）: (a) 正弦波 PWM の基本波 V̂₁ = mV_dc/2 と線間実効値 0.612 m V_dc、(b) 合成慣性の式
例題: 600 V・m=0.9 → 270 V / 330 V、THD、合成慣性の必要出力
### ch10 気象予測と再エネ出力（viz/weather.html）
図: ①那覇の晴天日射の日変化（夏至・冬至、`pws_common.solar_position / clear_sky_ghi`）②PV 出力 vs 日射（気温 20 / 35 °C の温度補正）③セル温度 vs 日射 ④べき法則の風速プロファイル（α=0.14, 0.3）⑤パワーカーブとワイブル風速分布（k=2, c=7 m/s）→ 期待出力と設備利用率 ⑥MAPE が夜間に発散する図と nRMSE ⑦平滑化 σ_N/σ₁ vs N（ρ 別）⑧NWP の格子（GSM 20 km / MSM 5 km / LFM 2 km を重ねた模式図）
導出（build）: (a) セル温度 NOCT 式と温度補正、(b) 平滑化 σ_N = σ₁√((1+(N−1)ρ)/N)
例題: 2 MW・G=800・32 °C → 1.26 MW、10 m 6 m/s → 80 m 8.0 m/s → 出力 2.4 倍、平滑化
### ch11 電力需要予測（統計）（viz/demand.html）
図: ①1 年分の需要（`pws_common.make_okinawa_demand`）と成分分解（トレンド・年・週・日）②需要 vs 気温の散布と V 字（度日）③THI vs 需要 ④重回帰の当てはめ（1 週間の実績と予測）⑤残差分布と MAE/RMSE ⑥前週同曜日 vs 重回帰の RMSE 棒 ⑦ランダム分割 vs 時系列分割の検証誤差（リークで過大評価）⑧自己相関（24 h・168 h のピーク）
導出（build）: (a) 最小二乗の正規方程式 β = (XᵀX)⁻¹Xᵀy、(b) 度日で V 字を 2 直線に
例題: 5 点の MAE 24 / RMSE 28.3 / MAPE 2.4%、度日、重回帰の予測値と Skill Score
### ch12 機械学習による予測（viz/ml.html）
図: ①決定木の 1 分割（気温で分ける）②ブースティングの逐次当てはめ（木 1, 5, 20, 80 本）③学習/検証誤差 vs 木の本数（早期停止）④線形 vs 木（交互作用データ）⑤外挿の失敗（学習範囲外で木が平ら）⑥リーク特徴量の検証/運用の逆転 ⑦分位点回帰の 5–95% 区間と PICP ⑧LSTM セルのゲート図 ⑨permutation importance の棒（自前計算。sklearn は使わず numpy で決定木・ブースティングを実装）
導出（build）: (a) F_m = F_{m−1} + ν h_m と残差、(b) 分位点損失（Pinball）
例題: 1 ステップで SSE 12,000 → 5,745、PICP/PINAW、外れ値 1 点の RMSE
### ch13 AI による系統解析（viz/ai.html）
図: ①case14 のグラフ描画（座標は手置きか簡易ばねモデルを numpy で）②GNN の集約 1 層・2 層の伝播（4 母線の直線グラフで数値）③状態推定 WLS（2 測定・1 変数の図）④PCA 再構成誤差の分布（正常 vs 線路故障、`pws_common` の直流潮流で生成）⑤Q 学習の学習曲線（逸脱率 vs エピソード。viz/ai.html の環境を Python で再現）⑥PINN の損失構成図 ⑦オートエンコーダの構造図 ⑧AI スクリーニング → 厳密計算の 2 段フロー
導出（build）: (a) WLS の正規方程式（HᵀR⁻¹H）Δx = HᵀR⁻¹(z − h(x))、(b) Q 学習の更新式
例題: GNN 4 母線の手計算、PCA 再構成誤差、Q 更新 1 ステップ
### ch14 AI による系統最適化（viz/opf.html）
図: ①2 台の費用曲線と限界費用 ②等 λ の図（λ の水平線と各機の交点、λ=16.7）③均等 vs 最適の費用差 ④メリットオーダーの階段と需要線 ⑤炭素価格 vs 石炭/LNG の費用（交点 ≈ 4,500 円/t）⑥2 ノード LMP（混雑なし/あり）⑦EMS のフロー ⑧3 母線 DC-OPF（`scipy.optimize.linprog`、線路容量で混雑 → LMP）
導出（build）: (a) ラグランジュ → dC_i/dP_i = λ、(b) LMP = λ + 混雑成分
例題: 2 台 400 MW（P₁=166.7, λ=16.7, 年 2.9 億円）、メリットオーダー、2 ノード LMP
### ch15 沖縄系統・統合演習（viz/island.html）
図: ①沖縄 5 母線モデル図（`pws_common.build_okinawa`）②6 制約の棒（PV 導入量に対する上限、律速を赤。viz/island.html の定数 S=1500, H0=4.5, K0=150, PMIN_TH=320, 線路 R=0.08/X=0.12, 脱落 180 MW を再現）③H_sys と K vs PV ④周波数 nadir vs PV（RK4）⑤末端電圧 vs PV（力率 1 / 0.95）⑥N-1 線路潮流 vs PV ⑦日負荷曲線と最低出力（最小需要 − 火力最低出力）⑧対策トグル前後の棒（律速の移動）
導出（build）: (a) 連系可能量 = min(6 制約) の定式化、(b) 蓄電池の必要 K_bat = ΔP/|ΔF|max − K
例題: 6 制約の最小 240 MW（律速 周波数）、H 混合、蓄電池、最低出力
