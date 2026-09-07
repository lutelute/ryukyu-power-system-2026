# -*- coding: utf-8 -*-
"""第2回 電力システムの構成 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch02.py  → ../図/ch02_*.png
"""
import numpy as np
from pws_common import setup_japanese_font, savefig, OKINAWA_BUSES, OKINAWA_LINES, OKINAWA_LOADS
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from pws_eqfig import analogy_figure

# ---- 共通スタイル（スライドの terracotta パレットに合わせる）----
C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
C_INK = "#1A1A17"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": C_INK, "figure.dpi": 100})

# ---- この回の共通条件：100 MW を 100 km、R = 0.1 Ω/km、力率 0.9 ----
P_MW, LEN_KM, R_PER_KM, PF = 100.0, 100.0, 0.1, 0.9
R_OHM = R_PER_KM * LEN_KM
LEVELS = [66, 154, 275, 500]


def current_A(P_mw, V_kv, pf):
    """三相送電の線路電流 I = P/(√3 V cosφ)"""
    return P_mw * 1e6 / (np.sqrt(3) * V_kv * 1e3 * pf)


def loss_MW(P_mw, V_kv, pf, R=R_OHM):
    """三相のジュール損 3I²R [MW]"""
    return 3 * current_A(P_mw, V_kv, pf) ** 2 * R / 1e6


# ============================================================ 1. 系統の階層図（電圧の山）
def fig_hierarchy():
    stages = [("発電機", 20.0, "10〜25 kV"), ("主変圧器\n（昇圧）", 500.0, "275〜500 kV"),
              ("基幹送電線", 500.0, "275〜500 kV"), ("一次変電所", 154.0, "154 / 66 kV"),
              ("配電用変電所", 6.6, "6.6 kV"), ("柱上変圧器", 0.1, "100 / 200 V"), ("需要家", 0.1, "100 / 200 V")]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10.5, 5.0), gridspec_kw={"height_ratios": [2.0, 0.85], "hspace": 0.08}, sharex=True)
    x = np.arange(len(stages)) * 1.5
    V = np.array([s[1] for s in stages])
    for i in range(len(stages)):
        a1.plot([x[i] - 0.55, x[i] + 0.55], [V[i], V[i]], color=C_MAIN, lw=3.2, solid_capstyle="round")
        # 隣と同じ電圧表示なら（主変圧器→基幹送電線）ラベルは重なるので省く
        if i == 0 or stages[i][2] != stages[i - 1][2]:
            a1.text(x[i], V[i] * 1.6, stages[i][2], ha="center", va="bottom", fontsize=11, color=C_MAIN, weight="bold")
        if i < len(stages) - 1:
            a1.plot([x[i] + 0.55, x[i + 1] - 0.55], [V[i], V[i + 1]], color=C_MAIN, lw=1.2, ls=":")
    xs = np.concatenate([[x[0] - 0.55]] + [[xi - 0.55, xi + 0.55] for xi in x] + [[x[-1] + 0.55]])
    vs = np.concatenate([[V[0]]] + [[vi, vi] for vi in V] + [[V[-1]]])
    a1.fill_between(xs, 0.03, vs, color="#E8C9C3", alpha=0.45, step=None)
    a1.axvspan(x[1] - 0.7, x[3] + 0.7, color=C_SEC, alpha=0.08)
    a1.text((x[1] + x[3]) / 2, 0.07, "送電：高電圧で損失を抑える区間", ha="center", fontsize=11, color=C_SEC)
    a1.annotate("", xy=(x[1] - 0.55, 400), xytext=(x[0] + 0.55, 25), arrowprops=dict(arrowstyle="-|>", color=C_ACC, lw=1.8))
    a1.text(x[1] - 0.45, 40, f"昇圧 ×{500/20:.0f}", fontsize=11.5, color=C_ACC, weight="bold", ha="left")
    a1.text(x[4] - 0.2, 60, "降圧", fontsize=11.5, color=C_BLUE, weight="bold")
    a1.set_yscale("log"); a1.set_ylim(0.03, 4000)
    a1.set_yticks([0.1, 1, 10, 100, 1000]); a1.set_yticklabels(["100 V", "1 kV", "10 kV", "100 kV", "1000 kV"])
    a1.set_ylabel("電圧（対数）"); a1.grid(axis="y", alpha=0.3)
    a1.set_title("電気の旅 — 上げて運び、下げて使う（電圧は発電機の 25 倍まで上がり、5,000 分の 1 まで下がる）", fontsize=11.5)
    for i, (name, _, _) in enumerate(stages):
        a2.add_patch(FancyBboxPatch((x[i] - 0.6, 0.15), 1.2, 0.7, boxstyle="round,pad=0.04", fc="#F2EFE6", ec=C_MAIN, lw=1.4))
        a2.text(x[i], 0.5, name, ha="center", va="center", fontsize=11, color=C_INK)
        if i < len(stages) - 1:
            a2.annotate("", xy=(x[i + 1] - 0.62, 0.5), xytext=(x[i] + 0.62, 0.5), arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=1.5))
    a2.set_ylim(0, 1); a2.set_xlim(x[0] - 0.9, x[-1] + 0.9); a2.axis("off")
    savefig(fig, "ch02_hierarchy.png"); plt.close(fig)
    return V


