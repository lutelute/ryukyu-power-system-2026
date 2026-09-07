# -*- coding: utf-8 -*-
"""第7回 電力系統の安定度 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch07.py  → ../図/ch07_*.png
   動揺方程式は RK4 で積分。等面積法・臨界除去角・臨界除去時間はすべて実計算。
   既定系統は viz/swing.html と同じ（P_m = 0.8, P_max = 2.0, H = 4 s, f0 = 60 Hz）。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arc

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

# ---- 既定の系統（viz/swing.html と同じ）----
PM, PMAX, H, F0 = 0.8, 2.0, 4.0, 60.0
W0 = 2 * np.pi * F0


def swing_rk4(pm, pmax_fault, pmax_post, t_clear, h=4.0, t_end=2.0, dt=1e-4, d=0.0):
    """動揺方程式 (2H/ω0)δ'' = Pm − Pmax sinδ − D δ' を RK4 で積分"""
    d0 = np.arcsin(pm / pmax_post)
    x = np.array([d0, 0.0])
    ts, ds, ws = [0.0], [d0], [0.0]
    n = int(t_end / dt)
    for i in range(n):
        t = i * dt
        pmx = pmax_fault if t < t_clear else pmax_post

        def f(s):
            return np.array([s[1], W0 / (2 * h) * (pm - pmx * np.sin(s[0]) - d * s[1])])
        k1 = f(x); k2 = f(x + dt / 2 * k1); k3 = f(x + dt / 2 * k2); k4 = f(x + dt * k3)
        x = x + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        ts.append(t + dt); ds.append(x[0]); ws.append(x[1])
    return np.array(ts), np.array(ds), np.array(ws)


def critical(pm=PM, pmax=PMAX, pmax_f=0.0):
    d0 = np.arcsin(pm / pmax)
    dmax = np.pi - d0
    cosc = (pm * (dmax - d0) + pmax * np.cos(dmax) - pmax_f * np.cos(d0)) / (pmax - pmax_f)
    dcr = np.arccos(np.clip(cosc, -1, 1))
    tcr = np.sqrt(2 * (2 * H) * (dcr - d0) / (W0 * pm)) if pmax_f == 0 else np.nan
    return d0, dmax, dcr, tcr


# ============================================================ 1. 系統図（発電機–無限大母線）
def fig_system():
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    ax.axis("off")
    ax.add_patch(Circle((0.115, 0.55), 0.055, fc="#F2EFE6", ec=C_MAIN, lw=2.2, transform=ax.transAxes))
    ax.text(0.115, 0.55, "G", ha="center", va="center", fontsize=16, weight="bold", color=C_MAIN, transform=ax.transAxes)
    ax.text(0.115, 0.40, "E′ = 1.05", ha="center", fontsize=12, transform=ax.transAxes)
    ax.add_patch(FancyBboxPatch((0.005, 0.49), 0.038, 0.12, boxstyle="round,pad=0.004",
                                fc=C_WARM, alpha=0.35, ec=C_WARM, transform=ax.transAxes))
    ax.text(0.024, 0.68, "タービン", ha="center", fontsize=11, color=C_WARM, transform=ax.transAxes)
    ax.text(0.024, 0.40, "P_m = 0.8", ha="center", fontsize=11, color=C_WARM, transform=ax.transAxes)
    ax.plot([0.17, 0.32], [0.55, 0.55], color="#1A1A17", lw=2, transform=ax.transAxes)
    ax.add_patch(Rectangle((0.32, 0.50), 0.05, 0.10, fc="none", ec="#1A1A17", lw=2, transform=ax.transAxes))
    ax.text(0.345, 0.66, "X′_d", ha="center", fontsize=11.5, transform=ax.transAxes)
    # 2 回線
    for dy, lab in [(0.12, "回線 1"), (-0.12, "回線 2")]:
        ax.plot([0.37, 0.45, 0.75, 0.83], [0.55, 0.55 + dy, 0.55 + dy, 0.55], color="#1A1A17", lw=2, transform=ax.transAxes)
        ax.add_patch(Rectangle((0.55, 0.55 + dy - 0.05), 0.05, 0.10, fc="none", ec="#1A1A17", lw=2, transform=ax.transAxes))
        ax.text(0.575, 0.55 + dy + 0.09, f"X_L ({lab})", ha="center", fontsize=11, transform=ax.transAxes)
    ax.plot([0.83, 0.90], [0.55, 0.55], color="#1A1A17", lw=2, transform=ax.transAxes)
    ax.plot([0.90, 0.90], [0.35, 0.75], color="#1A1A17", lw=5, transform=ax.transAxes)
    ax.text(0.915, 0.85, "無限大母線  V = 1.00∠0°", ha="center", va="center", fontsize=12, transform=ax.transAxes)
    # 事故点
    ax.plot([0.62], [0.435], marker="x", ms=16, mew=3, color=C_ACC, transform=ax.transAxes)
    ax.text(0.62, 0.33, "三相短絡（回線 2 の中央）", ha="center", fontsize=11.5, color=C_ACC, transform=ax.transAxes)
    ax.text(0.5, 0.10, "事故中は P_e ≈ 0 → 入る 0.8 と出る 0 の差がロータを加速させる",
            ha="center", fontsize=11, color=C_MAIN, transform=ax.transAxes)
    savefig(fig, "ch07_system.png"); plt.close(fig)


