# -*- coding: utf-8 -*-
"""第4回 潮流計算の理論(1) — スライド・ノート用の図を実計算から生成する
   python3 fig_ch04.py  → ../図/ch04_*.png
"""
import numpy as np
from pws_common import setup_japanese_font, savefig, build_ybus, power_injection
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch, Circle
from pws_eqfig import analogy_figure

# ---- 共通スタイル（スライドの terracotta パレットに合わせる）----
C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
C_TXT = "#1A1A17"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": C_TXT, "figure.dpi": 100})

# ---- 題材 ----
LINES_A = [(1, 2, 0.2), (1, 3, 0.25), (2, 3, 0.1)]      # Ⅰ章：Y_bus の 3 母線（無損失）
LINES_B = [(1, 2, 0.8), (1, 3, 0.5), (2, 3, 1.0)]       # Ⅳ章：直流法（教科書 例題 4.4）
P_B = np.array([1.0, 0.8, -1.8])                          # 注入（発電 +、負荷 −）
LINES_N = [(1, 2, 0.02, 0.06, 0.030), (1, 3, 0.08, 0.24, 0.025), (2, 3, 0.06, 0.18, 0.020)]  # ノート 4.2.2（R あり）


def ybus_lossless(n, lines):
    """x だけの線路から Y_bus を組む（R = 0、充電容量なし）"""
    Y = np.zeros((n, n), dtype=complex)
    for i, j, x in lines:
        y = 1.0 / (1j * x)
        Y[i-1, j-1] -= y; Y[j-1, i-1] -= y
        Y[i-1, i-1] += y; Y[j-1, j-1] += y
    return Y


def jfmt(v):
    """虚部だけを 'j5' / '−j9' の形に"""
    if abs(v) < 1e-9:
        return "0"
    return ("+j" if v > 0 else "−j") + f"{abs(v):g}"


def draw_matrix(ax, B, x0, y0, cw=0.75, ch=0.55, hl=None, label=None, diag_color=C_MAIN, off_color=C_BLUE):
    """虚部行列 B を x0,y0（左上）にセルで描く。hl は強調するセル (i,j) の集合"""
    n = B.shape[0]
    for i in range(n):
        for j in range(n):
            x, y = x0 + j * cw, y0 - (i + 1) * ch
            fc = diag_color if i == j else off_color
            alpha = 0.16 if abs(B[i, j]) > 1e-9 else 0.03
            ax.add_patch(Rectangle((x, y), cw, ch, fc=fc, alpha=alpha, ec=C_LIGHT, lw=0.8))
            if hl and (i, j) in hl:
                ax.add_patch(Rectangle((x, y), cw, ch, fc="none", ec=C_ACC, lw=2.4))
            ax.text(x + cw / 2, y + ch / 2, jfmt(B[i, j]), ha="center", va="center", fontsize=12,
                    color=C_TXT, weight="bold" if (hl and (i, j) in hl) else "normal")
    # 括弧
    ax.plot([x0 - 0.05, x0 - 0.05], [y0 - n * ch, y0], color=C_TXT, lw=1.6)
    ax.plot([x0 + n * cw + 0.05, x0 + n * cw + 0.05], [y0 - n * ch, y0], color=C_TXT, lw=1.6)
    if label:
        ax.text(x0 + n * cw / 2, y0 + 0.12, label, ha="center", va="bottom", fontsize=12, color=C_TXT)


def draw_bus(ax, x, y, name, w=0.9, color=C_TXT, below=False):
    ax.plot([x - w / 2, x + w / 2], [y, y], color=color, lw=5, solid_capstyle="butt", zorder=3)
    if below:
        ax.text(x, y - 0.13, name, ha="center", va="top", fontsize=12, color=color, weight="bold")
    else:
        ax.text(x, y + 0.13, name, ha="center", va="bottom", fontsize=12, color=color, weight="bold")