# ============================================================ 2. 損失率 vs 電圧
def fig_loss_voltage():
    V = np.linspace(30, 620, 500)
    rate = loss_MW(P_MW, V, PF) / P_MW * 100
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    ax.plot(V, rate, color=C_MAIN, lw=2.3, label=f"損失率 = R P / (V² cos²φ)（P = {P_MW:.0f} MW, R = {R_OHM:.0f} Ω, cos φ = {PF}）")
    ax.axhline(100, color=C_GREY, ls=":", lw=1.2); ax.text(55, 118, "損失 100%（送れない）", fontsize=11, color=C_GREY)
    out = {}
    offs = {66: (14, 6), 154: (14, 6), 275: (14, 4), 500: (14, 12)}
    for v in LEVELS:
        I, L = current_A(P_MW, v, PF), loss_MW(P_MW, v, PF)
        r = L / P_MW * 100; out[v] = (I, L, r)
        ax.scatter([v], [r], color=C_ACC, s=55, zorder=4)
        ax.annotate(f"{v} kV：I = {I:,.0f} A\n損失 {L:.2f} MW（{r:.1f}%）", (v, r), textcoords="offset points",
                    xytext=offs[v], fontsize=11, color=C_INK)
    ax.text(150, 0.45, "対数軸で傾き −2：電圧 2 倍で損失 1/4", fontsize=11, color=C_MAIN)
    ax.set_yscale("log"); ax.set_ylim(0.2, 300); ax.set_xlim(30, 620)
    ax.set_xlabel("送電電圧 V [kV]（線間）"); ax.set_ylabel("損失率 [%]（対数）"); ax.grid(alpha=0.3, which="both")
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title(f"{P_MW:.0f} MW を {LEN_KM:.0f} km 送る損失率 — 電圧の 2 乗に反比例、66 → 500 kV で {out[66][2]/out[500][2]:.0f} 分の 1", fontsize=11)
    savefig(fig, "ch02_loss_voltage.png"); plt.close(fig)
    return out


# ============================================================ 3. 損失 vs 力率
def fig_loss_pf():
    pf = np.linspace(0.6, 1.0, 300)
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ax.plot(pf, 1 / pf ** 2, color=C_MAIN, lw=2.3, label="損失の倍率 1 / cos²φ（力率 1.0 を 1 とする）")
    out = {}
    for p, (tx, ty, ha, va) in [(0.8, (0.8, 1.92, "center", "bottom")), (0.9, (0.9, 1.66, "center", "bottom")),
                                (0.95, (0.95, 1.40, "center", "bottom")), (1.0, (1.0, 0.92, "right", "top"))]:
        r = 1 / p ** 2; L = loss_MW(P_MW, 275, p); out[p] = (r, L)
        ax.scatter([p], [r], color=C_ACC, s=55, zorder=4)
        ax.plot([p, p], [r, ty], color=C_GREY, lw=0.8, ls=":", zorder=1)
        ax.text(tx, ty, f"cos φ = {p:.2f}：{r:.2f} 倍\n275 kV なら {L:.2f} MW", ha=ha, va=va, fontsize=11, color=C_INK)
    ax.axvspan(0.85, 1.0, color=C_SEC, alpha=0.08); ax.text(0.925, 2.45, "実系統の運用範囲", ha="center", fontsize=11, color=C_SEC)
    ax.set_xlim(0.6, 1.02); ax.set_ylim(0.7, 3.0)
    ax.set_xlabel("力率 cos φ"); ax.set_ylabel("損失の倍率"); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title("もう 1 つの 2 乗 — 力率 0.8 で損失 1.56 倍、力率改善は設備を増やさない省エネ", fontsize=11)
    savefig(fig, "ch02_loss_pf.png"); plt.close(fig)
    return out


# ============================================================ 4. 単線結線図（3 母線・3 線路）
def _bus(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], color=C_INK, lw=5.5, solid_capstyle="butt", zorder=3)


def _cb(ax, x, y, s=0.17):
    ax.add_patch(Rectangle((x - s / 2, y - s / 2), s, s, fc="white", ec=C_MAIN, lw=1.7, zorder=4))


def _trafo(ax, x, y, r=0.19, vertical=False):
    d = 0.105
    cs = [(x, y + d), (x, y - d)] if vertical else [(x - d, y), (x + d, y)]
    for c in cs:
        ax.add_patch(Circle(c, r, fc="white", ec=C_MAIN, lw=1.7, zorder=4))


def _gen(ax, x, y, r=0.27):
    ax.add_patch(Circle((x, y), r, fc="#F2EFE6", ec=C_MAIN, lw=1.9, zorder=4))
    ax.text(x, y, "G", ha="center", va="center", fontsize=11, weight="bold", color=C_MAIN, zorder=5)


