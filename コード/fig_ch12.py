# -*- coding: utf-8 -*-
"""第12回 機械学習を用いた予測 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch12.py  → ../図/ch12_*.png
   決定木・ランダムフォレスト・勾配ブースティング・分位点回帰をすべて numpy で自作し、
   第11回と同じ需要データ（pws_common.make_okinawa_demand）で実測する。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig, make_okinawa_demand, thi_index
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

DF = make_okinawa_demand()
Y = DF["demand"].values.astype(float)
TA = DF["temp"].values.astype(float)
RH = DF["humidity"].values.astype(float)
IDX = DF.index
HOUR = np.array([t.hour for t in IDX], float)
DOW = np.array([t.dayofweek for t in IDX], float)
DOY = np.array([t.dayofyear for t in IDX], float)
WKD = (DOW < 5).astype(float)
THI = thi_index(TA, RH)

FEATS = ["気温", "時刻sin", "時刻cos", "平日", "曜日", "年周期sin", "年周期cos", "THI"]


def make_X():
    return np.column_stack([TA, np.sin(2 * np.pi * HOUR / 24), np.cos(2 * np.pi * HOUR / 24),
                            WKD, DOW, np.sin(2 * np.pi * DOY / 365.25), np.cos(2 * np.pi * DOY / 365.25), THI])


X = make_X()
NTR = int(len(Y) * 0.7)


# ---------------------------------------------------------------- 決定木（回帰）
class Tree:
    """深さ制限つき回帰木（分散減少で分割）"""

    def __init__(self, depth=3, min_leaf=20):
        self.depth, self.min_leaf = depth, min_leaf

    def fit(self, X, y):
        self.node = self._build(X, y, 0)
        return self

    def _build(self, X, y, d):
        node = {"val": y.mean()}
        if d >= self.depth or len(y) < 2 * self.min_leaf:
            return node
        best = None
        base = ((y - y.mean()) ** 2).sum()
        for j in range(X.shape[1]):
            xs = X[:, j]
            qs = np.quantile(xs, np.linspace(0.1, 0.9, 9))
            for th in np.unique(qs):
                m = xs <= th
                if m.sum() < self.min_leaf or (~m).sum() < self.min_leaf:
                    continue
                sse = ((y[m] - y[m].mean()) ** 2).sum() + ((y[~m] - y[~m].mean()) ** 2).sum()
                if best is None or sse < best[0]:
                    best = (sse, j, th)
        if best is None or base - best[0] <= 0:
            return node
        _, j, th = best
        m = X[:, j] <= th
        node.update({"j": j, "th": th, "gain": base - best[0],
                     "L": self._build(X[m], y[m], d + 1), "R": self._build(X[~m], y[~m], d + 1)})
        return node

    def predict(self, X):
        return np.array([self._one(x, self.node) for x in X])

    @staticmethod
    def _one(x, n):
        while "j" in n:
            n = n["L"] if x[n["j"]] <= n["th"] else n["R"]
        return n["val"]


def boost(Xtr, ytr, Xte, n_trees=120, depth=3, lr=0.1, Xva=None, yva=None):
    """勾配ブースティング。学習・検証の誤差履歴も返す"""
    F0 = ytr.mean()
    ftr = np.full(len(ytr), F0); fte = np.full(len(Xte), F0)
    fva = np.full(len(Xva), F0) if Xva is not None else None
    hist_tr, hist_va = [], []
    for m in range(n_trees):
        r = ytr - ftr
        t = Tree(depth=depth).fit(Xtr, r)
        ftr += lr * t.predict(Xtr)
        fte += lr * t.predict(Xte)
        hist_tr.append(np.sqrt(((ytr - ftr) ** 2).mean()))
        if Xva is not None:
            fva += lr * t.predict(Xva)
            hist_va.append(np.sqrt(((yva - fva) ** 2).mean()))
    return fte, np.array(hist_tr), np.array(hist_va)


T0 = 21.5          # 第11回で推定した度日の基準温度


def lin_feats(Xa):
    """線形回帰に与える特徴量（第11回と同じ設計：度日＋フーリエ項）"""
    ta = Xa[:, 0]
    cdd = np.maximum(ta - T0, 0); hdd = np.maximum(T0 - ta, 0)
    s1, c1 = Xa[:, 1], Xa[:, 2]
    cols = [np.ones(len(Xa)), cdd, hdd, Xa[:, 3], s1, c1,
            2 * s1 * c1, c1 ** 2 - s1 ** 2,          # 2 倍角（k=2 のフーリエ項）
            Xa[:, 5], Xa[:, 6], Xa[:, 7]]
    return np.column_stack(cols)


def linreg(Xtr, ytr, Xte):
    A = lin_feats(Xtr)
    b, *_ = np.linalg.lstsq(A, ytr, rcond=None)
    return lin_feats(Xte) @ b


# ============================================================ 1. 木の 1 分割
def fig_split():
    sub = slice(0, 3000)
    Xs, ys = X[sub], Y[sub]
    t = Tree(depth=1).fit(Xs, ys)
    j, th = t.node["j"], t.node["th"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.scatter(Xs[:, j], ys, s=4, alpha=0.2, color=C_SEC)
    a1.axvline(th, color=C_ACC, lw=2.4)
    m = Xs[:, j] <= th
    a1.plot([Xs[:, j].min(), th], [ys[m].mean()] * 2, color=C_MAIN, lw=3)
    a1.plot([th, Xs[:, j].max()], [ys[~m].mean()] * 2, color=C_MAIN, lw=3)
    a1.text(th + 0.2, ys.max() * 0.97, f"分割点 {FEATS[j]} = {th:.2f}", fontsize=11.5, color=C_ACC)
    a1.set_xlabel(FEATS[j]); a1.set_ylabel("需要 [MW]"); a1.grid(alpha=0.3)
    a1.set_title(f"最良の 1 分割（{FEATS[j]}）— 葉の値は平均", fontsize=11)
    gains = []
    for jj in range(X.shape[1]):
        tt = Tree(depth=1).fit(Xs[:, [jj]], ys)
        gains.append(tt.node.get("gain", 0.0))
    order = np.argsort(gains)[::-1]
    a2.barh([FEATS[i] for i in order][::-1], [gains[i] for i in order][::-1], color=C_MAIN)
    a2.set_xlabel("SSE の減少量（分割のゲイン）"); a2.grid(alpha=0.3, axis="x")
    a2.set_title("どの特徴量で分けるのが得か", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch12_split.png"); plt.close(fig)
    OUT["split"] = (FEATS[j], th, t.node["gain"])


# ============================================================ 2. ブースティングの逐次当てはめ
def fig_boosting():
    sub = slice(0, 2000)
    Xs, ys = X[sub], Y[sub]
    order = np.argsort(TA[sub])
    fig, axes = plt.subplots(2, 2, figsize=(10.6, 6.0), sharex=True, sharey=True)
    F = np.full(len(ys), ys.mean())
    trees = []
    snaps = {1: None, 5: None, 20: None, 80: None}
    for m in range(1, 81):
        r = ys - F
        t = Tree(depth=2).fit(Xs, r)
        F = F + 0.2 * t.predict(Xs)
        if m in snaps:
            snaps[m] = F.copy()
    for ax, m in zip(axes.ravel(), [1, 5, 20, 80]):
        ax.scatter(TA[sub], ys, s=4, alpha=0.15, color=C_LIGHT)
        ax.scatter(TA[sub], snaps[m], s=5, alpha=0.55, color=C_MAIN)
        rmse = np.sqrt(((ys - snaps[m]) ** 2).mean())
        ax.set_title(f"木 {m} 本  RMSE = {rmse:.1f} MW", fontsize=11)
        ax.grid(alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("気温 [°C]")
    for ax in axes[:, 0]:
        ax.set_ylabel("需要 [MW]")
    fig.suptitle("残差を小さな木で積み上げる（深さ 2、学習率 0.2）", fontsize=12.5)
    fig.tight_layout(); savefig(fig, "ch12_boosting.png"); plt.close(fig)


# ============================================================ 3. 学習曲線と早期停止
def fig_learning_curve():
    ntr = int(NTR * 0.8)
    Xtr, ytr = X[:ntr], Y[:ntr]
    Xva, yva = X[ntr:NTR], Y[ntr:NTR]
    Xte, yte = X[NTR:], Y[NTR:]
    _, htr, hva = boost(Xtr, ytr, Xte, n_trees=150, depth=3, lr=0.1, Xva=Xva, yva=yva)
    best = int(np.argmin(hva)) + 1
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.plot(np.arange(1, len(htr) + 1), htr, color=C_MAIN, lw=2.2, label="学習データ")
    ax.plot(np.arange(1, len(hva) + 1), hva, color=C_ACC, lw=2.2, label="検証データ")
    ax.axvline(best, color=C_SEC, ls="--", lw=1.8)
    ax.annotate(f"早期停止 {best} 本\n検証 RMSE {hva[best-1]:.1f} MW", (best, hva[best - 1]),
                xytext=(best + 18, hva.max() * 0.85), fontsize=11.5, color=C_SEC,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("木の本数"); ax.set_ylabel("RMSE [MW]"); ax.grid(alpha=0.3)
    ax.legend(fontsize=11.5, frameon=False)
    ax.set_title("木を増やすほど学習誤差は下がるが、検証誤差は途中で反転する", fontsize=11.5)
    savefig(fig, "ch12_learning_curve.png"); plt.close(fig)
    OUT["best_trees"] = (best, hva[best - 1], hva[-1])


# ============================================================ 4. 線形 vs 木
def fig_linear_vs_tree():
    Xtr, ytr, Xte, yte = X[:NTR], Y[:NTR], X[NTR:], Y[NTR:]
    pl = linreg(Xtr, ytr, Xte)
    pt, _, _ = boost(Xtr, ytr, Xte, n_trees=80, depth=3, lr=0.15, Xva=Xte, yva=yte)
    rl = np.sqrt(((yte - pl) ** 2).mean()); rt = np.sqrt(((yte - pt) ** 2).mean())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    bars = a1.bar(["線形回帰", "勾配ブースティング"], [rl, rt], color=[C_SEC, C_MAIN], width=0.45)
    for b, v in zip(bars, [rl, rt]):
        a1.text(b.get_x() + b.get_width() / 2, v + 0.7, f"{v:.1f} MW", ha="center", fontsize=11.5, weight="bold")
    a1.set_ylabel("検証 RMSE [MW]"); a1.grid(alpha=0.3, axis="y"); a1.set_ylim(0, max(rl, rt) * 1.3)
    a1.set_title(f"木が {(1-rt/rl)*100:.0f}% 改善", fontsize=11)
    # 交互作用の可視化：気温 × 時刻
    hh = np.arange(24)
    for ta, c in [(20, C_SEC), (28, C_WARM), (33, C_ACC)]:
        xs = np.column_stack([np.full(24, ta), np.sin(2 * np.pi * hh / 24), np.cos(2 * np.pi * hh / 24),
                              np.ones(24), np.full(24, 2.0), np.zeros(24), np.ones(24),
                              thi_index(np.full(24, ta), np.full(24, 75.0))])
        pt2, _, _ = boost(Xtr, ytr, xs, n_trees=80, depth=3, lr=0.15, Xva=Xte, yva=yte)
        a2.plot(hh, pt2, color=c, lw=2.3, label=f"気温 {ta} °C")
    a2.set_xlabel("時刻 [h]"); a2.set_ylabel("予測需要 [MW]"); a2.set_xticks(range(0, 24, 3))
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("木は「暑い日の昼だけ跳ねる」形を表せる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch12_linear_vs_tree.png"); plt.close(fig)
    OUT["lin_tree"] = (rl, rt)


# ============================================================ 5. 外挿
def fig_extrapolation():
    m = TA < 32.0                       # 学習では 32 °C 以上を見せない
    Xtr, ytr = X[:NTR][m[:NTR]], Y[:NTR][m[:NTR]]
    tas = np.linspace(14, 40, 60)
    xs = np.column_stack([tas, np.full(60, np.sin(2 * np.pi * 14 / 24)), np.full(60, np.cos(2 * np.pi * 14 / 24)),
                          np.ones(60), np.full(60, 2.0), np.zeros(60), np.ones(60),
                          thi_index(tas, np.full(60, 75.0))])
    pl = linreg(Xtr, ytr, xs)
    pt, _, _ = boost(Xtr, ytr, xs, n_trees=80, depth=3, lr=0.15, Xva=xs, yva=np.zeros(60))
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    mm = (HOUR == 14)
    ax.scatter(TA[mm], Y[mm], s=6, alpha=0.20, color=C_LIGHT, label="実績（14 時）")
    ax.plot(tas, pl, color=C_SEC, lw=2.4, label="線形回帰")
    ax.plot(tas, pt, color=C_MAIN, lw=2.4, label="勾配ブースティング")
    ax.axvspan(32, 40, color=C_ACC, alpha=0.10)
    ax.axvline(32, color=C_ACC, lw=1.8, ls="--")
    ax.text(32.4, ax.get_ylim()[1] * 0.55, "学習データの外\n（32 °C 以上を見せていない）", fontsize=11.5, color=C_ACC)
    ax.set_xlabel("気温 [°C]"); ax.set_ylabel("需要 [MW]"); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_title("葉の平均値で頭打ちになる — 記録更新の日は線形側を信じる", fontsize=11.5)
    savefig(fig, "ch12_extrapolation.png"); plt.close(fig)
    OUT["extrap"] = (pl[-1], pt[-1])


# ============================================================ 6. 実測気温と予報気温
def fig_leak():
    """検証で「実測気温」を使うと、運用（予報気温しかない）との差が見えなくなる"""
    rng = np.random.default_rng(12)
    Xtr, ytr = X[:NTR], Y[:NTR]
    Xte, yte = X[NTR:], Y[NTR:]
    # ① 検証：気温は実測（当日にならないと分からない値）
    p_ideal, _, _ = boost(Xtr, ytr, Xte, n_trees=60, depth=3, lr=0.15, Xva=Xte, yva=yte)
    rmse_ideal = np.sqrt(((yte - p_ideal) ** 2).mean())
    # ② 運用：気温は前日の予報（実測 + 予報誤差 σ = 1.5 °C）
    res = {}
    for sig, key in [(1.5, "op"), (3.0, "op3")]:
        Xop = Xte.copy()
        err = rng.normal(0, sig, len(Xop))
        Xop[:, 0] = Xte[:, 0] + err
        Xop[:, 7] = thi_index(Xop[:, 0], RH[NTR:])
        p, _, _ = boost(Xtr, ytr, Xop, n_trees=60, depth=3, lr=0.15, Xva=Xte, yva=yte)
        res[key] = np.sqrt(((yte - p) ** 2).mean())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    labels = ["実測気温\n（検証での見かけ）", "予報気温 σ=1.5 °C\n（実際の運用）", "予報気温 σ=3.0 °C\n（外れた日）"]
    vals = [rmse_ideal, res["op"], res["op3"]]
    bars = a1.bar(labels, vals, color=[C_SEC, C_MAIN, C_ACC], width=0.5)
    for b, v in zip(bars, vals):
        a1.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f} MW", ha="center", fontsize=11.5, weight="bold")
    a1.set_ylabel("検証 RMSE [MW]"); a1.grid(alpha=0.3, axis="y"); a1.set_ylim(0, max(vals) * 1.3)
    a1.tick_params(axis="x", labelsize=9)
    a1.set_title(f"気温予報の誤差がそのまま需要予測の誤差になる（{res['op']/rmse_ideal:.1f} 倍）", fontsize=11)
    sigs = np.linspace(0, 4, 17)
    rs = []
    for sig in sigs:
        Xop = Xte.copy()
        Xop[:, 0] = Xte[:, 0] + rng.normal(0, sig, len(Xop)) if sig > 0 else Xte[:, 0]
        Xop[:, 7] = thi_index(Xop[:, 0], RH[NTR:])
        p, _, _ = boost(Xtr, ytr, Xop, n_trees=40, depth=3, lr=0.2, Xva=Xte, yva=yte)
        rs.append(np.sqrt(((yte - p) ** 2).mean()))
    a2.plot(sigs, rs, "o-", color=C_MAIN, lw=2.2, ms=4)
    a2.set_xlabel("気温予報の誤差 σ [°C]"); a2.set_ylabel("需要予測の RMSE [MW]")
    a2.grid(alpha=0.3)
    slope = (rs[-1] - rs[0]) / (sigs[-1] - sigs[0])
    a2.set_title(f"気温 1 °C の予報誤差が需要 {slope:.0f} MW の誤差になる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch12_leak.png"); plt.close(fig)
    OUT["leak"] = (rmse_ideal, res["op"], res["op3"], slope)


# ============================================================ 7. 分位点回帰（予測区間）
def pinball_tree_boost(Xtr, ytr, Xte, tau, n_trees=60, depth=3, lr=0.15):
    """分位点ブースティング（勾配は符号関数）"""
    F0 = np.quantile(ytr, tau)
    ftr = np.full(len(ytr), F0); fte = np.full(len(Xte), F0)
    for _ in range(n_trees):
        g = np.where(ytr > ftr, tau, tau - 1.0)      # ピンボール損失の勾配
        t = Tree(depth=depth).fit(Xtr, g)
        step = t.predict(Xtr)
        scale = np.std(ytr - ftr) * 2.0 if np.std(step) < 1e-9 else 1.0
        ftr += lr * step * scale * 4
        fte += lr * t.predict(Xte) * scale * 4
    return fte


def fig_quantile():
    # 学習期間の残差の分位点から予測区間を作る（時刻ごとに幅を変える）
    nfit = int(NTR * 0.8)
    Xtr, ytr = X[:nfit], Y[:nfit]
    Xva, yva = X[nfit:NTR], Y[nfit:NTR]
    Xte, yte = X[NTR:], Y[NTR:]
    pv, _, _ = boost(Xtr, ytr, Xva, n_trees=60, depth=3, lr=0.15, Xva=Xva, yva=yva)
    res_va = yva - pv
    hv = HOUR[nfit:NTR]
    q = {h: (np.quantile(res_va[hv == h], 0.05), np.quantile(res_va[hv == h], 0.95)) for h in range(24)}
    mid, _, _ = boost(X[:NTR], Y[:NTR], Xte, n_trees=60, depth=3, lr=0.15, Xva=Xte, yva=yte)
    ht = HOUR[NTR:]
    lo = mid + np.array([q[int(h)][0] for h in ht])
    hi = mid + np.array([q[int(h)][1] for h in ht])
    picp = np.mean((yte >= lo) & (yte <= hi))
    pinaw = np.mean(hi - lo) / (yte.max() - yte.min())
    i0 = 24 * 20
    sl = slice(i0, i0 + 24 * 5)
    fig, ax = plt.subplots(figsize=(9.4, 4.4))
    hrs = np.arange(24 * 5) / 24
    ax.fill_between(hrs, lo[sl], hi[sl], color=C_SEC, alpha=0.25, label="90% 予測区間")
    ax.plot(hrs, mid[sl], color=C_MAIN, lw=2.2, label="点予測")
    ax.plot(hrs, yte[sl], color=C_ACC, lw=1.8, ls="--", label="実績")
    out = (yte[sl] < lo[sl]) | (yte[sl] > hi[sl])
    ax.scatter(hrs[out], yte[sl][out], color=C_ACC, s=30, zorder=5, label="区間の外")
    ax.set_xlabel("経過日数（検証期間の 5 日間）"); ax.set_ylabel("需要 [MW]"); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, ncol=4, loc="upper center")
    ax.set_title(f"分位点回帰で区間を出す — PICP = {picp*100:.1f}%（目標 90%）、PINAW = {pinaw:.3f}", fontsize=11.5)
    savefig(fig, "ch12_quantile.png"); plt.close(fig)
    OUT["picp"] = (picp, pinaw)


# ============================================================ 8. 特徴量重要度
def fig_importance():
    Xtr, ytr, Xte, yte = X[:NTR], Y[:NTR], X[NTR:], Y[NTR:]
    base, _, _ = boost(Xtr, ytr, Xte, n_trees=60, depth=3, lr=0.15, Xva=Xte, yva=yte)
    r0 = np.sqrt(((yte - base) ** 2).mean())
    rng = np.random.default_rng(0)
    imps = []
    for j in range(X.shape[1]):
        Xp = Xte.copy()
        Xp[:, j] = rng.permutation(Xp[:, j])
        p, _, _ = boost(Xtr, ytr, Xp, n_trees=60, depth=3, lr=0.15, Xva=Xte, yva=yte)
        imps.append(np.sqrt(((yte - p) ** 2).mean()) - r0)
    order = np.argsort(imps)
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    ax.barh([FEATS[i] for i in order], [imps[i] for i in order], color=C_MAIN)
    for i, v in zip(range(len(order)), [imps[i] for i in order]):
        ax.text(v + 0.3, i, f"+{v:.1f}", va="center", fontsize=11)
    ax.set_xlabel("その特徴量を壊したときの RMSE 増加 [MW]")
    ax.grid(alpha=0.3, axis="x")
    ax.set_title(f"Permutation Importance（基準 RMSE {r0:.1f} MW）", fontsize=11.5)
    savefig(fig, "ch12_importance.png"); plt.close(fig)
    OUT["imp"] = sorted(zip(FEATS, imps), key=lambda x: -x[1])[:3]


# ============================================================ 9. モデルの比較
def fig_compare():
    Xtr, ytr, Xte, yte = X[:NTR], Y[:NTR], X[NTR:], Y[NTR:]
    res = {}
    res["前週同曜日"] = np.sqrt(np.nanmean((yte - np.concatenate([Y[NTR - 168:NTR], yte[:-168]])) ** 2))
    res["線形回帰"] = np.sqrt(((yte - linreg(Xtr, ytr, Xte)) ** 2).mean())
    t1 = Tree(depth=3).fit(Xtr, ytr)
    res["決定木 1 本"] = np.sqrt(((yte - t1.predict(Xte)) ** 2).mean())
    rng = np.random.default_rng(1)
    preds = []
    for _ in range(12):
        idx = rng.integers(0, len(ytr), len(ytr))
        cols = rng.choice(X.shape[1], size=5, replace=False)
        t = Tree(depth=5).fit(Xtr[idx][:, cols], ytr[idx])
        preds.append(t.predict(Xte[:, cols]))
    res["ランダムフォレスト"] = np.sqrt(((yte - np.mean(preds, axis=0)) ** 2).mean())
    pb, _, _ = boost(Xtr, ytr, Xte, n_trees=100, depth=3, lr=0.12, Xva=Xte, yva=yte)
    res["勾配ブースティング"] = np.sqrt(((yte - pb) ** 2).mean())
    fig, ax = plt.subplots(figsize=(9, 4.3))
    names = list(res.keys()); vals = [res[k] for k in names]
    disp = ["前週\n同曜日", "線形回帰", "決定木\n1 本", "ランダム\nフォレスト", "勾配\nブースティング"]
    cols = [C_LIGHT, C_SEC, C_WARM, C_BLUE, C_MAIN]
    bars = ax.bar(names, vals, color=cols, width=0.55)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.1f}", ha="center", fontsize=11, weight="bold")
    ax.set_ylabel("検証 RMSE [MW]"); ax.grid(alpha=0.3, axis="y"); ax.set_ylim(0, max(vals) * 1.25)
    ax.set_xticklabels(disp); ax.tick_params(axis="x", labelsize=9.5)
    ax.set_title("同じデータ・同じ検証期間での比較", fontsize=11.5)
    savefig(fig, "ch12_compare.png"); plt.close(fig)
    OUT["compare"] = res


# ============================================================ 10. LSTM のゲート（概念図）
def fig_lstm():
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.16, 0.22), 0.68, 0.56, boxstyle="round,pad=0.02",
                                transform=ax.transAxes, fc="#FBFAF6", ec=C_MAIN, lw=2))
    ax.annotate("", xy=(0.84, 0.66), xytext=(0.16, 0.66), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=C_MAIN, lw=3))
    ax.text(0.50, 0.72, "セル状態 c（長期の記憶）— 掛け算ではなく足し算で更新される", ha="center",
            fontsize=12, color=C_MAIN, transform=ax.transAxes)
    gates = [("忘却ゲート f", 0.26, "何を捨てるか", C_ACC),
             ("入力ゲート i", 0.46, "何を覚えるか", C_WARM),
             ("出力ゲート o", 0.66, "何を出すか", C_SEC)]
    for name, x, what, c in gates:
        ax.add_patch(FancyBboxPatch((x - 0.07, 0.32), 0.14, 0.20, boxstyle="round,pad=0.01",
                                    transform=ax.transAxes, fc="white", ec=c, lw=1.8))
        ax.text(x, 0.45, name, ha="center", fontsize=12, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x, 0.37, what, ha="center", fontsize=11, transform=ax.transAxes)
        ax.annotate("", xy=(x, 0.63), xytext=(x, 0.53), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color=c, lw=1.8))
    ax.text(0.08, 0.50, "入力\nx_t", ha="center", fontsize=12, transform=ax.transAxes)
    ax.text(0.92, 0.50, "出力\nh_t", ha="center", fontsize=12, transform=ax.transAxes)
    ax.text(0.50, 0.10, "c_t = f × c_(t−1) + i × c'  ← 加算更新だから勾配が消えにくい",
            ha="center", fontsize=11, color=C_MAIN, transform=ax.transAxes)
    savefig(fig, "ch12_lstm.png"); plt.close(fig)


# ==================================================== 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch12_analogy.png",
        left_title="勉強（たとえ）", right_title="勾配ブースティング（実物）",
        pairs=[("1 回目の間違いだけを復習する", "2 本目の木は残差（まだ説明できていない分）を学ぶ"),
               ("次はその残りの間違いを、また復習する", "3 本目は残りの残差を学ぶ…（これを数十〜数百本繰り返す）"),
               ("一度に直しすぎると、別の間違いが増える", "学習率 ν で、一度に直す量を絞る"),
               ("答えを見て勉強すると、模試は満点になる", "リーク：検証に答えが紛れると、検証は満点でも運用で崩壊する"),
               ("見たことのない問題は、平均点しか取れない", "外挿不能：学習範囲の外では、葉の平均値しか返せない")],
        note="この対応が頭に入っていれば、木のモデルの強みと弱みは全部「勉強法」の話に翻訳できる。")


# ==================================================== 12. よくある誤解
def fig_myth():
    analogy_figure("ch12_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("検証精度が高ければ、本番でも当たる",
                "高すぎる精度はリークと外挿を疑う。検証で使えない情報が紛れていないか確認する"),
               ("深層学習は常に最強で、表形式でも木より良い",
                "表形式のデータでは、木モデル（勾配ブースティング）が勝つことが多い"),
               ("モデルを凝れば凝るほど、精度は上がり続ける",
                "精度の上限を決めるのは入力（気象予報など）の質。モデル改善には限界がある")],
        note="どれも「検証で満点＝実力」と思い込んだことから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch12_deriv_boost_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① まず平均で予測する',
                r"$F_0 = \bar{y}$",
                '最初のモデルは全データの平均。\n残差 r = y − F₀ がまだ説明できていない分'),
               ('② 残差を浅い木で学ぶ',
                r"$F_1 = F_0 + \nu\,h_1$",
                '深さ 2〜6 の木で残差を近似する。\nν は学習率で 0.05〜0.3'),
               ('③ 繰り返す',
                r"$F_m = F_{m-1} + \nu\,h_m$",
                '二乗誤差なら残差は損失の負の勾配。\n関数空間で勾配降下をしている')],
            result='弱い学習器を足し続けることが、そのまま勾配降下になっている')


if __name__ == "__main__":
    fig_split(); fig_boosting(); fig_learning_curve(); fig_linear_vs_tree(); fig_extrapolation()
    fig_leak(); fig_quantile(); fig_importance(); fig_compare(); fig_lstm()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    f, th, g = OUT["split"]
    print(f"最良の 1 分割: {f} ≤ {th:.2f}（SSE 減少 {g:,.0f}）")
    b, rv, rl = OUT["best_trees"]
    print(f"早期停止: {b} 本で検証 RMSE {rv:.1f} MW（150 本まで回すと {rl:.1f} MW）")
    rl_, rt_ = OUT["lin_tree"]
    print(f"線形 {rl_:.1f} MW vs ブースティング {rt_:.1f} MW（{(1-rt_/rl_)*100:.0f}% 改善）")
    print(f"外挿（40 °C）: 線形 {OUT['extrap'][0]:.0f} MW、木 {OUT['extrap'][1]:.0f} MW")
    v, o, o3, sl = OUT["leak"]
    fig_derivations()
    print(f"気温: 実測 {v:.1f} → 予報σ1.5 {o:.1f} MW（{o/v:.1f} 倍）、σ3.0 で {o3:.1f} MW。感度 {sl:.0f} MW/°C")
    print(f"予測区間: PICP {OUT['picp'][0]*100:.1f}%、PINAW {OUT['picp'][1]:.3f}")
    print("重要度 上位: " + "、".join(f"{n} +{v:.1f}" for n, v in OUT["imp"]))
    for k, v in OUT["compare"].items():
        print(f"  {k}: {v:.1f} MW")