# ============================================================ 1. 3 母線系統と Y_bus
def fig_ybus3():
    Y = ybus_lossless(3, LINES_A)
    B = Y.imag
    fig, ax = plt.subplots(figsize=(9.6, 4.4))
    # --- 左：系統図
    pos = {1: (0.6, 2.4), 2: (3.2, 2.4), 3: (1.9, 0.5)}
    for (i, j, x) in LINES_A:
        (x1, y1), (x2, y2) = pos[i], pos[j]
        ax.plot([x1, x2], [y1, y2], color=C_GREY, lw=1.8, zorder=1)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        nx, ny = -dy, dx
        nn = np.hypot(nx, ny); nx, ny = nx / nn * 0.26, ny / nn * 0.26
        if i == 1 and j == 2: nx, ny = 0, -0.28
        ax.text(mx + nx, my + ny, f"x{i}{j} = {x}\ny = −j{1/x:g}", ha="center", va="center", fontsize=11,
                color=C_BLUE, bbox=dict(fc="white", ec="none", pad=1.5))
    for k, (x, y) in pos.items():
        draw_bus(ax, x, y, f"母線 {k}", below=(k == 3))
    ax.text(1.9, 3.15, "3 母線・3 線路（R = 0、p.u.）", ha="center", fontsize=12, color=C_GREY)
    # --- 右：行列
    x0, y0 = 5.0, 2.75
    draw_matrix(ax, B, x0, y0, cw=0.9, ch=0.6, label="Y_bus = j × 下の行列")
    for i in range(3):
        ax.text(x0 + 3 * 0.9 + 0.25, y0 - (i + 0.5) * 0.6, f"行和 = {B[i].sum():g}", va="center", fontsize=11, color=C_SEC)
    ax.text(x0 + 1.35, y0 - 3 * 0.6 - 0.18,
            "対角 Y_ii = Σ y_ij（例 Y11 = −j5 −j4 = −j9）\n非対角 Y_ij = −y_ij（例 Y12 = +j5）\n無損失・対地分なし → 各行の和は 0（検算）",
            ha="center", va="top", fontsize=11, color=C_TXT)
    ax.set_xlim(-0.1, 9.4); ax.set_ylim(-0.6, 3.5); ax.axis("off")
    ax.set_title("3 母線の Y_bus — 対角は「つながる線路の和」、非対角は「−y」", fontsize=12, color=C_TXT)
    savefig(fig, "ch04_ybus3.png"); plt.close(fig)
    return Y


# ============================================================ 2. 線路 1 本追加で 4 か所更新
def fig_add_line():
    Y0 = ybus_lossless(3, LINES_A[:2]).imag
    Y1 = ybus_lossless(3, LINES_A).imag
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    # 左：小さな系統図（追加線路は破線）
    # 下の注記が幅いっぱいに広がるため、系統図とバス3のラベルを上に逃がして重なりを避ける
    pos = {1: (0.5, 2.6), 2: (2.3, 2.6), 3: (1.4, 1.1)}
    for (i, j, x) in LINES_A[:2]:
        ax.plot([pos[i][0], pos[j][0]], [pos[i][1], pos[j][1]], color=C_GREY, lw=1.8)
    ax.plot([pos[2][0], pos[3][0]], [pos[2][1], pos[3][1]], color=C_ACC, lw=2.2, ls="--")
    ax.text(2.2, 1.75, "追加\nx23 = 0.1\ny = −j10", fontsize=11, color=C_ACC, ha="left", va="center")
    for k, (x, y) in pos.items():
        draw_bus(ax, x, y, f"{k}", w=0.6, below=(k == 3))
    # 中：追加前
    draw_matrix(ax, Y0, 3.4, 2.9, cw=0.78, ch=0.56, label="追加前（線路 1–2, 1–3）")
    ax.annotate("", xy=(6.55, 2.05), xytext=(5.95, 2.05), arrowprops=dict(arrowstyle="->", color=C_ACC, lw=2.2))
    # 右：追加後
    hl = {(1, 1), (2, 2), (1, 2), (2, 1)}
    draw_matrix(ax, Y1, 6.75, 2.9, cw=0.78, ch=0.56, hl=hl, label="追加後（線路 2–3 を足す）")
    ax.text(5.15, 0.55, "更新は 4 か所だけ：Y22 += y、Y33 += y、Y23 −= y、Y32 −= y（y = −j10）\n"
                        "他の要素は触らない → 線路数に比例した手間で組める（プログラムなら 10 行）",
            ha="center", va="top", fontsize=11.3, color=C_TXT)
    ax.set_xlim(0, 9.6); ax.set_ylim(-0.3, 3.5); ax.axis("off")
    ax.set_title("線路を 1 本足すと Y_bus は 4 か所だけ変わる", fontsize=12, color=C_TXT)
    savefig(fig, "ch04_add_line.png"); plt.close(fig)


