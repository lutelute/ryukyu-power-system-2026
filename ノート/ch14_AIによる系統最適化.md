# 第14回: AI を用いた電力システム最適化

**Day 4 / コマ14** ｜ 電力エネルギーシステム解析の基礎と応用

> **教科書対応**: 本講義の独自部分（教科書の範囲外）。
> ただし第8回 7.4 節の **ELD（経済負荷配分運転）**を出発点とし、
> 第4〜6回の潮流計算、第6回の電圧制約を統合したものが本回の主題である。

> **🖥 動くインフォグラフ**：[`viz/opf.html`](../viz/opf.html) — 等λ法の実解・DC-OPF と LMP の分裂。
> ブラウザで「次へ ▶」を押しながら、この回の核心を実計算で追えます（`index.html` から全回に飛べます）。


<!-- intuition:start（tools/sync-intuition.mjs が スライド/ch14.md から生成。直接編集せずスライドを直す）-->
> **✍ 演習**：[`ex/ch14.html`](../ex/ch14.html) — 学籍番号ごとに数値が変わる問題。採点・途中式つき。
> **📊 スライド**：`スライド/ch14.pptx`（講義用）

---

## まず直感で（3 分でつかむ）

> **📌 一言でいうと**：発電機を安い順に使うのが経済負荷配分で、最適条件は「限界費用 λ が全機で等しい」。制約を足すと OPF になり、混雑があると地点ごとに価格が分かれる。

> **🪄 たとえ話：つながった水槽と渋滞**
>
> | 水槽と道路 | 経済負荷配分 |
> |:--|:--|
> | パイプでつないだ水槽は **水面が揃う** | 水面＝**限界費用 λ**。全機で等しい |
> | 断面の広い水槽ほどたくさん入る | 断面＝**費用曲線の緩さ**（c が小さい） |
> | 水槽には **上限**（あふれる高さ）がある | 上限＝**出力上限**。当たった機は λ から外れる |
> | 安い道が **渋滞** すると迂回路を使う | 渋滞＝**線路容量の制約**（混雑） |
> | 迂回した先の値段が上がる | 迂回先の値段＝**LMP**（地点別限界価格） |
>
> 崩れる点：水槽は独立に上限があるが、発電機は起動停止に時間と費用がかかる。それを扱うのがユニットコミットメント。

> **📰 事例：2021年1月 スポット価格が 200 円/kWh を超えた**
> 日本卸電力取引所（JEPX）のスポット市場は、安い電源から順に積み上げて需要と交わる点で価格が決まる。寒波と LNG 在庫不足で **高い電源まで** 使う日が続き、価格は平時の 10 倍以上に跳ねた。

> **📰 事例：地点で違う価格 — 米国 PJM の LMP**
> 送電線が混雑すると、安い電気を運びきれない地点では高い電源で賄うしかなく、その地点の価格（地点別限界価格 LMP）が上がる。沖縄は他地域と連系がなく市場取引もないため、沖縄電力が自社内で経済負荷配分を行う。

> **🤔 この回の式で読むと**：今日の λ が、市場では「価格」として目に見える。理論と制度が直結している回。

> **🤔 なぜ「等しい」が最適なのか**
> ラグランジュ乗数 λ は「需要を 1 MW 増やしたときの総費用の増分」。どの機で増やしても同じでなければ、安い方へ移す余地が残っている。

> **🤔 なぜ DC-OPF は線形計画になるのか**
> 直流法の 3 近似（|V| = 1、R = 0、sin θ ≈ θ）で潮流制約が線形になる。費用も区分線形にすれば完全な LP で、数万変数でも秒で解ける。

> **⚠ ユニットコミットメント（UC）**
> 「どの機を起動するか」は 0/1 の変数。混合整数計画で NP 困難。起動費用と最低運転時間が絡む。

**この回の地図**：Ⅰ 経済負荷配分（ELD）と等 λ 法 — なぜ「等しい」が最適か → Ⅱ 市場のメリットオーダーと価格の決まり方 → Ⅲ OPF と DC-OPF — 制約を足すとどうなるか → Ⅳ LMP と混雑、そして EMS の中での位置づけ

<!-- intuition:end -->
---

## 14.1 導入

### 学習目標

1. **経済負荷配分（ELD）**を定式化し、**等 λ 法**で解ける。
2. **最適潮流計算（OPF）**の定式化を書き下し、ELD との違いを説明できる。
3. **DC-OPF** と **AC-OPF** の違いと使い分けを説明できる。
4. **ユニットコミットメント（UC）**の構造を理解し、なぜ難しいかを説明できる。
5. 機械学習による **OPF の高速化**の手法と、その限界を論じられる。
6. **EMS / スマートグリッド**における最適化の役割を説明できる。

### 前提知識（第8回との接続）

第8回で、負荷変動の制御分担を学んだ。

```
 自己制御性 → 調速制御（ガバナ）→ LFC → ELD
  〜数十秒        〜数十秒        〜10分   10分〜
```

最も遅い階層である **ELD（経済負荷配分運転）**が本回の出発点である。
ELD は「予測可能なゆっくりした負荷変動」に対し、
**どの発電機にどれだけ発電させるか**を経済的に決める。

第8回では ELD の存在だけを述べた。本回でその中身を扱う。

---

## 14.2 理論

### 14.2.1 経済負荷配分（ELD）と等 λ 法

**問題設定**: $N$ 台の発電機で総需要 $P_D$ を賄う。各機の燃料費を最小化する。

**燃料費関数**（2 次関数で近似するのが標準）:

$$C_i(P_{Gi}) = a_iP_{Gi}^2 + b_iP_{Gi} + c_i \quad [\text{円/h}]$$

**最適化問題**:

$$\min\ \sum_{i=1}^{N}C_i(P_{Gi}) \quad\text{s.t.}\quad
\sum_{i=1}^{N}P_{Gi} = P_D, \qquad P_{Gi}^\text{min} \leq P_{Gi} \leq P_{Gi}^\text{max}$$