def _load(ax, x, y, dy=-0.45):
    ax.annotate("", xy=(x, y + dy), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", color=C_SEC, lw=2.2, mutation_scale=16), zorder=4)


def _ds(ax, x, y):
    """断路器：線路に隙間を作って斜めの刃を描く（水平線路用）"""
    ax.plot([x - 0.12, x - 0.12], [y - 0.06, y + 0.06], color=C_MAIN, lw=1.5, zorder=4)
    ax.plot([x - 0.12, x + 0.16], [y, y + 0.2], color=C_MAIN, lw=1.7, zorder=4)


def _seg(ax, x0, y0, x1, y1, c=None, lw=1.8):
    ax.plot([x0, x1], [y0, y1], color=c or C_INK, lw=lw, zorder=2)


def fig_sld():
    fig, ax = plt.subplots(figsize=(11.5, 4.9)); ax.set_aspect("equal")
    B1, B2, B3 = 2.7, 6.2, 9.7
    for x in (B1, B2, B3):
        _bus(ax, x, -0.9, 0.9)
    ax.text(B1 - 0.15, 0.55, "母線 1", ha="right", fontsize=11.5, weight="bold", color=C_MAIN)
    ax.text(B2, 1.02, "母線 2", ha="center", va="bottom", fontsize=11.5, weight="bold", color=C_MAIN)
    ax.text(B3 + 0.15, 0.55, "母線 3", ha="left", fontsize=11.5, weight="bold", color=C_MAIN)
    ax.text(B1 - 0.15, 0.25, "275 kV", ha="right", fontsize=11, color=C_GREY)
    ax.text(B3 + 0.15, 0.25, "275 kV", ha="left", fontsize=11, color=C_GREY)
    # 発電機 → 主変圧器 → CB → 母線 1
    _gen(ax, 0.5, 0.0); _seg(ax, 0.77, 0, 1.2, 0); _trafo(ax, 1.42, 0.0); _seg(ax, 1.64, 0, 2.15, 0); _cb(ax, 2.3, 0.0); _seg(ax, 2.39, 0, B1, 0)
    ax.text(0.5, -0.42, "G1\n20 kV", ha="center", va="top", fontsize=11, color=C_GREY)
    ax.text(1.42, -0.32, "Tr1\n20/275 kV", ha="center", va="top", fontsize=11, color=C_GREY)
    ax.text(2.3, -0.2, "CB", ha="center", va="top", fontsize=11, color=C_GREY)
    # 線路 L12（CB の外側に DS）
    y = 0.4
    _seg(ax, B1, y, 2.96, y); _cb(ax, 3.05, y); _seg(ax, 3.14, y, 3.33, y); _ds(ax, 3.45, y); _seg(ax, 3.55, y, 5.76, y); _cb(ax, 5.85, y); _seg(ax, 5.94, y, B2, y)
    ax.text(3.05, y + 0.14, "CB", ha="center", va="bottom", fontsize=11, color=C_GREY)
    ax.text(3.6, y + 0.3, "DS", ha="center", va="bottom", fontsize=11, color=C_GREY)
    ax.text(4.65, y + 0.12, "線路 L12", ha="center", va="bottom", fontsize=11, color=C_INK)
    # 線路 L23
    _seg(ax, B2, y, 6.46, y); _cb(ax, 6.55, y); _seg(ax, 6.64, y, 9.26, y); _cb(ax, 9.35, y); _seg(ax, 9.44, y, B3, y)
    ax.text(7.95, y + 0.12, "線路 L23", ha="center", va="bottom", fontsize=11, color=C_INK)
    # 線路 L13（上を回る）
    _seg(ax, B1, 0.9, B1, 1.11); _cb(ax, B1, 1.2); _seg(ax, B1, 1.29, B1, 1.7); _seg(ax, B1, 1.7, B3, 1.7)
    _seg(ax, B3, 1.7, B3, 1.29); _cb(ax, B3, 1.2); _seg(ax, B3, 1.11, B3, 0.9)
    ax.text(B2, 1.82, "線路 L13（ループを作る）", ha="center", va="bottom", fontsize=11, color=C_INK)
    # 負荷フィーダ（母線 2, 3 の下）
    for x, name in [(B2, "Tr2"), (B3, "Tr3")]:
        _seg(ax, x, -0.9, x, -1.06); _cb(ax, x, -1.15); _seg(ax, x, -1.24, x, -1.45); _trafo(ax, x, -1.75, vertical=True)
        _seg(ax, x, -2.05, x, -2.2); _load(ax, x, -2.2)
        ax.text(x + 0.28, -1.75, f"{name}\n275/66 kV", ha="left", va="center", fontsize=11, color=C_GREY)
    ax.text(B2, -2.75, "負荷 A（66 kV）", ha="center", va="top", fontsize=11, color=C_SEC)
    ax.text(B3, -2.75, "負荷 B（66 kV）", ha="center", va="top", fontsize=11, color=C_SEC)
    # 凡例
    lx, ty = 11.0, [1.55, 1.05, 0.55, 0.05, -0.45, -0.95, -1.45]
    _bus(ax, lx, ty[0] - 0.15, ty[0] + 0.15); ax.text(lx + 0.3, ty[0], "母線（太線）＝節点", va="center", fontsize=11)
    _cb(ax, lx, ty[1]); ax.text(lx + 0.3, ty[1], "遮断器 CB：事故電流を切る", va="center", fontsize=11)
    _seg(ax, lx - 0.15, ty[2], lx - 0.12, ty[2]); _ds(ax, lx, ty[2] - 0.05); ax.text(lx + 0.3, ty[2], "断路器 DS：無電流で開閉", va="center", fontsize=11)
    _trafo(ax, lx, ty[3]); ax.text(lx + 0.3, ty[3], "変圧器", va="center", fontsize=11)
    _gen(ax, lx, ty[4], r=0.2); ax.text(lx + 0.3, ty[4], "発電機", va="center", fontsize=11)
    _load(ax, lx, ty[5] + 0.2, dy=-0.4); ax.text(lx + 0.3, ty[5], "負荷", va="center", fontsize=11)
    _seg(ax, lx - 0.2, ty[6], lx + 0.2, ty[6]); ax.text(lx + 0.3, ty[6], "送電線＝枝", va="center", fontsize=11)
    ax.set_xlim(-0.1, 13.4); ax.set_ylim(-3.15, 2.2); ax.axis("off")
    ax.set_title("単線結線図の例 — 3 母線・3 線路。母線が節点、線路が枝。CB を開いてから DS を開く", fontsize=11.5)
    savefig(fig, "ch02_sld.png"); plt.close(fig)


# ============================================================ 5. 並列 2 回線の分流と 1 回線開放
def fig_parallel():
    Z1, Z2, I, RATING = 10.0, 15.0, 1000.0, 700.0
    I1, I2 = I * Z2 / (Z1 + Z2), I * Z1 / (Z1 + Z2)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    for k, ax in enumerate(axes):
        open1 = (k == 1)
        for x, name in [(0.0, "母線 A"), (4.0, "母線 B")]:
            ax.plot([x, x], [-1.15, 1.15], color=C_INK, lw=5.5, solid_capstyle="butt")
            ax.text(x, 1.28, name, ha="center", va="bottom", fontsize=11.5, weight="bold", color=C_MAIN)
        ax.annotate("", xy=(-0.05, 0), xytext=(-1.1, 0), arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=2.2))
        ax.text(-0.58, 0.16, f"I = {I:,.0f} A", ha="center", fontsize=11.5, color=C_INK)
        ax.annotate("", xy=(5.1, 0), xytext=(4.05, 0), arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=2.2))
        ax.text(4.58, 0.16, f"{I:,.0f} A", ha="center", fontsize=11.5, color=C_INK)
        y1, y2 = 0.65, -0.65
        ax.text(2.0, y1 + 0.28, f"回線 1　$Z_1$ = {Z1:.0f} Ω", ha="center", fontsize=11, color=C_GREY)
        ax.text(2.0, y2 - 0.42, f"回線 2　$Z_2$ = {Z2:.0f} Ω（定格 {RATING:.0f} A）", ha="center", va="top", fontsize=11, color=C_GREY)
        if open1:
            ax.plot([0, 1.45], [y1, y1], color=C_LIGHT, lw=2.5); ax.plot([2.55, 4], [y1, y1], color=C_LIGHT, lw=2.5)
            ax.text(2.0, y1, "× 開放", ha="center", va="center", fontsize=11, color=C_ACC, weight="bold")
            ax.text(2.0, y1 - 0.32, "$I_1$ = 0 A", ha="center", va="top", fontsize=12, color=C_GREY)
            cur2, c2 = I, C_ACC
            lab2 = f"$I_2$ = {cur2:,.0f} A（定格の {cur2/RATING*100:.0f}%：過負荷）"
        else:
            ax.plot([0, 4], [y1, y1], color=C_MAIN, lw=2.5)
            ax.annotate("", xy=(2.55, y1), xytext=(1.45, y1), arrowprops=dict(arrowstyle="-|>", color=C_MAIN, lw=2.5))
            ax.text(2.0, y1 - 0.32, f"$I_1$ = {I1:,.0f} A", ha="center", va="top", fontsize=12, color=C_MAIN, weight="bold")
            cur2, c2 = I2, C_MAIN
            lab2 = f"$I_2$ = {cur2:,.0f} A（定格の {cur2/RATING*100:.0f}%）"
        ax.plot([0, 4], [y2, y2], color=c2, lw=2.5 if not open1 else 4.0)
        ax.annotate("", xy=(2.55, y2), xytext=(1.45, y2), arrowprops=dict(arrowstyle="-|>", color=c2, lw=2.5))
        ax.text(2.0, y2 + 0.12, lab2, ha="center", va="bottom", fontsize=12, color=c2, weight="bold")
        ax.set_xlim(-1.3, 5.3); ax.set_ylim(-1.75, 1.75); ax.axis("off")
    axes[0].set_title(f"通常：$I_1/I_2 = Z_2/Z_1$ = {Z2:.0f}/{Z1:.0f} → {I1:,.0f} A / {I2:,.0f} A", fontsize=11)
    axes[1].set_title(f"回線 1 開放：残りが全電流 {I:,.0f} A を負う → {I/RATING*100:.0f}% 過負荷", fontsize=11, color=C_ACC)
    fig.tight_layout(); savefig(fig, "ch02_parallel.png"); plt.close(fig)
    return I1, I2, I / RATING * 100