# ============================================================ 3. IEEE 14 / 118 母線の spy 図
def fig_spy():
    import scipy.sparse as sps
    import pandapower as pp, pandapower.networks as pn
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.6))
    stats = {}
    for ax, name in zip(axes, ("case14", "case118")):
        net = getattr(pn, name)()
        pp.runpp(net)
        Y = net._ppc["internal"]["Ybus"]
        Y = Y.tocsr() if sps.issparse(Y) else sps.csr_matrix(Y)
        n, nnz = Y.shape[0], Y.nnz
        dens = 100 * nnz / n**2
        stats[name] = (n, nnz, dens, len(net.line) + len(net.trafo))
        ax.spy(Y, markersize=(9 if n < 20 else 2.2), color=C_MAIN)
        ax.set_title(f"IEEE {n} 母線：非零 {nnz} / {n*n:,} = {dens:.1f}%", fontsize=11)
        ax.set_xlabel("列 j（母線番号）"); ax.set_ylabel("行 i")
        ax.tick_params(labelsize=9)
    fig.suptitle("Y_bus は疎 — 母線が増えるほど非零の割合は下がる（1 行に非零は数個）", fontsize=12, color=C_TXT, y=1.0)
    fig.tight_layout(); savefig(fig, "ch04_spy.png"); plt.close(fig)
    return stats


# ============================================================ 4. 母線種別の表図
def fig_bus_types():
    fig, ax = plt.subplots(figsize=(9.6, 3.6))
    cols = ["種別", "P", "Q", "V", "θ", "該当する設備", "個数", "未知数"]
    cw = [1.5, 0.7, 0.7, 0.7, 0.7, 3.4, 0.95, 1.1]
    rows = [("スラック", "未知", "未知", "既知", "既知", "系統最大の発電機（損失を吸収）", "1", "0"),
            ("PV 母線", "既知", "未知", "既知", "未知", "AVR 付き発電機", "N_PV", "1（θ）"),
            ("PQ 母線", "既知", "既知", "未知", "未知", "負荷・浮遊母線・力率固定の PV", "N_PQ", "2（V, θ）")]
    x = np.concatenate([[0], np.cumsum(cw)])
    y_top, rh = 3.2, 0.62
    for j, c in enumerate(cols):
        ax.add_patch(Rectangle((x[j], y_top - rh), cw[j], rh, fc=C_MAIN, ec="white"))
        ax.text(x[j] + cw[j] / 2, y_top - rh / 2, c, ha="center", va="center", color="white", fontsize=12, weight="bold")
    for i, r in enumerate(rows):
        y = y_top - (i + 2) * rh
        for j, v in enumerate(r):
            if v == "既知":
                fc, tc = C_SEC, "white"
            elif v == "未知":
                fc, tc = C_ACC, "white"
            else:
                fc, tc = ("#F2EFE6" if i % 2 == 0 else "white"), C_TXT
            ax.add_patch(Rectangle((x[j], y), cw[j], rh, fc=fc, ec="white", lw=1.5))
            ax.text(x[j] + cw[j] / 2, y + rh / 2, v, ha="center", va="center", color=tc, fontsize=(10 if j == 5 else 10.5),
                    weight="bold" if j == 0 else "normal")
    ax.text(x[-1] / 2, y_top - 4 * rh - 0.22,
            "各母線で 4 量 (P, Q, V, θ) のうち 2 つを与え、残り 2 つを解く。未知数の総数 = N_PV + 2 N_PQ（= 方程式の数）",
            ha="center", va="top", fontsize=12, color=C_TXT)
    ax.set_xlim(-0.05, x[-1] + 0.05); ax.set_ylim(0.05, 3.3); ax.axis("off")
    ax.set_title("母線種別 — 4 量のうち 2 つを与え、残り 2 つを解く", fontsize=12, color=C_TXT)
    savefig(fig, "ch04_bus_types.png"); plt.close(fig)


