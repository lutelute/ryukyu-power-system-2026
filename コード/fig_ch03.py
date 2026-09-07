# -*- coding: utf-8 -*-
"""第3回 基本量と等価回路 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch03.py  → ../図/ch03_*.png
   （デモ用の ch03_basics.py とはファイル名を分けている）
"""
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import Arc, Circle, FancyBboxPatch
from pws_eqfig import analogy_figure

# ---- 共通スタイル（スライドの terracotta パレットに合わせる）----
C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
C_INK = "#1A1A17"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": C_INK, "figure.dpi": 100})
ARROW = dict(arrowstyle="-|>", mutation_scale=16, lw=2.2, shrinkA=0, shrinkB=0)


# ---- 回路記号（patches / plot で描く）----
def zigzag(ax, x0, x1, y, n=6, h=0.16, **kw):
    xs = np.linspace(x0, x1, 2 * n + 1)
    ys = y + np.array([0] + [h if k % 2 == 0 else -h for k in range(2 * n - 1)] + [0])
    ax.plot(xs, ys, **kw)


def coil(ax, x0, x1, y, n=4, **kw):
    r = (x1 - x0) / (2 * n)
    th = np.linspace(0, np.pi, 30)
    for k in range(n):
        ax.plot(x0 + r * (2 * k + 1) - r * np.cos(th), y + r * np.sin(th), **kw)


def capacitor(ax, x, y_top, y_bot, w=0.36, gap=0.12, **kw):
    ym = (y_top + y_bot) / 2
    ax.plot([x, x], [y_top, ym + gap / 2], **kw); ax.plot([x, x], [ym - gap / 2, y_bot], **kw)
    ax.plot([x - w / 2, x + w / 2], [ym + gap / 2] * 2, **kw); ax.plot([x - w / 2, x + w / 2], [ym - gap / 2] * 2, **kw)


def ground(ax, x, y, **kw):
    for k, w in enumerate((0.42, 0.26, 0.10)):
        ax.plot([x - w / 2, x + w / 2], [y - 0.1 * k] * 2, **kw)


def arrow(ax, p0, p1, color, ls="-", lw=2.2):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(color=color, ls=ls, **{**ARROW, "lw": lw}))


# ============================================================ 1. 瞬時電力の分解（力率 0.8）
def fig_inst_power(pf=0.8):
    f = 60.0; w = 2 * np.pi * f
    phi = np.arccos(pf); V = I = 1.0
    t = np.linspace(0, 2 / f, 4000, endpoint=False); ms = t * 1000
    v = np.sqrt(2) * V * np.sin(w * t); i = np.sqrt(2) * I * np.sin(w * t - phi)
    p = v * i
    P, Q = V * I * np.cos(phi), V * I * np.sin(phi)
    p_act, p_rea = P * (1 - np.cos(2 * w * t)), -Q * np.sin(2 * w * t)
    neg = (p < 0).mean()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True, gridspec_kw={"height_ratios": [1, 1.45]})
    a1.plot(ms, v, color=C_MAIN, lw=2, label="v(t) = √2 V sin ωt")
    a1.plot(ms, i, color=C_BLUE, lw=2, label=f"i(t) = √2 I sin(ωt − φ)、φ = {np.degrees(phi):.1f}°")
    a1.axhline(0, color=C_GREY, lw=0.6); a1.set_ylim(-1.7, 2.9); a1.set_ylabel("v, i [p.u.]")
    a1.legend(frameon=False, fontsize=11, loc="upper right", ncol=2)
    a1.set_title(f"力率 {pf}：電流が電圧より φ = {np.degrees(phi):.1f}° 遅れる（誘導性負荷、V = I = 1）", fontsize=12)
    a2.plot(ms, p, color=C_INK, lw=2.2, label="瞬時電力 p(t) = v·i")
    a2.plot(ms, p_act, color=C_SEC, lw=1.6, ls="--", label=f"P(1 − cos 2ωt)：平均 P = {P:.2f}")
    a2.plot(ms, p_rea, color=C_BLUE, lw=1.6, ls="--", label=f"−Q sin 2ωt：平均 0、振幅 Q = {Q:.2f}")
    a2.fill_between(ms, p, 0, where=(p < 0), color=C_ACC, alpha=0.4, label=f"p < 0：電源へ戻る（1 周期の {neg*100:.1f}%）")
    a2.axhline(P, color=C_SEC, lw=1, ls=":"); a2.axhline(0, color=C_GREY, lw=0.6)
    a2.text(ms[-1] * 0.995, P + 0.07, f"平均 P = {P:.2f}", ha="right", fontsize=11, color=C_SEC,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    a2.set_xlabel("時間 [ms]（60 Hz、2 周期）"); a2.set_ylabel("p(t) [p.u.]"); a2.set_ylim(-1.1, 3.1)
    a2.legend(frameon=False, fontsize=11, loc="upper right", ncol=2)
    a2.set_title("p(t) = P(1 − cos 2ωt) − Q sin 2ωt — 往復するだけの成分の振幅が無効電力 Q", fontsize=12)
    for a in (a1, a2): a.grid(alpha=0.3)
    fig.tight_layout(); savefig(fig, "ch03_inst_power.png"); plt.close(fig)
    return P, Q, neg, p.min(), p.max()


# ============================================================ 2. 電力三角形
def fig_triangle(P=80.0, pf=0.8):
    phi = np.arccos(pf); S = P / pf; Q = S * np.sin(phi)
    fig, ax = plt.subplots(figsize=(7.2, 4.9))
    arrow(ax, (0, 0), (P, 0), C_MAIN); arrow(ax, (P, 0), (P, Q), C_BLUE); arrow(ax, (0, 0), (P, Q), C_SEC)
    ax.add_patch(Arc((0, 0), 34, 34, theta1=0, theta2=np.degrees(phi), color=C_ACC, lw=1.6))
    ax.text(19, 4.5, f"φ = {np.degrees(phi):.1f}°", color=C_ACC, fontsize=12)
    ax.plot([P - 4, P - 4, P], [0, 4, 4], color=C_GREY, lw=1)
    ax.text(P / 2, -4, f"有効電力 P = {P:.0f} MW（仕事をする）", ha="center", va="top", color=C_MAIN, fontsize=11, weight="bold")
    ax.text(P + 3, Q / 2, f"無効電力\nQ = {Q:.0f} Mvar\n（往復するだけ）", va="center", color=C_BLUE, fontsize=11, weight="bold")
    ax.text(P / 2 - 7, Q / 2 + 6, f"皮相電力 S = {S:.0f} MVA（設備容量）", rotation=np.degrees(phi),
            ha="center", va="center", color=C_SEC, fontsize=11, weight="bold", rotation_mode="anchor")
    txt = (f"S² = P² + Q²  →  {S:.0f}² = {P:.0f}² + {Q:.0f}²\n"
           f"cos φ = P/S = {pf:.2f}（力率）,  sin φ = Q/S = {np.sin(phi):.2f}\n"
           f"S = V I* = P + jQ = {P:.0f} + j{Q:.0f}  [MVA]")
    ax.text(0, 78, txt, fontsize=11.5, va="top", bbox=dict(boxstyle="round,pad=0.5", fc="#F2EFE6", ec=C_LIGHT))
    ax.set_xlim(-6, 122); ax.set_ylim(-14, 82); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"電力三角形 — 力率 {pf} の {P:.0f} MW 負荷は S = {S:.0f} MVA、Q = {Q:.0f} Mvar", fontsize=11.5)
    savefig(fig, "ch03_triangle.png"); plt.close(fig)
    return S, Q, np.degrees(phi)