# ============================================================ 2. 等面積法
def fig_equal_area():
    d0, dmax, dcr, tcr = critical()
    d = np.linspace(0, np.pi, 500)
    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    ax.plot(np.rad2deg(d), PMAX * np.sin(d), color=C_MAIN, lw=2.4, label="事故前・除去後 P_e = 2.0 sinδ")
    ax.axhline(0, color=C_ACC, lw=2.2, ls="--", label="事故中 P_e = 0（三相短絡）")
    ax.axhline(PM, color=C_WARM, lw=2, label="機械入力 P_m = 0.8")
    da = np.linspace(d0, dcr, 100)
    ax.fill_between(np.rad2deg(da), 0, PM, color=C_ACC, alpha=0.30)
    ax.text(np.rad2deg((d0 + dcr) / 2), PM * 0.45, "A1\n加速", ha="center", fontsize=12, weight="bold", color="#7A2A22")
    db = np.linspace(dcr, dmax, 100)
    ax.fill_between(np.rad2deg(db), PM, PMAX * np.sin(db), color=C_SEC, alpha=0.30)
    ax.text(np.rad2deg((dcr + dmax) / 2), PM + 0.35, "A2\n減速", ha="center", fontsize=12, weight="bold", color="#3D544A")
    ax.axvline(np.rad2deg(d0), color=C_GREY, lw=1.2, ls=":")
    ax.text(np.rad2deg(d0), 2.62, f"δ₀ = {np.rad2deg(d0):.1f}°", ha="center", fontsize=11, color=C_GREY)
    for x, lab, c in [(dcr, f"δ_cr = {np.rad2deg(dcr):.1f}°", C_ACC),
                      (dmax, f"δ_max = {np.rad2deg(dmax):.1f}°", C_GREY)]:
        ax.axvline(np.rad2deg(x), color=c, lw=1.2, ls=":")
        ax.text(np.rad2deg(x), -0.12, lab, ha="center", va="top", fontsize=11, color=c)
    ax.set_xlabel("相差角 δ [°]"); ax.set_ylabel("電力 [p.u.]")
    ax.set_xlim(0, 180); ax.set_ylim(-0.55, 2.8); ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=11, frameon=False)
    ax.set_title(f"等面積法：A1 = A2 となる除去角が δ_cr = {np.rad2deg(dcr):.1f}°", fontsize=12)
    savefig(fig, "ch07_equal_area.png"); plt.close(fig)
    OUT["d0"], OUT["dmax"], OUT["dcr"], OUT["tcr"] = np.rad2deg(d0), np.rad2deg(dmax), np.rad2deg(dcr), tcr