# ============================================================ 5. 直流法潮流の 3 母線例
def dc_solve(n, lines, P, slack=1):
    Bp = np.zeros((n, n))
    for i, j, x in lines:
        Bp[i-1, i-1] += 1 / x; Bp[j-1, j-1] += 1 / x
        Bp[i-1, j-1] -= 1 / x; Bp[j-1, i-1] -= 1 / x
    keep = [k for k in range(n) if k != slack - 1]
    th = np.zeros(n)
    th[keep] = np.linalg.solve(Bp[np.ix_(keep, keep)], P[keep])
    flows = {(i, j): (th[i-1] - th[j-1]) / x for i, j, x in lines}
    return Bp, th, flows


def fig_dcpf3():
    Bp, th, flows = dc_solve(3, LINES_B, P_B)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    pos = {1: (0.7, 2.7), 2: (4.3, 2.7), 3: (2.5, 0.45)}
    # 発電・負荷
    for k, p in ((1, P_B[0]), (2, P_B[1])):
        x, y = pos[k]
        ax.add_patch(Circle((x, y + 0.78), 0.22, fc="white", ec=C_SEC, lw=1.8))
        ax.text(x, y + 0.78, "G", ha="center", va="center", fontsize=11.5, color=C_SEC, weight="bold")
        ax.plot([x, x], [y, y + 0.56], color=C_SEC, lw=1.6)
        ax.text(x + 0.32, y + 0.78, f"発電 {p:.1f}", va="center", fontsize=11.5, color=C_SEC)
    x, y = pos[3]
    ax.annotate("", xy=(x, y - 0.75), xytext=(x, y), arrowprops=dict(arrowstyle="-|>", color=C_ACC, lw=1.8))
    ax.text(x + 0.12, y - 0.55, f"負荷 {-P_B[2]:.1f}", va="center", fontsize=11.5, color=C_ACC)
    # 線路と潮流矢印（ラベルは三角形の外側）
    label_pos = {(1, 2): (2.5, 2.2), (1, 3): (0.55, 1.35), (2, 3): (4.55, 1.35)}
    for (i, j, xl) in LINES_B:
        (x1, y1), (x2, y2) = pos[i], pos[j]
        ax.plot([x1, x2], [y1, y2], color=C_GREY, lw=1.8, zorder=1)
        p = flows[(i, j)]
        a, b = ((x1, y1), (x2, y2)) if p >= 0 else ((x2, y2), (x1, y1))
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        ux, uy = (b[0] - a[0]), (b[1] - a[1]); L = np.hypot(ux, uy); ux, uy = ux / L, uy / L
        ax.annotate("", xy=(mx + ux * 0.32, my + uy * 0.32), xytext=(mx - ux * 0.32, my - uy * 0.32),
                    arrowprops=dict(arrowstyle="-|>", color=C_MAIN, lw=2.6, mutation_scale=18), zorder=4)
        lx, ly = label_pos[(i, j)]
        ax.text(lx, ly, f"x{i}{j} = {xl}\nP{i}{j} = {p:+.3f}", ha="center", va="center",
                fontsize=11.3, color=C_TXT, bbox=dict(fc="white", ec="none", pad=1.5))
    for k, (x, y) in pos.items():
        draw_bus(ax, x, y, f"母線 {k}", w=0.8)
        lab = "δ1 = 0（基準）" if k == 1 else f"δ{k} = {th[k-1]:+.3f} rad ({np.degrees(th[k-1]):+.1f}°)"
        ax.text(x, y - 0.15, lab, ha="center", va="top", fontsize=11, color=C_BLUE)
    # 右：式
    tx = 5.65
    ax.text(tx, 3.4, "直流法：P_i = Σ_j (δ_i − δ_j)/x_ij を δ1 = 0 で解く", fontsize=12, color=C_TXT, weight="bold")
    ax.text(tx, 2.85, f"母線 2：{P_B[1]:.1f} = (δ2 − 0)/{LINES_B[0][2]} + (δ2 − δ3)/{LINES_B[2][2]}", fontsize=11.7, color=C_TXT)
    ax.text(tx, 2.45, f"母線 3：{P_B[2]:.1f} = (δ3 − 0)/{LINES_B[1][2]} + (δ3 − δ2)/{LINES_B[2][2]}", fontsize=11.7, color=C_TXT)
    ax.text(tx, 1.9, f"→ [{Bp[1,1]:.2f}  {Bp[1,2]:.2f}; {Bp[2,1]:.2f}  {Bp[2,2]:.2f}] [δ2; δ3] = [{P_B[1]:.1f}; {P_B[2]:.1f}]",
            fontsize=11.7, color=C_BLUE)
    ax.text(tx, 1.45, f"→ δ2 = {th[1]:.3f} rad、δ3 = {th[2]:.3f} rad", fontsize=12, color=C_BLUE, weight="bold")
    ax.text(tx, 0.9, f"線路潮流 P_ij = (δ_i − δ_j)/x_ij：\nP12 = {flows[(1,2)]:+.3f}（2→1 へ流れる）、P13 = {flows[(1,3)]:+.3f}、P23 = {flows[(2,3)]:+.3f}",
            fontsize=11.7, color=C_TXT, va="top")
    ax.text(tx, 0.05, f"検算：母線 1 の流出 P12 + P13 = {flows[(1,2)] + flows[(1,3)]:.3f} ✓、母線 2 の流出 −P12 + P23 = {-flows[(1,2)] + flows[(2,3)]:.3f} ✓",
            fontsize=11.5, color=C_SEC, va="top")
    ax.set_xlim(-0.35, 10.6); ax.set_ylim(-0.7, 3.75); ax.axis("off")
    ax.set_title("直流法の 3 母線例（教科書 例題 4.4）— δ を解けば線路潮流は (δ_i − δ_j)/x", fontsize=12, color=C_TXT)
    savefig(fig, "ch04_dcpf3.png"); plt.close(fig)
    return th, flows