**ラグランジュ未定乗数法**（上下限を無視した場合）:

$$\mathcal{L} = \sum_i C_i(P_{Gi}) + \lambda\left(P_D - \sum_i P_{Gi}\right)$$

$$\frac{\partial\mathcal{L}}{\partial P_{Gi}} = \frac{dC_i}{dP_{Gi}} - \lambda = 0$$

$$\boxed{\frac{dC_1}{dP_{G1}} = \frac{dC_2}{dP_{G2}} = \cdots = \frac{dC_N}{dP_{GN}} = \lambda}$$

**これが等 λ 法（equal incremental cost method）である。**

**$\lambda$ の意味**: **限界費用**（incremental cost）。
需要が 1 MW 増えたときに増える費用 \[円/MWh\]。
電力市場における**システムプライス**の理論的な基礎でもある。

**直感的な理解**: もし機 1 の限界費用が機 2 より安いなら、
機 1 を増やし機 2 を減らせば総費用が下がる。
**すべての限界費用が等しくなったときに最適**である。

2 次費用関数なら $dC_i/dP_{Gi} = 2a_iP_{Gi}+b_i = \lambda$ より

$$P_{Gi} = \frac{\lambda - b_i}{2a_i}$$

これを需給バランス式に代入すると

$$\sum_i\frac{\lambda-b_i}{2a_i} = P_D
\quad\Longrightarrow\quad
\boxed{\lambda = \frac{P_D + \sum_i\dfrac{b_i}{2a_i}}{\sum_i\dfrac{1}{2a_i}}}$$

**上下限制約の扱い**: $P_{Gi}$ が上下限を超えたら**その値に固定**し、
残りの機で再計算する。これを収束するまで繰り返す。
（第5回の PV 母線の $Q$ 限界処理と同じ考え方である。）

**送電損失を考慮する場合**: 損失 $P_L$ を含めると

$$\sum_i P_{Gi} = P_D + P_L(\mathbf{P}_G)$$

最適条件は**ペナルティ係数** $L_i$ を用いて

$$L_i\frac{dC_i}{dP_{Gi}} = \lambda, \qquad L_i = \frac{1}{1-\partial P_L/\partial P_{Gi}}$$

$\partial P_L/\partial P_{Gi}$ は**増分損失率**。
損失を増やす発電機（需要地から遠い）は不利に評価される。

<!-- fig:ch14_cost_curves.png -->
![図 14.1](../図/ch14_cost_curves.png)
*図 14.1　3 機の費用曲線（左）と限界費用（右）。費用は出力の 2 次関数で近似され、その傾きである限界費用は右上がりの直線になる。石炭は安いが傾きが急、石油は高いが傾きが緩い。*
<!-- /fig -->

<!-- fig:ch14_equal_lambda.png -->
![図 14.2](../図/ch14_equal_lambda.png)
*図 14.2　需要 600 MW の等 λ 配分。λ = 17.81 千円/MWh の水平線と各機の限界費用曲線の交点が最適出力（石炭 245・LNG 242・石油 113 MW）。均等配分との差は 123 千円/h、年に約 10.7 億円になる。*
<!-- /fig -->

<!-- fig:ch14_lambda_iteration.png -->
![図 14.3](../図/ch14_lambda_iteration.png)
*図 14.3　λ の探索。λ を仮定すると各機の出力が決まるので、合計が需要に一致するまで二分法で修正する。数十機あっても探すのは λ ただ 1 つで、12 回程度の反復で収束する。*
<!-- /fig -->

<!-- fig:ch14_dispatch_curve.png -->
![図 14.4](../図/ch14_dispatch_curve.png)
*図 14.4　需要に対する配分（左）とシステム λ（右）。需要が増えると高い機が入り、λ は 11.6 から 23.8 千円/MWh へ上昇する。折れ点は、ある機が出力上限に達した瞬間である。*
<!-- /fig -->

### 14.2.2 最適潮流計算（OPF）

ELD の限界: **系統の制約（電圧・線路容量）を一切考慮していない**。
経済的に最適でも、線路が過負荷になったり電圧が逸脱したりしては運用できない。

**OPF は ELD に潮流方程式と系統制約を加えたもの**である。

$$\begin{aligned}
\min_{\mathbf{u}}\quad & f(\mathbf{x},\mathbf{u}) = \sum_i C_i(P_{Gi})\\
\text{s.t.}\quad
& \mathbf{g}(\mathbf{x},\mathbf{u}) = \mathbf{0}
&&\textbf{等式制約: 電力方程式（第4回）}\\
& \mathbf{h}(\mathbf{x},\mathbf{u}) \leq \mathbf{0}
&&\textbf{不等式制約: 運用制約}
\end{aligned}$$

**制約の内訳**:

| 種類 | 制約 | 由来 |
|:---|:---|:---|
| 等式 | $P_i = V_i\sum_j V_j(G_{ij}\cos\theta_{ij}+B_{ij}\sin\theta_{ij})$ | 第4回 |
| 等式 | $Q_i = V_i\sum_j V_j(G_{ij}\sin\theta_{ij}-B_{ij}\cos\theta_{ij})$ | 第4回 |
| 不等式 | $P_{Gi}^\text{min} \leq P_{Gi} \leq P_{Gi}^\text{max}$ | 発電機出力 |
| 不等式 | $Q_{Gi}^\text{min} \leq Q_{Gi} \leq Q_{Gi}^\text{max}$ | 第5回の $Q$ 限界 |
| 不等式 | $V_i^\text{min} \leq V_i \leq V_i^\text{max}$（0.95〜1.05） | 第6回の電圧 |
| 不等式 | $\|S_{ij}\| \leq S_{ij}^\text{max}$ | 線路熱容量 |
| 不等式 | $\|\theta_{ij}\| \leq \theta^\text{max}$ | 第7回の安定度 |

**制御変数 $\mathbf{u}$**: 発電機有効電力、発電機端子電圧、変圧器タップ、調相設備。
**状態変数 $\mathbf{x}$**: 各母線の電圧・位相角。

