# -*- coding: utf-8 -*-
"""第8回 受給バランスと周波数制御 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch08.py  → ../図/ch08_*.png
   周波数応答は慣性 → ガバナ → LFC の 3 段を常微分方程式で RK4 積分する。
   沖縄（1,500 MW, H=4.5 s, %K=1.0）と九州（16,000 MW）を同じモデルで比べる。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}
F0 = 60.0


def K_of(S, pctK=1.0):
    """系統定数 K [MW/Hz]。%K は %MW/0.1Hz なので 10 倍して %/Hz にする"""
    return pctK * 10.0 / 100.0 * S


def response(S, H, dP, pctK=1.0, Tg=8.0, Kl_share=0.3, lfc=True, alpha=None, beta=None,
             t_end=300.0, dt=0.01):
    """周波数応答（慣性・ガバナ一次遅れ・LFC の PI）を RK4 で積分
       df/dt = f0/(2H S) (dP + dPg + dPl + dPv)、dPg はガバナ、dPl は負荷の自己制御性
    """
    K = K_of(S, pctK)
    Kl = K * Kl_share            # 負荷の自己制御性
    Kg = K - Kl                  # ガバナ（発電力特性）
    # LFC の PI ゲイン（系統規模に比例させる）。単位は MW/Hz と MW/(Hz·s)
    if alpha is None:
        alpha = 0.3 * K
    if beta is None:
        beta = 0.02 * K
    n = int(t_end / dt)
    f = F0
    pg = 0.0                     # ガバナ出力の増分
    ig = 0.0                     # LFC の積分項
    ts, fs, pgs, plfc = [0.0], [F0], [0.0], [0.0]
    for i in range(n):
        t = i * dt

        def deriv(state):
            f_, pg_, ig_ = state
            df = f_ - F0
            p_load = Kl * df                      # 周波数が下がると負荷も減る（正で吸収）
            p_lfc = -(alpha * df + ig_) if lfc else 0.0
            dpg = (-Kg * df - pg_) / Tg           # ガバナは一次遅れで −Kg Δf に向かう
            dig = beta * df if lfc else 0.0
            dfdt = F0 / (2 * (H) * S) * (dP + pg_ - p_load + p_lfc)
            return np.array([dfdt, dpg, dig])

        s = np.array([f, pg, ig])
        k1 = deriv(s); k2 = deriv(s + dt / 2 * k1); k3 = deriv(s + dt / 2 * k2); k4 = deriv(s + dt * k3)
        s = s + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        f, pg, ig = s
        ts.append(t + dt); fs.append(f); pgs.append(pg)
        plfc.append(-(alpha * (f - F0) + ig) if lfc else 0.0)
    return np.array(ts), np.array(fs), np.array(pgs), np.array(plfc)


# ============================================================ 1. 天秤（需給バランスの模式図）
def fig_balance():
    fig, ax = plt.subplots(figsize=(9.4, 3.8))
    ax.axis("off")
    for x0, gen, load, tilt, title, c in [(0.05, 1500, 1500, 0.0, "つり合い：60.00 Hz", C_SEC),
                                          (0.55, 1250, 1500, -0.16, "250 MW 脱落：58.33 Hz", C_ACC)]:
        cx = x0 + 0.20
        ax.plot([cx, cx], [0.18, 0.50], color="#1A1A17", lw=3, transform=ax.transAxes)
        dx, dy = 0.155, tilt * 0.55
        ax.plot([cx - dx, cx + dx], [0.50 - dy, 0.50 + dy], color="#1A1A17", lw=3, transform=ax.transAxes)
        ax.add_patch(FancyBboxPatch((cx - dx - 0.055, 0.50 - dy + 0.02), 0.11, gen / 1500 * 0.16,
                                    boxstyle="round,pad=0.004", fc=C_SEC, alpha=0.55, ec=C_SEC,
                                    transform=ax.transAxes))
        ax.text(cx - dx, 0.50 - dy + gen / 1500 * 0.16 + 0.05, f"発電 {gen} MW", ha="center", fontsize=11.5, transform=ax.transAxes)
        ax.add_patch(FancyBboxPatch((cx + dx - 0.055, 0.50 + dy + 0.02), 0.11, load / 1500 * 0.16,
                                    boxstyle="round,pad=0.004", fc=C_WARM, alpha=0.55, ec=C_WARM,
                                    transform=ax.transAxes))
        ax.text(cx + dx, 0.50 + dy + load / 1500 * 0.16 + 0.05, f"消費 {load} MW", ha="center", fontsize=11.5, transform=ax.transAxes)
        ax.text(cx, 0.06, title, ha="center", fontsize=12, weight="bold", color=c, transform=ax.transAxes)
        
    ax.text(0.5, 0.93, "周波数は系統全体で 1 つの「天秤の傾き」— 傾き = 周波数のずれ ΔF", ha="center", fontsize=12.5, transform=ax.transAxes)
    savefig(fig, "ch08_balance.png"); plt.close(fig)


# ============================================================ 2. 速度調定率（F–P 直線）
def fig_droop():
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    GN = 300.0
    for eps, c in [(3.0, C_SEC), (5.0, C_MAIN), (8.0, C_ACC)]:
        F_no = F0 * (1 + eps / 100)
        P = np.array([0, GN])
        F = np.array([F_no, F0])
        ax.plot(P, F, color=c, lw=2.3, label=f"ε = {eps}%（%K_G = {10000/(eps*F0):.1f} %MW/Hz）")
    ax.axhline(F0, color=C_GREY, ls=":", lw=1.2)
    ax.text(5, F0 + 0.08, "定格 60 Hz", fontsize=11, color=C_GREY)
    eps = 5.0
    Kg = 10000 / (eps * F0) / 100 * GN
    ax.annotate("", xy=(GN * 0.5 + Kg * 0.2, F0 - 0.2), xytext=(GN * 0.5, F0 - 0.2),
                arrowprops=dict(arrowstyle="->", color=C_MAIN, lw=2))
    ax.text(GN * 0.5 + 8, F0 - 0.42, f"0.2 Hz 下がると\n出力 +{Kg*0.2:.1f} MW", fontsize=11, color=C_MAIN)
    ax.set_xlabel("発電機出力 P [MW]（定格 300 MW）"); ax.set_ylabel("周波数 F [Hz]")
    ax.set_xlim(0, GN * 1.05); ax.set_ylim(59.3, 65.2); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper right")
    ax.set_title("速度調定率 ε — 直線の傾きが「周波数が下がったら何 MW 増やすか」", fontsize=11.5)
    savefig(fig, "ch08_droop.png"); plt.close(fig)
    OUT["Kg_5pct"] = Kg


# ============================================================ 3. 発電特性と負荷特性の交点
def fig_intersection():
    S = 1500.0
    K = K_of(S)
    Kg, Kl = K * 0.7, K * 0.3
    f = np.linspace(57.8, 61.2, 300)
    Pg = 1500 - Kg * (f - F0)
    Pl = 1500 + Kl * (f - F0)
    Pg2 = Pg - 250
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    ax.plot(Pg, f, color=C_MAIN, lw=2.3, label=f"発電特性（K_G = {Kg:.0f} MW/Hz）")
    ax.plot(Pl, f, color=C_WARM, lw=2.3, label=f"負荷特性（K_L = {Kl:.0f} MW/Hz）")
    ax.plot(Pg2, f, color=C_ACC, lw=2.3, ls="--", label="発電特性（250 MW 脱落後）")
    ax.scatter([1500], [F0], color=C_SEC, s=90, zorder=5)
    ax.text(1500 + 14, F0 + 0.10, "事故前 60.00 Hz", fontsize=12, color=C_SEC, weight="bold")
    fnew = F0 - 250 / K
    Pnew = 1500 + Kl * (fnew - F0)
    ax.scatter([Pnew], [fnew], color=C_ACC, s=90, zorder=5)
    ax.text(Pnew + 14, fnew - 0.16, f"事故後 {fnew:.2f} Hz\n（ガバナ応答後・LFC なし）", fontsize=12, color=C_ACC, weight="bold")
    ax.set_xlabel("電力 [MW]"); ax.set_ylabel("周波数 F [Hz]"); ax.grid(alpha=0.3)
    ax.set_ylim(57.8, 61.2)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_title(f"交点が運転点 — K = K_G + K_L = {K:.0f} MW/Hz、ΔF = ΔP/K = {-250/K:.2f} Hz", fontsize=11.5)
    savefig(fig, "ch08_intersection.png"); plt.close(fig)
    OUT["K_oki"], OUT["dF_oki"] = K, -250 / K


# ============================================================ 4. 沖縄 vs 九州（時間応答）
def fig_compare():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.4, 5.0))
    res = {}
    for name, S, H, c in [("沖縄本島（1,500 MW, H=4.5 s）", 1500.0, 4.5, C_ACC),
                          ("九州（16,000 MW, H=5.0 s）", 16000.0, 5.0, C_SEC)]:
        t, f, pg, pl = response(S, H, -250.0)
        res[name] = (t, f, pg, pl)
        a1.plot(t, f, color=c, lw=2.6, label=name)
        a2.plot(t, f, color=c, lw=2.6)
        i = int(np.argmin(f))
        a1.scatter([t[i]], [f[i]], color=c, s=70, zorder=5)
        a1.annotate(f"最低 {f[i]:.2f} Hz\n(t = {t[i]:.1f} s)", (t[i], f[i]),
                    textcoords="offset points", xytext=(10, -6 if S < 5000 else 8),
                    fontsize=12, color=c, weight="bold")
        OUT.setdefault("nadir", {})[name] = (f.min(), f[-1], K_of(S))
    for a in (a1, a2):
        a.axhline(F0, color=C_GREY, ls=":", lw=1)
        a.axhline(59.0, color=C_WARM, ls="--", lw=1.2)
        a.grid(alpha=0.3); a.set_xlabel("時間 [s]"); a.set_ylabel("周波数 [Hz]")
    a1.text(2, 59.08, "UFR 整定の例 59.0 Hz", fontsize=11, color=C_WARM)
    a1.set_xlim(0, 30); a1.set_ylim(57.8, 60.3)
    a1.set_title("最初の 30 秒（慣性とガバナ）", fontsize=12.5)
    a2.set_xlim(0, 300); a2.set_ylim(57.8, 60.3)
    a2.set_title("5 分間（LFC が偏差を 0 に戻す）", fontsize=12.5)
    # 凡例は 2 枚に共通なので図の上にまとめる（曲線・注記との重なりを避ける）
    fig.legend(*a1.get_legend_handles_labels(), loc="upper center", ncol=2,
               frameon=False, fontsize=12, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    savefig(fig, "ch08_compare.png"); plt.close(fig)


# ============================================================ 5. 3 段応答の分解
def fig_stages():
    t, f, pg, pl = response(1500.0, 4.5, -250.0)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.2, 5.6), sharex=True,
                                 gridspec_kw={"height_ratios": [1.2, 1]})
    a1.plot(t, f, color=C_MAIN, lw=2.4)
    a1.axhline(F0, color=C_GREY, ls=":", lw=1)
    nadir_i = int(np.argmin(f))
    a1.scatter([t[nadir_i]], [f[nadir_i]], color=C_ACC, s=70, zorder=5)
    a1.annotate(f"最低点（nadir）{f[nadir_i]:.2f} Hz\nt = {t[nadir_i]:.1f} s", (t[nadir_i], f[nadir_i]),
                xytext=(t[nadir_i] + 45, f[nadir_i] + 0.55), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a1.set_ylabel("周波数 [Hz]"); a1.grid(alpha=0.3); a1.set_ylim(57.9, 60.62)
    for x0, x1, xlab, lab, c in [(0, 2, 2, "① 慣性（0〜2 s）", C_ACC),
                                 (2, 30, 74, "② ガバナ（〜30 s）", C_WARM),
                                 (30, 300, 168, "③ LFC（30 s〜）", C_SEC)]:
        a1.axvspan(x0, x1, color=c, alpha=0.08)
        a1.text(xlab, 60.42, lab, ha="left", va="center", fontsize=11,
                color=c, weight="bold")
    a2.plot(t, pg, color=C_WARM, lw=2.2, label="ガバナの出力増分")
    a2.plot(t, pl, color=C_SEC, lw=2.2, label="LFC の出力増分")
    a2.plot(t, pg + pl, color=C_MAIN, lw=1.6, ls="--", label="合計")
    a2.axhline(250, color=C_ACC, ls=":", lw=1.4)
    a2.text(150, 258, "脱落した 250 MW", fontsize=11, color=C_ACC)
    a2.set_xlabel("時間 [s]"); a2.set_ylabel("出力増分 [MW]"); a2.grid(alpha=0.3)
    a2.legend(fontsize=11, frameon=False, loc="lower right"); a2.set_xlim(0, 300)
    fig.tight_layout(); savefig(fig, "ch08_stages.png"); plt.close(fig)
    OUT["nadir_oki"], OUT["t_nadir"] = f[nadir_i], t[nadir_i]


# ============================================================ 6. ΔF vs 脱落量
def fig_dfdp():
    dps = np.linspace(0, 400, 200)
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    for S, pctK, lab, c in [(1500, 1.0, "沖縄（1,500 MW, %K=1.0）", C_ACC),
                            (1500, 1.5, "沖縄（%K=1.5 に強化）", C_WARM),
                            (16000, 1.0, "九州（16,000 MW）", C_SEC)]:
        K = K_of(S, pctK)
        ax.plot(dps, F0 - dps / K, color=c, lw=2.3)
        ax.text(404, F0 - 400 / K, f" {lab}\n K = {K:.0f} MW/Hz", fontsize=12,
                color=c, va="center", ha="left")
    ax.axhline(59.0, color=C_MAIN, ls="--", lw=1.4)
    ax.text(5, 59.08, "UFR 整定の例 59.0 Hz", fontsize=11, color=C_MAIN)
    ax.scatter([250], [F0 - 250 / K_of(1500)], color=C_ACC, s=80, zorder=5)
    ax.annotate(f"250 MW → {F0 - 250/K_of(1500):.2f} Hz", (250, F0 - 250 / K_of(1500)),
                xytext=(30, 57.6), fontsize=12, color=C_ACC, weight="bold",
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("脱落した電源の大きさ ΔP [MW]"); ax.set_ylabel("定常の周波数 [Hz]")
    ax.set_ylim(57.0, 60.2); ax.set_xlim(0, 400); ax.grid(alpha=0.3)
    fig.subplots_adjust(right=0.70)          # 右端の直接ラベルの場所をあける
    savefig(fig, "ch08_dfdp.png"); plt.close(fig)


# ============================================================ 7. RoCoF と慣性
def fig_rocof():
    Hs = np.linspace(1.0, 6.0, 200)
    S, dP = 1500.0, -250.0
    roco = dP * F0 / (2 * Hs * S)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(Hs, roco, color=C_MAIN, lw=2.4)
    for h, c in [(4.5, C_SEC), (2.5, C_ACC)]:
        r = dP * F0 / (2 * h * S)
        a1.scatter([h], [r], color=c, s=70, zorder=5)
        a1.annotate(f"H={h} s → {r:.2f} Hz/s", (h, r), textcoords="offset points",
                    xytext=(6, -16 if h == 4.5 else 8), fontsize=11.5, color=c)
    a1.set_xlabel("系統慣性定数 H [s]"); a1.set_ylabel("RoCoF [Hz/s]")
    a1.grid(alpha=0.3); a1.set_title("RoCoF は H に反比例（沖縄・250 MW 脱落）", fontsize=11)
    for h, c, lab in [(4.5, C_SEC, "H = 4.5 s（現状）"), (3.0, C_WARM, "H = 3.0 s"), (2.0, C_ACC, "H = 2.0 s（再エネ増）")]:
        t, f, _, _ = response(S, h, dP, t_end=20.0)
        a2.plot(t, f, color=c, lw=2.2, label=f"{lab}  nadir {f.min():.2f} Hz")
    a2.axhline(59.0, color=C_MAIN, ls="--", lw=1.2)
    a2.text(11, 59.05, "UFR 59.0 Hz", fontsize=11, color=C_MAIN)
    a2.set_xlabel("時間 [s]"); a2.set_ylabel("周波数 [Hz]"); a2.set_xlim(0, 20); a2.set_ylim(57.5, 60.2)
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False, loc="lower right")
    a2.set_title("慣性が減ると落ち方が速く、最低点も深い", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch08_rocof.png"); plt.close(fig)
    OUT["rocof45"] = dP * F0 / (2 * 4.5 * S)
    OUT["rocof20"] = dP * F0 / (2 * 2.0 * S)


# ============================================================ 8. 制御の階層
def fig_hierarchy():
    fig, ax = plt.subplots(figsize=(9.8, 3.8))
    ax.axis("off")
    stages = [("慣性応答", "0〜数秒", "回転体の運動エネルギー", "制御なし・自動", C_ACC),
              ("ガバナ（調速）", "数秒〜数十秒", "周波数低下を見て出力増", "偏差が残る", C_WARM),
              ("LFC", "数十秒〜十数分", "中給からの PI 制御", "偏差を 0 に戻す", C_SEC),
              ("EDC / ELD", "数分〜", "経済的な配分に組み替え", "第14回へ", C_BLUE)]
    for i, (name, tsc, what, note, c) in enumerate(stages):
        x = 0.02 + i * 0.245
        ax.add_patch(FancyBboxPatch((x, 0.30), 0.215, 0.46, boxstyle="round,pad=0.012",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x + 0.108, 0.68, name, ha="center", fontsize=11.5, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.108, 0.59, tsc, ha="center", fontsize=11.5, color=C_GREY, transform=ax.transAxes)
        ax.text(x + 0.108, 0.47, what, ha="center", fontsize=11, transform=ax.transAxes)
        ax.text(x + 0.108, 0.36, note, ha="center", fontsize=11, color=c, transform=ax.transAxes)
        if i < 3:
            ax.annotate("", xy=(x + 0.238, 0.53), xytext=(x + 0.218, 0.53), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=C_GREY, lw=2))
    ax.text(0.5, 0.13, "速い順に効く。前段が時間を稼ぎ、後段が精度を上げる",
            ha="center", fontsize=11, color=C_MAIN, transform=ax.transAxes)
    savefig(fig, "ch08_hierarchy.png"); plt.close(fig)


# ============================================================ 9. 連系系統と AR
def fig_tie():
    SA, SB, pctK = 300.0, 500.0, 1.0
    KA, KB = K_of(SA, pctK), K_of(SB, pctK)
    L = 50.0
    dPA, dPB = -L, 0.0
    dF = (dPA + dPB) / (KA + KB)
    dPT = (KB * dPA - KA * dPB) / (KA + KB)
    dF_alone = dPA / KA
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.axis("off")
    for x, name, S, K, c in [(0.08, "A 系統", SA, KA, C_MAIN), (0.60, "B 系統", SB, KB, C_SEC)]:
        a1.add_patch(FancyBboxPatch((x, 0.35), 0.30, 0.40, boxstyle="round,pad=0.015",
                                    transform=a1.transAxes, fc="#FBFAF6", ec=c, lw=2))
        a1.text(x + 0.15, 0.66, name, ha="center", fontsize=12, weight="bold", color=c, transform=a1.transAxes)
        a1.text(x + 0.15, 0.55, f"{S:.0f} MW", ha="center", fontsize=12, transform=a1.transAxes)
        a1.text(x + 0.15, 0.44, f"K = {K:.0f} MW/Hz", ha="center", fontsize=12, transform=a1.transAxes)
    a1.annotate("", xy=(0.60, 0.55), xytext=(0.38, 0.55), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="<->", color=C_ACC, lw=2.5))
    a1.text(0.49, 0.60, "連系線", ha="center", fontsize=12, color=C_ACC, transform=a1.transAxes)
    a1.text(0.49, 0.30, f"ΔP_T = {dPT:.1f} MW\nB → A の応援", ha="center", va="top",
            fontsize=11, color=C_ACC, weight="bold", transform=a1.transAxes)
    a1.text(0.23, 0.84, f"負荷 +{L:.0f} MW", ha="center", fontsize=11.5, color=C_WARM,
            weight="bold", transform=a1.transAxes)
    a1.text(0.5, 0.04, f"ΔF = (ΔP_A + ΔP_B)/(K_A + K_B) = {dF:.3f} Hz", ha="center",
            fontsize=11.5, color=C_MAIN, transform=a1.transAxes)
    labels = ["A 単独", "A + B 連系"]
    vals = [abs(dF_alone), abs(dF)]
    bars = a2.bar(labels, vals, color=[C_ACC, C_SEC], width=0.5)
    for b, v in zip(bars, vals):
        a2.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.3f} Hz", ha="center", fontsize=11, weight="bold")
    a2.set_ylabel("周波数偏差の大きさ |ΔF| [Hz]"); a2.grid(alpha=0.3, axis="y")
    a2.set_ylim(0, max(vals) * 1.3)
    a2.set_title(f"連系で {abs(dF_alone)/abs(dF):.1f} 分の 1 に", fontsize=12.5)
    fig.tight_layout(); savefig(fig, "ch08_tie.png"); plt.close(fig)
    OUT["tie"] = (KA, KB, dF, dPT, dF_alone)


# ============================================================ 10. LFC ゲインの影響
def fig_lfc_gain():
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    K = K_of(1500.0)
    for mult, c, lab in [(0.2, C_LIGHT, "β 小（戻りが遅い）"),
                         (1.0, C_MAIN, "β 適正"),
                         (6.0, C_ACC, "β 大（行き過ぎ・振動）")]:
        t, f, _, _ = response(1500.0, 4.5, -250.0, beta=0.02 * K * mult, t_end=200.0)
        ax.plot(t, f, color=c, lw=2.2, label=lab)
    ax.axhline(F0, color=C_GREY, ls=":", lw=1.2)
    ax.set_xlabel("時間 [s]"); ax.set_ylabel("周波数 [Hz]"); ax.set_xlim(0, 200); ax.set_ylim(57.8, 60.6)
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="lower right")
    ax.set_title("LFC の積分ゲイン β — 大きすぎても小さすぎても良くない", fontsize=11.5)
    savefig(fig, "ch08_lfc_gain.png"); plt.close(fig)




# ============================================================ 11〜14. 数式・導出・例題の図版
from pws_eqfig import eq_figure, derivation_figure, worked_example, analogy_figure


def fig_eq_and_examples():
    eq_figure("ch08_eq_kdf.png",
              latex=r"$\Delta P \;=\; K\,\Delta F$",
              terms=[("ΔP", "需給アンバランス [MW]", "発電が余れば正\n足りなければ負", C_ACC),
                     ("K", "系統定数 [MW/Hz]", "周波数 1 Hz あたり\n何 MW 動くか", C_MAIN),
                     ("ΔF", "周波数偏差 [Hz]", "発電不足なら負\n（周波数が下がる）", C_SEC)],
              read="需給の食い違いを、系統の硬さで割ったものが周波数のずれになる。",
              note="実務の単位は %MW/0.1Hz。K [MW/Hz] = %K × S / 10（S は系統容量）。")

    eq_figure("ch08_eq_rocof.png",
              latex=r"$\dfrac{df}{dt} \;=\; \dfrac{\Delta P\, f_0}{2\,H_{sys}\,S}$",
              terms=[("H_sys", "系統慣性定数 [s]", "回転体の運動エネルギー\n÷ 系統容量", C_MAIN),
                     ("S", "系統容量 [MW]", "沖縄 1,500\n九州 16,000", C_SEC),
                     (r"$f_0$", "定格周波数 [Hz]", "沖縄・西日本は 60\n東日本は 50", C_WARM),
                     ("ΔP", "アンバランス [MW]", "脱落が大きいほど\n速く落ちる", C_ACC)],
              read="慣性が小さいほど、同じ事故でも周波数は速く落ちる。",
              note="沖縄（H = 4.5 s）で 250 MW 脱落なら −1.11 Hz/s。1 秒で 1 Hz 落ちる。")

    derivation_figure("ch08_deriv_kdf.png",
        steps=[("発電側：ガバナが出力を上げる", r"$\Delta G = -K_G\,\Delta F$",
                "周波数が下がると出力が増える。\n傾きは速度調定率から決まる"),
               ("負荷側：モータ負荷が自然に減る", r"$\Delta L = +K_L\,\Delta F$",
                "負荷の自己制御性。\n制御装置なしに働く"),
               ("釣り合い：両者で吸収される", r"$\Delta P + (\Delta G - \Delta L) = 0$",
                "アンバランスは発電の増加と\n負荷の減少で受け止められる")],
        result=(r"$\Delta P = (K_G + K_L)\,\Delta F = K\,\Delta F$",
                "K が大きいほど、同じ ΔP でも周波数は動かない"))

    derivation_figure("ch08_deriv_tie.png",
        steps=[("各系統のバランスを書く", r"$\Delta P_A = K_A \Delta F + \Delta P_T$",
                "自分の分と連系線の分。\nB 系統も同じ形（符号が逆）"),
               ("足すと連系線が消える", r"$\Delta F = \dfrac{\Delta P_A + \Delta P_B}{K_A + K_B}$",
                "周波数は系統全体で 1 つ、\nが式に表れる"),
               ("引くと潮流が出る", r"$\Delta P_T = \dfrac{K_B \Delta P_A - K_A \Delta P_B}{K_A + K_B}$",
                "測った ΔF と ΔP_T から\n各系統の AR を逆算できる")],
        result=(r"$AR_A = K_A \Delta F + \Delta P_T$",
                "これが TBC の地域要求量。沖縄には連系線が無い"))

    worked_example("ch08_example_trip.png",
        given=[("系統容量 S", "1,500 MW"), ("系統定数 %K", "1.0 %MW/0.1Hz"),
               ("慣性定数 H", "4.5 s"), ("脱落量 ΔP", "−250 MW")],
        steps=[("系統定数を MW/Hz に直す", r"$K = \%K \times S/10 = 1.0 \times 1500/10$", "150 MW/Hz"),
               ("定常の周波数偏差", r"$\Delta F = \Delta P/K = -250/150$", "−1.67 Hz"),
               ("落ち方の速さ（RoCoF）", r"$\Delta P f_0/(2HS) = -250 \times 60/(2 \times 4.5 \times 1500)$", "−1.11 Hz/s"),
               ("59 Hz に達するまで", r"$1.0\ \mathrm{Hz} \div 1.11\ \mathrm{Hz/s}$", "0.9 s")],
        answer="定常 58.33 Hz。1 秒足らずで 59 Hz を割り、ガバナが間に合わない")

    worked_example("ch08_example_droop.png",
        given=[("速度調定率 ε", "5 %"), ("定格出力 G_N", "300 MW"),
               ("定格周波数 F_N", "60 Hz"), ("周波数低下", "0.2 Hz")],
        steps=[("無負荷と全負荷の周波数差", r"$F_0 - F_N = \varepsilon F_N/100 = 0.05 \times 60$", "3.0 Hz"),
               ("発電力特性（%表示）", r"$\%K_G = 10000/(\varepsilon F_N) = 10000/300$", "33.3 %MW/Hz"),
               ("MW に直す", r"$K_G = 33.3/100 \times 300$", "100 MW/Hz"),
               ("出力の増加量", r"$\Delta G = K_G \times 0.2$", "20 MW")],
        answer="0.2 Hz の低下で 20 MW 増える。ε が小さいほど強く効く")


# ==================================================== 11. 3 つの時間帯（過渡と定常を分ける）
def fig_timescales():
    """同じ 250 MW 脱落を 3 つの時間窓で見る。RoCoF / 最低点 / 最終値は別々の量。"""
    fig = plt.figure(figsize=(12.6, 6.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.30, 1.00], hspace=0.52, wspace=0.26,
                          left=0.055, right=0.975, top=0.875, bottom=0.05)
    cases = [("沖縄本島", 1500.0, 4.5, C_ACC), ("九州", 16000.0, 5.0, C_SEC)]
    dP = -250.0
    sim = {}
    for name, S, H, c in cases:
        t, f, _, _ = response(S, H, dP, t_end=300.0)
        t0, f0_, _, _ = response(S, H, dP, t_end=300.0, lfc=False)
        sim[name] = dict(t=t, f=f, t0=t0, f0=f0_, S=S, H=H, c=c,
                         rocof=F0 / (2 * H * S) * dP, K=K_of(S),
                         nadir=f.min(), tn=t[int(np.argmin(f))], dfs=dP / K_of(S))

    windows = [(0.0, 2.0, "0 〜 数秒"), (0.0, 30.0, "数秒 〜 十数秒"), (0.0, 300.0, "数十秒 〜 数分")]
    band = [C_MAIN, C_WARM, C_SEC]
    for i, (ta, tb, lab) in enumerate(windows):
        ax = fig.add_subplot(gs[0, i])
        for name, S, H, c in cases:
            d = sim[name]
            m = (d["t"] >= ta) & (d["t"] <= tb)
            ax.plot(d["t"][m], d["f"][m], color=c, lw=2.4, label=name)
            if i == 2 and name == "沖縄本島":            # LFC が無い場合の行き先だけ点線で
                m0 = (d["t0"] >= 20.0) & (d["t0"] <= tb)
                ax.plot(d["t0"][m0], d["f0"][m0], color=c, lw=1.6, ls=":", alpha=0.9)
        d = sim["沖縄本島"]
        if i == 0:                                       # 接線 = RoCoF
            tt = np.linspace(0, 1.2, 10)
            ax.plot(tt, F0 + d["rocof"] * tt, color=C_GREY, lw=1.4, ls="--")
            ax.text(0.97, 0.62, f"接線の傾き = RoCoF\n沖縄 {d['rocof']:.2f} Hz/s",
                    transform=ax.transAxes, ha="right", va="top",
                    fontsize=11, color=C_GREY)
        if i == 1:                                       # 最低点
            for name, _, _, c in cases:
                dd = sim[name]
                ax.scatter([dd["tn"]], [dd["nadir"]], color=c, s=55, zorder=5)
            ax.annotate(f"最低 {d['nadir']:.2f} Hz", (d["tn"], d["nadir"]),
                        textcoords="offset points", xytext=(18, 2),
                        fontsize=11.5, color=C_ACC, weight="bold")
        if i == 2:
            ax.set_ylim(57.9, 60.35)
            ax.text(292, d["f0"][-1] + 0.16, f"LFC 無しなら {d['f0'][-1]:.2f} Hz",
                    fontsize=11, color=C_ACC, va="bottom", ha="right")
        ax.axhline(F0, color=C_GREY, lw=0.9, ls=":")
        ax.set_xlim(ta, tb)
        ax.set_xlabel("時間 [s]")
        if i == 0:
            ax.set_ylabel("周波数 [Hz]")
        ax.set_title(lab, fontsize=13.5, color=band[i], weight="bold", pad=8)
        ax.grid(alpha=0.25)
    fig.legend(*fig.axes[0].get_legend_handles_labels(), loc="upper center",
               ncol=2, frameon=False, fontsize=12, bbox_to_anchor=(0.5, 1.0))

    rows = [
        ("慣性が支える", "落ち方の速さ RoCoF",
         "df/dt = ΔP·f_0 / (2 H S)",
         [("沖縄", f"{sim['沖縄本島']['rocof']:.2f} Hz/s"),
          ("九州", f"{sim['九州']['rocof']:.2f} Hz/s")]),
        ("ガバナが効き始める", "最低点（nadir）",
         "慣性とガバナの競争。式 1 本では書けない",
         [("沖縄", f"{sim['沖縄本島']['nadir']:.2f} Hz"),
          ("九州", f"{sim['九州']['nadir']:.2f} Hz")]),
        ("LFC が偏差を消す", "LFC 無しの定常偏差",
         "ΔF = ΔP / K。LFC を入れれば 0 に戻る",
         [("沖縄", f"{sim['沖縄本島']['dfs']:+.2f} Hz"),
          ("九州", f"{sim['九州']['dfs']:+.2f} Hz")]),
    ]
    for i, (主役, 量, 式, vals) in enumerate(rows):
        ax = fig.add_subplot(gs[1, i]); ax.axis("off")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                                    fc="#FBFAF6", ec=band[i], lw=1.8, transform=ax.transAxes))
        ax.text(0.5, 0.90, 主役, ha="center", va="center", fontsize=13,
                color=band[i], weight="bold")
        ax.text(0.5, 0.71, "決まる量：" + 量, ha="center", va="center", fontsize=11.5,
                color="#1A1A17")
        ax.text(0.5, 0.53, 式, ha="center", va="center", fontsize=12, color=C_GREY)
        for j, (nm, v) in enumerate(vals):
            x = 0.28 + j * 0.44
            ax.text(x, 0.31, nm, ha="center", va="center", fontsize=12, color=C_GREY)
            ax.text(x, 0.15, v, ha="center", va="center", fontsize=15,
                    color=C_ACC if j == 0 else C_SEC, weight="bold")
    savefig(fig, "ch08_timescales.png")
    plt.close(fig)
    OUT["ts"] = {k: (v["rocof"], v["nadir"], v["dfs"]) for k, v in sim.items()}


# ==================================================== 12. 単位換算（%MW/0.1Hz → MW/Hz）
def fig_unit():
    derivation_figure("ch08_unit.png",
        steps=[("%K の定義を言葉に戻す", "%K = 1.0  [%MW/0.1Hz]",
                "周波数が 0.1 Hz 動くと\n容量の 1.0 % が動く、という約束"),
               ("容量の 1 % は何 MW か", r"$1500 \times 1.0/100 = 15$  MW",
                "沖縄の 1 % は 15 MW。\nこれが「0.1 Hz あたり」の量"),
               ("1 Hz あたりに直す", r"$15 \div 0.1 = 150$  MW/Hz",
                "0.1 Hz で 15 MW なら\n1 Hz では 10 倍の 150 MW")],
        result=(r"$K = \dfrac{\%K \times S}{10}$  [MW/Hz]",
                "「10 で割る」の中身は、100 で割って 0.1 で割ること"))


# ==================================================== 13. たとえ話の対応表
def fig_analogy():
    analogy_figure("ch08_analogy.png",
        left_title="天秤（たとえ）", right_title="電力系統（実物）",
        pairs=[("左の皿に「発電」、右の皿に「消費」を載せる", "皿の重さの差＝需給アンバランス ΔP [MW]"),
               ("重さが釣り合わないと、天秤は傾く", "傾きの大きさ＝周波数偏差 ΔF [Hz]"),
               ("天秤の腕が重いほど、傾き出すのが遅い", "動き出しの遅さ＝慣性定数 H [s]"),
               ("傾きを見て錘を足し直す係がいる", "錘を足す係＝ガバナ（速い）と LFC（正確）"),
               ("隣の天秤と棒でつなぐと、傾きが分散する", "つなぐ棒＝連系線（沖縄本島には無い）")],
        note="この対応が頭に入っていれば、式は全部「天秤の話」に翻訳できる。")


# ==================================================== 14. 実際の事故と「抜けた割合」
def fig_cases():
    """3 つの事例を「脱落量 ÷ 系統の大きさ」で並べる。沖縄がどこに位置するかを見る。"""
    cases = [
        ("2019年8月\n英国大停電", 30000.0, 1400.0, "48.8 Hz まで低下\n約 100 万戸が停電", C_SEC),
        ("沖縄本島\n（本日の想定）", 1500.0, 250.0, "最低 58.12 Hz\nUFR 整定 59.0 Hz を割る", C_WARM),
        ("2018年9月\n北海道ブラックアウト", 3100.0, 1300.0, "支えきれず全域停電\n約 295 万戸・復旧 45 時間", C_ACC),
    ]
    fig = plt.figure(figsize=(12.4, 5.9))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.05], hspace=0.42,
                          left=0.055, right=0.975, top=0.93, bottom=0.10)

    ax = fig.add_subplot(gs[0])
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    for i, (name, S, dP, result, c) in enumerate(cases):
        x = 0.012 + i * 0.3293
        ax.add_patch(FancyBboxPatch((x, 0.03), 0.3053, 0.94,
                                    boxstyle="round,pad=0.012", fc="#FBFAF6",
                                    ec=c, lw=1.8, transform=ax.transAxes))
        ax.text(x + 0.1527, 0.80, name, ha="center", va="center", fontsize=13,
                color=c, weight="bold")
        ax.text(x + 0.1527, 0.50, f"系統 {S:,.0f} MW　脱落 {dP:,.0f} MW",
                ha="center", va="center", fontsize=11.5, color="#1A1A17")
        ax.text(x + 0.1527, 0.20, result, ha="center", va="center",
                fontsize=11, color=C_GREY)

    a2 = fig.add_subplot(gs[1])
    ratio = [c[2] / c[1] * 100 for c in cases]
    cols = [c[4] for c in cases]
    bars = a2.bar(range(len(cases)), ratio, color=cols, width=0.42)
    for b, r in zip(bars, ratio):
        a2.text(b.get_x() + b.get_width() / 2, r + 1.2, f"{r:.0f} %", ha="center",
                fontsize=17, weight="bold", color=b.get_facecolor())
    a2.set_xticks(range(len(cases))); a2.set_xticklabels([])
    a2.set_xlim(-0.5, len(cases) - 0.5); a2.set_ylim(0, 50)
    a2.set_ylabel("抜けた電源の割合\nΔP ÷ 系統容量 S　[%]")
    a2.grid(alpha=0.3, axis="y"); a2.tick_params(axis="x", length=0)
    savefig(fig, "ch08_cases.png"); plt.close(fig)


# ==================================================== 15. よくある誤解
def fig_myth():
    analogy_figure("ch08_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("周波数は場所ごとに違う値をとる",
                "つながっている限り、周波数は系統全体で 1 つ。場所で違うのは電圧のほう"),
               ("1 台落ちても他が自動で埋めるから、周波数は変わらない",
                "ガバナが出力を上げるには、まず周波数が下がる必要がある。偏差 ΔF = ΔP/K が残る"),
               ("K を大きくすれば、最低点も浅くなる",
                "最低点を決めるのは慣性 H とガバナの速さ。K が決めるのは落ち着く先")],
        note="どれも「いつの話か」を取り違えたことから来ている。")


if __name__ == "__main__":
    fig_balance(); fig_droop(); fig_intersection(); fig_compare(); fig_stages()
    fig_dfdp(); fig_rocof(); fig_hierarchy(); fig_tie(); fig_lfc_gain()
    fig_eq_and_examples(); fig_timescales(); fig_unit(); fig_analogy(); fig_cases(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    print(f"沖縄 K = {OUT['K_oki']:.0f} MW/Hz、250 MW 脱落で定常 ΔF = {OUT['dF_oki']:.2f} Hz")
    for name, (nadir, fend, K) in OUT["nadir"].items():
        print(f"  {name}: K = {K:.0f} MW/Hz, nadir = {nadir:.2f} Hz, 5 分後 = {fend:.3f} Hz")
    print(f"沖縄の nadir = {OUT['nadir_oki']:.2f} Hz（t = {OUT['t_nadir']:.1f} s）")
    print(f"RoCoF: H=4.5 s で {OUT['rocof45']:.2f} Hz/s、H=2.0 s で {OUT['rocof20']:.2f} Hz/s")
    KA, KB, dF, dPT, dFa = OUT["tie"]
    print(f"連系: K_A={KA:.0f}, K_B={KB:.0f} MW/Hz、ΔF={dF:.3f} Hz、ΔP_T={dPT:.1f} MW、A 単独なら {dFa:.3f} Hz")
    print(f"ε=5%・定格 300 MW の K_G = {OUT['Kg_5pct']:.1f} MW/Hz")