# ============================================================ 3. 損失 vs 力率
def fig_loss_pf():
    pf = np.linspace(0.6, 1.0, 300)
    fig, ax = plt.subplots(figsize=(8.2, 4.5))
    ax.plot(pf, 1 / pf, color=C_SEC, lw=2.2, label="電流比 1/cos φ（同じ P を送るとき）")
    ax.plot(pf, 1 / pf**2, color=C_MAIN, lw=2.4, label="損失比 1/cos²φ（損失 ∝ I²）")
    out = {}
    # x=0.9/0.95 の 4 ラベルは値が近接して重なるため、点ごとに個別のオフセットで離す
    loss_off = {0.95: (14, 16), 0.9: (-16, 20), 0.8: (-8, 12)}
    cur_off = {0.95: (14, -20), 0.9: (-16, -24), 0.8: (8, -18)}
    loss_ha = {0.95: "left", 0.9: "right", 0.8: "right"}
    cur_ha = {0.95: "left", 0.9: "right", 0.8: "left"}
    for x in (0.95, 0.9, 0.8):
        out[x] = (1 / x, 1 / x**2)
        ax.scatter([x], [1 / x], color=C_SEC, s=36, zorder=3); ax.scatter([x], [1 / x**2], color=C_MAIN, s=36, zorder=3)
        ax.annotate(f"{1/x**2:.2f} 倍", (x, 1 / x**2), textcoords="offset points", xytext=loss_off[x], ha=loss_ha[x], fontsize=11, color=C_MAIN)
        ax.annotate(f"{1/x:.2f} 倍", (x, 1 / x), textcoords="offset points", xytext=cur_off[x], ha=cur_ha[x], fontsize=11, color=C_SEC)
    ax.axvline(0.85, color=C_WARM, ls="--", lw=1.2); ax.text(0.853, 2.25, "力率割引・割増の基準 0.85", color=C_WARM, fontsize=11)
    ax.set_xlabel("力率 cos φ"); ax.set_ylabel("力率 1 のときとの比"); ax.set_ylim(0.9, 2.9); ax.set_xlim(0.6, 1.02); ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title("同じ P を送るとき、力率が下がると電流は 1/cos φ、損失は 1/cos²φ で増える", fontsize=11.5)
    savefig(fig, "ch03_loss_pf.png"); plt.close(fig)
    return out