**AC-OPF は非凸**であり、大域最適解を保証するのが難しい。
これが電力系統工学の長年の難問である。

<!-- fig:ch14_merit_order.png -->
![図 14.5](../図/ch14_merit_order.png)
*図 14.5　メリットオーダー。安い電源から順に積み上げ、需要と交わる高さが約定価格になる。需要 900 MW では LNG が最後の 1 台となり、価格は 13 円/kWh。安い電源も同じ価格で売れる。*
<!-- /fig -->

<!-- fig:ch14_price_curve.png -->
![図 14.6](../図/ch14_price_curve.png)
*図 14.6　需要と約定価格。需要がどの電源まで届くかで価格が階段状に跳ねる。軽負荷の夜は 2 円/kWh、猛暑日のピークでは 30 円/kWh。2021 年 1 月の高騰は、この階段の一番上まで需要が届いた結果である。*
<!-- /fig -->

<!-- fig:ch14_carbon.png -->
![図 14.7](../図/ch14_carbon.png)
*図 14.7　炭素価格の効果。石炭は燃料が安いが CO₂ が 0.86 kg/kWh、LNG は燃料が高いが 0.37 kg/kWh。約 11,200 円/t-CO₂ で両者が逆転し、メリットオーダーの順位そのものが入れ替わる。*
<!-- /fig -->

### 14.2.3 DC-OPF — 実務の主力

第4回 4.2.7 節で学んだ**直流法潮流計算**を使うと、OPF が**線形計画問題**になる。

$$\begin{aligned}
\min\quad & \sum_i C_i(P_{Gi}) \quad(\text{区分線形近似すれば LP})\\
\text{s.t.}\quad
& \sum_i P_{Gi} = \sum_i P_{Di} && \text{需給バランス（損失なし）}\\
& P_{ij} = \frac{\theta_i-\theta_j}{x_{ij}}, \quad |P_{ij}| \leq P_{ij}^\text{max} && \text{線路潮流と容量}\\
& P_{Gi}^\text{min} \leq P_{Gi}\leq P_{Gi}^\text{max}
\end{aligned}$$

**DC-OPF の位置づけ**:

| 長所 | 短所 |
|:---|:---|
| **線形計画** → 必ず大域最適解が求まる | 無効電力・電圧を扱えない |
| 高速（大規模系統でも実用的） | 損失を無視 |
| 双対変数から**ノード価格（LMP）**が直接得られる | 精度が落ちる |
| 整数変数を加えやすい（UC） | 重負荷時に誤差が大きい |

**LMP（Locational Marginal Price、ノード限界価格）**:
各ノードの需給バランス制約に対する双対変数（ラグランジュ乗数）。

$$\text{LMP}_i = \underbrace{\lambda}_{\text{エネルギー}}
+ \underbrace{\text{混雑成分}}_{\text{送電制約}} + \underbrace{\text{損失成分}}_{\text{AC-OPFのみ}}$$

**混雑がなければ全ノードで LMP は同じ**（$=\lambda$、ELD と一致）。
線路が容量上限に達すると、その先のノードの LMP が跳ね上がる。
これが**日本の卸電力市場（JEPX）のエリアプライス**の理論的基礎である。

$$\boxed{\text{第4回で学んだ直流法潮流が、電力市場の価格形成を支えている}}$$

<!-- fig:ch14_lmp.png -->
![図 14.8](../図/ch14_lmp.png)
*図 14.8　3 母線の DC-OPF。混雑がなければ安い母線1 が 300 MW すべてを賄うが、線路 1–3 を 120 MW に制限すると母線1 は 60 MW しか出せず、高い母線2 が 240 MW を負担する。総費用は 3.30 → 5.41 百万円/h に増える。*
<!-- /fig -->

<!-- fig:ch14_congestion.png -->
![図 14.9](../図/ch14_congestion.png)
*図 14.9　線路容量と費用・価格の関係。容量が十分なら一定だが、混雑した瞬間から総費用と地点価格（LMP）が跳ね上がる。LMP は 14.0 から 36.5 千円/MWh へと 2.6 倍になり、この傾きが送電線増強の価値を測る材料になる。*
<!-- /fig -->

### 14.2.4 ユニットコミットメント（UC）

OPF は「起動している発電機の出力配分」を決める。
**どの発電機を起動するか**を決めるのが **UC（起動停止計画）**である。

$$\min\ \sum_{t=1}^{T}\sum_{i=1}^{N}
\Bigl[\underbrace{C_i(P_{Gi,t})u_{i,t}}_{\text{燃料費}}
+ \underbrace{SU_i\,y_{i,t}}_{\text{起動費}}
+ \underbrace{SD_i\,z_{i,t}}_{\text{停止費}}\Bigr]$$

$u_{i,t}\in\{0,1\}$ は起動状態を表す**二値変数**である。

**追加される制約**:

| 制約 | 内容 |
|:---|:---|
| **最小運転時間** | 一度起動したら $T_i^\text{on}$ 時間は止められない |
| **最小停止時間** | 一度止めたら $T_i^\text{off}$ 時間は起動できない |
| **ランプ制約** | $\|P_{Gi,t}-P_{Gi,t-1}\| \leq R_i$（出力変化速度の限界） |
| **予備力制約** | $\sum_i(P_{Gi}^\text{max} u_{i,t} - P_{Gi,t}) \geq R_t$ |
| 起動・停止の論理 | $y_{i,t}-z_{i,t} = u_{i,t}-u_{i,t-1}$ |

**なぜ難しいか**: 二値変数を含むため **MILP（混合整数線形計画）**となり、
**NP 困難**である。$N$ 台 $T$ 時間なら $2^{NT}$ の組み合わせがある。
実系統（数百台 × 168 時間）では厳密解が現実的でない。

**再エネがさらに難しくする**:

| 要因 | 影響 |
|:---|:---|
| 再エネの不確実性 | 確率的 UC（シナリオを多数考慮）が必要 → 問題規模が爆発 |
| **ランプ要求の増大** | 第11回のダックカーブ。夕方の急な立ち上がりに対応できる機が必要 |
| **起動停止の頻発** | 昼に火力を止め夕方に起動。設備劣化と起動費の増加 |
| 最低出力制約 | 昼に太陽光が多いと、火力を最低出力まで下げても余る → **出力抑制** |

### 14.2.5 機械学習による OPF の高速化

**なぜ高速化が必要か**:

| 用途 | 必要な計算回数 |
|:---|:---|
| リアルタイム運用（5 分ごと） | 短時間で 1 回 |
| **N-1 制約付き OPF（SCOPF）** | 全ての想定事故 × OPF = 数千回 |
| **確率的 UC** | シナリオ数 × 時間 = 数万回 |
| 系統計画 | 年間 8760 時間 × 多数のシナリオ |

**アプローチ 1: 直接予測（end-to-end）**

系統状態（需要・再エネ）→ 最適解（発電機出力）を直接学習する。

$$\mathbf{u}^* = f_\theta(\mathbf{P}_D, \mathbf{P}_\text{RE})$$

**問題**: 予測された解が**制約を満たす保証がない**。
そのまま運用すると過負荷や電圧逸脱を起こす。

**対策**:
- 出力層で制約を満たすように射影する（**projection layer**）
- 予測解を初期値として厳密解法を数回だけ回す（**warm start**）
- 制約違反を損失関数に加える（第13回の PINN と同じ発想）

**アプローチ 2: アクティブ制約の予測**

最適解では、多数ある不等式制約のうち**ごく一部だけが有効（等号成立）**である。

$$\boxed{\text{どの制約がアクティブかが分かれば、残りは無視でき問題が劇的に小さくなる}}$$

分類器でアクティブ制約集合を予測 → 縮小した問題を厳密に解く。

| 利点 | 内容 |
|:---|:---|
| **厳密解が得られる** | 縮小問題を厳密に解くので実行可能性が保証される |
| 大幅な高速化 | 制約数が 1/10 以下になることも |
| 誤りに対応可能 | 予測を外しても、制約違反をチェックして追加すればよい |

**アプローチ 3: warm start**

学習モデルの出力を反復解法の初期値にする。
第5回で見たとおり、ニュートン法は**初期値が良ければ反復回数が減る**。

**アプローチ 4: 代理モデルによるスクリーニング**（第13回 例題 13-2）

GNN で高速に評価 → 危険なケースだけ厳密計算。

### 14.2.6 EMS とスマートグリッド

**EMS（Energy Management System）**: 中央給電指令所の中核システム。

```
   [計測] SCADA / PMU
       ↓
   [状態推定]（第13回）── 今どうなっているか
       ↓
   [想定事故解析]（N-1、第15回）── 危険はないか
       ↓
   [OPF / SCOPF]（本回）── どう動かすべきか
       ↓
   [ELD / LFC / AGC 指令]（第8回）── 実際の指令
       ↓
   [発電機・調相設備・タップ]
```

**本講義で学んだことが、この流れの中に位置づけられる。**

| 本講義の内容 | EMS での位置づけ |
|:---|:---|
| 第4〜6回 潮流計算 | 状態推定・想定事故解析の基礎 |
| 第7回 安定度 | 動的安定度監視 |
| 第8回 周波数制御 | LFC / ELD |
| 第10〜12回 予測 | 需給計画の入力 |
| 第13回 AI 解析 | 状態推定・異常検知の高度化 |
| 第14回 最適化 | OPF / UC |

**スマートグリッドの方向性**:

| 論点 | 内容 |
|:---|:---|
| **分散化** | 中央集権的な制御から、分散電源の自律協調へ |
| **デマンドレスポンス（DR）** | 需要側を制御可能な資源として扱う |
| **VPP（仮想発電所）** | 多数の分散資源を束ねて 1 つの発電所として運用 |
| **P2P 電力取引** | 需要家間の直接取引 |
| **セクターカップリング** | 電気・熱・水素・モビリティの統合最適化 |

**沖縄での意義**: 独立系統（第2回・第8回）であり、
**連系線による応援がない**ため、系統内の資源を最大限活用する必要がある。
需要側資源（DR）、蓄電池、EV（V2G）を統合的に最適化する必要性が本土より高い。

<!-- fig:ch14_ems.png -->
![図 14.10](../図/ch14_ems.png)
*図 14.10　EMS の流れ。状態推定で現在を把握し、想定事故解析で危険箇所を洗い出し、OPF で制約を守る最安の配分を求め、ELD と LFC で発電機に指令する。この輪が数分ごとに回っている。*
<!-- /fig -->

---

## 14.3 シミュレーション

### 14.3.1 経済負荷配分（等 λ 法）