# ============================================================ 6. P_i の非線形性
def fig_nonlinear():
    X = 0.5
    th = np.linspace(0, 90, 300)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    a1.plot(th, np.sin(np.radians(th)) / X, color=C_MAIN, lw=2.2, label="P = V1V2 sinθ / X（V = 1）")
    a1.plot(th, np.radians(th) / X, color=C_BLUE, lw=1.6, ls="--", label="直線近似 P ≈ θ / X")
    err30 = (np.radians(30) - np.sin(np.radians(30))) / np.sin(np.radians(30)) * 100
    a1.scatter([30], [np.sin(np.radians(30)) / X], color=C_ACC, s=45, zorder=4)
    a1.annotate(f"θ = 30°：直線近似の誤差 {err30:.1f}%", (30, np.sin(np.radians(30)) / X), xytext=(33, 0.45), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a1.set_xlabel("位相差 θ = θ_i − θ_j [°]"); a1.set_ylabel("P [p.u.]"); a1.grid(alpha=0.3)
    a1.legend(frameon=False, fontsize=11, loc="upper left"); a1.set_xlim(0, 90); a1.set_ylim(0, 3.2)
    a1.set_title("θ には sin が掛かる", fontsize=11)
    V = np.linspace(0.8, 1.1, 200); th0 = 20
    P = V**2 * np.sin(np.radians(th0)) / X
    P1 = np.sin(np.radians(th0)) / X
    a2.plot(V, P, color=C_MAIN, lw=2.2, label=f"P = V·V·sin{th0}° / X（V1 = V2 = V）")
    a2.plot(V, P1 * (1 + 2 * (V - 1)), color=C_BLUE, lw=1.6, ls="--", label="V = 1 での接線")
    r95 = 0.95**2
    a2.scatter([1.0, 0.95], [P1, P1 * r95], color=C_ACC, s=45, zorder=4)
    a2.annotate(f"V が 5% 下がると P は {100*(1-r95):.1f}% 下がる", (0.95, P1 * r95), xytext=(0.812, 0.74), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.set_xlabel("電圧の大きさ V [p.u.]"); a2.set_ylabel("P [p.u.]"); a2.grid(alpha=0.3)
    a2.legend(frameon=False, fontsize=11, loc="upper left"); a2.set_xlim(0.8, 1.1); a2.set_ylim(0.4, 0.95)
    a2.set_title("V は積で効く", fontsize=11)
    fig.suptitle("電力方程式が非線形な理由 — 未知数の積 V_iV_j と三角関数 cos θ, sin θ", fontsize=12, color=C_TXT, y=1.0)
    fig.tight_layout(); savefig(fig, "ch04_nonlinear.png"); plt.close(fig)
    return err30, r95


# ============================================================ 7. 未知数の数 vs 母線数
def fig_unknowns(case_stats):
    n = np.arange(2, 131)
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    for f, c, ls in ((0.1, C_SEC, "-"), (0.3, C_MAIN, "-"), (0.5, C_WARM, "-")):
        ax.plot(n, (n - 1) * (2 - f), color=c, lw=2, ls=ls, label=f"PV 母線の割合 {int(f*100)}%：未知数 = (n−1)(2 − {f})")
    ax.plot(n, 2 * (n - 1), color=C_GREY, lw=1.2, ls=":", label="上限 2(n − 1)（全部 PQ）")
    # 12 母線と IEEE14 は x がほぼ同じで近接するため上下に振り分け、IEEE118 は凡例と
    # 曲線を避けて右下の空きに置く
    marks = [(12, 3, 8, "12 母線（PV 3, PQ 8）", (8, 62)), (14, 4, 9, "IEEE 14（PV 4, PQ 9）", (48, 6)),
             (118, case_stats["case118_pv"], case_stats["case118_pq"],
              f"IEEE 118（PV {case_stats['case118_pv']}, PQ {case_stats['case118_pq']}）", (88, 55))]
    for nb, npv, npq, lab, xy in marks:
        u = npv + 2 * npq
        ax.scatter([nb], [u], color=C_ACC, s=55, zorder=4)
        ax.annotate(f"{lab}\n未知数 {u}", (nb, u), xytext=xy, fontsize=11,
                    arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("母線数 n"); ax.set_ylabel("未知数の数 N_PV + 2 N_PQ"); ax.grid(alpha=0.3)
    ax.set_xlim(0, 130); ax.set_ylim(0, 270); ax.legend(frameon=False, fontsize=11, loc="upper left")
    ax.set_title("未知数 N_PV + 2N_PQ は母線数のほぼ 2 倍で増える — これがヤコビアンの大きさ", fontsize=11.5)
    savefig(fig, "ch04_unknowns.png"); plt.close(fig)


# ============================================================ 8. case14 交流法 vs 直流法
def fig_ac_vs_dc():
    import pandapower as pp, pandapower.networks as pn
    net = pn.case14()
    pp.runpp(net)
    ac = np.concatenate([net.res_line.p_from_mw.values, net.res_trafo.p_hv_mw.values])
    loss_ac = net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()
    vmin, vmax = net.res_bus.vm_pu.min(), net.res_bus.vm_pu.max()
    thmin = net.res_bus.va_degree.min()
    pp.rundcpp(net)
    dc = np.concatenate([net.res_line.p_from_mw.values, net.res_trafo.p_hv_mw.values])
    names = [f"{a+1}–{b+1}" for a, b in zip(net.line.from_bus, net.line.to_bus)] + \
            [f"{a+1}–{b+1}" for a, b in zip(net.trafo.hv_bus, net.trafo.lv_bus)]
    diff = dc - ac
    k = np.argmax(np.abs(diff))
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    lim = max(abs(ac).max(), abs(dc).max()) * 1.1
    ax.plot([-lim, lim], [-lim, lim], color=C_GREY, lw=1, ls="--", label="一致する線")
    nl = len(net.line)
    ax.scatter(ac[:nl], dc[:nl], color=C_MAIN, s=42, zorder=3, label=f"線路（{nl} 本）")
    ax.scatter(ac[nl:], dc[nl:], color=C_BLUE, s=42, marker="s", zorder=3, label=f"変圧器（{len(net.trafo)} 台）")
    ax.annotate(f"最大のずれ 線路 {names[k]}：交流 {ac[k]:.1f}\n→ 直流 {dc[k]:.1f} MW（{diff[k]:+.1f} MW）",
                (ac[k], dc[k]), xytext=(28, -80), fontsize=11, arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("交流法（pp.runpp）の送電端有効電力 [MW]"); ax.set_ylabel("直流法（pp.rundcpp）[MW]")
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.grid(alpha=0.3); ax.set_aspect("equal")
    ax.legend(frameon=False, fontsize=11, loc="lower right")
    ax.text(-lim * 0.95, lim * 0.62, f"|ずれ| の平均 {np.abs(diff).mean():.1f} MW、最大 {np.abs(diff).max():.1f} MW\n"
                                      f"交流法の総損失 {loss_ac:.1f} MW（直流法では 0）\nV は {vmin:.3f}〜{vmax:.3f} p.u.、θ の最小 {thmin:.1f}°",
            fontsize=11, color=C_TXT, va="top")
    ax.set_title(f"IEEE 14 母線：直流法の線路潮流は交流法とほぼ一致（最大 {np.abs(diff).max():.0f} MW のずれ）", fontsize=11.5)
    savefig(fig, "ch04_ac_vs_dc.png"); plt.close(fig)
    return ac, dc, loss_ac, names, k, (vmin, vmax, thmin)


# ============================================================ 9. 電圧を与えて注入電力を計算（順問題）
def fig_injection():
    Y = build_ybus(3, LINES_N)
    V = np.array([1.05, 1.02, 0.98]); th = np.deg2rad([0.0, -2.5, -5.1])
    P, Q = power_injection(V, th, Y)
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    idx = np.arange(3); w = 0.36
    ax.bar(idx - w / 2, P, w, color=C_MAIN, label="P_i（有効）")
    ax.bar(idx + w / 2, Q, w, color=C_BLUE, label="Q_i（無効）")
    for i in range(3):
        ax.text(i - w / 2, P[i] + (0.03 if P[i] >= 0 else -0.03), f"{P[i]:+.3f}", ha="center", va="bottom" if P[i] >= 0 else "top", fontsize=11, color=C_MAIN)
        ax.text(i + w / 2, Q[i] + (0.03 if Q[i] >= 0 else -0.03), f"{Q[i]:+.3f}", ha="center", va="bottom" if Q[i] >= 0 else "top", fontsize=11, color=C_BLUE)
    ax.axhline(0, color=C_GREY, lw=0.8)
    ax.set_xticks(idx); ax.set_xticklabels([f"母線 {i+1}\nV = {V[i]:.2f}, θ = {np.degrees(th[i]):.1f}°" for i in range(3)])
    ax.set_ylabel("注入電力 [p.u.]（発電 +、負荷 −）"); ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    # 軸フラクション右上だと母線1の Q_i ラベルに重なるため、母線2・3 の間の
    # 空き列（データ座標）に置く
    ax.text(1.5, 1.05, f"Σ P_i = {P.sum():+.4f} p.u. = {P.sum()*100:.2f} MW（= 線路の有効損失）\nΣ Q_i = {Q.sum():+.4f} p.u.",
            ha="center", va="top", fontsize=11.5, color=C_TXT, bbox=dict(fc="#F2EFE6", ec="none", pad=4))
    ax.set_ylim(min(P.min(), Q.min()) * 1.35, max(P.max(), Q.max()) * 1.45)
    ax.set_title("電圧を与えれば P, Q は式で計算できる（順問題）— 和が損失になる", fontsize=11.5)
    savefig(fig, "ch04_injection.png"); plt.close(fig)
    return P, Q


def fig_analogy():
    analogy_figure("ch04_analogy.png",
        left_title="道路網（たとえ）", right_title="潮流計算（実物）",
        pairs=[("交差点どうしの通りやすさを表にする", "通りやすさ＝アドミタンス y = 1/z"),
               ("表の対角＝その交差点の道を全部足す", "Y_ii ＝ Σ y_ij ＋ 対地分"),
               ("表の非対角＝直結する道（マイナス）", "Y_ij ＝ −y_ij"),
               ("帳尻係・出発点係・目的地の役割分担", "スラック・PV・PQ の 3 種類の母線"),
               ("車は全経路に勝手に分かれる", "電流はインピーダンスの逆比で分流")],
        note="この対応が頭に入っていれば、Y_bus の組み立ても電力方程式もすべて「道路網の通りやすさ表」の話に翻訳できる。")


def fig_myth():
    analogy_figure("ch04_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("Y_bus の非対角要素は線路のアドミタンスをそのまま入れる",
                "非対角要素はマイナス符号付き（Y_ij = −y_ij）"),
               ("潮流計算は電流を求める計算なのでオームの法則で一発で解ける",
                "与えられるのは電力（P, Q）。式は非線形になり、反復が要る"),
               ("直流法は直流送電の計算法",
                "直流法は 3 つの近似で交流の式を直流回路と同じ形にした特別な場合")],
        note="どれも、単純な直流回路のイメージをそのまま潮流計算に持ち込んだことから来ている。")


if __name__ == "__main__":
    Y_A = fig_ybus3(); fig_add_line()
    stats = fig_spy()
    # case118 の母線種別（ppc の bus type：1=PQ, 2=PV, 3=slack）
    import pandapower as pp, pandapower.networks as pn
    net = pn.case118(); pp.runpp(net)
    bt = net._ppc["bus"][:, 1]
    stats["case118_pv"], stats["case118_pq"] = int((bt == 2).sum()), int((bt == 1).sum())
    fig_bus_types()
    th, flows = fig_dcpf3()
    err30, r95 = fig_nonlinear()
    fig_unknowns(stats)
    ac, dc, loss_ac, names, k, (vmin, vmax, thmin) = fig_ac_vs_dc()
    P, Q = fig_injection()
    fig_analogy(); fig_myth()

    print("\n==== 計算値 ====")
    print("Y_bus(3 母線, x12=0.2, x13=0.25, x23=0.1) の虚部:\n", np.round(Y_A.imag, 3))
    print("各行の和:", np.round(Y_A.sum(axis=1), 6))
    for name in ("case14", "case118"):
        n, nnz, dens, nbr = stats[name]
        print(f"{name}: n={n}, ブランチ {nbr}, 非零 {nnz}/{n*n}, 密度 {dens:.2f}%")
    print(f"case118: PV {stats['case118_pv']}, PQ {stats['case118_pq']}, 未知数 {stats['case118_pv'] + 2*stats['case118_pq']}")
    for nb in (1000, 10000):
        nl = int(nb * 2.5); nnz = nb + 2 * nl
        print(f"推定 {nb} 母線（線路 {nl}）: 非零 {nnz:,}, 密度 {100*nnz/nb**2:.3f}%")
    print(f"直流法: δ2 = {th[1]:.4f} rad ({np.degrees(th[1]):.2f}°), δ3 = {th[2]:.4f} rad ({np.degrees(th[2]):.2f}°)")
    print(f"  P12 = {flows[(1,2)]:+.4f}, P13 = {flows[(1,3)]:+.4f}, P23 = {flows[(2,3)]:+.4f}; 母線1 流出 {flows[(1,2)]+flows[(1,3)]:.4f}, 母線2 流出 {-flows[(1,2)]+flows[(2,3)]:.4f}")
    print(f"非線形: θ=30° の直線近似誤差 {err30:.2f}%, V=0.95 で P は {100*(1-r95):.2f}% 減")
    diff = dc - ac
    print(f"case14 AC vs DC: |ずれ| 平均 {np.abs(diff).mean():.2f} MW, 最大 {np.abs(diff).max():.2f} MW（{names[k]}: AC {ac[k]:.1f}, DC {dc[k]:.1f}）, AC 損失 {loss_ac:.2f} MW, V {vmin:.3f}〜{vmax:.3f}, θmin {thmin:.1f}°")
    print(f"順問題（ノート 4.2.2 の系統）: P = {np.round(P, 4)}, Q = {np.round(Q, 4)}, ΣP = {P.sum():.4f} p.u. = {P.sum()*100:.2f} MW")
    # 例題 2：Ⅰ章の 3 母線で P_2 を手計算
    V2 = np.array([1.0, 0.98, 0.96]); th2 = np.deg2rad([0, -3, -5])
    B = Y_A.imag
    t21 = V2[1] * V2[0] * B[1, 0] * np.sin(th2[1] - th2[0]); t23 = V2[1] * V2[2] * B[1, 2] * np.sin(th2[1] - th2[2])
    P2, Q2 = power_injection(V2, th2, Y_A)
    print(f"例題 2: P2 = V2[V1 B21 sin(θ21) + V3 B23 sin(θ23)] = {t21:+.4f} {t23:+.4f} = {t21+t23:+.4f} p.u.（式で {P2[1]:+.4f}）, 全母線 P = {np.round(P2, 4)}, Q = {np.round(Q2, 4)}")