# ============================================================ 4. 力率改善のベクトル図
def fig_pf_correction(P=80.0, pf0=0.8, targets=(1.0, 0.95)):
    phi0 = np.arccos(pf0); Q0 = P * np.tan(phi0); S0 = P / pf0
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.9))
    res = {}
    for ax, pf1 in zip(axes, targets):
        phi1 = np.arccos(pf1); Q1 = P * np.tan(phi1); Qc = Q0 - Q1; S1 = P / pf1
        res[pf1] = (Qc, S1, Q1)
        arrow(ax, (0, 0), (P, Q0), C_GREY, ls="--", lw=1.8)           # S（改善前）
        if Q1 > 0.5: arrow(ax, (0, 0), (P, Q1), C_ACC)                 # S（改善後）
        arrow(ax, (0, 0), (P, 0), C_MAIN)                              # P
        arrow(ax, (P, 0), (P, Q0), C_BLUE)                             # 負荷の遅れ Q
        arrow(ax, (P + 8, Q0), (P + 8, Q1), C_SEC)                     # コンデンサ Q_C（下向き）
        ax.plot([P, P + 8], [Q0, Q0], color=C_SEC, lw=0.8, ls=":")
        ax.plot([P, P + 8], [Q1, Q1], color=C_SEC, lw=0.8, ls=":")
        ax.text(P / 2, -3, f"P = {P:.0f} MW（変わらない）", ha="center", va="top", color=C_MAIN, fontsize=11.5, weight="bold")
        ax.text(P - 2, Q0 / 2, f"負荷の Q\n{Q0:.0f} Mvar", ha="right", va="center", color=C_BLUE, fontsize=11.5, weight="bold")
        ax.text(P + 11, (Q0 + Q1) / 2, f"コンデンサ\nQ_C = {Qc:.1f} Mvar\n（進み＝負の Q）", va="center", color=C_SEC, fontsize=11.5, weight="bold")
        ax.text(P / 2 - 8, Q0 / 2 + 6, f"S = {S0:.0f} MVA（前）", rotation=np.degrees(phi0), ha="center", va="center",
                color=C_GREY, fontsize=11, rotation_mode="anchor")
        if Q1 > 0.5:
            ax.text(P / 2 + 6, Q1 / 2 - 4.5, f"S′ = {S1:.1f} MVA（後）", rotation=np.degrees(phi1), ha="center", va="center",
                    color=C_ACC, fontsize=11, rotation_mode="anchor")
        else:
            ax.text(P / 2, 7, f"S′ = P = {S1:.0f} MVA（後）", ha="center", color=C_ACC, fontsize=11)
        box = (f"線路が運ぶ S：{S0:.0f} → {S1:.1f} MVA\n電流（力率 1 比）：{1/pf0:.2f} → {1/pf1:.2f} 倍\n"
               f"損失（力率 1 比）：{1/pf0**2:.2f} → {1/pf1**2:.2f} 倍")
        ax.text(0, 84, box, fontsize=11, va="top", bbox=dict(boxstyle="round,pad=0.45", fc="#F2EFE6", ec=C_LIGHT))
        ax.set_xlim(-5, 140); ax.set_ylim(-13, 88); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"力率 {pf0} → {pf1}：Q_C = {Qc:.1f} Mvar", fontsize=11, color=C_INK)
    fig.suptitle("力率改善 — コンデンサが負荷の遅れ Q を現地で打ち消し、線路が運ぶ S と電流が減る", fontsize=11.5, y=0.99)
    fig.tight_layout(); savefig(fig, "ch03_pf_correction.png"); plt.close(fig)
    return Q0, S0, res