```python
"""第14回 デモ1: 等λ法による経済負荷配分"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'DejaVu Sans']

# 発電機データ: C = a*P^2 + b*P + c [円/h], P は [MW]
GENS = [
    # name,      a,     b,     c,     Pmin,  Pmax
    ("石炭火力", 0.0080, 7.50, 480.0,  80.0, 350.0),
    ("LNG-CC",  0.0125, 9.80, 320.0,  60.0, 280.0),
    ("LNG汽力", 0.0180, 11.2, 250.0,  40.0, 200.0),
    ("石油火力", 0.0300, 15.5, 180.0,  20.0, 120.0),
]

def economic_dispatch(P_D, gens=GENS, verbose=False):
    """等λ法（上下限制約を反復処理）"""
    a = np.array([g[1] for g in gens]); b = np.array([g[2] for g in gens])
    pmin = np.array([g[4] for g in gens]); pmax = np.array([g[5] for g in gens])
    free = np.ones(len(gens), dtype=bool)
    P = np.zeros(len(gens))

    for it in range(30):
        # 自由な機について λ を求める
        num = P_D - P[~free].sum() + np.sum(b[free]/(2*a[free]))
        den = np.sum(1.0/(2*a[free]))
        lam = num/den
        P[free] = (lam - b[free])/(2*a[free])
        # 上下限違反をチェック
        viol = False
        for i in np.where(free)[0]:
            if P[i] > pmax[i]:   P[i], free[i], viol = pmax[i], False, True
            elif P[i] < pmin[i]: P[i], free[i], viol = pmin[i], False, True
        if not viol:
            if verbose: print(f"  {it+1} 回の反復で収束")
            return P, lam
    return P, lam

P_D = 700.0
P, lam = economic_dispatch(P_D, verbose=True)

print(f"\n=== 経済負荷配分（需要 {P_D:.0f} MW）===")
print(f"{'発電機':<12} {'出力[MW]':>10} {'限界費用':>12} {'費用[円/h]':>14}")
total = 0.0
for (name,a,b,c,pmin,pmax), p in zip(GENS, P):
    ic = 2*a*p + b
    cost = a*p**2 + b*p + c
    total += cost
    flag = ""
    if abs(p-pmax) < 1e-6: flag = " (上限)"
    elif abs(p-pmin) < 1e-6: flag = " (下限)"
    print(f"{name:<12} {p:10.2f} {ic:12.3f} {cost:14.1f}{flag}")
print(f"{'合計':<12} {P.sum():10.2f} {'λ='+f'{lam:.3f}':>12} {total:14.1f}")
print(f"\n平均発電単価: {total/P_D:.2f} 円/MWh")
print("→ 上下限に達していない機の限界費用はすべて λ に等しい（等λ法）")

# --- 需要を変えたときの配分の変化 ---
demands = np.linspace(220, 950, 120)
alloc = np.array([economic_dispatch(d)[0] for d in demands])
lams  = np.array([economic_dispatch(d)[1] for d in demands])

fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
axes[0].stackplot(demands, alloc.T, labels=[g[0] for g in GENS], alpha=0.85)
axes[0].plot(demands, demands, "k--", lw=1, label="総需要")
axes[0].set_xlabel("総需要 [MW]"); axes[0].set_ylabel("発電機出力 [MW]")
axes[0].set_title("経済負荷配分（メリットオーダー）")
axes[0].legend(fontsize=8, loc="upper left"); axes[0].grid(alpha=0.3)

axes[1].plot(demands, lams, lw=2.5, color="#e63946")
axes[1].set_xlabel("総需要 [MW]"); axes[1].set_ylabel("$\\lambda$ [円/MWh]")
axes[1].set_title("限界費用（システムプライス）")
axes[1].grid(alpha=0.3)
plt.tight_layout(); plt.savefig("../図/ch14_eld.png", dpi=150)
```

**観察してほしいこと**: 需要が増えるにつれ、
**安い電源から順に上限まで使い、次に高い電源が入る**（メリットオーダー）。
$\lambda$ のグラフに折れ点が現れるのは、ある発電機が上限に達した瞬間である。

### 14.3.2 DC-OPF と LMP

```python
"""第14回 デモ2: DC-OPF とノード価格（LMP）"""
import numpy as np
from scipy.optimize import linprog

# 3ノード系統
#   G1(安い) --- 線路容量が小さい --- 需要
#   G2(高い) --- 需要の近く
BUSES = 3
LINES = [(0,1,0.10,60.0), (1,2,0.15,100.0), (0,2,0.20,80.0)]   # (from,to,x,容量MW)
GEN   = {0: (6.0, 0.0, 250.0),      # bus: (単価[円/MWh], Pmin, Pmax)
         1: (18.0, 0.0, 200.0)}
LOAD  = {2: 180.0}

def dc_opf(line_caps=None):
    caps = line_caps or [l[3] for l in LINES]
    n_g = len(GEN); n_th = BUSES - 1              # θ1 を基準(=0)
    n_var = n_g + n_th
    gbus = sorted(GEN)

    # 目的関数
    c = np.zeros(n_var)
    for k, b in enumerate(gbus): c[k] = GEN[b][0]

    # 等式制約: 各ノードの電力収支
    Aeq = np.zeros((BUSES, n_var)); beq = np.zeros(BUSES)
    def th_col(b): return None if b == 0 else n_g + (b-1)
    for f, t, x, _ in LINES:
        for (i, j, sgn) in [(f, t, 1.0), (t, f, -1.0)]:
            if th_col(i) is not None: Aeq[i, th_col(i)] += sgn/x
            if th_col(j) is not None: Aeq[i, th_col(j)] -= sgn/x
    for k, b in enumerate(gbus): Aeq[b, k] = -1.0
    for b, d in LOAD.items(): beq[b] = -d

    # 不等式制約: 線路容量 |P_ij| <= cap
    Aub, bub = [], []
    for (f, t, x, _), cap in zip(LINES, caps):
        row = np.zeros(n_var)
        if th_col(f) is not None: row[th_col(f)] += 1/x
        if th_col(t) is not None: row[th_col(t)] -= 1/x
        Aub.append(row.copy());  bub.append(cap)
        Aub.append(-row.copy()); bub.append(cap)

    bounds = [(GEN[b][1], GEN[b][2]) for b in gbus] + [(-np.pi, np.pi)]*n_th
    res = linprog(c, A_ub=np.array(Aub), b_ub=np.array(bub),
                  A_eq=Aeq, b_eq=beq, bounds=bounds, method="highs")
    return res, gbus, Aeq

for label, caps in [("混雑なし（線路0-1を200MWに増強）", [200.0, 100.0, 80.0]),
                    ("混雑あり（線路0-1が60MW）",       [60.0, 100.0, 80.0])]:
    res, gbus, _ = dc_opf(caps)
    print(f"\n=== {label} ===")
    if not res.success:
        print("  解けませんでした:", res.message); continue
    print(f"  総費用: {res.fun:,.1f} 円/h")
    for k, b in enumerate(gbus):
        print(f"  ノード{b+1} 発電: {res.x[k]:7.2f} MW（単価 {GEN[b][0]:.1f} 円/MWh）")
    theta = np.r_[0.0, res.x[len(gbus):]]
    for (f,t,x,_), cap in zip(LINES, caps):
        flow = (theta[f]-theta[t])/x
        mark = " ★上限" if abs(abs(flow)-cap) < 1e-4 else ""
        print(f"  線路{f+1}-{t+1}: {flow:7.2f} MW / 容量 {cap:.0f} MW{mark}")
    # LMP = 等式制約の双対変数
    lmp = -res.eqlin.marginals
    print("  LMP（ノード価格）:")
    for b in range(BUSES):
        print(f"    ノード{b+1}: {lmp[b]:8.3f} 円/MWh")
    if np.ptp(lmp) > 1e-6:
        print(f"  → 混雑によりノード間で価格差 {np.ptp(lmp):.2f} 円/MWh が発生")
    else:
        print("  → 混雑なし。全ノードで価格が等しい（ELD と一致）")
```