# ============================================================ 3. δ(t) の時間応答
def fig_swing():
    d0, dmax, dcr, tcr = critical()
    fig, ax = plt.subplots(figsize=(9, 4.6))
    for tc, c, ls in [(0.20, C_SEC, "-"), (0.24, C_MAIN, "-"), (0.26, C_ACC, "-")]:
        t, dd, _ = swing_rk4(PM, 0.0, PMAX, tc, h=H, t_end=2.0)
        stable = np.rad2deg(dd).max() < 179
        ax.plot(t, np.rad2deg(dd), ls, color=c, lw=2.2,
                label=f"除去 {tc*1000:.0f} ms — {'安定（振れ戻る）' if stable else '脱調'}")
    ax.axhline(np.rad2deg(dmax), color=C_GREY, ls=":", lw=1.2)
    ax.text(1.55, np.rad2deg(dmax) + 4, f"δ_max = {np.rad2deg(dmax):.0f}°", fontsize=11, color=C_GREY)
    ax.axhline(np.rad2deg(d0), color=C_GREY, ls=":", lw=1.2)
    ax.text(1.55, np.rad2deg(d0) + 4, f"δ₀ = {np.rad2deg(d0):.1f}°", fontsize=11, color=C_GREY)
    ax.axvline(tcr, color=C_ACC, lw=1.4, ls="--")
    ax.text(tcr + 0.03, 12, f"t_cr = {tcr*1000:.0f} ms", fontsize=11.5, color=C_ACC, weight="bold")
    ax.set_xlabel("時間 t [s]"); ax.set_ylabel("相差角 δ [°]")
    ax.set_xlim(0, 2.0); ax.set_ylim(0, 300); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_title("動揺方程式を RK4 で積分 — 247 ms を境に安定と脱調が分かれる", fontsize=12)
    savefig(fig, "ch07_swing.png"); plt.close(fig)


# ============================================================ 4. 除去時間スイープ
def fig_sweep():
    d0, dmax, dcr, tcr = critical()
    tcs = np.arange(0.05, 0.40, 0.005)
    peaks = []
    for tc in tcs:
        t, dd, _ = swing_rk4(PM, 0.0, PMAX, tc, h=H, t_end=3.0)
        peaks.append(np.rad2deg(dd).max())
    peaks = np.array(peaks)
    stable = peaks < 179
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot(tcs[stable] * 1000, peaks[stable], "o-", color=C_SEC, ms=4, lw=2, label="安定（振れ戻る）")
    ax.plot(tcs[~stable] * 1000, np.minimum(peaks[~stable], 300), "o-", color=C_ACC, ms=4, lw=2, label="脱調")
    ax.axvline(tcr * 1000, color=C_MAIN, lw=1.8, ls="--")
    ax.text(tcr * 1000 + 3, 120, f"等面積法の予測\nt_cr = {tcr*1000:.0f} ms", fontsize=11.5, color=C_MAIN, weight="bold")
    ax.axhline(np.rad2deg(dmax), color=C_GREY, ls=":", lw=1.2)
    ax.text(60, np.rad2deg(dmax) + 5, f"δ_max = {np.rad2deg(dmax):.0f}°（これを超えると戻れない）", fontsize=11, color=C_GREY)
    ax.set_xlabel("故障除去時間 t_c [ms]"); ax.set_ylabel("最大相差角 [°]")
    ax.set_ylim(0, 300); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=11, loc="upper left")
    last_stable = tcs[stable][-1] * 1000
    ax.set_title(f"RK4 の実測では {last_stable:.0f} ms まで安定 — 等面積法の予測とほぼ一致", fontsize=11.5)
    savefig(fig, "ch07_sweep.png"); plt.close(fig)
    OUT["sweep_last_stable"] = last_stable