# ============================================================ 5. π 型等価回路
def fig_pi_circuit(f=60.0, length=200.0, r=0.030, x=0.35, c=0.0090e-6, kv=275):
    Z = (r + 1j * x) * length; B = 2 * np.pi * f * c * length; Y = 1j * B
    A = 1 + Z * Y / 2; Bc = Z; Cc = Y * (1 + Z * Y / 4); D = A
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    lw = dict(color=C_INK, lw=1.8)
    yt, yb = 3.6, 1.3
    ax.plot([0.6, 3.0], [yt, yt], **lw); ax.plot([4.2, 4.9], [yt, yt], **lw); ax.plot([6.1, 9.4], [yt, yt], **lw)
    ax.plot([0.6, 9.4], [yb, yb], color=C_GREY, lw=1.4)
    zigzag(ax, 3.0, 4.2, yt, **lw); coil(ax, 4.9, 6.1, yt, **lw)
    for xn in (1.5, 8.5):
        ax.scatter([xn], [yt], color=C_MAIN, s=60, zorder=4)
        capacitor(ax, xn, yt, yb, **lw)
        # 右側のコンデンサは「受電端」ラベルと反対側（左）に出す
        if xn < 5:
            ax.text(xn + 0.3, (yt + yb) / 2, "jB/2", color=C_SEC, fontsize=11, va="center", ha="left", weight="bold")
        else:
            ax.text(xn - 0.3, (yt + yb) / 2, "jB/2", color=C_SEC, fontsize=11, va="center", ha="right", weight="bold")
    ax.scatter([0.6, 0.6, 9.4, 9.4], [yt, yb, yt, yb], color=C_INK, s=18, zorder=4)
    ax.text(3.6, yt - 0.42, "R", ha="center", va="top", color=C_MAIN, fontsize=11, weight="bold")
    ax.text(5.5, yt - 0.3, "jX", ha="center", va="top", color=C_MAIN, fontsize=11, weight="bold")
    ax.text(4.55, yt + 0.5, "直列インピーダンス Z = R + jX", ha="center", color=C_MAIN, fontsize=12)
    arrow(ax, (2.0, yt + 0.22), (2.7, yt + 0.22), C_BLUE, lw=1.8); ax.text(2.35, yt + 0.32, r"$\dot{I}_s$", ha="center", color=C_BLUE, fontsize=12)
    arrow(ax, (7.2, yt + 0.22), (7.9, yt + 0.22), C_BLUE, lw=1.8); ax.text(7.55, yt + 0.32, r"$\dot{I}_r$", ha="center", color=C_BLUE, fontsize=12)
    ax.text(0.55, (yt + yb) / 2, r"送電端" + "\n" + r"$\dot{V}_s$", ha="right", va="center", color=C_INK, fontsize=11)
    ax.text(9.45, (yt + yb) / 2, r"受電端" + "\n" + r"$\dot{V}_r$", ha="left", va="center", color=C_INK, fontsize=11)
    ax.text(5.0, yb - 0.25, "対地アドミタンス Y = jB を半分ずつ両端へ（B = ωC）", ha="center", va="top", color=C_SEC, fontsize=11.5)
    box = (f"例：{kv} kV・{length:.0f} km 架空線（r = {r} Ω/km, x = {x} Ω/km, c = {c*1e6:.4f} µF/km, {f:.0f} Hz）\n"
           f"Z = {Z.real:.0f} + j{Z.imag:.0f} Ω,  B = {B*1e6:.0f} µS  →  A = D = 1 + ZY/2 = {A.real:.4f} + j{A.imag:.4f},  "
           f"B = Z,  C = Y(1 + ZY/4) = j{Cc.imag*1e6:.0f} µS,  AD − BC = {(A*D-Bc*Cc).real:.4f}")
    ax.text(5.0, 0.35, box, ha="center", va="center", fontsize=11, bbox=dict(boxstyle="round,pad=0.5", fc="#F2EFE6", ec=C_LIGHT))
    ax.set_xlim(-0.6, 10.6); ax.set_ylim(-0.3, 4.5); ax.axis("off")
    ax.set_title("π 型等価回路 — 中距離送電線（50〜250 km）の標準モデル。架空線では X ≫ R", fontsize=11.5)
    savefig(fig, "ch03_pi_circuit.png"); plt.close(fig)
    return Z, B, A, Cc