**期待される結論**: 混雑がなければ全ノードの LMP が等しく、ELD と同じ結果になる。
線路が容量に達すると、**安い電源を使えなくなり、需要地の LMP が上がる**。
これがエリアプライスが分かれる仕組みである。

### 14.3.3 AC-OPF（pandapower）

```python
"""第14回 デモ3: AC-OPF で電圧制約も考慮する"""
import numpy as np
import pandapower as pp
import pandapower.networks as pn

net = pn.case14()

# 発電機に費用関数を設定
for idx in net.gen.index:
    pp.create_poly_cost(net, idx, "gen",
                        cp1_eur_per_mw=np.random.uniform(12, 30),
                        cp2_eur_per_mw2=0.01)
pp.create_poly_cost(net, 0, "ext_grid", cp1_eur_per_mw=8.0)

# 運用制約
net.bus["min_vm_pu"] = 0.95
net.bus["max_vm_pu"] = 1.05
net.gen["min_p_mw"]  = 0.0
net.gen["max_p_mw"]  = 150.0
net.gen["min_q_mvar"] = -50.0
net.gen["max_q_mvar"] =  60.0
net.line["max_loading_percent"]  = 100.0
net.trafo["max_loading_percent"] = 100.0
net.ext_grid["min_p_mw"], net.ext_grid["max_p_mw"] = 0.0, 300.0
net.ext_grid["min_q_mvar"], net.ext_grid["max_q_mvar"] = -100.0, 100.0

# --- 通常の潮流計算（最適化なし）---
pp.runpp(net)
cost_pf = sum(net.res_gen.p_mw*np.random.uniform(12,30,len(net.res_gen)))
print("=== 通常の潮流計算 ===")
print(f"  電圧範囲: {net.res_bus.vm_pu.min():.4f} 〜 {net.res_bus.vm_pu.max():.4f} p.u.")
print(f"  最大線路負荷率: {net.res_line.loading_percent.max():.2f} %")
print(f"  系統損失: {net.res_line.pl_mw.sum():.3f} MW")

# --- AC-OPF ---
try:
    pp.runopp(net, verbose=False)
    print("\n=== AC-OPF ===")
    print(f"  総費用: {net.res_cost:,.2f}")
    print(f"  電圧範囲: {net.res_bus.vm_pu.min():.4f} 〜 {net.res_bus.vm_pu.max():.4f} p.u.")
    print(f"  最大線路負荷率: {net.res_line.loading_percent.max():.2f} %")
    print(f"  系統損失: {net.res_line.pl_mw.sum():.3f} MW")
    print("\n  発電機出力:")
    for i in net.res_gen.index:
        print(f"    gen{i}: P={net.res_gen.p_mw[i]:7.2f} MW, "
              f"Q={net.res_gen.q_mvar[i]:7.2f} Mvar")
    print(f"    ext_grid: P={net.res_ext_grid.p_mw[0]:7.2f} MW")
    print("\n  → すべての制約（電圧・容量）を満たしつつ費用最小化されている")
except Exception as e:
    print(f"\nAC-OPF が解けませんでした: {e}")
    print("（AC-OPF は非凸で収束が難しいことがある。PYPOWER/PowerModels 等を試すとよい）")
```

### 14.3.4 機械学習による OPF の高速化

```python
"""第14回 デモ4: アクティブ制約の予測による高速化"""
import numpy as np
import time
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

rng = np.random.default_rng(7)

def solve_and_label(scale):
    """DC-OPF を解き、どの制約がアクティブかを返す"""
    global LOAD
    LOAD = {2: 180.0*scale}
    res, gbus, _ = dc_opf([60.0, 100.0, 80.0])
    if not res.success: return None, None
    theta = np.r_[0.0, res.x[len(gbus):]]
    active = []
    for (f,t,x,_), cap in zip(LINES, [60.0, 100.0, 80.0]):
        flow = (theta[f]-theta[t])/x
        active.append(1 if abs(abs(flow)-cap) < 1e-4 else 0)
    for k, b in enumerate(gbus):
        active.append(1 if abs(res.x[k]-GEN[b][2]) < 1e-4 else 0)
    return res, np.array(active)

print("学習データ生成中...")
Xs, Ys, costs = [], [], []
for _ in range(1200):
    s = rng.uniform(0.35, 1.45)
    res, act = solve_and_label(s)
    if res is None: continue
    Xs.append([s*180.0]); Ys.append(act); costs.append(res.fun)
Xs, Ys = np.array(Xs), np.array(Ys)
print(f"生成: {len(Xs)} ケース、制約数 {Ys.shape[1]}")

n_tr = int(len(Xs)*0.75)
print(f"\n=== アクティブ制約の予測精度 ===")
for j in range(Ys.shape[1]):
    if len(np.unique(Ys[:n_tr, j])) < 2:
        print(f"  制約{j}: 常に {'アクティブ' if Ys[0,j] else '非アクティブ'}（学習不要）")
        continue
    clf = RandomForestClassifier(n_estimators=100, random_state=0)
    clf.fit(Xs[:n_tr], Ys[:n_tr, j])
    acc = accuracy_score(Ys[n_tr:, j], clf.predict(Xs[n_tr:]))
    rate = Ys[:, j].mean()*100
    print(f"  制約{j}: 予測精度 {acc*100:5.1f}%  （アクティブ率 {rate:5.1f}%）")

print("\n=== 考察 ===")
print(f"全制約数: {Ys.shape[1]}")
print(f"常にアクティブ: {(Ys.mean(0) > 0.99).sum()} 個")
print(f"常に非アクティブ: {(Ys.mean(0) < 0.01).sum()} 個  ← 除去できる")
print(f"ケースにより変わる: {((Ys.mean(0) >= 0.01) & (Ys.mean(0) <= 0.99)).sum()} 個")
print("\n→ 非アクティブと分かった制約を除けば問題規模が小さくなり高速化できる。")
print("→ 予測を外しても、解いた後に制約違反をチェックして追加すれば厳密性は保てる。")
```