# ============================================================ 5. 慣性 H と臨界除去時間
def fig_inertia():
    Hs = np.linspace(1.0, 8.0, 200)
    d0, dmax, dcr, _ = critical()
    tcrs = np.sqrt(2 * (2 * Hs) * (dcr - d0) / (W0 * PM))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    a1.plot(Hs, tcrs * 1000, color=C_MAIN, lw=2.4)
    for h, c in [(4.0, C_MAIN), (2.0, C_ACC)]:
        t = np.sqrt(2 * (2 * h) * (dcr - d0) / (W0 * PM)) * 1000
        a1.scatter([h], [t], color=c, s=70, zorder=5)
        a1.annotate(f"H = {h:.0f} s → {t:.0f} ms", (h, t), textcoords="offset points",
                    xytext=(8, -14 if h == 4 else 8), fontsize=11.5, color=c)
    a1.set_xlabel("系統慣性定数 H [s]"); a1.set_ylabel("臨界除去時間 t_cr [ms]")
    a1.grid(alpha=0.3); a1.set_title("t_cr ∝ √H — 慣性が半分なら 0.71 倍", fontsize=11)
    kinds = ["火力\n(3〜6)", "原子力\n(4〜7)", "水力\n(2〜4)", "太陽光\nPCS", "風力\n(GFL)"]
    vals = [4.5, 5.5, 3.0, 0.0, 0.0]
    a2.bar(kinds, vals, color=[C_MAIN, C_MAIN, C_MAIN, C_ACC, C_ACC])
    for i, v in enumerate(vals):
        a2.text(i, v + 0.15, f"{v:.1f}" if v > 0 else "0", ha="center", fontsize=11,
                color=C_MAIN if v > 0 else C_ACC)
    a2.text(3.5, 0.55, "慣性なし", ha="center", fontsize=11, color=C_ACC)
    a2.set_ylabel("慣性定数 H [s]"); a2.set_ylim(0, 6.8); a2.grid(alpha=0.3, axis="y")
    a2.set_title("インバータ電源は回転体を持たない", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch07_inertia.png"); plt.close(fig)
    t2 = np.sqrt(2 * (2 * 2.0) * (dcr - d0) / (W0 * PM))
    OUT["tcr_H2"] = t2


# ============================================================ 6. 3 本の P–δ 曲線（1 回線開放）
def fig_three_curves():
    E, V, Xd, XL = 1.05, 1.0, 0.25, 0.60
    Xpre = Xd + XL / 2
    Xpost = Xd + XL
    # 事故中：片回線の中央で短絡すると、Y–Δ 変換で発電機–母線間の等価リアクタンスが約 3 倍になる
    Xf = Xpre * 2.85
    Pmax_pre, Pmax_post, Pmax_f = E * V / Xpre, E * V / Xpost, E * V / Xf
    pm = 0.8
    d = np.linspace(0, np.pi, 500)
    d0 = np.arcsin(pm / Pmax_pre)
    dmax = np.pi - np.arcsin(pm / Pmax_post)
    cosc = (pm * (dmax - d0) + Pmax_post * np.cos(dmax) - Pmax_f * np.cos(d0)) / (Pmax_post - Pmax_f)
    dcr = np.arccos(np.clip(cosc, -1, 1))
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    ax.plot(np.rad2deg(d), Pmax_pre * np.sin(d), color=C_SEC, lw=2.2, label=f"事故前 2 回線 P_max = {Pmax_pre:.2f}")
    ax.plot(np.rad2deg(d), Pmax_f * np.sin(d), color=C_ACC, lw=2.2, ls="--", label=f"事故中 P_max = {Pmax_f:.2f}")
    ax.plot(np.rad2deg(d), Pmax_post * np.sin(d), color=C_MAIN, lw=2.4, label=f"除去後 1 回線 P_max = {Pmax_post:.2f}")
    ax.axhline(pm, color=C_WARM, lw=1.8, label=f"P_m = {pm}")
    da = np.linspace(d0, dcr, 80)
    ax.fill_between(np.rad2deg(da), Pmax_f * np.sin(da), pm, color=C_ACC, alpha=0.25)
    db = np.linspace(dcr, dmax, 80)
    ax.fill_between(np.rad2deg(db), pm, Pmax_post * np.sin(db), color=C_SEC, alpha=0.25)
    ax.text(np.rad2deg((d0 + dcr) / 2), pm * 0.55, "A1", ha="center", fontsize=13, weight="bold", color="#7A2A22")
    ax.text(np.rad2deg((dcr + dmax) / 2) - 5, pm + 0.18, "A2", ha="center", fontsize=13, weight="bold", color="#3D544A")
    for x, lab in [(d0, f"δ₀={np.rad2deg(d0):.0f}°"), (dcr, f"δ_cr={np.rad2deg(dcr):.0f}°"), (dmax, f"δ_max={np.rad2deg(dmax):.0f}°")]:
        ax.axvline(np.rad2deg(x), color=C_GREY, lw=1, ls=":")
        ax.text(np.rad2deg(x), -0.10, lab, ha="center", va="top", fontsize=11, color=C_GREY)
    ax.set_xlabel("相差角 δ [°]"); ax.set_ylabel("電力 [p.u.]"); ax.set_xlim(0, 180); ax.set_ylim(-0.55, 2.3)
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="upper right")
    ax.set_title("1 回線開放：除去後の曲線が下がるぶん、減速に使える面積が減る", fontsize=11.5)
    savefig(fig, "ch07_three_curves.png"); plt.close(fig)
    OUT["three"] = (Pmax_pre, Pmax_f, Pmax_post, np.rad2deg(d0), np.rad2deg(dcr), np.rad2deg(dmax))