# ============================================================ 6. P–δ 曲線と Q–V 曲線
def fig_pd_qv(X=0.3, Vs=1.0, Vr=1.0, d_ex=15.0):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.5))
    d = np.linspace(0, 180, 361); dr = np.radians(d)
    P = Vs * Vr / X * np.sin(dr); Pmax = Vs * Vr / X
    P_ex = Vs * Vr / X * np.sin(np.radians(d_ex))
    a1.plot(d, P, color=C_MAIN, lw=2.4, label="P = V_sV_r sin δ / X")
    a1.plot(d[d <= 60], Vs * Vr / X * dr[d <= 60], color=C_GREY, lw=1.4, ls=":", label="近似 P ≒ V_sV_r δ / X（δ 小）")
    a1.axvspan(90, 180, color=C_LIGHT, alpha=0.5); a1.text(135, Pmax * 0.55, "δ > 90°\n送ろうとするほど\n送れない（不安定）", ha="center", fontsize=11, color=C_GREY)
    a1.axvline(90, color=C_ACC, ls="--", lw=1.2)
    a1.scatter([90], [Pmax], color=C_ACC, s=50, zorder=4); a1.text(88, Pmax + 0.12, f"P_max = 1/{X} = {Pmax:.2f}", ha="right", fontsize=11, color=C_ACC)
    a1.scatter([d_ex], [P_ex], color=C_MAIN, s=50, zorder=4)
    a1.annotate(f"δ = {d_ex:.0f}°：P = {P_ex:.3f}\n（P_max の {P_ex/Pmax*100:.0f}%）", (d_ex, P_ex), xytext=(30, 0.35), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a1.set_xlabel("相差角 δ [°]"); a1.set_ylabel("有効電力 P [p.u.]"); a1.set_xlim(0, 180); a1.set_ylim(0, Pmax * 1.42); a1.grid(alpha=0.3)
    a1.legend(frameon=False, fontsize=11, loc="upper right"); a1.set_title(f"P は相差角 δ で決まる（V_s = V_r = 1, X = {X}）", fontsize=11)
    vs = np.linspace(0.9, 1.1, 201)
    Q_ex = (Vs * Vr * np.cos(np.radians(d_ex)) - Vr**2) / X
    for dd, c in ((0, C_SEC), (d_ex, C_MAIN), (30, C_BLUE)):
        a2.plot(vs, (vs * Vr * np.cos(np.radians(dd)) - Vr**2) / X, color=c, lw=2.2, label=f"δ = {dd:.0f}°")
    a2.axhline(0, color=C_GREY, lw=0.8); a2.axvline(1.0, color=C_GREY, lw=0.8, ls=":")
    a2.scatter([Vs], [Q_ex], color=C_MAIN, s=50, zorder=4)
    a2.annotate(f"δ = {d_ex:.0f}°, V_s = V_r = 1 → Q_r = {Q_ex:.3f}", (Vs, Q_ex), xytext=(1.012, -0.14), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.set_xlabel("送電端電圧 V_s [p.u.]（V_r = 1 固定）"); a2.set_ylabel("受電端の無効電力 Q_r [p.u.]"); a2.set_xlim(0.9, 1.1); a2.set_ylim(-0.42, 0.42)
    a2.grid(alpha=0.3); a2.legend(frameon=False, fontsize=11, loc="upper left"); a2.set_title("Q は電圧の大きさの差で決まる", fontsize=11)
    # 右図は横幅 0.2 p.u. しかなく符号の説明文が収まらないため、図全体の下に注記として置く
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    fig.text(0.5, 0.01, "V_s > V_r → Q が受電端へ流れ込む（Q_r > 0）　　V_s < V_r → 受電端から吸い出す（Q_r < 0）",
              fontsize=11, color=C_INK, ha="center", va="bottom")
    savefig(fig, "ch03_pd_qv.png"); plt.close(fig)
    return P_ex, Pmax, Q_ex


# ============================================================ 7. 単位法：変圧器の両側で Z_pu が同じ
def fig_per_unit(X_ohm=10.0, kv_lo=66.0, kv_hi=275.0, S_base=100.0):
    a = kv_hi / kv_lo; X_hi = X_ohm * a**2
    Zb_lo, Zb_hi = kv_lo**2 / S_base, kv_hi**2 / S_base
    pu_lo, pu_hi = X_ohm / Zb_lo, X_hi / Zb_hi
    fig, ax = plt.subplots(figsize=(13.2, 5.6))
    def box(x0, y0, w, h, text, ec, fs=10):
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0.08", fc="#F2EFE6", ec=ec, lw=1.6))
        ax.text(x0 + w / 2, y0 + h / 2, text, ha="center", va="center", fontsize=fs, color=C_INK)
    def transformer(xc, yc, faded=False):
        col = C_LIGHT if faded else C_MAIN
        for dx in (-0.28, 0.28):
            ax.add_patch(Circle((xc + dx, yc), 0.42, fc="none", ec=col, lw=1.8, ls="--" if faded else "-"))
        ax.plot([xc - 1.5, xc - 0.7], [yc, yc], color=col, lw=1.6); ax.plot([xc + 0.7, xc + 1.5], [yc, yc], color=col, lw=1.6)
    # 上段：実単位（box を高さ 0.85 に抑え、ラベル／タイトルとの間隔を計算して確保する）
    y1 = 4.10
    ax.text(0.15, y1 + 1.25, "実単位 [Ω]：変圧器をまたぐたびに巻数比の 2 乗で換算する", fontsize=12, color=C_MAIN, weight="bold")
    box(0.25, y1 - 0.40, 4.35, 0.80, f"{kv_lo:.0f} kV 側の線路\nX = {X_ohm:.0f} Ω", C_MAIN, 10.5)
    transformer(5.75, y1)
    ax.text(5.75, y1 + 0.80, f"変圧器 {kv_hi:.0f}/{kv_lo:.0f} kV（a = {a:.2f}）", ha="center", fontsize=11, color=C_MAIN)
    box(6.95, y1 - 0.40, 6.0, 0.80, f"{kv_hi:.0f} kV 側から見ると\nX′ = a²X = {a**2:.1f} × {X_ohm:.0f} = {X_hi:.1f} Ω", C_MAIN, 10.5)
    ax.text(5.75, y1 - 1.05, f"10 Ω と {X_hi:.1f} Ω：数値が {a**2:.1f} 倍違う", ha="center", fontsize=11, color=C_ACC)
    # 下段：単位法（3 行テキストの下端を確保するため box 高さは 1.2 のまま、ラベル／タイトル／注記との間隔だけ広げる）
    y2 = 0.95
    ax.text(0.15, y2 + 1.50, f"単位法 [p.u.]（S_base = {S_base:.0f} MVA、V_base は各側の定格電圧）：換算が要らない", fontsize=12, color=C_SEC, weight="bold")
    box(0.25, y2 - 0.6, 4.35, 1.2, f"V_base = {kv_lo:.0f} kV\nZ_base = {kv_lo:.0f}²/{S_base:.0f} = {Zb_lo:.1f} Ω\nX_pu = {X_ohm:.0f}/{Zb_lo:.1f} = {pu_lo:.3f}", C_SEC, 10)
    transformer(5.75, y2, faded=True)
    ax.text(5.75, y2 + 1.01, "変圧器が「消える」", ha="center", fontsize=11, color=C_GREY)
    box(6.95, y2 - 0.6, 6.0, 1.2, f"V_base = {kv_hi:.0f} kV\nZ_base = {kv_hi:.0f}²/{S_base:.0f} = {Zb_hi:.0f} Ω\nX_pu = {X_hi:.1f}/{Zb_hi:.0f} = {pu_hi:.3f}", C_SEC, 10)
    ax.text(5.75, y2 - 1.15, f"{pu_lo:.3f} = {pu_hi:.3f}：両側で同じ数値。電圧も 0.95〜1.05 に揃う", ha="center", fontsize=11, color=C_SEC, weight="bold")
    ax.set_xlim(0, 13.2); ax.set_ylim(-0.5, 5.6); ax.axis("off")
    ax.set_title("単位法 — V_base を巻数比に合わせて取ると、変圧器の両側で同じ p.u. 値になる", fontsize=11.5)
    savefig(fig, "ch03_per_unit.png"); plt.close(fig)
    return Zb_lo, pu_lo, Zb_hi, pu_hi, a**2


# ============================================================ 8. フェランチ効果
def fig_ferranti(x=0.4, b=3e-6, lmax=400):
    beta = np.sqrt(x * b)                      # 位相定数 [rad/km]（R, G 無視）
    l = np.linspace(0, lmax, 401)
    exact = 1 / np.cos(beta * l)               # 分布定数：無負荷の V_r/V_s
    pi_ap = 1 / np.abs(1 - x * b * l**2 / 2)   # π 型：V_r/V_s = 1/|A|, A = 1 + ZY/2
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    ax.plot(l, exact, color=C_MAIN, lw=2.4, label="分布定数（厳密）V_r/V_s = 1/cos βl")
    ax.plot(l, pi_ap, color=C_SEC, lw=1.8, ls="--", label="π 型等価回路 1/|A| = 1/(1 − xb l²/2)")
    ax.axhline(1.0, color=C_GREY, lw=0.8)
    vals = {}
    # 100 km は左端に近く右揃えだと軸外にはみ出すため左揃えに、400 km は上が凡例と
    # 重なるため点の下側に配置する
    label_pos = {100: dict(xytext=(0, 14), ha="center"),
                 200: dict(xytext=(-10, 10), ha="right"),
                 300: dict(xytext=(-10, 10), ha="right"),
                 400: dict(xytext=(-12, -22), ha="right")}
    for L in (100, 200, 300, 400):
        v = 1 / np.cos(beta * L); vals[L] = (v, 1 / abs(1 - x * b * L**2 / 2))
        ax.scatter([L], [v], color=C_MAIN, s=40, zorder=4)
        pos = label_pos[L]
        ax.annotate(f"{L} km：{v:.3f}（+{(v-1)*100:.1f}%）", (L, v), textcoords="offset points", xytext=pos["xytext"], ha=pos["ha"], fontsize=11, color=C_MAIN)
    ax.text(392, 1.002, f"x = {x} Ω/km, b = {b*1e6:.0f} µS/km\nβ = √(xb) = {beta:.5f} rad/km\n（1/4 波長 = π/2β ≒ {np.pi/2/beta:.0f} km）",
            fontsize=11, va="bottom", ha="right", bbox=dict(boxstyle="round,pad=0.45", fc="#F2EFE6", ec=C_LIGHT))
    ax.set_xlabel("線路の長さ l [km]"); ax.set_ylabel("無負荷時の受電端電圧 V_r / V_s"); ax.set_xlim(0, lmax); ax.set_ylim(0.99, 1.12); ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=11, loc="upper left")
    ax.set_title("フェランチ効果 — 無負荷の長い線路では受電端電圧が送電端より高くなる", fontsize=11.5)
    savefig(fig, "ch03_ferranti.png"); plt.close(fig)
    return beta, vals


# ============================================================ 9. 2 母線系統とフェーザ図
def fig_twobus(X=0.3, Vs=1.0, Vr=1.0, d_deg=15.0, i_scale=0.5):
    d = np.radians(d_deg)
    Vs_c = Vs * np.exp(1j * d); Vr_c = Vr + 0j
    I = (Vs_c - Vr_c) / (1j * X); Sr = Vr_c * np.conj(I)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.4), gridspec_kw={"width_ratios": [1.15, 1]})
    # 左：回路
    lw = dict(color=C_INK, lw=1.8); y = 2.5
    for xb in (1.6, 8.4): a1.plot([xb, xb], [1.4, 3.6], color=C_MAIN, lw=5, solid_capstyle="butt")
    a1.plot([1.6, 4.2], [y, y], **lw); a1.plot([5.8, 8.4], [y, y], **lw); coil(a1, 4.2, 5.8, y, **lw)
    a1.text(5.0, y - 0.35, f"jX = j{X}（R ≒ 0）", ha="center", va="top", color=C_MAIN, fontsize=12, weight="bold")
    a1.add_patch(Circle((0.7, y), 0.42, fc="#F2EFE6", ec=C_INK, lw=1.6)); a1.plot([1.12, 1.6], [y, y], **lw)
    tt = np.linspace(-0.3, 0.3, 40); a1.plot(0.7 + tt, y + 0.15 * np.sin(tt / 0.3 * np.pi), color=C_INK, lw=1.3)
    a1.plot([8.4, 9.3], [y, y], **lw); arrow(a1, (9.3, y), (9.3, 1.5), C_INK, lw=1.6); a1.text(9.45, 1.9, "負荷", fontsize=11.5, color=C_INK)
    a1.text(1.6, 3.8, r"$\dot{V}_s = V_s\angle\delta$" + f"\n（{Vs:.1f}∠{d_deg:.0f}°）", ha="center", va="bottom", color=C_MAIN, fontsize=12)
    a1.text(8.4, 3.8, r"$\dot{V}_r = V_r\angle 0$" + f"\n（{Vr:.1f}∠0°）", ha="center", va="bottom", color=C_BLUE, fontsize=12)
    arrow(a1, (2.5, y + 0.28), (3.5, y + 0.28), C_BLUE, lw=1.8)
    a1.text(3.05, y + 0.42, r"$\dot{I} = (\dot{V}_s - \dot{V}_r)/jX$", ha="center", color=C_BLUE, fontsize=12)
    arrow(a1, (6.4, y + 0.28), (7.6, y + 0.28), C_SEC, lw=1.8); a1.text(7.0, y + 0.42, r"$S_r = P + jQ_r$", ha="center", color=C_SEC, fontsize=12)
    a1.text(1.6, 1.15, "送電端（発電機側）", ha="center", va="top", fontsize=11, color=C_GREY)
    a1.text(8.4, 1.15, "受電端（負荷側）", ha="center", va="top", fontsize=11, color=C_GREY)
    a1.set_xlim(0, 10.2); a1.set_ylim(0.5, 4.9); a1.axis("off"); a1.set_title("2 母線系統 — 講義でいちばん単純な「系統」", fontsize=11)
    # 右：フェーザ図（電流は縮尺 i_scale）
    Is = I * i_scale
    arrow(a2, (0, 0), (Vr_c.real, Vr_c.imag), C_BLUE)
    a2.text(0.86, -0.04, r"$\dot{V}_r = 1\angle 0$", color=C_BLUE, fontsize=12, ha="center", va="top")
    arrow(a2, (0, 0), (Vs_c.real, Vs_c.imag), C_MAIN)
    a2.text(0.45, Vs_c.imag / Vs_c.real * 0.45 + 0.035, r"$\dot{V}_s = 1\angle 15°$", color=C_MAIN, fontsize=12, ha="center",
            rotation=d_deg, rotation_mode="anchor")
    arrow(a2, (Vr_c.real, Vr_c.imag), (Vs_c.real, Vs_c.imag), C_SEC)
    a2.text(Vs_c.real + 0.025, Vs_c.imag / 2, r"$jX\dot{I} = \dot{V}_s - \dot{V}_r$", color=C_SEC, fontsize=12, va="center")
    arrow(a2, (0, 0), (Is.real, Is.imag), C_ACC, ls="--", lw=1.8)
    # 横に長いと V_r ラベルと衝突するため 2 行に分けて幅を抑える
    a2.annotate(r"$\dot{I}$" + f" = {abs(I):.3f}∠{np.degrees(np.angle(I)):.1f}°\n（図は 1/2 縮尺）", (Is.real, Is.imag), xytext=(0.05, -0.13),
                fontsize=11.5, color=C_ACC, arrowprops=dict(arrowstyle="->", color=C_ACC, lw=1))
    a2.add_patch(Arc((0, 0), 1.2, 1.2, theta1=0, theta2=d_deg, color=C_MAIN, lw=1.4)); a2.text(0.62, 0.055, f"δ = {d_deg:.0f}°", color=C_MAIN, fontsize=12)
    a2.text(0.02, 0.43, r"$S_r = \dot{V}_r \dot{I}^*$" + f" = {Sr.real:.3f} {'−' if Sr.imag < 0 else '+'} j{abs(Sr.imag):.3f}\n"
            f"P = V_sV_r sin δ / X = {Sr.real:.3f}\nQ_r = (V_sV_r cos δ − V_r²)/X = {Sr.imag:.3f}",
            fontsize=11, va="top", bbox=dict(boxstyle="round,pad=0.45", fc="#F2EFE6", ec=C_LIGHT))
    a2.set_xlim(-0.05, 1.32); a2.set_ylim(-0.22, 0.47); a2.set_aspect("equal"); a2.axis("off")
    a2.set_title("フェーザ図 — " + r"$\dot{I}$" + " は " + r"$\dot{V}_s - \dot{V}_r$" + " に直交（jX で割る）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch03_twobus.png"); plt.close(fig)
    return I, Sr


