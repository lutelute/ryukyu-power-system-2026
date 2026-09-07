# -*- coding: utf-8 -*-
"""第1回 エネルギー変換の基礎 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch01.py  → ../図/ch01_*.png
"""
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Polygon
from pws_eqfig import analogy_figure, derivation_figure

# ---- 共通スタイル（スライドの terracotta パレットに合わせる）----
C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})

# ============================================================ 1. 変換の連鎖（サンキー風）
def fig_chain():
    stages = [("燃料\n(化学)", None), ("ボイラ\n→ 熱", 0.90), ("タービン\n→ 回転", 0.45), ("発電機\n→ 電気", 0.98)]
    e = [100.0]
    for _, eta in stages[1:]:
        e.append(e[-1] * eta)
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(stages)) * 2.6
    scale = 0.03
    for i, (name, eta) in enumerate(stages):
        h = e[i] * scale
        ax.add_patch(FancyBboxPatch((x[i], 1.5 - h / 2), 1.3, h, boxstyle="round,pad=0.05",
                                    fc="#F2EFE6", ec=C_MAIN, lw=1.5))
        ax.text(x[i] + 0.65, 1.5, name, ha="center", va="center", fontsize=12, color="#1A1A17")
        ax.text(x[i] + 0.65, 1.5 + h / 2 + 0.18, f"{e[i]:.1f}", ha="center", fontsize=11, weight="bold", color=C_MAIN)
        if i < len(stages) - 1:
            h2 = e[i + 1] * scale
            ax.add_patch(Polygon([[x[i] + 1.3, 1.5 + h / 2], [x[i + 1], 1.5 + h2 / 2],
                                  [x[i + 1], 1.5 - h2 / 2], [x[i] + 1.3, 1.5 - h / 2]],
                                 closed=True, fc="#E8C9C3", ec="none", alpha=0.9))
            loss = e[i] - e[i + 1]
            ax.add_patch(Polygon([[x[i] + 1.3, 1.5 - h / 2], [x[i + 1], 1.5 - h2 / 2],
                                  [x[i + 1] - 0.15, 0.15], [x[i] + 1.45, 0.15]],
                                 closed=True, fc="#DCD8CC", ec="none", alpha=0.8))
            ax.text((x[i] + 1.3 + x[i + 1]) / 2, -0.18, f"損失 {loss:.1f}\n(η = {stages[i+1][1]:.2f})",
                    ha="center", va="bottom", fontsize=11, color=C_GREY)
    ax.text(x[-1] + 0.65, 2.45, f"総合効率\n0.90 × 0.45 × 0.98 = {e[-1]/100:.3f}", ha="center", va="bottom",
            fontsize=12, color=C_MAIN, weight="bold")
    ax.set_xlim(-0.3, x[-1] + 1.8); ax.set_ylim(-0.75, 3.4); ax.axis("off")
    ax.set_title("火力発電は 4 回の変換 — 効率は各段の「積」で減っていく（入力 100 として）", fontsize=12, color="#1A1A17")
    savefig(fig, "ch01_chain.png"); plt.close(fig)
    return e