# ============================================================ 7. 安定度の 3 分類と時間スケール
def fig_timescale():
    fig, ax = plt.subplots(figsize=(9.6, 3.8))
    rows = [("同期安定度\n（相差角）", 0.1, 10, C_MAIN, "第7回：等面積法・脱調"),
            ("周波数安定度", 1, 900, C_WARM, "第8回：ΔP = KΔF・LFC"),
            ("電圧安定度", 1, 3600, C_SEC, "第6回：PV カーブ・鼻先")]
    for i, (name, t1, t2, c, note) in enumerate(rows):
        ax.barh(i, np.log10(t2) - np.log10(t1), left=np.log10(t1), color=c, alpha=0.8, height=0.5)
        ax.text(np.log10(t1) - 0.1, i, name, ha="right", va="center", fontsize=12)
        ax.text((np.log10(t1) + np.log10(t2)) / 2, i + 0.32, note, ha="center", fontsize=11, color=c)
    for x, lab in [(-1, "0.1 s"), (0, "1 s"), (1, "10 s"), (2, "100 s"), (3, "1000 s")]:
        ax.axvline(x, color=C_LIGHT, lw=0.8, zorder=0)
    ax.set_xticks([-1, 0, 1, 2, 3]); ax.set_xticklabels(["0.1 s", "1 s", "10 s", "100 s", "1000 s"])
    ax.set_yticks([]); ax.set_xlim(-1.5, 3.8); ax.set_ylim(-0.6, 2.8)
    ax.set_xlabel("現象の時間スケール（対数）")
    ax.text(-1.45, 2.55, "保護リレー＋遮断器：50〜100 ms", fontsize=11, color=C_ACC,
            bbox=dict(facecolor="white", edgecolor="none", pad=1.5))
    savefig(fig, "ch07_timescale.png"); plt.close(fig)


# ============================================================ 8. 対策の効果
def fig_measures():
    d0, dmax, dcr0, tcr0 = critical()
    cases = [("対策なし\nP_max = 2.0", 2.0, 4.0), ("高速除去\n(A1 を減らす)", 2.0, 4.0),
             ("直列補償\nP_max = 2.4", 2.4, 4.0), ("慣性低下\nH = 2 s", 2.0, 2.0)]
    labels, tcrs, colors = [], [], []
    for name, pmax, h in cases:
        d0_, dmax_, dcr_, _ = critical(PM, pmax)
        t = np.sqrt(2 * (2 * h) * (dcr_ - d0_) / (W0 * PM))
        labels.append(name); tcrs.append(t * 1000)
        colors.append(C_ACC if h < 4 else (C_SEC if pmax > 2.0 else C_MAIN))
    tcrs[1] = tcrs[0]                      # 高速除去は t_cr を変えず、実際の除去時間を短くする対策
    fig, ax = plt.subplots(figsize=(9, 4.2))
    bars = ax.bar(labels, tcrs, color=colors, alpha=0.9)
    for b, t in zip(bars, tcrs):
        ax.text(b.get_x() + b.get_width() / 2, t + 5, f"{t:.0f} ms", ha="center", fontsize=11, weight="bold")
    ax.axhline(80, color=C_WARM, lw=2, ls="--")
    ax.text(1.5, 295, "保護の実力（3〜5 サイクル = 50〜80 ms、破線）", ha="center", fontsize=11, color=C_WARM)
    ax.set_ylabel("臨界除去時間 t_cr [ms]"); ax.set_ylim(0, 320); ax.grid(alpha=0.3, axis="y")
    ax.set_title("対策は A1 を減らすか A2 を増やすか — 慣性低下は余裕そのものを削る", fontsize=11.5)
    savefig(fig, "ch07_measures.png"); plt.close(fig)
    OUT["measures"] = list(zip([c[0].replace("\n", " ") for c in cases], tcrs))