# ============================================================ 6. 変圧器：巻数比・電流・インピーダンス換算
def fig_transformer():
    V1, V2, S = 275.0, 66.0, 100.0
    a = V1 / V2
    I1, I2 = S * 1e6 / (np.sqrt(3) * V1 * 1e3), S * 1e6 / (np.sqrt(3) * V2 * 1e3)
    Z2 = complex(0.5, 8.0); Z1 = a ** 2 * Z2
    Zb1, Zb2 = V1 ** 2 / S, V2 ** 2 / S
    pu1, pu2 = abs(Z1) / Zb1, abs(Z2) / Zb2
    fig, ax = plt.subplots(figsize=(10, 4.6)); ax.set_aspect("equal")
    # 一次側
    ax.annotate("", xy=(2.35, 0.9), xytext=(0.2, 0.9), arrowprops=dict(arrowstyle="-|>", color=C_MAIN, lw=2.4))
    ax.text(1.25, 1.05, f"$I_1$ = {I1:.0f} A", ha="center", va="bottom", fontsize=11, color=C_MAIN, weight="bold")
    ax.text(1.25, 0.62, f"$V_1$ = {V1:.0f} kV（一次）", ha="center", va="top", fontsize=11.5, color=C_INK)
    # 変圧器記号
    _trafo(ax, 3.0, 0.9, r=0.42)
    ax.text(3.0, 1.55, f"巻数比 a = $N_1/N_2 = V_1/V_2$ = {a:.2f}", ha="center", fontsize=12, color=C_MAIN, weight="bold")
    # 二次側
    ax.annotate("", xy=(5.8, 0.9), xytext=(3.65, 0.9), arrowprops=dict(arrowstyle="-|>", color=C_ACC, lw=3.2))
    ax.text(5.0, 1.05, f"$I_2 = a\\,I_1$ = {I2:.0f} A", ha="center", va="bottom", fontsize=11, color=C_ACC, weight="bold")
    ax.text(4.72, 0.62, f"$V_2$ = {V2:.0f} kV（二次）", ha="center", va="top", fontsize=11.5, color=C_INK)
    # 二次側のインピーダンスと一次換算
    ax.add_patch(Rectangle((5.8, 0.72), 1.2, 0.36, fc="#F2EFE6", ec=C_SEC, lw=1.6))
    ax.text(6.4, 0.9, "$Z_2$", ha="center", va="center", fontsize=12, color=C_SEC, weight="bold")
    ax.text(6.4, 1.3, f"$Z_2$ = {Z2.real:.1f} + j{Z2.imag:.1f} Ω", ha="center", va="bottom", fontsize=11, color=C_SEC)
    ax.add_patch(Rectangle((0.2, -0.85), 1.7, 0.55, fc="white", ec=C_SEC, lw=1.4, ls="--"))
    ax.text(1.05, -0.575, "一次から見た\n$Z_1 = a^2 Z_2$", ha="center", va="center", fontsize=11, color=C_SEC)
    ax.annotate("", xy=(2.05, -0.575), xytext=(6.4, 0.7), arrowprops=dict(arrowstyle="-|>", color=C_SEC, lw=1.2, ls="--", connectionstyle="arc3,rad=-0.3"))
    ax.text(5.0, -0.62, f"$a^2$ = {a**2:.1f}", ha="left", va="center", fontsize=11, color=C_SEC)
    # まとめの箱
    lines = [f"① 電圧は a 倍、電流は 1/a 倍：S = √3 $V_1 I_1$ = √3 $V_2 I_2$ = {S:.0f} MVA で保存",
             f"② $Z_1 = a^2 Z_2$ = {a**2:.1f} × ({Z2.real:.1f} + j{Z2.imag:.1f}) = {Z1.real:.1f} + j{Z1.imag:.0f} Ω（変圧器を挟むたびに換算が要る）",
             f"③ 単位法（第3回）：$|Z_1|/Z_{{base1}}$ = {abs(Z1):.1f}/{Zb1:.0f} = {pu1:.3f}、$|Z_2|/Z_{{base2}}$ = {abs(Z2):.2f}/{Zb2:.1f} = {pu2:.3f} → 両側で同じ値"]
    for i, t in enumerate(lines):
        ax.text(0.2, -1.25 - 0.4 * i, t, fontsize=11, color=C_INK, va="top")
    ax.set_xlim(0, 8.0); ax.set_ylim(-2.6, 1.9); ax.axis("off")
    ax.set_title(f"変圧器 {V1:.0f}/{V2:.0f} kV・{S:.0f} MVA — 電圧を a 倍にすると電流は 1/a 倍、インピーダンスは a² 倍", fontsize=11)
    savefig(fig, "ch02_transformer.png"); plt.close(fig)
    return a, I1, I2, Z1, pu1, pu2