# ============================================================ 2. カルノー効率の曲線と実機
def fig_carnot_curve():
    TL = 30 + 273.15
    TH_C = np.linspace(150, 1700, 400)
    eta = 1 - TL / (TH_C + 273.15)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.plot(TH_C, eta * 100, color=C_MAIN, lw=2.2, label="カルノー効率 η_C = 1 − T_L/T_H（T_L = 30 °C）")
    # ラベルは「offset points」ではなく data 座標で個別に置く（キャンバス縮小でズレないように）
    # 540 °C と 600 °C は 60 °C しか離れておらず個別ラベルが重なるので、2 つまとめて 1 つの注記にする
    plants = [("原子力 (PWR)", 285, 34, (170, 8, "left", "bottom")),
              ("石炭 亜臨界", 540, 38, None),
              ("石炭 USC", 600, 42, None),
              ("コンバインド", 1400, 58, (1000, 66, "left", "bottom")),
              ("最新 CC", 1600, 63, (1430, 70, "left", "bottom"))]
    ecs = {}
    for name, th, real, off in plants:
        ec = (1 - TL / (th + 273.15)) * 100
        ecs[name] = ec
        ax.plot([th, th], [real, ec], color=C_LIGHT, lw=1.2, zorder=1)
        ax.scatter([th], [ec], color=C_MAIN, s=28, zorder=3)
        ax.scatter([th], [real], color=C_SEC, s=40, zorder=3)
        if off is not None:
            tx, ty, ha, va = off
            ax.text(tx, ty, f"{name}\n実機 {real}% / 上限 {ec:.0f}%", ha=ha, va=va,
                    fontsize=11, color="#1A1A17")
    ax.text(680, 30, f"石炭 亜臨界　実機 38% / 上限 {ecs['石炭 亜臨界']:.0f}%\n石炭 USC　　実機 42% / 上限 {ecs['石炭 USC']:.0f}%",
            ha="left", va="bottom", fontsize=11, color="#1A1A17")
    ax.scatter([], [], color=C_SEC, s=40, label="実機の発電端効率（典型値）")
    ax.set_xlabel("高温側の温度 T_H [°C]"); ax.set_ylabel("効率 [%]")
    ax.set_ylim(0, 90); ax.set_xlim(150, 1750); ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=11, frameon=False)
    ax.set_title("上限を上げる唯一の方法は T_H を上げること — 実機はどれも上限の 6〜7 割", fontsize=11.5)
    savefig(fig, "ch01_carnot_curve.png"); plt.close(fig)

# ============================================================ 3. T–S 図（カルノーサイクルの導出用）
def fig_carnot_ts():
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    TH, TL, S1, S2 = 900, 300, 1.0, 3.0
    ax.fill_between([S1, S2], [TL, TL], [TH, TH], color="#E8C9C3", alpha=0.9)
    ax.fill_between([S1, S2], [0, 0], [TL, TL], color="#DCD8CC", alpha=0.9)
    ax.plot([S1, S2], [TH, TH], color=C_MAIN, lw=2.5); ax.plot([S1, S2], [TL, TL], color=C_BLUE, lw=2.5)
    ax.plot([S1, S1], [TL, TH], color=C_GREY, lw=1.8); ax.plot([S2, S2], [TL, TH], color=C_GREY, lw=1.8)
    ax.annotate("", xy=(2.0, TH), xytext=(1.6, TH), arrowprops=dict(arrowstyle="->", color=C_MAIN, lw=2))
    ax.annotate("", xy=(1.6, TL), xytext=(2.0, TL), arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=2))
    ax.text(2.0, TH + 35, "① 等温膨張 T_H：熱 Q_H = T_H ΔS を受け取る", ha="center", fontsize=11, color=C_MAIN)
    ax.text(2.0, TL - 55, "③ 等温圧縮 T_L：熱 Q_L = T_L ΔS を捨てる", ha="center", fontsize=11, color=C_BLUE)
    ax.text(S2 + 0.08, 600, "② 断熱膨張\n(S 一定)", fontsize=11, color=C_GREY)
    ax.text(S1 - 0.55, 600, "④ 断熱圧縮\n(S 一定)", fontsize=11, color=C_GREY)
    ax.text(2.0, 600, "仕事 W = Q_H − Q_L\n= (T_H − T_L) ΔS", ha="center", va="center", fontsize=11, weight="bold", color="#1A1A17")
    ax.text(2.0, 150, "捨てる熱 Q_L = T_L ΔS", ha="center", va="center", fontsize=11.5, color="#1A1A17")
    ax.text(3.35, 50, "η = W/Q_H = 1 − T_L/T_H", fontsize=12, color=C_MAIN, weight="bold", ha="right")
    ax.set_xlim(0.3, 3.6); ax.set_ylim(0, 1050)
    ax.set_xlabel("エントロピー S"); ax.set_ylabel("温度 T [K]")
    ax.set_xticks([S1, S2]); ax.set_xticklabels(["S₁", "S₂"]); ax.set_yticks([TL, TH]); ax.set_yticklabels(["T_L", "T_H"])
    ax.set_title("T–S 図で見るカルノーサイクル：面積が熱、差が仕事", fontsize=11.5)
    savefig(fig, "ch01_carnot_ts.png"); plt.close(fig)