# ============================================================ 9. 減衰（PSS の効果）
def fig_damping():
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    for dd, c, lab in [(0.0, C_LIGHT, "制動なし D = 0（振動が続く）"),
                       (2.0, C_SEC, "自然減衰 D = 2"),
                       (8.0, C_MAIN, "PSS 相当 D = 8（速く収まる）")]:
        t, delta, _ = swing_rk4(PM, 0.0, PMAX, 0.20, h=H, t_end=6.0, d=dd)
        ax.plot(t, np.rad2deg(delta), color=c, lw=2.2, label=lab)
    d0, _, _, _ = critical()
    ax.axhline(np.rad2deg(d0), color=C_GREY, ls=":", lw=1.2)
    ax.text(5.2, np.rad2deg(d0) + 3, f"平衡点 δ₀ = {np.rad2deg(d0):.1f}°", fontsize=11, color=C_GREY)
    ax.set_xlabel("時間 t [s]"); ax.set_ylabel("相差角 δ [°]"); ax.set_xlim(0, 6)
    ax.set_ylim(-40, 145); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper right")
    ax.set_title("制動係数 D の効果（除去 200 ms）— PSS は「振動を減らす」装置", fontsize=11.5)
    savefig(fig, "ch07_damping.png"); plt.close(fig)