def fig_analogy():
    analogy_figure("ch03_analogy.png",
        left_title="ジョッキ（たとえ）", right_title="電力（実物）",
        pairs=[("ジョッキの容量が決まっている", "容量＝皮相電力 S = |V||I|"),
               ("飲めるのはビールの分だけ", "ビール＝有効電力 P（仕事をする）"),
               ("泡は飲めないが容量を占める", "泡＝無効電力 Q（磁界を往復する）"),
               ("泡が多いと注ぐ管を太くする必要", "管を太く＝電流が増え損失が増える"),
               ("ビールの割合＝ジョッキの「実力」", "割合＝力率 cos φ = P/S")],
        note="この対応が頭に入っていれば、力率改善やコンデンサ容量の計算も全部「ジョッキの容量と泡」の話に翻訳できる。")


def fig_myth():
    analogy_figure("ch03_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("無効電力は「役に立たない電力」なので無くせばよい",
                "Q は磁界を作るために必要で、無いとモータは回らない。ただし線路を占有し電圧を左右する"),
               ("有効電力は電圧の高い方から低い方へ流れる",
                "P は電圧差ではなく位相差 δ で流れる（交流の送電線は X ≫ R）"),
               ("p.u. 値は単位が無いから物理量ではない",
                "p.u. は基準（S_base・V_base）を掛ければ実量に戻る")],
        note="どれも、直流回路や実数の感覚をそのまま交流・単位法に持ち込んだことから来ている。")