# ============================================================ 4. 発電方式ごとの総合効率
def fig_methods():
    rows = [("汽力(石炭・LNG)", 40, 43, True), ("コンバインド", 55, 64, True), ("原子力", 33, 35, True),
            ("水力", 80, 90, False), ("風力(C_p)", 35, 45, False), ("太陽光(モジュール)", 15, 22, False), ("燃料電池", 40, 60, False)]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    for i, (name, lo, hi, carnot) in enumerate(rows):
        c = C_MAIN if carnot else C_SEC
        ax.barh(i, hi - lo, left=lo, color=c, alpha=0.85, height=0.55)
        ax.text(hi + 1, i, f"{lo}〜{hi}%", va="center", fontsize=11, color="#1A1A17")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows]); ax.invert_yaxis()
    ax.set_xlim(0, 100); ax.set_xlabel("総合効率（一次エネルギー → 電気）[%]"); ax.grid(axis="x", alpha=0.3)
    # 空の barh を凡例に使うと色が付かない（既定の青になる）。Patch で明示する
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C_MAIN, alpha=0.85, label="熱を経由する（カルノー上限を受ける）"),
                       Patch(facecolor=C_SEC, alpha=0.85, label="熱を経由しない（別の上限：落差・ベッツ・バンドギャップ）")],
              loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=1, fontsize=11, frameon=False)
    ax.set_title("熱を通るかどうかで、効率の「壁」の種類が変わる", fontsize=11.5)
    savefig(fig, "ch01_methods.png"); plt.close(fig)

# ============================================================ 5. 水力の出力式
def fig_hydro():
    H = np.linspace(0, 300, 200); eta = 0.85
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    for Q, c in [(4, C_SEC), (8, C_MAIN), (12, C_ACC)]:
        ax.plot(H, 9.8 * Q * H * eta / 1000, color=c, lw=2, label=f"Q = {Q} m³/s")
    P_ex = 9.8 * 8 * 120 * eta / 1000
    ax.scatter([120], [P_ex], color=C_MAIN, s=60, zorder=4)
    ax.annotate(f"例題：H = 120 m, Q = 8 m³/s, η = 0.85\nP = 9.8 × 8 × 120 × 0.85 = {9.8*8*120*eta:.0f} kW ≈ {P_ex:.1f} MW",
                (120, P_ex), xytext=(130, 20), fontsize=11, arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("有効落差 H [m]"); ax.set_ylabel("出力 P [MW]"); ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=11); ax.set_ylim(0, 32)
    ax.set_title("水力 P = 9.8 Q H η [kW] — 落差と流量に比例、係数 9.8 は ρg/1000", fontsize=11.5)
    savefig(fig, "ch01_hydro.png"); plt.close(fig)

