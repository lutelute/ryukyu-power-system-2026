# -*- coding: utf-8 -*-
"""第13回 AI を用いた電力系統解析 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch13.py  → ../図/ch13_*.png
   GNN の集約・状態推定（WLS）・PCA 異常検知・Q 学習をすべて numpy で自作し、
   系統は IEEE 14 母線（pandapower）と沖縄 5 母線を使う。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig, build_okinawa
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Circle
import pandapower as pp
import pandapower.networks as pn

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

NET = pn.case14()
pp.runpp(NET)
EDGES = list(zip(NET.line.from_bus.values, NET.line.to_bus.values)) + \
        list(zip(NET.trafo.hv_bus.values, NET.trafo.lv_bus.values))
NB = len(NET.bus)


def spring_layout(n, edges, iters=300, seed=3):
    """簡易ばねモデルでノード座標を作る（外部ライブラリを使わない）"""
    rng = np.random.default_rng(seed)
    pos = rng.normal(0, 1, (n, 2))
    A = np.zeros((n, n))
    for i, j in edges:
        A[i, j] = A[j, i] = 1
    k = 1.0
    for it in range(iters):
        disp = np.zeros_like(pos)
        d = pos[:, None, :] - pos[None, :, :]
        dist = np.linalg.norm(d, axis=2) + 1e-9
        rep = (k ** 2 / dist ** 2)[:, :, None] * d
        disp += rep.sum(axis=1)
        att = (dist / k)[:, :, None] * d * A[:, :, None]
        disp -= att.sum(axis=1)
        step = 0.1 * (1 - it / iters)
        norm = np.linalg.norm(disp, axis=1, keepdims=True) + 1e-9
        pos += disp / norm * step
    pos -= pos.mean(axis=0)
    pos /= np.abs(pos).max()
    return pos


POS = spring_layout(NB, EDGES)


# ============================================================ 1. 系統はグラフ
def fig_graph():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.6))
    for i, j in EDGES:
        a1.plot([POS[i, 0], POS[j, 0]], [POS[i, 1], POS[j, 1]], color=C_LIGHT, lw=1.8, zorder=1)
    v = NET.res_bus.vm_pu.values
    sc = a1.scatter(POS[:, 0], POS[:, 1], c=v, cmap="RdYlGn", s=320, zorder=3,
                    edgecolors=C_GREY, linewidths=1.2, vmin=1.0, vmax=1.09)
    for i in range(NB):
        a1.text(POS[i, 0], POS[i, 1], str(i + 1), ha="center", va="center", fontsize=11, weight="bold")
    a1.axis("off"); a1.set_title("IEEE 14 母線をグラフとして描く（色は電圧）", fontsize=11)
    plt.colorbar(sc, ax=a1, shrink=0.8, label="電圧 [p.u.]")
    A = np.zeros((NB, NB))
    for i, j in EDGES:
        A[i, j] = A[j, i] = 1
    a2.imshow(A, cmap="Greys", interpolation="nearest")
    a2.set_xticks(range(0, NB, 2)); a2.set_xticklabels(range(1, NB + 1, 2), fontsize=11)
    a2.set_yticks(range(0, NB, 2)); a2.set_yticklabels(range(1, NB + 1, 2), fontsize=11)
    a2.set_xlabel("母線番号"); a2.set_ylabel("母線番号")
    dens = A.sum() / (NB * NB) * 100
    a2.set_title(f"隣接行列（非零 {dens:.1f}%）— Y_bus と同じパターン", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_graph.png"); plt.close(fig)
    OUT["graph"] = (NB, len(EDGES), dens)


# ============================================================ 2. GNN の集約
def fig_gnn():
    """4 母線の直線グラフで、1 層・2 層の伝播を数値で見せる"""
    h0 = np.array([1.0, 2.0, 0.5, 1.5])
    nb = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2]}
    Ws, Wn = 0.5, 0.5

    def layer(h):
        return np.array([Ws * h[i] + Wn * np.mean([h[j] for j in nb[i]]) for i in range(4)])

    h1 = layer(h0); h2 = layer(h1); h3 = layer(h2)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    xs = np.arange(4)
    for k, (h, c, lab) in enumerate([(h0, C_LIGHT, "入力 h⁰"), (h1, C_SEC, "1 層後 h¹"),
                                     (h2, C_MAIN, "2 層後 h²"), (h3, C_ACC, "3 層後 h³")]):
        a1.plot(xs, h, "o-", color=c, lw=2.2, ms=9, label=lab)
        if k == 0:                                    # 入力だけ数値を添える（他は近すぎて重なる）
            for i in range(4):
                a1.text(i, h[i] + 0.09, f"{h[i]:.3f}", ha="center", fontsize=11, color=c)
    a1.set_xticks(xs); a1.set_xticklabels([f"母線 {i+1}" for i in range(4)])
    a1.set_ylabel("特徴量"); a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title("1 層 = 1 ホップ。層を重ねると平均化が進む", fontsize=11)
    # 情報の到達範囲
    reach = np.zeros((4, 4))
    for L in range(1, 5):
        for i in range(4):
            for j in range(4):
                if abs(i - j) <= L:
                    reach[L - 1, j] = L if reach[L - 1, j] == 0 else reach[L - 1, j]
    a2.axis("off")
    for L in range(1, 5):
        for i in range(4):
            c = C_MAIN if abs(i - 0) <= L else "#EFECE4"
            a2.add_patch(FancyBboxPatch((0.12 + i * 0.20, 0.78 - (L - 1) * 0.20), 0.17, 0.14,
                                        boxstyle="round,pad=0.006", transform=a2.transAxes,
                                        fc=c, alpha=0.75 if abs(i) <= L else 0.3, ec=C_GREY))
            a2.text(0.205 + i * 0.20, 0.85 - (L - 1) * 0.20, f"{i+1}", ha="center", va="center",
                    fontsize=11.5, color="white" if abs(i) <= L else C_GREY, weight="bold", transform=a2.transAxes)
        a2.text(0.06, 0.85 - (L - 1) * 0.20, f"{L} 層", ha="center", va="center", fontsize=11.5,
                color=C_MAIN, transform=a2.transAxes)
    a2.text(0.5, 0.05, "母線 1 の情報が届く範囲（層数 = ホップ数）", ha="center", fontsize=11,
            color=C_MAIN, transform=a2.transAxes)
    a2.set_title("影響の届く範囲を層数で設計する", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_gnn.png"); plt.close(fig)
    OUT["gnn"] = (h1, h2, h3)


# ============================================================ 3. 過平滑化
def fig_oversmooth():
    A = np.zeros((NB, NB))
    for i, j in EDGES:
        A[i, j] = A[j, i] = 1
    deg = A.sum(axis=1)
    h = NET.res_bus.vm_pu.values.copy()
    hs = [h.copy()]
    for _ in range(12):
        h = 0.5 * h + 0.5 * (A @ h) / deg
        hs.append(h.copy())
    hs = np.array(hs)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for i in range(NB):
        a1.plot(range(len(hs)), hs[:, i], lw=1.6, alpha=0.8)
    a1.set_xlabel("層数"); a1.set_ylabel("ノードの特徴量"); a1.grid(alpha=0.3)
    a1.set_title("層を重ねると全ノードが同じ値へ", fontsize=11)
    spread = hs.std(axis=1)
    a2.plot(range(len(hs)), spread, "o-", color=C_MAIN, lw=2.4, ms=5)
    a2.set_xlabel("層数"); a2.set_ylabel("ノード間のばらつき（標準偏差）")
    a2.grid(alpha=0.3)
    a2.annotate(f"2〜4 層が実用域\n（{spread[3]/spread[0]*100:.0f}% 残る）", (3, spread[3]),
                xytext=(5.5, spread[0] * 0.7), fontsize=11.5, color=C_ACC,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.set_title("ノード間ばらつきの推移", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_oversmooth.png"); plt.close(fig)
    OUT["oversmooth"] = spread[3] / spread[0]


# ============================================================ 4. 状態推定（WLS）
def fig_state_estimation():
    """2 母線・1 状態の最小例で WLS の考え方を見せる"""
    x_true = 0.95
    rng = np.random.default_rng(7)
    sigmas = np.array([0.01, 0.03])
    zs = x_true + rng.normal(0, sigmas)
    xs = np.linspace(0.90, 1.00, 400)
    J1 = ((zs[0] - xs) / sigmas[0]) ** 2
    J2 = ((zs[1] - xs) / sigmas[1]) ** 2
    J = J1 + J2
    x_wls = np.sum(zs / sigmas ** 2) / np.sum(1 / sigmas ** 2)
    x_avg = zs.mean()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(xs, J1, color=C_SEC, lw=2, ls="--", label=f"計測1（σ=0.01）z={zs[0]:.4f}")
    a1.plot(xs, J2, color=C_WARM, lw=2, ls="--", label=f"計測2（σ=0.03）z={zs[1]:.4f}")
    a1.plot(xs, J, color=C_MAIN, lw=2.6, label="合計 J(x)")
    a1.axvline(x_wls, color=C_ACC, lw=2)
    a1.axvline(x_true, color=C_GREY, lw=1.5, ls=":")
    a1.text(x_wls + 0.002, J.max() * 0.75, f"WLS 解 {x_wls:.4f}", fontsize=11.5, color=C_ACC)
    a1.text(x_true - 0.019, J.max() * 0.55, f"真値 {x_true:.2f}", fontsize=11.5, color=C_GREY)
    a1.set_xlabel("推定する電圧 x [p.u.]"); a1.set_ylabel("目的関数 J(x)")
    a1.set_ylim(0, J.max() * 1.05); a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title("精度の良い計測を重く扱う", fontsize=11)
    errs = {"単純平均": abs(x_avg - x_true), "WLS": abs(x_wls - x_true)}
    bars = a2.bar(list(errs.keys()), [v * 1000 for v in errs.values()], color=[C_LIGHT, C_MAIN], width=0.45)
    for b, v in zip(bars, errs.values()):
        a2.text(b.get_x() + b.get_width() / 2, v * 1000 + 0.05, f"{v*1000:.2f}", ha="center", fontsize=11, weight="bold")
    a2.set_ylabel("真値からの誤差 [×0.001 p.u.]"); a2.grid(alpha=0.3, axis="y")
    a2.set_title("重み付けで誤差が小さくなる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_state_estimation.png"); plt.close(fig)
    OUT["wls"] = (zs[0], zs[1], x_wls, x_avg, x_true)


# ============================================================ 5. 不良データの検出
def fig_bad_data():
    rng = np.random.default_rng(2)
    n = 60
    x = 0.97
    z = x + rng.normal(0, 0.01, n)
    z[23] = 1.08                       # 不良データ
    x_hat = np.median(z)
    r = z - x_hat
    thr = 3 * 0.01
    fig, ax = plt.subplots(figsize=(9, 4.2))
    col = [C_ACC if abs(v) > thr else C_SEC for v in r]
    ax.bar(range(n), r, color=col)
    ax.axhline(thr, color=C_MAIN, ls="--", lw=1.5); ax.axhline(-thr, color=C_MAIN, ls="--", lw=1.5)
    ax.text(1, thr + 0.002, "検定のしきい値 3σ", fontsize=11, color=C_MAIN)
    bad = int(np.argmax(np.abs(r)))
    ax.annotate(f"不良データ（計測 {bad+1}）\n残差 {r[bad]:+.3f}", (bad, r[bad]),
                xytext=(bad + 6, r[bad] * 0.8), fontsize=11.5, color=C_ACC,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("計測番号"); ax.set_ylabel("残差 z − h(x_hat) [p.u.]"); ax.grid(alpha=0.3, axis="y")
    ax.set_title("残差の大きさで不良データを見つける（冗長な計測があるから可能）", fontsize=11.5)
    savefig(fig, "ch13_bad_data.png"); plt.close(fig)


# ============================================================ 6. PCA 異常検知
def fig_pca():
    """直流法潮流で正常データを作り、線路故障を PCA の再構成誤差で検出"""
    rng = np.random.default_rng(5)
    nl = len(NET.line)
    Xn = []
    base_p = pn.case14().load.p_mw.values.copy()
    for _ in range(400):
        net = pn.case14()
        net.load.p_mw = base_p * (1.0 + rng.normal(0, 0.12, len(base_p)))   # 負荷ごとに独立に変動
        pp.rundcpp(net)
        Xn.append(net.res_line.p_from_mw.values)
    Xn = np.array(Xn)
    mu, sd = Xn.mean(axis=0), Xn.std(axis=0) + 1e-9
    Z = (Xn - mu) / sd
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    k = 5
    P = Vt[:k].T

    def recon_err(Xa):
        Za = (Xa - mu) / sd
        return ((Za - Za @ P @ P.T) ** 2).sum(axis=1)

    e_norm = recon_err(Xn)
    thr = np.percentile(e_norm, 99)
    Xf = []
    for li in range(nl):
        for _ in range(12):
            net = pn.case14()
            net.load.p_mw = base_p * (1.0 + rng.normal(0, 0.12, len(base_p)))
            net.line.in_service[li] = False
            try:
                pp.rundcpp(net); Xf.append(net.res_line.p_from_mw.values)
            except Exception:
                pass
    Xf = np.array(Xf)
    e_f = recon_err(Xf)
    det = (e_f > thr).mean() * 100
    fp = (e_norm > thr).mean() * 100
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(np.arange(1, len(S) + 1), np.cumsum(S ** 2) / (S ** 2).sum() * 100, "o-",
            color=C_MAIN, lw=2.2, ms=5)
    a1.axvline(k, color=C_ACC, ls="--", lw=1.6)
    a1.text(k + 0.4, 60, f"{k} 主成分で\n{np.cumsum(S**2)[k-1]/(S**2).sum()*100:.1f}% 説明", fontsize=11.5, color=C_ACC)
    a1.set_xlabel("主成分の数"); a1.set_ylabel("累積寄与率 [%]"); a1.grid(alpha=0.3)
    a1.set_title("主成分数と累積寄与率", fontsize=11)
    bins = np.logspace(np.log10(max(e_norm.min(), 1e-6)), np.log10(e_f.max() * 1.2), 45)
    a2.hist(e_norm, bins=bins, color=C_SEC, alpha=0.7, label="正常")
    a2.hist(e_f, bins=bins, color=C_ACC, alpha=0.6, label="線路故障")
    a2.axvline(thr, color=C_MAIN, lw=2, ls="--", label=f"しきい値（正常の 99%）")
    a2.set_xscale("log"); a2.set_xlabel("再構成誤差（対数）"); a2.set_ylabel("度数")
    a2.grid(alpha=0.3, axis="y"); a2.legend(fontsize=11, frameon=False)
    a2.set_title(f"検出率 {det:.0f}%、誤検出 {fp:.0f}%", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_pca.png"); plt.close(fig)
    OUT["pca"] = (np.cumsum(S ** 2)[k - 1] / (S ** 2).sum() * 100, det, fp)


# ============================================================ 7. オートエンコーダの考え方
def fig_autoencoder():
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    ax.axis("off")
    layers = [(0.10, 8, "入力\n（計測値）"), (0.30, 5, "圧縮"), (0.50, 2, "潜在\n（少数の軸）"),
              (0.70, 5, "復元"), (0.90, 8, "出力\n（再構成）")]
    prev = None
    for x, n, lab in layers:
        ys = np.linspace(0.30, 0.78, n)
        c = C_ACC if n == 2 else C_SEC
        for y in ys:
            ax.add_patch(Circle((x, y), 0.016, transform=ax.transAxes, fc=c, ec="none", alpha=0.85))
        if prev is not None:
            for y0 in prev[1]:
                for y1 in ys:
                    ax.plot([prev[0], x], [y0, y1], color=C_LIGHT, lw=0.5, alpha=0.6,
                            transform=ax.transAxes, zorder=0)
        ax.text(x, 0.20, lab, ha="center", fontsize=11.5, transform=ax.transAxes)
        prev = (x, ys)
    ax.annotate("", xy=(0.90, 0.88), xytext=(0.10, 0.88), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="<->", color=C_MAIN, lw=2))
    ax.text(0.50, 0.91, "この差（再構成誤差）が大きければ「普段と違う」", ha="center",
            fontsize=11, color=C_MAIN, transform=ax.transAxes)
    ax.text(0.50, 0.06, "正常データだけで学習する → 未知の異常も検出できる", ha="center",
            fontsize=11, color=C_ACC, transform=ax.transAxes)
    ax.set_title("オートエンコーダ — 「普段の形」を覚えて、外れを測る", fontsize=12.5)
    savefig(fig, "ch13_autoencoder.png"); plt.close(fig)


# ============================================================ 8. 強化学習（電圧制御）
def fig_rl():
    """1 母線の電圧制御を Q 学習で学ぶ（状態＝電圧の離散化、行動＝Q の増減）"""
    rng = np.random.default_rng(3)
    R, X = 0.08, 0.08
    acts = np.array([-0.125, 0.0, 0.125])
    nS, nA = 21, len(acts)
    Q = np.zeros((nS, nA))
    alpha, gamma, eps = 0.2, 0.9, 0.3

    def v_of(p, q):
        return 1.0 - (R * (-p) + X * q) / 1.0

    def s_of(v):
        return int(np.clip((v - 0.90) / 0.01, 0, nS - 1))

    hist = []
    for ep in range(1500):
        p = 0.2 + 0.6 * rng.random()
        q = 0.0
        bad = 0
        for t in range(8):
            v = v_of(p, q)
            s = s_of(v)
            a = rng.integers(nA) if rng.random() < eps else int(np.argmax(Q[s]))
            q = float(np.clip(q + acts[a], -0.5, 0.5))
            v2 = v_of(p, q)
            r = 1.0 if 0.95 <= v2 <= 1.05 else -abs(v2 - 1.0) * 20
            if not (0.95 <= v2 <= 1.05):
                bad += 1
            s2 = s_of(v2)
            Q[s, a] += alpha * (r + gamma * Q[s2].max() - Q[s, a])
        hist.append(bad / 8 * 100)
        eps = max(0.02, eps * 0.998)
    hist = np.array(hist)
    w = 50
    sm = np.convolve(hist, np.ones(w) / w, mode="valid")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(np.arange(len(sm)) + w, sm, color=C_MAIN, lw=2.2)
    a1.set_xlabel("エピソード"); a1.set_ylabel("電圧逸脱の割合 [%]"); a1.grid(alpha=0.3)
    a1.set_title(f"学習で逸脱が {sm[0]:.0f}% → {sm[-1]:.1f}% に", fontsize=11)
    im = a2.imshow(Q.T, aspect="auto", cmap="RdYlGn", origin="lower",
                   extent=[0.90, 1.11, -0.5, 2.5])
    a2.set_yticks([0, 1, 2]); a2.set_yticklabels(["Q を減らす", "何もしない", "Q を増やす"])
    a2.set_xlabel("状態（電圧 [p.u.]）")
    plt.colorbar(im, ax=a2, shrink=0.8, label="Q 値")
    a2.set_title("学習された方策 — 電圧が高いなら Q を減らす", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch13_rl.png"); plt.close(fig)
    OUT["rl"] = (sm[0], sm[-1])


# ============================================================ 9. PINN（物理制約）
def fig_pinn():
    """データが少ない領域で、物理項の有無で外挿がどう変わるか"""
    rng = np.random.default_rng(9)
    # 真の関係：P = sin(δ) / X（X = 0.3）
    X_ = 0.3
    d_obs = np.concatenate([rng.uniform(0.05, 0.6, 25)])
    p_obs = np.sin(d_obs) / X_ + rng.normal(0, 0.05, len(d_obs))
    d_all = np.linspace(0, 1.5, 200)

    def fit_poly(deg, phys_w=0.0):
        A = np.vander(d_obs, deg + 1)
        Aall = np.vander(d_all, deg + 1)
        if phys_w == 0:
            c, *_ = np.linalg.lstsq(A, p_obs, rcond=None)
            return Aall @ c
        # 物理項：全域で P ≈ sin(δ)/X を弱く課す
        Ap = np.vander(d_all, deg + 1)
        target = np.sin(d_all) / X_
        Aa = np.vstack([A, phys_w * Ap])
        ba = np.concatenate([p_obs, phys_w * target])
        c, *_ = np.linalg.lstsq(Aa, ba, rcond=None)
        return Aall @ c

    y_data = fit_poly(4, 0.0)
    y_pinn = fit_poly(4, 0.35)
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.plot(d_all, np.sin(d_all) / X_, color=C_GREY, lw=2, ls=":", label="真の関係 sinδ/X（物理）")
    ax.scatter(d_obs, p_obs, s=30, color=C_SEC, zorder=5, label="観測データ（δ < 0.6 のみ）")
    ax.plot(d_all, y_data, color=C_ACC, lw=2.3, label="データだけで学習")
    ax.plot(d_all, y_pinn, color=C_MAIN, lw=2.3, label="物理項を足す（PINN）")
    ax.axvspan(0.6, 1.5, color=C_ACC, alpha=0.08)
    ax.text(0.66, 7.0, "データが無い領域", fontsize=11.5, color=C_ACC)
    ax.set_xlabel("相差角 δ [rad]"); ax.set_ylabel("送電電力 P [p.u.]")
    ax.set_ylim(0, 8); ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="upper left")
    e_data = np.abs(y_data[d_all > 0.6] - np.sin(d_all[d_all > 0.6]) / X_).mean()
    e_pinn = np.abs(y_pinn[d_all > 0.6] - np.sin(d_all[d_all > 0.6]) / X_).mean()
    ax.set_title(f"データが無い領域の誤差：データのみ {e_data:.2f} → 物理項あり {e_pinn:.2f} p.u.", fontsize=11.5)
    savefig(fig, "ch13_pinn.png"); plt.close(fig)
    OUT["pinn"] = (e_data, e_pinn)


# ============================================================ 10. AI の使いどころ（2 段構え）
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(9.8, 4.0))
    ax.axis("off")
    boxes = [("計測", "SCADA・PMU\n数秒〜数十 ms", C_BLUE, 0.02),
             ("状態推定", "WLS で今の状態を復元\nAI は初期値・高速化", C_SEC, 0.26),
             ("スクリーニング", "AI で危険な候補を絞る\n数百ケース → 数ケース", C_ACC, 0.50),
             ("厳密計算", "潮流・安定度で確認\nここは物理", C_MAIN, 0.74)]
    for name, what, c, x in boxes:
        ax.add_patch(FancyBboxPatch((x, 0.34), 0.22, 0.40, boxstyle="round,pad=0.012",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x + 0.11, 0.64, name, ha="center", fontsize=12, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.11, 0.46, what, ha="center", fontsize=11, transform=ax.transAxes)
        if x < 0.7:
            ax.annotate("", xy=(x + 0.245, 0.54), xytext=(x + 0.225, 0.54), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=C_GREY, lw=2))
    ax.text(0.50, 0.20, "AI は「速く絞る」、物理は「正しさを保証する」", ha="center",
            fontsize=12, color=C_MAIN, transform=ax.transAxes)
    ax.text(0.50, 0.09, "AI 単独で遮断器を操作しない — 説明責任と信頼性の要求", ha="center",
            fontsize=12, color=C_ACC, transform=ax.transAxes)
    savefig(fig, "ch13_pipeline.png"); plt.close(fig)


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch13_analogy.png",
        left_title="日常のたとえ", right_title="AI × 系統（実物）",
        pairs=[("噂は、隣人の話を聞いて自分の考えを更新すること", "GNN は、隣接する母線の特徴量を集約して自分の値を更新する"),
               ("1 回聞けば隣まで、2 回聞けば隣の隣まで伝わる", "1 層で 1 ホップ先、層を重ねるほど遠くまで情報が届く"),
               ("健康診断は、普段の範囲から外れたら警告を出す", "異常検知は、正常なデータだけを学び、そこからの距離で異常を測る"),
               ("自転車は、転んで（罰を受けて）バランスの取り方を覚える", "強化学習は、報酬（罰）をもとに試行錯誤で制御則を学ぶ"),
               ("物理の先生がいれば、独学より早く上達する", "PINN は、損失関数に潮流方程式（物理）を入れて学習を助ける")],
        note="この対応が頭に入っていれば、AI の仕組みは全部「日常のたとえ」に翻訳できる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch13_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("AI があれば、潮流計算や状態推定は要らなくなる",
                "AI は物理計算の上に載る道具で、絞り込みと高速化が仕事"),
               ("異常検知は、過去の事故データを学習させて作る",
                "異常検知は正常なデータだけを学ぶ。事故データが無くても作れる"),
               ("GNN は、層を深くするほど賢くなる",
                "GNN は深すぎると過平滑化が起き、かえって区別がつかなくなる")],
        note="どれも「AI に任せれば物理は要らない」という思い込みから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch13_deriv_wls_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 計測は誤差を含む',
                r"$z = h(x) + e$",
                '計測 z と状態 x を結ぶのが潮流の式。\n誤差の分散は計器ごとに違う'),
               ('② 精度の良い計測を重く扱う',
                r"$J(x) = \sum_i \dfrac{(z_i - h_i(x))^{2}}{\sigma_i^{2}}$",
                'σ が小さい計測ほど、ずれたときの\nペナルティが大きい'),
               ('③ 反復で解く',
                r"$(H^{T}R^{-1}H)\,\Delta x = H^{T}R^{-1}(z - h(x))$",
                '形は第5回のニュートン法と同じ。\n計測が未知数より多いことが前提')],
            result='状態推定は「解く」のではなく「もっともらしい値を選ぶ」')


if __name__ == "__main__":
    fig_graph(); fig_gnn(); fig_oversmooth(); fig_state_estimation(); fig_bad_data()
    fig_pca(); fig_autoencoder(); fig_rl(); fig_pinn(); fig_pipeline()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    nb, ne, dens = OUT["graph"]
    print(f"IEEE14: {nb} 母線、{ne} 枝、隣接行列の非零 {dens:.1f}%")
    h1, h2, h3 = OUT["gnn"]
    print(f"GNN 4 母線: 1 層後 {np.round(h1,3)}、2 層後 {np.round(h2,3)}")
    print(f"過平滑化: 4 層でばらつきが {OUT['oversmooth']*100:.0f}% に")
    z1, z2, xw, xa, xt = OUT["wls"]
    print(f"WLS: 計測 {z1:.4f}/{z2:.4f} → 推定 {xw:.4f}（単純平均 {xa:.4f}、真値 {xt:.2f}）")
    cum, det, fp = OUT["pca"]
    fig_derivations()
    print(f"PCA: 5 主成分で {cum:.1f}% 説明、線路故障の検出率 {det:.0f}%、誤検出 {fp:.0f}%")
    print(f"強化学習: 逸脱 {OUT['rl'][0]:.0f}% → {OUT['rl'][1]:.1f}%")
    print(f"PINN: データのみ {OUT['pinn'][0]:.2f} → 物理項あり {OUT['pinn'][1]:.2f} p.u.")