# ============================================================ 7. 沖縄本島の簡略 5 母線モデル（pandapower の潮流つき）
def fig_okinawa():
    """5 母線のループ系統。潮流は直流法（第4回）で概算：B'θ = P、P_ij = (θ_i − θ_j)/x_ij"""
    pos = {0: (2.3, 1.7), 1: (1.1, 0.6), 2: (0.0, 0.0), 3: (0.6, 2.0), 4: (2.3, 3.6)}
    S_BASE, V_KV, X_PER_KM = 100.0, 132.0, 0.35
    z_base = V_KV ** 2 / S_BASE
    n = len(OKINAWA_BUSES)
    P = np.zeros(n); P[1] = 250.0                       # 牧港の発電
    for b, (p, q) in OKINAWA_LOADS.items():
        P[b] -= p
    P[0] = -P.sum()                                     # スラック（具志川）が残りを賄う
    B = np.zeros((n, n)); x = []
    for f, t, L, par in OKINAWA_LINES:
        xij = X_PER_KM * L / z_base / par; x.append(xij)   # 回線数だけリアクタンスが下がる
        B[f, f] += 1 / xij; B[t, t] += 1 / xij; B[f, t] -= 1 / xij; B[t, f] -= 1 / xij
    theta = np.zeros(n); theta[1:] = np.linalg.solve(B[1:, 1:], P[1:] / S_BASE)
    flows = np.array([(theta[f] - theta[t]) / x[k] * S_BASE for k, (f, t, L, par) in enumerate(OKINAWA_LINES)])
    fig, ax = plt.subplots(figsize=(9, 6)); ax.set_aspect("equal")
    lab_pos = [(1.72, 1.5, "right"), (1.15, -0.42, "center"), (-0.3, 1.05, "right"),
               (1.15, 3.02, "center"), (2.42, 2.65, "left")]
    for k, (f, t, L, par) in enumerate(OKINAWA_LINES):
        (x0, y0), (x1, y1) = pos[f], pos[t]
        p = flows[k]
        ax.plot([x0, x1], [y0, y1], color=C_MAIN, lw=1.5 + abs(p) / 60, zorder=1)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        (ax0, ay0), (ax1, ay1) = (pos[f], pos[t]) if p >= 0 else (pos[t], pos[f])
        d = np.hypot(ax1 - ax0, ay1 - ay0); ux, uy = (ax1 - ax0) / d, (ay1 - ay0) / d
        ax.annotate("", xy=(mx + ux * 0.2, my + uy * 0.2), xytext=(mx - ux * 0.2, my - uy * 0.2),
                    arrowprops=dict(arrowstyle="-|>", color=C_ACC, lw=2.2, mutation_scale=18), zorder=2)
        lx, ly, ha = lab_pos[k]
        ax.text(lx, ly, f"L{f+1}-{t+1}  {L:.0f} km\n{abs(p):.0f} MW", ha=ha, va="center", fontsize=11, color=C_GREY,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85), zorder=3)
    names_pos = {0: (2.55, 1.7, "left", "center"), 1: (1.35, 0.6, "left", "center"), 2: (-0.25, 0.0, "right", "center"),
                 3: (0.6, 2.3, "center", "bottom"), 4: (2.3, 3.88, "center", "bottom")}
    for b, (x0, y0) in pos.items():
        ax.add_patch(Circle((x0, y0), 0.17, fc="#F2EFE6", ec=C_MAIN, lw=2, zorder=4))
        tx, ty, ha, va = names_pos[b]
        ax.text(tx, ty, OKINAWA_BUSES[b], ha=ha, va=va, fontsize=11.5, weight="bold", color=C_INK, zorder=5)
    # 発電機（具志川：スラック、牧港：250 MW）
    for b, (gx, gy) in [(0, (2.45, 1.2)), (1, (1.2, 0.1))]:
        x0, y0 = pos[b]
        ax.plot([x0, gx], [y0, gy], color=C_SEC, lw=1.5, zorder=1)
        ax.add_patch(Circle((gx, gy), 0.17, fc="white", ec=C_SEC, lw=1.8, zorder=4))
        ax.text(gx, gy, "G", ha="center", va="center", fontsize=11, weight="bold", color=C_SEC, zorder=5)
        ax.text(gx + 0.25, gy, f"{P[b]:.0f} MW" + ("（スラック）" if b == 0 else ""), ha="left", va="center", fontsize=11, color=C_SEC)
    # 負荷（矢印の向きと文字の位置を母線ごとに指定）
    loads = {2: ((0.0, -0.2), (0.0, -0.62), (0.0, -0.7, "center", "top")),
             3: ((0.4, 2.0), (-0.02, 2.0), (-0.08, 2.0, "right", "center")),
             4: ((2.5, 3.6), (2.92, 3.6), (2.98, 3.6, "left", "center"))}
    for b, (p, q) in OKINAWA_LOADS.items():
        (x0, y0), (x1, y1), (tx, ty, ha, va) = loads[b]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=C_WARM, lw=2, mutation_scale=15))
        ax.text(tx, ty, f"負荷 {p:.0f} MW\n+ j{q:.0f} Mvar", ha=ha, va=va, fontsize=11, color=C_WARM)
    total = sum(p for p, q in OKINAWA_LOADS.values())
    ax.set_xlim(-1.5, 4.4); ax.set_ylim(-1.25, 4.35); ax.axis("off")
    ax.set_title(f"沖縄本島の簡略 5 母線モデル（132 kV）— 総負荷 {total:.0f} MW、潮流は直流法で概算（第4回）", fontsize=11)
    ax.text(-1.45, 4.25, "線の太さ＝潮流の大きさ\n矢印＝有効電力の向き",
            fontsize=11, color=C_GREY, ha="left", va="top", linespacing=1.5)
    savefig(fig, "ch02_okinawa.png"); plt.close(fig)
    return {"P": P, "theta": theta, "flows": flows}