# ============================================================ 6. 風の 3 乗則とパワーカーブ
def fig_wind():
    rho, D, Cp, Prated = 1.225, 90.0, 0.45, 2.0e6
    A = np.pi * D**2 / 4
    v = np.linspace(0, 27, 400)
    Pw = 0.5 * rho * A * v**3
    Pt = np.where((v >= 3) & (v <= 25), np.minimum(Pw * Cp, Prated), 0)
    v_rated = (Prated / (0.5 * rho * A * Cp)) ** (1 / 3)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    a1.plot(v, 0.5 * rho * v**3, color=C_MAIN, lw=2.2)
    for v0 in (8, 10):
        a1.scatter([v0], [0.5 * rho * v0**3], color=C_ACC, s=40, zorder=3)
    a1.annotate(f"8 → 10 m/s で {((10/8)**3):.2f} 倍", (10, 0.5 * rho * 1000), xytext=(3.5, 700), fontsize=11.5,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a1.set_xlabel("風速 v [m/s]"); a1.set_ylabel("風のパワー密度 ½ρv³ [W/m²]"); a1.grid(alpha=0.3)
    a1.set_title("風のエネルギーは v の 3 乗", fontsize=11); a1.set_xlim(0, 15); a1.set_ylim(0, 2200)
    a2.plot(v, Pw * Cp / 1e6, color=C_LIGHT, lw=1.5, ls="--", label="½ρAv³·C_p（制限なし）")
    a2.plot(v, Pt / 1e6, color=C_MAIN, lw=2.4, label=f"実機のパワーカーブ（D = {D:.0f} m, C_p = {Cp}）")
    for x, lab in [(3, "カットイン 3 m/s"), (v_rated, f"定格 {v_rated:.1f} m/s"), (25, "カットアウト 25 m/s")]:
        a2.axvline(x, color=C_GREY, lw=0.8, ls=":"); a2.text(x + 0.3, 2.35, lab, fontsize=11, color=C_GREY, rotation=90, va="top")
    a2.set_ylim(0, 2.6); a2.set_xlim(0, 27); a2.set_xlabel("風速 v [m/s]"); a2.set_ylabel("出力 [MW]"); a2.grid(alpha=0.3)
    a2.legend(frameon=False, fontsize=11, loc="lower right"); a2.set_title("定格で頭打ち、強風で停止", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch01_wind.png"); plt.close(fig)
    return v_rated, A

# ============================================================ 7. ベッツの限界（運動量理論）
def fig_betz():
    a = np.linspace(0, 0.5, 300)
    Cp = 4 * a * (1 - a)**2
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.plot(a, Cp, color=C_MAIN, lw=2.4, label="C_p(a) = 4a(1 − a)²")
    ax.scatter([1/3], [16/27], color=C_ACC, s=70, zorder=4)
    ax.annotate(f"最大：a = 1/3 で C_p = 16/27 = {16/27:.3f}（ベッツの限界）", (1/3, 16/27), xytext=(0.05, 0.64), fontsize=11.5,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.axhspan(0.35, 0.45, color=C_SEC, alpha=0.15); ax.text(0.42, 0.40, "実機 0.35〜0.45", fontsize=11, color=C_SEC, va="center")
    ax.set_xlabel("軸方向誘導係数 a = (v₁ − v_ロータ)/v₁（風をどれだけ減速させるか）"); ax.set_ylabel("パワー係数 C_p")
    ax.set_xlim(0, 0.5); ax.set_ylim(0, 0.7); ax.grid(alpha=0.3); ax.legend(frameon=False, loc="lower right")
    ax.set_title("風を止めすぎても取れない — 減速 1/3 が最適", fontsize=11.5)
    savefig(fig, "ch01_betz.png"); plt.close(fig)

# ============================================================ 8. 太陽光スペクトルとバンドギャップ
def fig_pv_spectrum():
    kT = 8.617e-5 * 5778           # eV
    E = np.linspace(0.2, 4.5, 2000)
    N = E**2 / (np.exp(E / kT) - 1)  # 光子数スペクトル（黒体、任意単位）
    Eg = 1.12
    tot = np.trapz(E * N, E)
    usable = Eg * np.trapz(N[E >= Eg], E[E >= Eg])
    below = np.trapz((E * N)[E < Eg], E[E < Eg])
    therm = np.trapz(((E - Eg) * N)[E >= Eg], E[E >= Eg])
    u = usable / tot
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    ax.plot(E, E * N / (E * N).max(), color=C_MAIN, lw=2, label="太陽光のエネルギースペクトル（5778 K 黒体）")
    m = E < Eg
    ax.fill_between(E[m], 0, (E * N / (E * N).max())[m], color=C_LIGHT, alpha=0.9, label=f"吸収されない（E < E_g）{below/tot*100:.0f}%")
    m2 = E >= Eg
    ax.fill_between(E[m2], 0, (Eg * N / (E * N).max())[m2], color=C_SEC, alpha=0.6, label=f"電気になれる分（E_g × 光子数）{u*100:.0f}%")
    ax.fill_between(E[m2], (Eg * N / (E * N).max())[m2], (E * N / (E * N).max())[m2], color="#E8C9C3", alpha=0.9,
                    label=f"熱になる（E − E_g）{therm/tot*100:.0f}%")
    ax.axvline(Eg, color=C_ACC, lw=1.5, ls="--"); ax.text(Eg + 0.06, 0.06, "Si のバンドギャップ\nE_g = 1.12 eV", fontsize=11, color=C_ACC)
    ax.set_xlabel("光子のエネルギー E [eV]"); ax.set_ylabel("相対エネルギー密度"); ax.set_ylim(0, 1.05); ax.set_xlim(0.2, 4.5)
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title(f"単接合セルの究極効率 ≈ {u*100:.0f}%（この計算）→ 再結合まで入れた詳細釣り合い限界 33.7%", fontsize=11)
    savefig(fig, "ch01_pv_spectrum.png"); plt.close(fig)
    return u

# ============================================================ 9. 電力品質の 3 指標
def fig_quality():
    rng = np.random.default_rng(1)
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11, 3.6))
    t = np.arange(0, 24, 0.1)
    v = 101 + 2.5 * np.sin(2 * np.pi * t / 24 + 1.5) + np.cumsum(rng.normal(0, 0.12, t.size))
    a1.plot(t, v, color=C_MAIN, lw=1.5); a1.axhspan(95, 107, color=C_SEC, alpha=0.12)
    a1.axhline(107, color=C_SEC, ls="--", lw=1); a1.axhline(95, color=C_SEC, ls="--", lw=1)
    a1.set_ylim(90, 112); a1.set_xlim(0, 24); a1.set_xlabel("時刻 [h]"); a1.set_ylabel("電圧 [V]")
    a1.set_title("電圧：101 ± 6 V（場所ごとに違う）", fontsize=12)
    f = 60 + np.cumsum(rng.normal(0, 0.006, t.size)); f -= (f.mean() - 60)
    a2.plot(t, f, color=C_MAIN, lw=1.5); a2.axhspan(59.8, 60.2, color=C_SEC, alpha=0.12)
    a2.axhline(60.2, color=C_SEC, ls="--", lw=1); a2.axhline(59.8, color=C_SEC, ls="--", lw=1)
    a2.set_ylim(59.6, 60.4); a2.set_xlim(0, 24); a2.set_xlabel("時刻 [h]"); a2.set_ylabel("周波数 [Hz]")
    a2.set_title("周波数：60 ± 0.2 Hz（系統全体で 1 つ）", fontsize=12)
    th = np.linspace(0, 2 * np.pi, 600)
    v1, v5, v7 = 1.0, 0.05, 0.03
    a3.plot(th / np.pi, v1 * np.sin(th), color=C_LIGHT, lw=1.2, ls="--", label="基本波")
    a3.plot(th / np.pi, v1 * np.sin(th) + v5 * np.sin(5 * th) + v7 * np.sin(7 * th), color=C_MAIN, lw=1.8, label="5 次 5% + 7 次 3%")
    thd = np.sqrt(v5**2 + v7**2) / v1 * 100
    a3.text(0.05, -0.95, f"THD = √(0.05² + 0.03²) = {thd:.1f}%\n（高圧の上限 5%）", fontsize=11)
    a3.set_xlabel("位相 [π rad]"); a3.set_ylabel("電圧 [p.u.]"); a3.set_ylim(-1.2, 1.25); a3.legend(frameon=False, fontsize=11, loc="upper right")
    a3.set_title("高調波：波形のひずみ", fontsize=12)
    for a in (a1, a2, a3): a.grid(alpha=0.3)
    fig.tight_layout(); savefig(fig, "ch01_quality.png"); plt.close(fig)

# ============================================================ 10. エネルギーの単位はしご
def fig_units():
    items = [("1 kWh（電気の単位）", 3.6e6), ("家庭 1 日（約 10 kWh）", 3.6e7), ("石炭 1 t（約 25 GJ）", 2.5e10),
             ("1 toe（石油換算トン）", 4.1868e10), ("沖縄本島 1 日の需要（概算 24 GWh）", 8.64e13)]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    for i, (name, J) in enumerate(items):
        ax.barh(i, J, color=C_MAIN if i in (0, 3) else C_SEC, height=0.55)
        ax.text(J * 1.3, i, f"{J:.3g} J = {J/3.6e6:,.0f} kWh", va="center", fontsize=11)
    ax.set_xscale("log"); ax.set_xlim(1e6, 1e15); ax.set_yticks(range(len(items))); ax.set_yticklabels([i[0] for i in items]); ax.invert_yaxis()
    ax.set_xlabel("エネルギー [J]（対数）"); ax.grid(axis="x", alpha=0.3)
    ax.set_title("1 kWh = 3.6 MJ、1 toe ≈ 11,630 kWh — 桁を体で覚える", fontsize=11.5)
    savefig(fig, "ch01_units.png"); plt.close(fig)

# ============================================================ 11. たとえ話・よくある誤解（他回と同じく analogy_figure で統一）
def fig_analogy():
    analogy_figure("ch01_analogy.png",
        left_title="滝とバケツリレー", right_title="発電",
        pairs=[("水車が取り出せるのは落差の分だけ", "落差＝温度差 T_H − T_L"),
               ("落差が大きいほど取り出せる", "高温化＝効率向上（コンバインド）"),
               ("下の川面より下には落とせない", "下の川面＝環境温度 T_L（捨てる熱）"),
               ("バケツリレーは 1 人ずつ少しこぼす", "各段の損失＝ボイラ・タービン・発電機"),
               ("最後に残る水＝全員のこぼし残しの積", "総合効率＝各段の効率の積")],
        note="この対応が頭に入っていれば、なぜ復水器を冷やしたいのか、なぜタービンの改良に投資が集中するのかが「落差の話」として説明できる。")


def fig_myth():
    analogy_figure("ch01_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("技術が進めば火力の効率はいずれ 100% に近づく",
                "熱を通る限り上限はカルノー効率で、上げる道は高温化だけ"),
               ("風力の出力は風速に比例する",
                "風力は風速の 3 乗（½ρAv³）で効く"),
               ("原子力は技術が古いから効率が低い",
                "燃料被覆管の制約で T_H を上げられないから上限自体が低い")],
        note="どれも「今より良くなるはず」という直感ではなく、比の物理（カルノー・ベッツ）で上限を語る。")


