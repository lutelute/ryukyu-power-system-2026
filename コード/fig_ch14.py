# -*- coding: utf-8 -*-
"""第14回 系統最適化と市場 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch14.py  → ../図/ch14_*.png
   等 λ 法・メリットオーダー・DC-OPF・LMP をすべて自作の求解器で実計算する。
   DC-OPF は scipy.optimize.linprog（無ければ自前の反復）で解く。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

# 発電機（千円/h の費用曲線 C = a + bP + cP^2、P は MW）
GENS = [("石炭 A", 500.0, 8.0, 0.020, 60.0, 400.0),
        ("LNG B", 300.0, 12.0, 0.012, 40.0, 350.0),
        ("石油 C", 200.0, 16.0, 0.008, 20.0, 250.0)]


def eld(D, gens=GENS, with_limits=True):
    """等 λ 法（上下限つき）。λ を二分法で探す"""
    def total(lam):
        p = []
        for _, a, b, c, pmin, pmax in gens:
            pi = (lam - b) / (2 * c)
            if with_limits:
                pi = min(max(pi, pmin), pmax)
            p.append(pi)
        return np.array(p)
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if total(mid).sum() < D:
            lo = mid
        else:
            hi = mid
    lam = (lo + hi) / 2
    p = total(lam)
    cost = sum(a + b * pi + c * pi ** 2 for (_, a, b, c, _, _), pi in zip(gens, p))
    return p, lam, cost


# ============================================================ 1. 費用曲線と限界費用
def fig_cost_curves():
    P = np.linspace(0, 400, 300)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for (name, a, b, c, pmin, pmax), col in zip(GENS, [C_MAIN, C_SEC, C_ACC]):
        m = (P >= pmin) & (P <= pmax)
        a1.plot(P[m], (a + b * P[m] + c * P[m] ** 2) / 1000, color=col, lw=2.4, label=name)
        a2.plot(P[m], b + 2 * c * P[m], color=col, lw=2.4, label=f"{name}: λ = {b} + {2*c:.3f} P")
    a1.set_xlabel("出力 P [MW]"); a1.set_ylabel("費用 C(P) [百万円/h]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title("費用曲線（上に凸でなく、下に凸）", fontsize=11)
    a2.set_xlabel("出力 P [MW]"); a2.set_ylabel("限界費用 dC/dP [千円/MWh]")
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("限界費用は右上がりの直線", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_cost_curves.png"); plt.close(fig)


# ============================================================ 2. 等 λ 法
def fig_equal_lambda():
    D = 600.0
    p, lam, cost = eld(D)
    P = np.linspace(0, 400, 300)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.4))
    # 石炭 A・LNG B は λ 付近でほぼ同じ出力になり交点が重なるので、ラベルを上下に振り分ける。
    # 石炭 A を上に出すと λ の破線・「システム λ = …」の文字と衝突するので、両方とも右下（曲線の外側）へ出す
    offsets = [(10, -14), (10, -34), (6, -14)]
    for (name, a, b, c, pmin, pmax), col, pi, off in zip(GENS, [C_MAIN, C_SEC, C_ACC], p, offsets):
        m = (P >= pmin) & (P <= pmax)
        a1.plot(P[m], b + 2 * c * P[m], color=col, lw=2.4, label=name)
        a1.scatter([pi], [b + 2 * c * pi], color=col, s=90, zorder=5)
        a1.annotate(f"{pi:.0f} MW", (pi, b + 2 * c * pi), textcoords="offset points",
                    xytext=off, fontsize=11.5, color=col, weight="bold")
    a1.axhline(lam, color=C_WARM, lw=2.4, ls="--")
    a1.text(5, lam + 0.5, f"システム λ = {lam:.2f} 千円/MWh", fontsize=12, color=C_WARM, weight="bold")
    a1.set_xlabel("出力 P [MW]"); a1.set_ylabel("限界費用 [千円/MWh]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False, loc="upper left")
    a1.set_title(f"需要 {D:.0f} MW を等 λ で配分", fontsize=11)
    # 均等配分との比較
    peq = np.full(3, D / 3)
    ceq = sum(a + b * pi + c * pi ** 2 for (_, a, b, c, _, _), pi in zip(GENS, peq))
    names = ["最適配分\n（等 λ 法）", "均等配分\n（各 200 MW）"]
    vals = [cost / 1000, ceq / 1000]
    bars = a2.bar(names, vals, color=[C_MAIN, C_LIGHT], width=0.45)
    for b_, v in zip(bars, vals):
        a2.text(b_.get_x() + b_.get_width() / 2, v + 0.05, f"{v:.2f}", ha="center", fontsize=11.5, weight="bold")
    a2.set_ylabel("総費用 [百万円/h]"); a2.grid(alpha=0.3, axis="y")
    a2.set_ylim(0, max(vals) * 1.2)
    diff = (ceq - cost)
    a2.set_title(f"差は {diff:.0f} 千円/h ＝ 年 {diff*8760/1e5:.1f} 億円", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_equal_lambda.png"); plt.close(fig)
    OUT["eld"] = (p, lam, cost, ceq, diff)


# ============================================================ 3. λ の反復
def fig_lambda_iteration():
    D = 600.0
    lams, sums = [], []
    lo, hi = 0.0, 60.0
    for k in range(12):
        mid = (lo + hi) / 2
        p = np.array([min(max((mid - b) / (2 * c), pmin), pmax) for _, a, b, c, pmin, pmax in GENS])
        lams.append(mid); sums.append(p.sum())
        if p.sum() < D:
            lo = mid
        else:
            hi = mid
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(range(1, len(lams) + 1), lams, "o-", color=C_MAIN, lw=2.2, ms=5)
    a1.axhline(OUT["eld"][1], color=C_ACC, ls="--", lw=1.6)
    a1.text(6, OUT["eld"][1] + 0.6, f"収束値 {OUT['eld'][1]:.2f}", fontsize=11.5, color=C_ACC)
    a1.set_xlabel("反復回数"); a1.set_ylabel("λ [千円/MWh]"); a1.grid(alpha=0.3)
    a1.set_title("λ を二分法で探す", fontsize=11)
    a2.plot(range(1, len(sums) + 1), sums, "o-", color=C_SEC, lw=2.2, ms=5)
    a2.axhline(D, color=C_ACC, ls="--", lw=1.6)
    a2.text(6, D + 12, f"需要 {D:.0f} MW", fontsize=11.5, color=C_ACC)
    a2.set_xlabel("反復回数"); a2.set_ylabel("発電量の合計 [MW]"); a2.grid(alpha=0.3)
    a2.set_title("合計が需要に一致する λ が答え", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_lambda_iteration.png"); plt.close(fig)


# ============================================================ 4. 需要に対する λ と配分
def fig_dispatch_curve():
    Ds = np.arange(150, 1000, 5.0)
    ps, lams = [], []
    for D in Ds:
        p, lam, _ = eld(D)
        ps.append(p); lams.append(lam)
    ps = np.array(ps); lams = np.array(lams)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    a1.stackplot(Ds, ps.T, colors=[C_MAIN, C_SEC, C_ACC], labels=[g[0] for g in GENS], alpha=0.85)
    a1.plot(Ds, Ds, color=C_GREY, lw=1.2, ls=":")
    a1.set_xlabel("需要 [MW]"); a1.set_ylabel("各機の出力 [MW]")
    a1.legend(fontsize=11, frameon=False, loc="upper left"); a1.grid(alpha=0.3)
    a1.set_title("需要が増えると高い機が入ってくる", fontsize=11)
    a2.plot(Ds, lams, color=C_MAIN, lw=2.6)
    for _, a, b, c, pmin, pmax in GENS:
        a2.axhline(b, color=C_LIGHT, ls=":", lw=1.2)
    a2.set_xlabel("需要 [MW]"); a2.set_ylabel("システム λ [千円/MWh]")
    a2.grid(alpha=0.3)
    a2.set_title("λ は需要の増加とともに階段状に上がる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_dispatch_curve.png"); plt.close(fig)
    OUT["lam_range"] = (lams.min(), lams.max())


# ============================================================ 5. メリットオーダー
def fig_merit_order():
    units = [("再エネ・原子力", 400, 2.0, C_SEC), ("石炭", 400, 8.0, C_MAIN),
             ("LNG", 350, 13.0, C_WARM), ("石油", 250, 30.0, C_ACC)]
    D = 900.0
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    x = 0.0
    price = 0.0
    for name, cap, mc, col in units:
        used = min(cap, max(D - x, 0))
        ax.add_patch(Rectangle((x, 0), cap, mc, fc=col, alpha=0.35, ec=col, lw=1.5))
        if used > 0:
            ax.add_patch(Rectangle((x, 0), used, mc, fc=col, alpha=0.85, ec=col, lw=1.5))
            price = mc
        ax.text(x + cap / 2, mc + 0.8, f"{name}\n{mc:.0f} 円/kWh", ha="center", fontsize=11, color=col)
        x += cap
    ax.axvline(D, color=C_MAIN, lw=2.6)
    ax.text(D + 12, 26, f"需要 {D:.0f} MW", fontsize=11, color=C_MAIN, weight="bold")
    ax.axhline(price, color=C_ACC, lw=2, ls="--")
    # 文字を底上げした分、1 行だと LNG のラベル（y がほぼ同じ）と重なるので 2 行にして幅を抑える
    ax.text(20, price + 0.7, f"約定価格 {price:.0f} 円/kWh\n（最後の 1 台の限界費用）",
            fontsize=12, color=C_ACC, weight="bold", va="bottom")
    ax.set_xlabel("累積の供給力 [MW]"); ax.set_ylabel("限界費用 [円/kWh]")
    ax.set_xlim(0, x); ax.set_ylim(0, 36); ax.grid(alpha=0.3, axis="y")
    ax.set_title("メリットオーダー — 安い順に積み上げ、需要と交わる点が価格", fontsize=11.5)
    savefig(fig, "ch14_merit_order.png"); plt.close(fig)
    OUT["merit"] = price


# ============================================================ 6. 需要と価格
def fig_price_curve():
    units = [(400, 2.0), (400, 8.0), (350, 13.0), (250, 30.0)]
    Ds = np.arange(50, 1400, 5.0)
    prices = []
    for D in Ds:
        x, p = 0.0, 0.0
        for cap, mc in units:
            if D > x:
                p = mc
            x += cap
        prices.append(p)
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    ax.step(Ds, prices, where="post", color=C_MAIN, lw=2.6)
    for lab, d in [("軽負荷の夜", 300), ("平常", 700), ("猛暑日のピーク", 1250)]:
        i = int(np.argmin(np.abs(Ds - d)))
        ax.scatter([d], [prices[i]], color=C_ACC, s=80, zorder=5)
        ax.annotate(f"{lab}\n{prices[i]:.0f} 円/kWh", (d, prices[i]), textcoords="offset points",
                    xytext=(-20, 12), fontsize=11, color=C_ACC)
    ax.set_xlabel("需要 [MW]"); ax.set_ylabel("約定価格 [円/kWh]")
    ax.grid(alpha=0.3); ax.set_ylim(0, 36)
    ax.set_title("需要が高い電源まで届くと、価格は階段状に跳ねる", fontsize=11.5)
    savefig(fig, "ch14_price_curve.png"); plt.close(fig)


# ============================================================ 7. 炭素価格
def fig_carbon():
    coal = (5.5, 0.86)      # 燃料費 [円/kWh], 排出 [kg-CO2/kWh]
    lng = (11.0, 0.37)
    p = np.linspace(0, 20000, 400)
    c_coal = coal[0] + p / 1000 * coal[1]
    c_lng = lng[0] + p / 1000 * lng[1]
    pstar = (lng[0] - coal[0]) / (coal[1] - lng[1]) * 1000
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.plot(p, c_coal, color=C_MAIN, lw=2.6, label=f"石炭（燃料 {coal[0]} 円/kWh、{coal[1]} kg-CO₂/kWh）")
    ax.plot(p, c_lng, color=C_SEC, lw=2.6, label=f"LNG（燃料 {lng[0]} 円/kWh、{lng[1]} kg-CO₂/kWh）")
    ax.scatter([pstar], [coal[0] + pstar / 1000 * coal[1]], color=C_ACC, s=100, zorder=5)
    # relpos でテキスト左上から矢印を出す。文字を底上げすると 2 行のテキストの上に
    # 矢印が突き刺さって見えるうえ、下に置くと凡例（lower right）と重なるので
    # 凡例より上、両曲線より下のすき間に置く
    ax.annotate(f"逆転する炭素価格\n{pstar:,.0f} 円/t-CO2", (pstar, coal[0] + pstar / 1000 * coal[1]),
                xytext=(pstar + 2400, 12.0), fontsize=12, color=C_ACC, weight="bold",
                va="top", arrowprops=dict(arrowstyle="->", color=C_GREY, relpos=(0, 1)))
    ax.axvspan(pstar, 20000, color=C_SEC, alpha=0.08)
    ax.text(pstar + 1200, 22, "LNG の方が安い", fontsize=11.5, color=C_SEC)
    ax.text(1000, 22, "石炭の方が安い", fontsize=11.5, color=C_MAIN)
    ax.set_xlabel("炭素価格 [円/t-CO₂]"); ax.set_ylabel("発電の限界費用 [円/kWh]")
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="lower right")
    savefig(fig, "ch14_carbon.png"); plt.close(fig)
    OUT["carbon"] = pstar


# ============================================================ 8. DC-OPF と LMP（3 母線）
def dcopf(cap12=None, D3=300.0):
    """3 母線・3 線路の DC-OPF を素朴な列挙で解く（教材用）
       母線1：安い電源、母線2：高い電源、母線3：需要
    """
    b1 = (8.0, 0.010, 0.0, 500.0)      # b, c, Pmin, Pmax
    b2 = (18.0, 0.010, 0.0, 500.0)
    x12, x13, x23 = 0.20, 0.20, 0.20
    best = None
    for p1 in np.arange(0, 500.1, 0.5):
        p2 = D3 - p1
        if p2 < b2[2] or p2 > b2[3] or p1 > b1[3]:
            continue
        # 直流法：母線3が需要 D3、母線1と2が発電。θ3 = 0 を基準
        # ネットワークは 1-2, 1-3, 2-3 の三角形
        B = np.array([[1 / x12 + 1 / x13, -1 / x12], [-1 / x12, 1 / x12 + 1 / x23]])
        P = np.array([p1, p2])
        th = np.linalg.solve(B, P)
        f12 = (th[0] - th[1]) / x12
        f13 = th[0] / x13
        f23 = th[1] / x23
        if cap12 is not None and abs(f13) > cap12:
            continue
        cost = b1[0] * p1 + b1[1] * p1 ** 2 + b2[0] * p2 + b2[1] * p2 ** 2
        if best is None or cost < best[0]:
            best = (cost, p1, p2, f12, f13, f23)
    return best


def fig_lmp():
    D3 = 300.0
    free = dcopf(None, D3)
    cap = 120.0
    cong = dcopf(cap, D3)
    # LMP：各母線で需要を +1 MW したときの費用増
    def lmp_at(bus, capv):
        base = dcopf(capv, D3)
        if base is None:
            return np.nan
        pert = dcopf(capv, D3 + 1.0)
        return (pert[0] - base[0]) / 1.0 if pert else np.nan
    lmp_free = lmp_at(3, None)
    lmp_cong = lmp_at(3, cap)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.4))
    a1.axis("off")
    pos = {1: (0.15, 0.72), 2: (0.15, 0.25), 3: (0.78, 0.48)}
    for (i, j), lab in [((1, 2), "1–2"), ((1, 3), "1–3"), ((2, 3), "2–3")]:
        a1.plot([pos[i][0], pos[j][0]], [pos[i][1], pos[j][1]], color=C_LIGHT, lw=3,
                transform=a1.transAxes, zorder=1)
    for n, (x, y), lab, c in [(1, pos[1], "母線1\n安い電源\nλ = 8 + 0.02P", C_SEC),
                              (2, pos[2], "母線2\n高い電源\nλ = 18 + 0.02P", C_ACC),
                              (3, pos[3], f"母線3\n需要 {D3:.0f} MW", C_MAIN)]:
        a1.add_patch(FancyBboxPatch((x - 0.10, y - 0.10), 0.20, 0.20, boxstyle="round,pad=0.012",
                                    transform=a1.transAxes, fc="#FBFAF6", ec=c, lw=2))
        a1.text(x, y, lab, ha="center", va="center", fontsize=11, color=c, transform=a1.transAxes)
    # 文字を底上げすると母線1の箱の下端に食い込むので、線の中点付近まで下げて逃がす
    a1.text(0.46, 0.555, f"線路 1–3 の容量 {cap:.0f} MW", ha="center", fontsize=11.5, color=C_WARM,
            transform=a1.transAxes)
    a1.set_title("3 母線の DC-OPF", fontsize=11.5)
    labels = ["混雑なし", f"1–3 を {cap:.0f} MW に制限"]
    p1s = [free[1], cong[1]]; p2s = [free[2], cong[2]]
    xx = np.arange(2)
    a2.bar(xx - 0.19, p1s, 0.36, color=C_SEC, label="母線1（安い）")
    a2.bar(xx + 0.19, p2s, 0.36, color=C_ACC, label="母線2（高い）")
    for i in range(2):
        a2.text(xx[i] - 0.19, p1s[i] + 6, f"{p1s[i]:.0f}", ha="center", fontsize=12)
        a2.text(xx[i] + 0.19, p2s[i] + 6, f"{p2s[i]:.0f}", ha="center", fontsize=12)
    a2.set_xticks(xx); a2.set_xticklabels(labels); a2.set_ylabel("出力 [MW]")
    a2.grid(alpha=0.3, axis="y"); a2.legend(fontsize=11, frameon=False)
    a2.set_title(f"混雑すると高い電源を焚く（LMP {lmp_free:.1f} → {lmp_cong:.1f} 千円/MWh）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_lmp.png"); plt.close(fig)
    OUT["lmp"] = (free, cong, lmp_free, lmp_cong)


# ============================================================ 9. 混雑と価格差
def fig_congestion():
    D3 = 300.0
    caps = np.arange(80, 260, 5.0)
    costs, lmps, p1s = [], [], []
    for c in caps:
        r = dcopf(c, D3)
        if r is None:
            costs.append(np.nan); lmps.append(np.nan); p1s.append(np.nan); continue
        rp = dcopf(c, D3 + 1.0)
        costs.append(r[0] / 1000)
        lmps.append((rp[0] - r[0]) if rp else np.nan)
        p1s.append(r[1])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(caps, costs, color=C_MAIN, lw=2.4)
    a1.set_xlabel("線路 1–3 の容量 [MW]"); a1.set_ylabel("総発電費用 [百万円/h]")
    a1.grid(alpha=0.3)
    a1.set_title("容量が小さいほど高くつく", fontsize=11)
    a2.plot(caps, lmps, color=C_ACC, lw=2.4)
    a2.set_xlabel("線路 1–3 の容量 [MW]"); a2.set_ylabel("母線3 の LMP [千円/MWh]")
    a2.grid(alpha=0.3)
    a2.set_title("混雑するほど地点価格が上がる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch14_congestion.png"); plt.close(fig)
    OUT["cong_curve"] = (caps[0], costs[0], caps[-1], costs[-1])


# ============================================================ 10. EMS の流れ
def fig_ems():
    fig, ax = plt.subplots(figsize=(9.8, 3.9))
    ax.axis("off")
    # 文字を底上げすると横幅の長い行が箱の右端の矢印まで届いてしまうので、
    # 長い行だけ 3 行に割って 1 行あたりの幅を抑える
    steps = [("状態推定", "今の系統を計測から\n復元（第13回）", C_BLUE, "数秒〜数十秒"),
             ("想定事故解析", "N-1 を\n数百ケース評価\n危ない線路を洗い出す", C_SEC, "数分"),
             ("OPF", "制約を守る\n最安の配分\n（電圧・容量・安定度）", C_MAIN, "数分〜十数分"),
             ("ELD / LFC", "発電機へ指令\n周波数は LFC\n（第8回）", C_WARM, "数秒〜数分")]
    for i, (name, what, c, t) in enumerate(steps):
        x = 0.02 + i * 0.245
        ax.add_patch(FancyBboxPatch((x, 0.32), 0.215, 0.44, boxstyle="round,pad=0.012",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x + 0.108, 0.66, name, ha="center", fontsize=11.5, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.108, 0.48, what, ha="center", fontsize=11, transform=ax.transAxes)
        ax.text(x + 0.108, 0.36, t, ha="center", fontsize=11, color=C_GREY, transform=ax.transAxes)
        if i < 3:
            ax.annotate("", xy=(x + 0.238, 0.54), xytext=(x + 0.218, 0.54), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=C_GREY, lw=2))
    ax.annotate("", xy=(0.06, 0.28), xytext=(0.90, 0.28), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=C_LIGHT, lw=2, connectionstyle="arc3,rad=0.25"))
    ax.text(0.48, 0.14, "この輪が数分ごとに回っている", ha="center", fontsize=11, color=C_MAIN,
            transform=ax.transAxes)
    ax.set_title("EMS（給電指令システム）の流れ", fontsize=12.5)
    savefig(fig, "ch14_ems.png"); plt.close(fig)


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch14_analogy.png",
        left_title="水槽と道路（たとえ）", right_title="経済負荷配分（実物）",
        pairs=[("パイプでつないだ水槽は水面が揃う", "水面の高さ＝限界費用 λ。全機で等しい"),
               ("断面の広い水槽ほどたくさん入る", "断面の広さ＝費用曲線の緩さ（c が小さい）"),
               ("水槽には上限（あふれる高さ）がある", "上限＝出力上限。当たった機は λ から外れる"),
               ("安い道が渋滞すると迂回路を使う", "渋滞＝線路容量の制約（混雑）"),
               ("迂回した先では値段が上がる", "迂回先の値段＝LMP（地点別限界価格）")],
        note="この対応が頭に入っていれば、等 λ 法・OPF・LMP はすべて「水槽と渋滞の話」に翻訳できる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch14_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("全機を均等に運転するのが公平で最適",
                "最適は限界費用 λ を揃える配分（等 λ 法）"),
               ("安い電源から順に上限まで使えばよい",
                "出力を上げるほど限界費用が上がるので、安い機に全部任せるのも最適ではない"),
               ("電気の価格は系統のどこでも同じ",
                "送電線が混雑すると、地点ごとに価格（LMP）が分かれる")],
        note="どれも「限界費用は出力とともに動く」ことを見落としている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch14_deriv_lambda_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 問題を書く',
                r"$\min \sum_i C_i(P_i) \quad \mathrm{s.t.}\ \sum_i P_i = D$",
                '総費用を最小に、需給は一致。\n制約付きの最小化になる'),
               ('② ラグランジュ関数を微分する',
                r"$L = \sum_i C_i(P_i) - \lambda\left(\sum_i P_i - D\right)$",
                'P_i で偏微分して 0 と置くと、すべての i で\ndC/dP が等しくなる'),
               ('③ 等 λ 条件',
                r"$\dfrac{dC_i}{dP_i} = \lambda \quad (\forall i)$",
                'λ が違えば、安いほうを増やして高いほうを\n減らすだけで総費用が下がる')],
            result='λ は「あと 1 MWh の値段」。これが市場価格の正体')

    for i in (1, 2, 3):
        derivation_figure(f"ch14_deriv_lmp_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① LMP の定義',
                r"$LMP_i = \dfrac{\partial C_{total}}{\partial D_i}$",
                'その地点で需要を 1 MW 増やしたときの総費用の増分。\n混雑がなければ全地点で同じ値になる'),
               ('② 混雑すると安い電気が届かない',
                r"$P_{line} = P_{line}^{max}$",
                '線路が満杯だと、その先の需要はその地点側の\n高い電源で賄うしかない'),
               ('③ 3 つの成分に分解できる',
                'LMP ＝ λ ＋ 混雑成分 ＋ 損失成分',
                '混雑レント =（LMP の差）×（潮流）が、\n送電線を増強する価値の目安になる')],
            result='値段が地点で違うのは、電気が自由に動けないから')


if __name__ == "__main__":
    fig_cost_curves(); fig_equal_lambda(); fig_lambda_iteration(); fig_dispatch_curve()
    fig_merit_order(); fig_price_curve(); fig_carbon(); fig_lmp(); fig_congestion(); fig_ems()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    p, lam, cost, ceq, diff = OUT["eld"]
    for (name, *_), pi in zip(GENS, p):
        print(f"  {name}: {pi:.1f} MW")
    print(f"λ = {lam:.2f} 千円/MWh、総費用 {cost:,.0f} 千円/h")
    print(f"均等配分 {ceq:,.0f} 千円/h → 差 {diff:.0f} 千円/h（年 {diff*8760/1e5:.1f} 億円）")
    print(f"λ の範囲（需要 150〜1000 MW）: {OUT['lam_range'][0]:.1f}〜{OUT['lam_range'][1]:.1f} 千円/MWh")
    print(f"メリットオーダー（需要 900 MW）の約定価格: {OUT['merit']:.0f} 円/kWh")
    print(f"石炭と LNG が逆転する炭素価格: {OUT['carbon']:,.0f} 円/t-CO₂")
    free, cong, lf, lc = OUT["lmp"]
    print(f"DC-OPF 混雑なし: 母線1 {free[1]:.0f} MW / 母線2 {free[2]:.0f} MW、費用 {free[0]/1000:.2f} 百万円/h、LMP {lf:.2f}")
    print(f"      混雑あり: 母線1 {cong[1]:.0f} MW / 母線2 {cong[2]:.0f} MW、費用 {cong[0]/1000:.2f} 百万円/h、LMP {lc:.2f}")
    c0, k0, c1, k1 = OUT["cong_curve"]
    fig_derivations()
    print(f"容量 {c0:.0f} MW で {k0:.2f}、{c1:.0f} MW で {k1:.2f} 百万円/h")