# ============================================================ 8. 供給予備率と N-1
def fig_reserve():
    D, S, G = 1500.0, 1650.0, 250.0
    res, res_n1, need = (S - D) / D * 100, (S - G - D) / D * 100, D + G
    res_need = (need - D) / D * 100
    fig, ax = plt.subplots(figsize=(9, 4.8))
    w = 0.58
    ax.bar(0, D, width=w, color=C_GREY)
    ax.bar(1, S - G, width=w, color=C_SEC); ax.bar(1, G, bottom=S - G, width=w, color=C_ACC)
    ax.bar(2, S - G, width=w, color=C_SEC); ax.bar(2, D - (S - G), bottom=S - G, width=w, fc="none", ec=C_WARM, hatch="///", lw=1.2)
    ax.bar(3, need - G, width=w, color=C_SEC); ax.bar(3, G, bottom=need - G, width=w, color=C_ACC)
    ax.axhline(D, color=C_INK, ls="--", lw=1.2); ax.text(3.33, D + 15, f"需要\n{D:,.0f} MW", ha="left", va="bottom", fontsize=11, color=C_INK)
    ax.text(0, D + 40, f"{D:,.0f}", ha="center", fontsize=11.5, weight="bold", color=C_INK)
    ax.text(1, S + 40, f"{S:,.0f}\n予備率 {res:.1f}%", ha="center", fontsize=11.5, weight="bold", color=C_SEC)
    ax.text(2, D + 40, f"{S-G:,.0f}\n予備率 {res_n1:.1f}%\n（{D-(S-G):.0f} MW 不足）", ha="center", fontsize=11.5, weight="bold", color=C_WARM)
    ax.text(3, need + 40, f"{need:,.0f}\n予備率 {res_need:.1f}%", ha="center", fontsize=11.5, weight="bold", color=C_SEC)
    ax.text(1, S - G / 2, f"最大機\n{G:.0f}", ha="center", va="center", fontsize=11, color="white", weight="bold")
    ax.text(3, need - G / 2, f"最大機\n{G:.0f}", ha="center", va="center", fontsize=11, color="white", weight="bold")
    ax.text(1, (S - G) / 2, "その他の\n発電機", ha="center", va="center", fontsize=11, color="white")
    ax.text(2, (S - G) / 2, "その他の\n発電機", ha="center", va="center", fontsize=11, color="white")
    ax.text(3, (need - G) / 2, "その他の\n発電機", ha="center", va="center", fontsize=11, color="white")
    ax.set_xticks(range(4)); ax.set_xticklabels(["需要", "供給力", "最大機が\n脱落した後", "N-1 を満たす\n供給力"])
    ax.set_xlim(-0.5, 3.95); ax.set_ylim(0, 2150); ax.set_ylabel("電力 [MW]"); ax.grid(axis="y", alpha=0.3)
    ax.set_title(f"供給予備率と N-1 — 予備率 {res:.0f}% でも最大機 {G:.0f} MW が抜けると {D-(S-G):.0f} MW 足りない", fontsize=11)
    savefig(fig, "ch02_reserve.png"); plt.close(fig)
    return res, res_n1, need, res_need