# ==================================================== カルノー効率の導出（段階開示）
def fig_deriv_carnot():
    """1 段ずつ見せる 3 枚。スライドで順に出すと、板書と同じ順で追える。"""
    steps = [
        ("① エントロピー収支", r"$\dfrac{Q_H}{T_H} = \dfrac{Q_L}{T_L}$",
         "可逆サイクルは 1 周で元に戻る。\n高温で受けた分と低温で捨てた分が釣り合う"),
        ("② エネルギー保存", r"$W = Q_H - Q_L$",
         "仕事は受けた熱と捨てた熱の差。\n①より Q_L は正なので、ゼロにはできない"),
        ("③ 効率の定義に入れる", r"$\eta = \dfrac{W}{Q_H} = 1 - \dfrac{Q_L}{Q_H}$",
         "①を使って Q_L を消すと、\n熱量が全部消えて温度だけが残る"),
    ]
    result = (r"$\eta_C = 1 - \dfrac{T_L}{T_H}$",
              "効率は温度の「比」だけで決まる")
    for i in (1, 2, 3):
        derivation_figure(f"ch01_deriv_carnot_{i}.png", steps=steps,
                          result=result, reveal=i, width=11.6, height=5.8)


if __name__ == "__main__":
    e = fig_chain(); fig_carnot_curve(); fig_carnot_ts(); fig_methods(); fig_hydro()
    vr, A = fig_wind(); fig_betz(); u = fig_pv_spectrum(); fig_quality(); fig_units()
    fig_analogy(); fig_myth(); fig_deriv_carnot()
    TL = 303.15
    print(f"連鎖の総合効率 {e[-1]/100:.4f}")
    for th in (285, 540, 600, 1400, 1600):
        print(f"T_H={th} °C: η_C = {1 - TL/(th+273.15):.3f}")
    print(f"風車 D=90 m: A = {A:.0f} m², 定格風速 = {vr:.2f} m/s, 8 m/s で 0.85 MW なら C_p = {0.85e6/(0.5*1.225*A*8**3):.3f}")
    print(f"水力例題 P = {9.8*8*120*0.85:.0f} kW; PV 究極効率 = {u:.3f}")