if __name__ == "__main__":
    P, Q, neg, pmin, pmax = fig_inst_power(0.8)
    print(f"[1] 瞬時電力 力率 0.8: P = {P:.3f}, Q = {Q:.3f}, p<0 の割合 = {neg*100:.1f}%, p の範囲 {pmin:.2f}〜{pmax:.2f}")
    S, Qtri, phi = fig_triangle(80, 0.8)
    print(f"[2] 電力三角形 80 MW 力率 0.8: S = {S:.1f} MVA, Q = {Qtri:.1f} Mvar, φ = {phi:.2f}°")
    lp = fig_loss_pf()
    print("[3] 損失 vs 力率: " + ", ".join(f"pf {k}: 電流 {v[0]:.3f} 倍 / 損失 {v[1]:.3f} 倍" for k, v in lp.items()))
    Q0, S0, res = fig_pf_correction()
    for pf1, (Qc, S1, Q1) in res.items():
        print(f"[4] 力率改善 0.8 → {pf1}: Q_C = {Qc:.2f} Mvar, S′ = {S1:.2f} MVA, 残る Q = {Q1:.2f} Mvar")
    Z, B, A, Cc = fig_pi_circuit()
    print(f"[5] π 型 275 kV 200 km: Z = {Z:.1f} Ω, B = {B*1e6:.1f} µS, A = {A:.5f}, |A| = {abs(A):.4f}, C = {Cc*1e6:.3f} µS, 無負荷 V_r/V_s = {1/abs(A):.4f}")
    P_ex, Pmax, Q_ex = fig_pd_qv()
    print(f"[6] P–δ/Q–V X=0.3: δ=15° で P = {P_ex:.4f}, P_max = {Pmax:.3f}, P/P_max = {P_ex/Pmax*100:.1f}%, Q_r = {Q_ex:.4f}; "
          f"δ=30° で P = {np.sin(np.radians(30))/0.3:.3f}; 100 MVA 基準で P = {P_ex*100:.1f} MW, P_max = {Pmax*100:.0f} MW")
    Zb_lo, pu_lo, Zb_hi, pu_hi, a2 = fig_per_unit()
    print(f"[7] 単位法: Z_base(66 kV) = {Zb_lo:.2f} Ω → 10 Ω = {pu_lo:.4f} p.u.; Z_base(275 kV) = {Zb_hi:.2f} Ω → {10*a2:.1f} Ω = {pu_hi:.4f} p.u.; a² = {a2:.2f}; "
          f"I_base(66 kV) = {100e6/(np.sqrt(3)*66e3):.1f} A; 60 MVA %Z 12% → 100 MVA 基準 {0.12*100/60:.3f} p.u.")
    beta, vals = fig_ferranti()
    print(f"[8] フェランチ β = {beta*1e3:.4f}e-3 rad/km: " + ", ".join(f"{L} km 厳密 {v[0]:.4f} / π 型 {v[1]:.4f}" for L, v in vals.items()))
    I, Sr = fig_twobus()
    print(f"[9] 2 母線 X=0.3 δ=15°: I = {abs(I):.4f}∠{np.degrees(np.angle(I)):.2f}°, S_r = {Sr.real:.4f} + j{Sr.imag:.4f}")
    fig_analogy(); fig_myth()