# ============================================================ 9. 放射状 vs ループの停電範囲
def fig_topology():
    p = 0.01
    p_radial, p_loop = (1 - p) ** 3, 1 - p ** 2
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))
    nodes = [(1.2, 0), (2.4, 0), (3.6, 0), (4.8, 0)]
    for k, ax in enumerate(axes):
        loop = (k == 1)
        ax.add_patch(Rectangle((-0.3, -0.3), 0.6, 0.6, fc=C_MAIN, ec=C_MAIN, zorder=4))
        ax.text(0, 0, "S", ha="center", va="center", color="white", fontsize=11, weight="bold", zorder=5)
        ax.text(0, -0.55, "変電所", ha="center", va="top", fontsize=11, color=C_GREY)
        pts = [(0, 0)] + nodes
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            faulted = (i == 1)
            if faulted:
                ax.plot([x0, x1], [y0, y1], color=C_LIGHT, lw=2.5, ls="--", zorder=1)
                ax.text((x0 + x1) / 2, 0.0, "×", ha="center", va="center", fontsize=18, color=C_ACC, weight="bold", zorder=6)
                ax.text((x0 + x1) / 2, 0.32, "故障", ha="center", va="bottom", fontsize=11, color=C_ACC)
            else:
                ax.plot([x0, x1], [y0, y1], color=C_MAIN, lw=2.5, zorder=1)
        if loop:
            ax.plot([4.8, 4.8, 0, 0], [0, 1.3, 1.3, 0.3], color=C_MAIN, lw=2.5, zorder=1)
            ax.text(2.4, 1.42, "戻りの経路（ループ）", ha="center", va="bottom", fontsize=11, color=C_MAIN)
            for x in (1.45, 2.15):  # 故障区間を両側の開閉器で切り離す
                ax.add_patch(Rectangle((x - 0.09, -0.09), 0.18, 0.18, fc="white", ec=C_MAIN, lw=1.5, zorder=5))
            ax.text(1.8, -0.85, "両側の開閉器で切り離す", ha="center", va="top", fontsize=11, color=C_GREY)
            ax.annotate("", xy=(4.8, 0.35), xytext=(4.8, 1.0), arrowprops=dict(arrowstyle="-|>", color=C_SEC, lw=2))
            ax.text(5.0, 0.7, "逆から給電", ha="left", va="center", fontsize=11, color=C_SEC)
        for j, (x, y) in enumerate(nodes):
            dead = (not loop) and (j >= 1)
            ax.add_patch(Circle((x, y), 0.22, fc=(C_ACC if dead else C_SEC), ec="none", zorder=4))
            ax.text(x, y, str(j + 1), ha="center", va="center", color="white", fontsize=11.5, weight="bold", zorder=5)
            ax.text(x, -0.5, "停電" if dead else "供給", ha="center", va="top", fontsize=11, color=(C_ACC if dead else C_SEC), weight="bold")
        ax.set_xlim(-0.8, 6.2); ax.set_ylim(-1.65, 1.9); ax.set_aspect("equal"); ax.axis("off")
    axes[0].set_title("放射状：故障点より先はすべて停電（3 区間）", fontsize=11, color=C_ACC)
    axes[1].set_title("ループ：故障区間を切り離し、逆側から給電して継続", fontsize=11, color=C_SEC)
    axes[0].text(2.7, -1.35, f"各区間の年間故障確率 {p:.2f} → 末端に届く確率 (1 − {p:.2f})³ = {p_radial:.4f}", ha="center", fontsize=11, color=C_INK)
    axes[1].text(2.7, -1.35, f"2 経路とも壊れる確率 {p:.2f}² → 届く確率 1 − {p:.2f}² = {p_loop:.4f}", ha="center", fontsize=11, color=C_INK)
    fig.tight_layout(); savefig(fig, "ch02_topology.png"); plt.close(fig)
    return p_radial, p_loop