---

## 14.4 例題

### 例題 14-1（等 λ 法）

2 台の発電機の燃料費関数が次で与えられる。

$$C_1 = 0.010P_1^2 + 8.0P_1 + 400, \qquad C_2 = 0.015P_2^2 + 6.4P_2 + 300$$

出力制約は $50 \leq P_1 \leq 300$、$40 \leq P_2 \leq 250$。
総需要 400 MW を最小費用で分担せよ。

**解答**

限界費用は
$$\frac{dC_1}{dP_1} = 0.020P_1 + 8.0, \qquad \frac{dC_2}{dP_2} = 0.030P_2 + 6.4$$

等 λ 条件と需給バランスを連立する。

$$0.020P_1 + 8.0 = 0.030P_2 + 6.4 = \lambda, \qquad P_1 + P_2 = 400$$

第 1 式から $P_1 = (\lambda-8.0)/0.020$、$P_2 = (\lambda-6.4)/0.030$。
需給バランス式に代入すると

$$\frac{\lambda-8.0}{0.020} + \frac{\lambda-6.4}{0.030} = 400$$

両辺に 0.060 を掛けて

$$3(\lambda-8.0) + 2(\lambda-6.4) = 24 \quad\Longrightarrow\quad 5\lambda = 24+24+12.8 = 60.8$$

$$\lambda = \boxed{12.16\ \text{円/MWh}}$$

$$P_1 = \frac{12.16-8.0}{0.020} = \boxed{208.0\ \text{MW}}, \qquad
P_2 = \frac{12.16-6.4}{0.030} = \boxed{192.0\ \text{MW}}$$

**制約の確認**: $50 \leq 208 \leq 300$ ✓、$40 \leq 192 \leq 250$ ✓。制約内である。

**検算**: $P_1+P_2 = 400$ ✓、
限界費用 $0.020\times208+8.0 = 12.16$、$0.030\times192+6.4 = 12.16$ ✓ 一致。

**総費用**:
$$C_1 = 0.010(208)^2+8(208)+400 = 432.6+1664+400 = 2496.6$$
$$C_2 = 0.015(192)^2+6.4(192)+300 = 553.0+1228.8+300 = 2081.8$$
$$\text{合計} = \boxed{4578.4\ \text{円/h}}$$

### 例題 14-2（LMP と混雑）

2 ノード系統がある。ノード 1 に安い発電機（8 円/MWh、容量 200 MW）、
ノード 2 に高い発電機（25 円/MWh、容量 150 MW）と需要 180 MW がある。
連系線の容量を $C$ とする。

1. $C = 200$ MW のときの各ノードの LMP を求めよ。
2. $C = 120$ MW のときの発電配分と LMP を求めよ。
3. (2) のとき、混雑によって生じる費用（混雑レント）を求めよ。

**解答**

**(1)** 連系線に余裕があるので、安いノード 1 の発電機だけで 180 MW を賄える。
混雑がないので**両ノードの LMP は等しく**、追加 1 MW を供給するのは
ノード 1 の発電機だから

$$\text{LMP}_1 = \text{LMP}_2 = \boxed{8\ \text{円/MWh}}$$

**(2)** 連系線が 120 MW で頭打ちなので、
ノード 1 からは 120 MW しか送れない。残り 60 MW はノード 2 で発電する。

$$P_1 = \boxed{120\ \text{MW}}, \qquad P_2 = \boxed{60\ \text{MW}}$$

LMP は「そのノードで需要が 1 MW 増えたときの費用増」である。

- ノード 1 で 1 MW 増 → ノード 1 の安い発電機が 1 MW 増やす → $\text{LMP}_1 = \boxed{8\ \text{円/MWh}}$
- ノード 2 で 1 MW 増 → 連系線は既に満杯なのでノード 2 の発電機が増やす → $\text{LMP}_2 = \boxed{25\ \text{円/MWh}}$

**(3)** 混雑レント（congestion rent）は、
連系線の両端の価格差 × 潮流である。

$$\text{混雑レント} = (\text{LMP}_2 - \text{LMP}_1)\times C = (25-8)\times120 = \boxed{2040\ \text{円/h}}$$

**意味**: この金額が、送電線の容量不足によって生じている経済的な損失（の指標）である。
混雑レントが恒常的に大きい線路は**増強の経済的な根拠**になる。

### 例題 14-3（AI による OPF 高速化の妥当性）

機械学習で OPF の解を直接予測するモデルを作った。
検証データでの費用の誤差は 0.5%、しかし 3% のケースで
線路容量制約に違反していた。このモデルを実運用してよいか。

**解答**

**そのまま運用してはならない。**

**理由**: 費用の誤差 0.5% は許容できるが、**制約違反 3% は致命的**である。
100 回に 3 回、過負荷を引き起こす運転指令を出すことになる。
線路の過負荷は保護リレーの動作、最悪の場合は連鎖的な事故に至る。

$$\boxed{\text{最適性は妥協できるが、実行可能性（feasibility）は妥協できない}}$$

**取るべき対策**:

| 対策 | 内容 |
|:---|:---|
| **1. 事後チェック（必須）** | 予測解で潮流計算を実行し、制約違反がないか確認する |
| **2. warm start に用途を限定** | 予測解を初期値として厳密解法を回す。解は厳密解法が保証する |
| **3. アクティブ制約予測に切り替える** | 縮小した問題を厳密に解くので実行可能性が保証される |
| **4. 射影層を設ける** | 出力を実行可能領域に射影する |
| **5. 制約違反を損失に加える** | 学習時に違反を強く罰する（ただし保証にはならない） |

**推奨**: **2 または 3**。どちらも**最終的な解は厳密解法が出す**ので、
実行可能性が保証されつつ高速化の恩恵を受けられる。

**教訓**: 電力系統において AI は**解を出す主体ではなく、解法を助ける道具**として使うのが安全である。
第13回の結論（AI は物理の代替ではなく高速化と補完）と同じである。

---

## 14.5 演習問題

### 基礎問題

**問 14-1** 等 λ 法の最適条件を導出し、$\lambda$ の物理的・経済的意味を説明せよ。

**問 14-2** 3 台の発電機について、総需要 500 MW を経済負荷配分せよ。
$$C_1 = 0.012P_1^2+7.0P_1+350,\quad C_2 = 0.010P_2^2+9.0P_2+400,\quad C_3 = 0.020P_3^2+6.0P_3+280$$
出力制約は $P_1\in[50,250]$、$P_2\in[40,200]$、$P_3\in[30,150]$。

**問 14-3** ELD と OPF の違いを、考慮する制約の観点から説明せよ。

**問 14-4** DC-OPF が線形計画になる理由を、第4回 4.2.7 節の 3 つの近似から説明せよ。
また DC-OPF が扱えないものを 2 つ挙げよ。

**問 14-5** ユニットコミットメント（UC）が OPF より難しい理由を説明せよ。
また再生可能エネルギーの導入が UC をどう難しくするか 3 点挙げよ。

### 応用問題

**問 14-6** 14.3.1 節のコードを用いて、経済負荷配分を分析せよ。

(a) 需要を 220〜950 MW で変化させ、各発電機の出力と $\lambda$ をグラフ化せよ。
(b) $\lambda$ のグラフに折れ点が現れる需要値を特定し、その理由を説明せよ。
(c) 石炭火力に CO₂ 排出コスト（3,000 円/t-CO₂、排出係数 0.86 kg-CO₂/kWh）を
   上乗せしたとき、配分がどう変わるか計算せよ。
(d) (c) の結果から、カーボンプライシングが電源構成に与える影響を論じよ。

**問 14-7** 沖縄本島系統（第6回 問6-5 のモデル）で OPF を実行せよ。

(a) 各発電機に燃料費関数を設定し、AC-OPF を実行せよ。
(b) 太陽光 300 MW を導入した場合の総費用の変化を求めよ。
(c) 太陽光の導入により**出力抑制**が必要になる条件を求めよ。
   （火力の最低出力制約を考慮すること）
(d) 蓄電池（100 MW / 400 MWh）を導入した場合、
   1 日の運用（24 時間）を最適化し、出力抑制がどれだけ減るか評価せよ。
(e) 蓄電池の導入が経済的に見合うか、簡易的な費用便益分析を行え。

**問 14-8** 機械学習による OPF 高速化を実装・評価せよ。

(a) DC-OPF を 2000 ケース解き、需要 → 最適発電機出力のデータセットを作れ。
(b) 回帰モデルで最適解を直接予測し、費用の誤差と制約違反率を評価せよ。
(c) 予測解を初期値（warm start）として厳密解法を回し、
   反復回数がどれだけ減るか評価せよ。
(d) アクティブ制約を予測する分類器を作り、
   縮小問題を解いた場合の高速化率と厳密性を評価せよ。
(e) (b)(c)(d) の 3 手法を「速度・精度・実行可能性の保証」の観点で比較し、
   実運用に推奨する手法とその理由を述べよ。

---

## 14.6 まとめ

### キーポイント

- **経済負荷配分（ELD）**の最適条件は**等 λ 法**:
  $$\frac{dC_1}{dP_{G1}} = \cdots = \frac{dC_N}{dP_{GN}} = \lambda$$
  $\lambda$ は**限界費用**であり、電力市場のシステムプライスの基礎。
  上下限に達した機は固定して残りで再計算する（第5回の $Q$ 限界処理と同じ発想）。
- **OPF = ELD + 潮流方程式 + 系統制約**（電圧・線路容量・安定度）。
  AC-OPF は**非凸**で、大域最適解の保証が難しい。
- **DC-OPF** は第4回の直流法潮流に基づき**線形計画**になる。
  高速で必ず解け、双対変数から **LMP（ノード価格）**が得られる。
  混雑がなければ全ノードで LMP は等しく ELD と一致し、
  **混雑すると価格差が生じる**。これがエリアプライスの理論的基礎である。
- **ユニットコミットメント（UC）**は二値変数を含む **MILP** で NP 困難。
  再エネにより不確実性・ランプ要求・起動停止頻度が増し、さらに難しくなる。
- **AI による高速化**の 4 アプローチ:
  ①直接予測（制約違反のリスク大）②**アクティブ制約予測**（厳密性を保てる）
  ③**warm start**（厳密性を保てる）④スクリーニング。
  **最適性は妥協できても、実行可能性は妥協できない**。
  ②③のように、最終解を厳密解法が出す構成が安全である。
- **EMS** は 状態推定 → 想定事故解析 → OPF → ELD/LFC という流れで動く。
  本講義の第4〜14回の内容がこの流れの中に位置づけられる。

### 次回への橋渡し

第14回で、本講義の理論的な内容はすべて出揃った。

第15回は**総合演習**である。実際の系統データを用いて
**潮流計算 → 安定度評価 → 需要予測 → 最適化**という一連の解析を通しで行い、
第1回から積み上げてきたものを 1 つの流れとして統合する。

沖縄本島系統をモデルに、再生可能エネルギーの導入可能量を
自分の手で評価してもらう。**本講義の到達点**である。
