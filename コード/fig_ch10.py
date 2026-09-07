# -*- coding: utf-8 -*-
"""第10回 気象予測と再エネ出力 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch10.py  → ../図/ch10_*.png
   太陽位置と晴天日射は pws_common の天文計算、PV 出力と風力は物理モデルで実計算する。
   予測誤差・平滑化効果はシード付き乱数（再現可能）で生成する。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import (setup_japanese_font, savefig, solar_position, clear_sky_ghi,
                        pv_power, wind_shear, wind_power_curve)
from pws_eqfig import analogy_figure
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}
LAT, LON = 26.21, 127.68          # 那覇


# ============================================================ 1. 予測の流れ
def fig_pipeline():
    fig, ax = plt.subplots(figsize=(9.8, 3.6))
    ax.axis("off")
    steps = [("数値予報（NWP）", "日射・気温・風速\nGSM 20 km\nMSM 5 km", C_BLUE),
             ("地点への補正", "格子 → 地点\nハブ高さへ\n（べき法則）", C_SEC),
             ("変換モデル", "PV 式・パワーカーブ\nで MW に翻訳", C_MAIN),
             ("評価・運用", "nRMSE で採点\n予備力・出力制御へ", C_WARM)]
    for i, (name, what, c) in enumerate(steps):
        x = 0.02 + i * 0.245
        ax.add_patch(FancyBboxPatch((x, 0.24), 0.215, 0.52, boxstyle="round,pad=0.012",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x + 0.108, 0.68, name, ha="center", fontsize=11.5, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.108, 0.44, what, ha="center", fontsize=11.5, transform=ax.transAxes, linespacing=1.5)
        if i < 3:
            ax.annotate("", xy=(x + 0.238, 0.52), xytext=(x + 0.218, 0.52), xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="->", color=C_GREY, lw=2))
    ax.text(0.5, 0.14, "誤差は「空の予測」と「翻訳の式」の両方から来る", ha="center",
            fontsize=11.5, color=C_MAIN, transform=ax.transAxes)
    savefig(fig, "ch10_pipeline.png"); plt.close(fig)


# ============================================================ 2. 那覇の晴天日射
def fig_clearsky():
    hours = np.linspace(0, 24, 289)
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    peaks = {}
    for doy, lab, c in [(172, "夏至（6/21）", C_ACC), (264, "秋分（9/20）", C_WARM), (355, "冬至（12/21）", C_SEC)]:
        ghi = np.array([clear_sky_ghi(doy, h, LAT, LON) for h in hours])
        ax.plot(hours, ghi, color=c, lw=2.3, label=f"{lab}  最大 {ghi.max():.0f} W/m²")
        peaks[lab] = (ghi.max(), np.trapz(ghi, hours) / 1000)
    ax.set_xlabel("時刻 [h]"); ax.set_ylabel("水平面全天日射量 GHI [W/m²]")
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3)); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False)
    ax.set_title(f"那覇（北緯 {LAT}°）の晴天日射 — 太陽位置から実計算", fontsize=11.5)
    savefig(fig, "ch10_clearsky.png"); plt.close(fig)
    OUT["clearsky"] = peaks


# ============================================================ 3. PV 出力と温度損失
def fig_pv_temp():
    G = np.linspace(0, 1000, 200)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for Ta, c in [(15, C_SEC), (25, C_WARM), (35, C_ACC)]:
        P = np.array([pv_power(g, Ta, p_rated_kw=2000.0)[0] / 1000 for g in G])
        a1.plot(G, P, color=c, lw=2.3, label=f"気温 {Ta} °C")
    a1.plot(G, 2.0 * G / 1000, color=C_LIGHT, lw=2, ls="--", label="温度損失なし（理想）")
    a1.set_xlabel("面日射量 G [W/m²]"); a1.set_ylabel("出力 [MW]（定格 2 MW）")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False, loc="upper left")
    a1.set_title("日射に比例し、暑いほど目減りする", fontsize=11)
    Ta = np.linspace(5, 40, 100)
    for g, c in [(400, C_SEC), (800, C_MAIN), (1000, C_ACC)]:
        Tc = Ta + (45 - 20) / 800 * g
        a2.plot(Ta, Tc, color=c, lw=2.3, label=f"G = {g} W/m²")
    a2.plot(Ta, Ta, color=C_LIGHT, ls="--", lw=1.5, label="気温そのもの")
    a2.scatter([32], [32 + 25 / 800 * 800], color=C_ACC, s=70, zorder=5)
    # 凡例（左上）を避け、恒等線より下の空白（どの折れ線も通らない領域）に注記を置く
    a2.annotate("沖縄の真夏\n気温 32 °C → セル 57 °C", (32, 57), xytext=(24, 13), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.set_xlabel("気温 T_a [°C]"); a2.set_ylabel("セル温度 T_cell [°C]")
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False, loc="upper left")
    a2.set_title("セル温度は気温より 20〜30 °C 高い", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch10_pv_temp.png"); plt.close(fig)
    p_hot = pv_power(800, 32, p_rated_kw=2000.0)[0] / 1000
    p_cool = pv_power(800, 15, p_rated_kw=2000.0)[0] / 1000
    OUT["pv"] = (p_hot, p_cool)


# ============================================================ 4. 1 日の PV 出力（晴・曇）
def fig_pv_day():
    rng = np.random.default_rng(7)
    hours = np.linspace(0, 24, 1441)   # 1 分刻み
    doy = 200
    ghi_clear = np.array([clear_sky_ghi(doy, h, LAT, LON) for h in hours])
    # 雲：滑らかな乱数で透過率を作る
    cl = np.convolve(rng.random(len(hours) + 40), np.ones(25) / 25, mode="same")[:len(hours)]
    kt = np.clip(0.35 + 0.65 * (cl - cl.min()) / (cl.max() - cl.min()), 0.15, 1.0)
    ghi_cloud = ghi_clear * kt
    Ta = 28 + 5 * np.sin((hours - 9) / 24 * 2 * np.pi)
    P_clear = np.array([pv_power(g, t, p_rated_kw=2000.0)[0] / 1000 for g, t in zip(ghi_clear, Ta)])
    P_cloud = np.array([pv_power(g, t, p_rated_kw=2000.0)[0] / 1000 for g, t in zip(ghi_cloud, Ta)])
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.fill_between(hours, 0, P_clear, color=C_LIGHT, alpha=0.6, label=f"快晴 {np.trapz(P_clear, hours):.1f} MWh")
    ax.plot(hours, P_clear, color=C_WARM, lw=2)
    ax.plot(hours, P_cloud, color=C_MAIN, lw=2.2, label=f"雲あり {np.trapz(P_cloud, hours):.1f} MWh")
    ramp = np.max(np.abs(np.diff(P_cloud))) / (hours[1] - hours[0]) / 60
    ax.set_xlabel("時刻 [h]"); ax.set_ylabel("出力 [MW]（定格 2 MW）")
    ax.set_xlim(0, 24); ax.set_xticks(range(0, 25, 3)); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    ax.set_title(f"雲が通ると数分で大きく動く（最大変化率 {ramp:.2f} MW/分 = 定格の {ramp/2*100:.0f}%/分）", fontsize=11.5)
    savefig(fig, "ch10_pv_day.png"); plt.close(fig)
    OUT["ramp"] = ramp
    OUT["kwh"] = (np.trapz(P_clear, hours), np.trapz(P_cloud, hours))


# ============================================================ 5. べき法則
def fig_shear():
    z = np.linspace(1, 150, 200)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    for a, c, lab in [(0.10, C_SEC, "α = 0.10（海上・平坦）"), (0.14, C_MAIN, "α = 0.14（開けた土地）"),
                      (0.30, C_ACC, "α = 0.30（市街地）")]:
        v = 6.0 * (z / 10) ** a
        a1.plot(v, z, color=c, lw=2.3, label=lab)
    a1.axhline(10, color=C_LIGHT, ls=":", lw=1.5); a1.text(4.2, 12, "予報の高さ 10 m", fontsize=11, color=C_GREY)
    a1.axhline(80, color=C_WARM, ls="--", lw=1.5); a1.text(4.2, 84, "ハブ高さ 80 m", fontsize=11, color=C_WARM)
    a1.set_xlabel("風速 [m/s]（地上 10 m で 6 m/s）"); a1.set_ylabel("高さ z [m]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False, loc="lower right")
    a1.set_title("べき法則 v(z) = v₁₀ (z/10)^α", fontsize=11)
    alphas = np.linspace(0.05, 0.35, 100)
    v80 = 6.0 * (80 / 10) ** alphas
    ratio = (v80 / 6.0) ** 3
    a2.plot(alphas, ratio, color=C_MAIN, lw=2.4)
    for a, c in [(0.14, C_SEC), (0.30, C_ACC)]:
        r = ((80 / 10) ** a) ** 3
        a2.scatter([a], [r], color=c, s=70, zorder=5)
        a2.annotate(f"α={a} → 出力 {r:.1f} 倍\n（風速 {6*(8**a):.1f} m/s）", (a, r),
                    textcoords="offset points", xytext=(-100 if a > 0.2 else 8, 10), fontsize=11, color=c)
    a2.set_xlabel("べき指数 α"); a2.set_ylabel("地上 10 m 基準の出力比（3 乗）")
    a2.grid(alpha=0.3)
    a2.set_title("補正を怠ると出力を大きく見誤る", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch10_shear.png"); plt.close(fig)
    OUT["shear"] = (6.0 * (8 ** 0.14), ((8 ** 0.14)) ** 3)


# ============================================================ 6. パワーカーブとワイブル分布
def fig_weibull():
    v = np.linspace(0, 30, 400)
    P = np.array([wind_power_curve(x, p_rated=3.0) for x in v])
    k, c_scale = 2.0, 7.0
    pdf = k / c_scale * (v / c_scale) ** (k - 1) * np.exp(-(v / c_scale) ** k)
    E = np.trapz(P * pdf, v)
    cf = E / 3.0
    fig, ax = plt.subplots(figsize=(9, 4.4))
    ax.plot(v, P, color=C_MAIN, lw=2.6, label="パワーカーブ（定格 3 MW）")
    ax.fill_between(v, 0, P * pdf / pdf.max() * 3.0, color=C_ACC, alpha=0.20,
                    label="出力 × 出現確率（期待値の中身）")
    ax2 = ax.twinx()
    ax2.plot(v, pdf, color=C_SEC, lw=2, ls="--", label=f"風速の分布（ワイブル k={k}, c={c_scale}）")
    ax2.set_ylabel("確率密度", color=C_SEC); ax2.tick_params(axis="y", colors=C_SEC)
    ax2.set_ylim(0, pdf.max() * 2.4)
    # 「定格」「カットアウト」は上に置くと右上の凡例と重なるため下側に、
    # 「カットイン」は凡例の外（左）なので上側のままでよい
    # 「定格」は x=12 付近で風速分布（右軸）の裾とほぼ同じ高さになるため、
    # その裾より上（0.55）から書き始めて重ならないようにする
    for x, lab, y, va in [(3, "カットイン", 3.15, "top"), (12, "定格", 0.55, "bottom"),
                          (25, "カットアウト", 0.15, "bottom")]:
        ax.axvline(x, color=C_GREY, ls=":", lw=1)
        ax.text(x + 0.3, y, lab, fontsize=11, color=C_GREY, rotation=90, va=va)
    ax.set_xlabel("風速 [m/s]"); ax.set_ylabel("出力 [MW]"); ax.set_ylim(0, 3.4); ax.set_xlim(0, 30)
    ax.grid(alpha=0.3)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=11, frameon=False, loc="upper right")
    ax.set_title(f"年間の期待出力 = ∫P(v)f(v)dv = {E:.2f} MW → 設備利用率 {cf*100:.0f}%", fontsize=11.5)
    savefig(fig, "ch10_weibull.png"); plt.close(fig)
    OUT["wind_cf"] = (E, cf)


# ============================================================ 7. 誤差指標（MAPE の発散）
def fig_metrics():
    rng = np.random.default_rng(3)
    hours = np.arange(0, 24, 0.5)
    doy = 200
    act = np.array([clear_sky_ghi(doy, h, LAT, LON) for h in hours]) / 1000 * 2.0
    pred = act + rng.normal(0, 0.10, len(act))
    pred = np.clip(pred, 0, None)
    err = act - pred
    mae = np.abs(err).mean()
    rmse = np.sqrt((err ** 2).mean())
    nrmse = rmse / 2.0 * 100
    with np.errstate(divide="ignore", invalid="ignore"):
        ape = np.where(act > 1e-6, np.abs(err / act) * 100, np.nan)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(hours, act, color=C_MAIN, lw=2.2, label="実績")
    a1.plot(hours, pred, color=C_SEC, lw=1.8, ls="--", label="予測")
    a1.set_xlabel("時刻 [h]"); a1.set_ylabel("出力 [MW]"); a1.grid(alpha=0.3)
    a1.legend(fontsize=11, frameon=False); a1.set_xlim(0, 24)
    a1.set_title(f"MAE = {mae:.3f} MW、RMSE = {rmse:.3f} MW、nRMSE = {nrmse:.1f}%", fontsize=11)
    a2.plot(hours, ape, "o-", color=C_ACC, ms=4, lw=1.5)
    a2.set_yscale("log")
    a2.axvspan(0, 6, color=C_LIGHT, alpha=0.5); a2.axvspan(19, 24, color=C_LIGHT, alpha=0.5)
    a2.text(3, 1e4, "夜間\n実績 ≈ 0", ha="center", fontsize=11.5, color=C_GREY)
    a2.set_xlabel("時刻 [h]"); a2.set_ylabel("絶対百分率誤差 |e/y| [%]（対数）")
    a2.set_xlim(0, 24); a2.grid(alpha=0.3, which="both")
    a2.set_title("MAPE は夜間に発散する → 定格で割る nRMSE を使う", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch10_metrics.png"); plt.close(fig)
    OUT["metrics"] = (mae, rmse, nrmse)


# ============================================================ 8. 平滑化効果
def fig_smoothing():
    rng = np.random.default_rng(11)
    Ns = np.arange(1, 51)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for rho, c in [(0.0, C_SEC), (0.3, C_MAIN), (0.7, C_ACC)]:
        sig = 15.0 * np.sqrt((1 + (Ns - 1) * rho) / Ns)
        a1.plot(Ns, sig, color=c, lw=2.3, label=f"相関 ρ = {rho}")
        if rho > 0:
            a1.axhline(15.0 * np.sqrt(rho), color=c, ls=":", lw=1.2)
            a1.text(38, 15.0 * np.sqrt(rho) + 0.3, f"下限 {15*np.sqrt(rho):.1f}%", fontsize=11, color=c)
    a1.set_xlabel("地点数 N"); a1.set_ylabel("合計出力の nRMSE [%]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    # 時系列で見せる
    t = np.arange(0, 120)
    common = np.convolve(rng.normal(0, 1, len(t) + 10), np.ones(7) / 7, mode="same")[:len(t)]
    for N, c, lab in [(1, C_ACC, "1 地点"), (9, C_MAIN, "9 地点の平均"), (36, C_SEC, "36 地点の平均")]:
        each = np.array([np.convolve(rng.normal(0, 1, len(t) + 10), np.ones(7) / 7, mode="same")[:len(t)]
                         for _ in range(N)])
        y = 0.5 * common + 0.5 * each.mean(axis=0)
        a2.plot(t, y / y.std() * 10, color=c, lw=2 if N == 1 else 2.2, alpha=0.9, label=lab)
    a2.set_xlabel("時間 [分]"); a2.set_ylabel("出力の変動（規格化）[%]")
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("共通成分（雲・前線）は平均しても消えない", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch10_smoothing.png"); plt.close(fig)
    OUT["smooth"] = [(rho, 15.0 * np.sqrt((1 + 8 * rho) / 9)) for rho in (0.0, 0.3, 0.7)]


# ============================================================ 9. アンサンブル予報
def fig_ensemble():
    rng = np.random.default_rng(5)
    h = np.arange(0, 49)
    truth = 8 + 3 * np.sin(h / 10) + 1.5 * np.sin(h / 3.3)
    members = []
    for i in range(21):
        drift = np.cumsum(rng.normal(0, 0.12, len(h))) * (h / 48) ** 0.6
        members.append(truth + drift + rng.normal(0, 0.25, len(h)))
    members = np.array(members)
    fig, ax = plt.subplots(figsize=(9, 4.4))
    for m in members:
        ax.plot(h, m, color=C_LIGHT, lw=0.9, alpha=0.8)
    ax.plot(h, members.mean(axis=0), color=C_MAIN, lw=2.6, label="アンサンブル平均")
    ax.plot(h, truth, color=C_ACC, lw=2, ls="--", label="実況")
    sp = members.std(axis=0)
    ax.fill_between(h, members.mean(axis=0) - sp, members.mean(axis=0) + sp, color=C_SEC, alpha=0.20,
                    label="スプレッド（±1σ）")
    ax.plot([], [], color=C_LIGHT, lw=1.2, label="21 メンバー")
    ax.set_xlabel("予報時間 [h]"); ax.set_ylabel("ハブ高さ風速 [m/s]"); ax.grid(alpha=0.3)
    # 上左だと立ち上がりの線群に凡例が重なるため、値が下がる右上の空白へ
    ax.legend(fontsize=11, frameon=False, loc="upper right"); ax.set_xlim(0, 48)
    ax.set_title(f"先になるほど広がる — 24 h で ±{sp[24]:.1f}、48 h で ±{sp[-1]:.1f} m/s", fontsize=11.5)
    savefig(fig, "ch10_ensemble.png"); plt.close(fig)
    OUT["spread"] = (sp[24], sp[-1])


# ============================================================ 10. 出力制御（九州の例）
def fig_curtail():
    hours = np.linspace(0, 24, 145)
    doy = 100
    ghi = np.array([clear_sky_ghi(doy, h, LAT, LON) for h in hours])
    pv = ghi / ghi.max() * 500                      # 太陽光 500 MW 相当（沖縄の実勢）
    demand = 620 + 90 * np.sin((hours - 15) / 24 * 2 * np.pi) + 40 * np.sin((hours - 8) / 12 * 2 * np.pi)
    must_run = np.full_like(hours, 320.0)           # 火力の最低出力
    room = demand - must_run
    curtail = np.maximum(pv - room, 0)
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    ax.plot(hours, demand, color=C_MAIN, lw=2.4, label="需要（休日の軽負荷日）")
    ax.set_ylim(0, 900)
    ax.plot(hours, must_run, color=C_GREY, lw=2, ls="--", label="火力の最低出力 320 MW")
    ax.fill_between(hours, must_run, must_run + np.minimum(pv, room), color=C_WARM, alpha=0.35,
                    label="受け入れられる太陽光")
    ax.fill_between(hours, must_run + np.minimum(pv, room), must_run + pv,
                    where=curtail > 0, color=C_ACC, alpha=0.35, label="出力制御される分")
    ax.set_xlabel("時刻 [h]"); ax.set_ylabel("電力 [MW]"); ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3)); ax.grid(alpha=0.3)
    ax.legend(fontsize=11, frameon=False, loc="upper left")
    cur_mwh = np.trapz(curtail, hours)
    ax.set_title(f"晴天・軽負荷の休日は太陽光が余る — この日は {cur_mwh:.0f} MWh を出力制御", fontsize=11.5)
    savefig(fig, "ch10_curtail.png"); plt.close(fig)
    OUT["curtail"] = (curtail.max(), cur_mwh)


# ============================================================ 11. たとえ話 — 通訳と再エネ予測
def fig_analogy():
    analogy_figure("ch10_analogy.png",
        left_title="通訳（たとえ）", right_title="再エネ予測（実物）",
        pairs=[("脚本（明日の空）を、通訳が別の言葉に訳す", "翻訳の作業＝数値予報を変換モデルで MW に直すこと"),
               ("誤訳の原因は、脚本そのものの誤りと通訳の癖の両方", "誤差の源＝予報誤差とモデル誤差（温度・汚れ）の合計"),
               ("ビルの屋上に上がるほど、風は強く感じる", "高さの効果＝べき法則で地上 10 m からハブ高さへ補正する量"),
               ("通訳は言葉を 1 対 1 で置き換えるだけ", "風力の増幅＝風速の誤差が出力では v³ で 3 倍に拡大すること"),
               ("1 人に聞くより、大勢に聞いた方が平均は当たりやすい", "平滑化効果＝多地点を集約すると誤差が減ること（下限はある）")],
        note="この対応が頭に入っていれば、予測の誤差がどこから来るかを追える。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch10_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("天気予報が当たれば、出力予測も当たる",
                "変換モデル（温度・汚れ・高さ）の誤差も同じくらい効く"),
               ("予測の良し悪しは、MAPE で測ればよい",
                "太陽光は夜間ゼロで MAPE が発散するので、定格で割る nRMSE を使う"),
               ("定格 3 MW の風車は、3 MW を出し続ける",
                "風車の設備利用率は 20〜30%（kW と kWh は別物）")],
        note="どれも、数字の意味を確かめずに鵜呑みにしたことから来ている。")


if __name__ == "__main__":
    fig_pipeline(); fig_clearsky(); fig_pv_temp(); fig_pv_day(); fig_shear()
    fig_weibull(); fig_metrics(); fig_smoothing(); fig_ensemble(); fig_curtail()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    for lab, (mx, kwh) in OUT["clearsky"].items():
        print(f"  {lab}: 最大 {mx:.0f} W/m², 日積算 {kwh:.1f} kWh/m²")
    ph, pc = OUT["pv"]
    print(f"PV 2 MW・G=800: 気温 32 °C で {ph:.2f} MW、15 °C で {pc:.2f} MW（差 {(pc-ph)/pc*100:.0f}%）")
    print(f"雲の変化率 {OUT['ramp']:.2f} MW/分、快晴 {OUT['kwh'][0]:.1f} → 雲あり {OUT['kwh'][1]:.1f} MWh")
    v80, r = OUT["shear"]
    print(f"べき法則 α=0.14: 10 m で 6 m/s → 80 m で {v80:.1f} m/s、出力は {r:.2f} 倍")
    E, cf = OUT["wind_cf"]
    print(f"風力（ワイブル k=2, c=7）: 期待出力 {E:.2f} MW、設備利用率 {cf*100:.0f}%")
    mae, rmse, nrmse = OUT["metrics"]
    print(f"誤差指標: MAE {mae:.3f} MW、RMSE {rmse:.3f} MW、nRMSE {nrmse:.1f}%")
    for rho, s in OUT["smooth"]:
        print(f"  平滑化 9 地点・ρ={rho}: nRMSE {s:.1f}%（1 地点は 15.0%）")
    print(f"アンサンブルのスプレッド: 24 h で ±{OUT['spread'][0]:.1f}、48 h で ±{OUT['spread'][1]:.1f} m/s")
    print(f"出力制御: 最大 {OUT['curtail'][0]:.0f} MW、日量 {OUT['curtail'][1]:.0f} MWh")