# ============================================================ 10. たとえ話・よくある誤解（他回と同じく analogy_figure で統一）
def fig_analogy():
    analogy_figure("ch02_analogy.png",
        left_title="道路", right_title="電力系統",
        pairs=[("高速道路は少ない車線で大量輸送", "超高圧送電線（275〜500 kV）"),
               ("IC で降りて生活道路へ", "変電所で降圧（154 → 66 → 6.6 kV）"),
               ("交差点で道が分かれる", "交差点＝母線（bus）"),
               ("渋滞の摩擦で燃料を失う", "摩擦＝送電損失 3I²R"),
               ("車の台数が多いほど摩擦は増える", "台数＝電流 I。電圧を上げて台数を減らす")],
        note="この対応が頭に入っていれば、なぜ電圧を上げるのか、なぜ電流が経路を選べないのかが「道路の話」として説明できる。")


def fig_myth():
    analogy_figure("ch02_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("高電圧にするのは「たくさんの電気を押し込む」ため",
                "高電圧は同じ電力を少ない電流で運び、I²R 損失を減らすため"),
               ("ループにすれば 1 本落ちても安全",
                "ループでは残りの回線が全電流を負うので、耐えられるかは計算が要る"),
               ("沖縄が足りなければ九州から送ってもらえる",
                "沖縄本島は完全独立系統で、融通は物理的に存在しない")],
        note="「高電圧・ループ・連系」はどれも万能薬ではなく、効く条件と限界がある。")


if __name__ == "__main__":
    V = fig_hierarchy(); lv = fig_loss_voltage(); lp = fig_loss_pf(); fig_sld()
    I1, I2, ov = fig_parallel(); a, It1, It2, Z1, pu1, pu2 = fig_transformer(); ok = fig_okinawa()
    res, res_n1, need, res_need = fig_reserve(); pr, pl = fig_topology()
    fig_analogy(); fig_myth()
    print(f"階層：発電機 {V[0]:.0f} kV → 送電 {V[1]:.0f} kV（×{V[1]/V[0]:.0f}）→ 家庭 {V[-1]*1000:.0f} V")
    print(f"損失（P = {P_MW:.0f} MW, {LEN_KM:.0f} km, R = {R_OHM:.0f} Ω, cos φ = {PF}）")
    for v in LEVELS:
        I, L, r = lv[v]; print(f"  {v:>3} kV: I = {I:7.1f} A, 損失 {L:6.3f} MW, 損失率 {r:5.2f}%")
    print(f"  66 kV / 500 kV の損失比 = {lv[66][1]/lv[500][1]:.1f} 倍、(500/66)² = {(500/66)**2:.1f}")
    print("力率（275 kV）: " + ", ".join(f"cos φ {p:.2f} → {r:.3f} 倍 / {L:.3f} MW" for p, (r, L) in lp.items()))
    print(f"並列分流：I₁ = {I1:.0f} A, I₂ = {I2:.0f} A、回線 1 開放後は 1,000 A → 定格 700 A の {ov:.0f}%")
    print(f"変圧器 275/66 kV, 100 MVA: a = {a:.3f}, a² = {a**2:.2f}, I₁ = {It1:.1f} A, I₂ = {It2:.1f} A, "
          f"Z₁ = {Z1.real:.2f} + j{Z1.imag:.1f} Ω, p.u. 一次 {pu1:.4f} / 二次 {pu2:.4f}")
    print(f"沖縄 5 母線（直流法）：注入 P = {np.round(ok['P'], 0)} MW, θ = {np.round(np.rad2deg(ok['theta']), 2)} °, "
          f"線路潮流 = {np.round(ok['flows'], 1)} MW（{[f'L{f+1}-{t+1}' for f, t, L, par in OKINAWA_LINES]}）")
    print(f"予備率：{res:.2f}%、最大機脱落後 {res_n1:.2f}%、N-1 を満たす供給力 {need:.0f} MW（予備率 {res_need:.2f}%）")
    print(f"信頼度：放射状 (1−0.01)³ = {pr:.4f}、ループ 1 − 0.01² = {pl:.4f}")