# ============================================================ 10. 位相面（δ–ω 平面）
def fig_phase():
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for tc, c, lab in [(0.20, C_SEC, "200 ms（安定）"), (0.24, C_MAIN, "240 ms（ぎりぎり安定）"), (0.26, C_ACC, "260 ms（脱調）")]:
        t, d, w = swing_rk4(PM, 0.0, PMAX, tc, h=H, t_end=1.2)
        ax.plot(np.rad2deg(d), w, color=c, lw=2, label=lab)
    d0, dmax, dcr, _ = critical()
    ax.scatter([np.rad2deg(d0)], [0], color=C_GREY, s=70, zorder=5)
    ax.text(np.rad2deg(d0) + 3, 1.2, "安定平衡点 δ₀", fontsize=11, color=C_GREY)
    ax.scatter([np.rad2deg(dmax)], [0], color=C_ACC, s=70, marker="x", zorder=5)
    ax.text(np.rad2deg(dmax) - 5, 1.2, "不安定平衡点 δ_max", fontsize=11, color=C_ACC, ha="right")
    ax.axhline(0, color=C_LIGHT, lw=1)
    ax.set_xlabel("相差角 δ [°]"); ax.set_ylabel("角速度偏差 dδ/dt [rad/s]")
    ax.set_xlim(0, 200); ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False)
    ax.set_title("位相面で見る — 不安定平衡点を「速度を持ったまま」越えたら戻れない", fontsize=11.5)
    savefig(fig, "ch07_phase.png"); plt.close(fig)


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch07_analogy.png",
        left_title="台車とゴム紐（たとえ）", right_title="同期発電機（実物）",
        pairs=[("壁にゴム紐でつないだ台車を押し続ける", "押す力＝機械入力 P_m（タービン）"),
               ("ゴムの張力が押す力とつり合う位置で止まる", "電気出力 P_max sinδ とつり合う運転点 δ_0"),
               ("ゴムが切れた瞬間、台車は加速する", "短絡事故で P_e ≈ 0 になり、ロータが加速する"),
               ("ゴムを戻すと引き戻されるが、伸びきると戻らない", "除去後に P_e が戻り減速するが、δ_max を超えると脱調する"),
               ("戻す（ゴムをつなぎ直す）のが遅いほど台車は速く動いている", "故障除去時間 t_c が長いほど、δ は速度を持って進む")],
        note="崩れる点：ゴムの張力は伸びに比例して増え続けるが、同期化力は sinδ なので 90° を過ぎると弱くなる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch07_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("慣性 H が下がると、臨界除去角 δ_cr も小さくなる",
                "δ_cr は等面積法（P–δ 平面の幾何）だけで決まり、H には依らない"),
               ("事故さえ切れば、発電機は必ず安定に戻る",
                "除去が t_cr より遅れると δ が伸びきり、二度と戻らない（脱調する）"),
               ("δ が 90° を超えたら脱調する",
                "90° を超えても、速度 dδ/dt が 0 になれば戻ってくる。脱調は速度を持ったまま δ_max を越えたときだけ")],
        note="どれも「角度」と「時間」、「切ったか」と「間に合ったか」を取り違えたことから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch07_deriv_swing_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 回転体の運動方程式',
                r"$J\,\ddot{\theta} = T_m - T_e$",
                '慣性モーメント J のロータに、\n機械トルクと電気トルクがかかる'),
               ('② トルクを電力に直す',
                r"$(J\omega_0)\,\ddot{\delta} = P_m - P_e$",
                'P = ωT の両辺を ω で割る。\n定格の近くでは ω を ω₀ とみなせる'),
               ('③ 単位法にする',
                r"$\dfrac{2H}{\omega_0}\,\ddot{\delta} = P_m - P_e$",
                'H は「定格出力で何秒回り続けられるか」。\n単位は秒')],
            result='回転版の F = ma。教科書の M = 2H/ω₀ はこの係数')

    for i in (1, 2, 3):
        derivation_figure(f"ch07_deriv_area_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 動揺方程式に δ′ を掛ける',
                r"$\dfrac{2H}{\omega_0}\,\dot{\delta}\,\ddot{\delta} = (P_m - P_e)\,\dot{\delta}$",
                '左辺は運動エネルギーの\n時間変化そのもの'),
               ('② dt を dδ に変える',
                r"$\dfrac{H}{\omega_0}\,\dot{\delta}^{2} = \int (P_m - P_e)\,d\delta$",
                'δ′dt = dδ を使う。\n右辺は P–δ 平面の面積になる'),
               ('③ 戻れる条件を読む',
                r"$A_1 = A_2$",
                '加速で貯めた面積を減速で使い切れば\n速度が 0 になり、戻ってくる')],
            result='面積がエネルギー。だから等面積法で安定かどうかが判定できる')


if __name__ == "__main__":
    fig_system(); fig_equal_area(); fig_swing(); fig_sweep(); fig_inertia()
    fig_three_curves(); fig_timescale(); fig_measures(); fig_damping(); fig_phase()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    print(f"既定系統 P_m={PM}, P_max={PMAX}, H={H} s, f0={F0} Hz")
    print(f"δ0 = {OUT['d0']:.1f}°, δ_max = {OUT['dmax']:.1f}°, δ_cr = {OUT['dcr']:.1f}°, t_cr = {OUT['tcr']*1000:.0f} ms")
    print(f"RK4 スイープで安定だった最大除去時間 = {OUT['sweep_last_stable']:.0f} ms")
    print(f"H = 2 s のときの t_cr = {OUT['tcr_H2']*1000:.0f} ms（{OUT['tcr_H2']/OUT['tcr']:.3f} 倍 = √(2/4)）")
    pre, f, post, d0, dcr, dmax = OUT["three"]
    fig_derivations()
    print(f"1 回線開放: P_max 事故前 {pre:.2f} → 事故中 {f:.2f} → 除去後 {post:.2f}")
    print(f"  δ0 = {d0:.1f}°, δ_cr = {dcr:.1f}°, δ_max = {dmax:.1f}°")
    for n, t in OUT["measures"]:
        print(f"  対策 {n}: t_cr = {t:.0f} ms")
