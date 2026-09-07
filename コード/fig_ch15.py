# -*- coding: utf-8 -*-
"""第15回 沖縄系統・統合演習 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch15.py  → ../図/ch15_*.png
   6 つの制約（電圧・線路容量・N-1・周波数・安定度・最低出力）の上限を
   すべて実計算し、最小値として連系可能量を求める。対策で律速が移る様子も出す。
   系統定数は viz/island.html と同じ（S=1500 MW, H0=4.5 s, K0=150 MW/Hz, 火力最低出力 320 MW）。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig, build_okinawa
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandapower as pp

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

# ---- 沖縄本島系統の前提（viz/island.html と同じ）----
S_SYS = 1500.0      # 系統容量 [MW]
H0 = 4.5            # 現状の系統慣性定数 [s]
K0 = 150.0          # 現状の系統定数 [MW/Hz]
F0 = 60.0
PMIN_TH = 320.0     # 火力の最低出力の合計 [MW]
D_MIN = 620.0       # 休日昼の最小需要 [MW]
TRIP = 120.0        # 想定する電源脱落 [MW]（最大ユニットの一部脱落）
UFR = 58.5          # 低周波数リレー第1段の整定 [Hz]
PVS = np.arange(0, 801, 10.0)


def h_sys(pv, battery=False):
    """太陽光が増えると同期機が止まり H_sys が下がる"""
    h = H0 * max(1 - pv / 900.0, 0.15)
    return h + (2.5 if battery else 0.0)


def k_sys(pv, battery=False):
    k = K0 * max(1 - 0.75 * pv / 900.0, 0.15)
    return k + (200.0 if battery else 0.0)


def freq_nadir(pv, battery=False, trip=TRIP):
    """慣性 → ガバナの応答を積分して最低周波数を出す"""
    H, K = h_sys(pv, battery), k_sys(pv, battery)
    Kl, Kg = K * 0.3, K * 0.7
    dt, f, pg = 0.005, F0, 0.0
    fmin = F0
    for i in range(int(30 / dt)):
        df = f - F0
        dfdt = F0 / (2 * H * S_SYS) * (-trip + pg - Kl * df)
        pg += (-Kg * df - pg) / 8.0 * dt
        f += dfdt * dt
        fmin = min(fmin, f)
    return fmin


def t_cr(pv):
    """慣性低下による臨界除去時間（第7回の式、δ_cr は H に依らない）"""
    Pm, Pmax = 0.8, 2.0
    d0 = np.arcsin(Pm / Pmax); dmax = np.pi - d0
    dcr = np.arccos((Pm * (dmax - d0) + Pmax * np.cos(dmax)) / Pmax)
    return np.sqrt(4 * h_sys(pv) * (dcr - d0) / (2 * np.pi * F0 * Pm)) * 1000


def volt_max(pv, pf=1.0):
    """軽負荷時に太陽光を末端へ連系したときの最高電圧"""
    net = build_okinawa(pv_mw=float(pv), pv_pf=pf, pv_bus=4, load_scale=0.30)
    try:
        pp.runpp(net)
        return net.res_bus.vm_pu.max()
    except Exception:
        return np.nan


def line_load(pv):
    """軽負荷＋太陽光のときの最大線路利用率"""
    net = build_okinawa(pv_mw=float(pv), pv_bus=4, load_scale=0.30)
    try:
        pp.runpp(net)
        return net.res_line.loading_percent.max()
    except Exception:
        return np.nan


def limits(pf=1.0, battery_freq=False, battery_charge=0.0, relax_min=0.0):
    """6 制約それぞれの上限 [MW] を返す"""
    lim = {}
    # ① 電圧（1.05 p.u.）
    v = np.array([volt_max(p, pf) for p in PVS])
    over = np.where(v > 1.05)[0]
    lim["電圧"] = PVS[over[0]] if len(over) else PVS[-1]
    # ② 線路容量（100%）
    ld = np.array([line_load(p) for p in PVS])
    over = np.where(ld > 100)[0]
    lim["線路容量"] = PVS[over[0]] if len(over) else PVS[-1]
    # ③ N-1（1 回線停止相当：容量の 70% で判定）
    over = np.where(ld > 70)[0]
    lim["N-1"] = PVS[over[0]] if len(over) else PVS[-1]
    # ④ 周波数（nadir が UFR を割らない）
    nad = np.array([freq_nadir(p, battery_freq) for p in PVS])
    over = np.where(nad < UFR)[0]
    lim["周波数"] = PVS[over[0]] if len(over) else PVS[-1]
    # ⑤ 安定度（t_cr が保護の 100 ms を下回らない）
    tc = np.array([t_cr(p) for p in PVS])
    over = np.where(tc < 100)[0]
    lim["安定度"] = PVS[over[0]] if len(over) else PVS[-1]
    # ⑥ 火力の最低出力（最小需要 − 最低出力 + 蓄電池の充電）
    lim["最低出力"] = D_MIN - (PMIN_TH - relax_min) + battery_charge
    return lim, dict(v=v, ld=ld, nad=nad, tc=tc)


# ============================================================ 1. 沖縄系統モデル
def fig_system():
    net = build_okinawa(); pp.runpp(net)
    names = list(net.bus.name.values)
    pos = {0: (0.20, 0.78), 1: (0.20, 0.45), 2: (0.45, 0.22), 3: (0.72, 0.45), 4: (0.72, 0.80)}
    # 文字を底上げした分、キャンバスも一回り広げて母線の箱の中の文字間隔に余裕を持たせる
    fig, ax = plt.subplots(figsize=(11.4, 5.5))
    ax.axis("off")
    for _, row in net.line.iterrows():
        f, t = int(row.from_bus), int(row.to_bus)
        ax.plot([pos[f][0], pos[t][0]], [pos[f][1], pos[t][1]], color=C_LIGHT,
                lw=1.5 + row.parallel * 0.9, transform=ax.transAxes, zorder=1)
        mx, my = (pos[f][0] + pos[t][0]) / 2, (pos[f][1] + pos[t][1]) / 2
        if abs(pos[f][0] - pos[t][0]) < 0.05:
            # 縦の線は母線の箱と重なるので、1 行にまとめて線の右脇へ逃がす
            ax.text(mx + 0.06, my, f"{row.length_km:.0f} km・{int(row.parallel)} 回線", ha="left", va="center",
                    fontsize=11, color=C_GREY, transform=ax.transAxes)
        else:
            # 斜めの線は中点だと隣の箱に近すぎるので、線の向きと垂直な方向へさらに逃がす
            dx, dy = pos[t][0] - pos[f][0], pos[t][1] - pos[f][1]
            norm = (dx ** 2 + dy ** 2) ** 0.5
            ox, oy = -dy / norm * 0.045, dx / norm * 0.045
            if oy < 0:
                ox, oy = -ox, -oy
            ax.text(mx + ox, my + oy, f"{row.length_km:.0f} km\n{int(row.parallel)} 回線", ha="center",
                    fontsize=11, color=C_GREY, transform=ax.transAxes)
    loads = {int(r.bus): (r.p_mw, r.q_mvar) for _, r in net.load.iterrows()}
    for i, (x, y) in pos.items():
        has_gen = i in (0, 1)
        c = C_MAIN if has_gen else C_SEC
        ax.add_patch(FancyBboxPatch((x - 0.078, y - 0.07), 0.156, 0.14, boxstyle="round,pad=0.008",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x, y + 0.023, names[i], ha="center", fontsize=11.5, weight="bold", color=c, transform=ax.transAxes)
        sub = "発電" if has_gen else (f"負荷 {loads[i][0]:.0f} MW" if i in loads else "")
        ax.text(x, y - 0.033, sub, ha="center", fontsize=11, transform=ax.transAxes)
    ax.text(0.5, 0.03, f"系統容量 {S_SYS:.0f} MW ／ H = {H0} s ／ K = {K0:.0f} MW/Hz ／ 火力の最低出力 {PMIN_TH:.0f} MW ／ 60 Hz・連系線なし",
            ha="center", fontsize=12, color=C_MAIN, transform=ax.transAxes)
    ax.set_title("沖縄本島系統の簡略モデル（132 kV・5 母線）", fontsize=12.5)
    savefig(fig, "ch15_system.png"); plt.close(fig)
    OUT["base"] = (net.res_bus.vm_pu.min(), net.res_line.loading_percent.max(), net.res_line.pl_mw.sum())


# ============================================================ 2. 6 制約の棒グラフ
def bar_limits(lim, title, fname, note=None):
    order = ["電圧", "線路容量", "N-1", "周波数", "安定度", "最低出力"]
    vals = [lim[k] for k in order]
    mn = min(vals)
    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    cols = [C_ACC if v == mn else C_SEC for v in vals]
    bars = ax.bar(order, vals, color=cols, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 12, f"{v:.0f}", ha="center", fontsize=11, weight="bold")
    ax.axhline(mn, color=C_ACC, ls="--", lw=1.8)
    # 文字を底上げすると、最も低い棒自身の数値ラベルとこの注記が近すぎて重なるので、
    # 他の棒の色の上に出るのを承知でしっかり離す
    ax.text(5.45, mn + 45, f"連系可能量 = min = {mn:.0f} MW", ha="right", fontsize=11,
            color=C_ACC, weight="bold")
    ax.set_ylabel("太陽光の上限 [MW]"); ax.grid(alpha=0.3, axis="y")
    ax.set_ylim(0, max(vals) * 1.22)
    if note:
        ax.text(0.02, 0.94, note, transform=ax.transAxes, fontsize=11.5, color=C_GREY)
    ax.set_title(title, fontsize=11.5)
    savefig(fig, fname); plt.close(fig)
    return mn, order[int(np.argmin(vals))]


def fig_limits_base():
    lim, curves = limits()
    mn, who = bar_limits(lim, "6 つの制約の上限 — 最も低い板が連系可能量を決める", "ch15_limits.png")
    OUT["lim0"] = (lim, mn, who)
    OUT["curves"] = curves


# ============================================================ 3. 各制約の中身
def fig_curves():
    c = OUT["curves"]
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 6.4))
    a = axes[0, 0]
    a.plot(PVS, c["v"], color=C_MAIN, lw=2.3)
    a.axhline(1.05, color=C_ACC, ls="--", lw=1.5); a.text(10, 1.052, "上限 1.05", fontsize=11, color=C_ACC)
    a.set_xlabel("太陽光 [MW]"); a.set_ylabel("最高電圧 [p.u.]"); a.grid(alpha=0.3)
    a.set_title("① 電圧（軽負荷・末端連系）", fontsize=11)
    a = axes[0, 1]
    a.plot(PVS, c["ld"], color=C_MAIN, lw=2.3)
    a.axhline(100, color=C_ACC, ls="--", lw=1.5); a.text(10, 103, "容量 100%", fontsize=11, color=C_ACC)
    a.axhline(70, color=C_WARM, ls="--", lw=1.5); a.text(10, 72, "N-1 判定 70%", fontsize=11, color=C_WARM)
    a.set_xlabel("太陽光 [MW]"); a.set_ylabel("最大線路利用率 [%]"); a.grid(alpha=0.3)
    a.set_title("②③ 線路容量と N-1", fontsize=11)
    a = axes[1, 0]
    a.plot(PVS, c["nad"], color=C_MAIN, lw=2.3)
    a.axhline(UFR, color=C_ACC, ls="--", lw=1.5); a.text(10, UFR + 0.06, f"UFR {UFR} Hz", fontsize=11, color=C_ACC)
    a.set_xlabel("太陽光 [MW]"); a.set_ylabel(f"最低周波数 [Hz]\n（{TRIP:.0f} MW 脱落）"); a.grid(alpha=0.3)
    a.set_title("④ 周波数（慣性と K の低下）", fontsize=11)
    a = axes[1, 1]
    a.plot(PVS, c["tc"], color=C_MAIN, lw=2.3)
    a.axhline(100, color=C_ACC, ls="--", lw=1.5); a.text(10, 105, "保護の 100 ms", fontsize=11, color=C_ACC)
    a.set_xlabel("太陽光 [MW]"); a.set_ylabel("臨界除去時間 [ms]"); a.grid(alpha=0.3)
    a.set_title("⑤ 安定度（t_cr ∝ √H）", fontsize=11)
    fig.suptitle("制約ごとに「どこで破れるか」を実計算する", fontsize=12.5)
    # この図はスライド上でキャンバスを大きく縮めるので、文字が相対的に大きくなる分
    # サブプロット間の余白を広めに取ってタイトル・軸ラベルの重なりを防ぐ
    fig.tight_layout(rect=(0.03, 0.0, 1.0, 0.93))
    fig.subplots_adjust(hspace=0.85, wspace=0.42)
    savefig(fig, "ch15_curves.png"); plt.close(fig)


# ============================================================ 4. H と K の低下
def fig_hk():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(PVS, [h_sys(p) for p in PVS], color=C_MAIN, lw=2.4, label="対策なし")
    a1.plot(PVS, [h_sys(p, True) for p in PVS], color=C_SEC, lw=2.4, ls="--", label="蓄電池（合成慣性）")
    a1.set_xlabel("太陽光 [MW]"); a1.set_ylabel("系統慣性定数 H [s]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title("同期機を止めると H が下がる", fontsize=11)
    a2.plot(PVS, [k_sys(p) for p in PVS], color=C_MAIN, lw=2.4, label="対策なし")
    a2.plot(PVS, [k_sys(p, True) for p in PVS], color=C_SEC, lw=2.4, ls="--", label="蓄電池（高速応答）")
    a2.set_xlabel("太陽光 [MW]"); a2.set_ylabel("系統定数 K [MW/Hz]")
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("ガバナ付き火力が減ると K も下がる", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch15_hk.png"); plt.close(fig)
    OUT["hk"] = (h_sys(0), h_sys(400), k_sys(0), k_sys(400))


# ============================================================ 5. 周波数応答の比較
def fig_freq_response():
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    for pv, bat, c, lab in [(0, False, C_SEC, "太陽光 0 MW"),
                            (300, False, C_WARM, "太陽光 300 MW"),
                            (300, True, C_MAIN, "太陽光 300 MW ＋ 蓄電池")]:
        H, K = h_sys(pv, bat), k_sys(pv, bat)
        Kl, Kg = K * 0.3, K * 0.7
        dt, f, pg = 0.005, F0, 0.0
        ts, fs = [], []
        for i in range(int(30 / dt)):
            df = f - F0
            dfdt = F0 / (2 * H * S_SYS) * (-TRIP + pg - Kl * df)
            pg += (-Kg * df - pg) / 8.0 * dt
            f += dfdt * dt
            ts.append(i * dt); fs.append(f)
        ax.plot(ts, fs, color=c, lw=2.3, label=f"{lab}  最低 {min(fs):.2f} Hz")
    # 破線を全幅に引くと右下の凡例の上を横切ってしまうので、凡例の手前までで止める。
    # 注記も横に長いと凡例に届くので 2 行にして幅を抑える
    ax.plot([0, 13.5], [UFR, UFR], color=C_ACC, ls="--", lw=1.6)
    ax.text(0.5, UFR + 0.10, f"UFR {UFR} Hz\n（負荷遮断）", fontsize=11.5, color=C_ACC, va="bottom")
    ax.set_xlabel("時間 [s]"); ax.set_ylabel("周波数 [Hz]"); ax.set_xlim(0, 30)
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="lower right")
    ax.set_title(f"{TRIP:.0f} MW 脱落時の周波数 — 太陽光が増えるほど深く落ちる", fontsize=11.5)
    savefig(fig, "ch15_freq_response.png"); plt.close(fig)


# ============================================================ 6. 対策で律速が移る
def fig_measures():
    cases = [("対策なし", dict()),
             ("力率 0.95", dict(pf=0.95)),
             ("＋蓄電池（周波数）", dict(pf=0.95, battery_freq=True)),
             ("＋蓄電池（昼充電 150 MW）", dict(pf=0.95, battery_freq=True, battery_charge=150.0))]
    order = ["電圧", "線路容量", "N-1", "周波数", "安定度", "最低出力"]
    res = []
    for name, kw in cases:
        lim, _ = limits(**kw)
        vals = [lim[k] for k in order]
        res.append((name, vals, min(vals), order[int(np.argmin(vals))]))
    fig, ax = plt.subplots(figsize=(10.2, 4.6))
    w = 0.2
    xs = np.arange(len(order))
    for i, (name, vals, mn, who) in enumerate(res):
        ax.bar(xs + (i - 1.5) * w, vals, w, label=f"{name}（{mn:.0f} MW・律速 {who}）",
               color=[C_LIGHT, C_SEC, C_WARM, C_MAIN][i])
    ax.set_xticks(xs); ax.set_xticklabels(order)
    ax.set_ylabel("太陽光の上限 [MW]"); ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=11, frameon=False, ncol=2, loc="upper left")
    ax.set_ylim(0, 1050)
    ax.set_title("対策を打つと律速が別の制約へ移る", fontsize=11.5)
    savefig(fig, "ch15_measures.png"); plt.close(fig)
    OUT["measures"] = res


# ============================================================ 7. 対策の効き先
def fig_measure_map():
    fig, ax = plt.subplots(figsize=(9.8, 4.2))
    ax.axis("off")
    rows = [("力率 0.95 運転", ["電圧"], "インバータが Q を吸う（第9回）", C_SEC),
            ("蓄電池（合成慣性）", ["周波数", "安定度"], "H と K を補う（第9回）", C_MAIN),
            ("蓄電池（昼に充電）", ["最低出力"], "最小需要を持ち上げる", C_WARM),
            ("送電線の増強", ["線路容量", "N-1"], "容量そのものを増やす（第14回）", C_BLUE)]
    cols = ["電圧", "線路容量", "N-1", "周波数", "安定度", "最低出力"]
    for k, c in enumerate(cols):
        ax.text(0.34 + k * 0.108, 0.88, c, ha="center", fontsize=11.5, color=C_GREY, transform=ax.transAxes)
    for i, (name, targets, how, col) in enumerate(rows):
        y = 0.72 - i * 0.17
        ax.text(0.02, y, name, fontsize=12, weight="bold", color=col, transform=ax.transAxes)
        ax.text(0.02, y - 0.055, how, fontsize=11, color=C_GREY, transform=ax.transAxes)
        for k, c in enumerate(cols):
            x = 0.34 + k * 0.108
            if c in targets:
                ax.add_patch(FancyBboxPatch((x - 0.042, y - 0.035), 0.084, 0.075,
                                            boxstyle="round,pad=0.004", transform=ax.transAxes,
                                            fc=col, alpha=0.75, ec="none"))
                ax.text(x, y, "◎", ha="center", va="center", fontsize=12, color="white", transform=ax.transAxes)
            else:
                ax.text(x, y, "—", ha="center", va="center", fontsize=11, color=C_LIGHT, transform=ax.transAxes)
    ax.text(0.5, 0.04, "律速でない制約に投資しても連系可能量は増えない", ha="center",
            fontsize=11.5, color=C_ACC, transform=ax.transAxes)
    ax.set_title("どの対策がどの制約に効くか", fontsize=12.5)
    savefig(fig, "ch15_measure_map.png"); plt.close(fig)


# ============================================================ 8. 日負荷曲線と最低出力
def fig_duck():
    hours = np.linspace(0, 24, 145)
    demand = 780 + 130 * np.sin((hours - 15) / 24 * 2 * np.pi) + 60 * np.sin((hours - 8) / 12 * 2 * np.pi)
    demand = demand * 0.82
    pv_shape = np.clip(np.sin((hours - 6) / 12 * np.pi), 0, None) ** 1.3
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    day = (hours >= 9) & (hours <= 15)          # 昼＝太陽光が効く時間帯
    for pv_cap, c, ls in [(0, C_GREY, ":"), (300, C_WARM, "--"), (600, C_ACC, "-")]:
        net_load = demand - pv_shape * pv_cap
        # 最低出力制約が問題になるのは昼。全体の最小（明け方）ではなく昼の最小を示す
        ax.plot(hours, net_load, color=c, ls=ls, lw=2.3,
                label=f"太陽光 {pv_cap} MW（昼の正味需要 最小 {net_load[day].min():.0f} MW）")
    ax.axhline(PMIN_TH, color=C_MAIN, lw=2.2)
    ax.text(0.4, PMIN_TH + 20, f"火力の最低出力 {PMIN_TH:.0f} MW",
            fontsize=12.5, color=C_MAIN, weight="bold")
    ax.text(23.6, PMIN_TH - 55, "この帯より下へは落とせない", fontsize=11.5,
            color=C_MAIN, ha="right")
    ax.fill_between(hours, 0, PMIN_TH, color=C_MAIN, alpha=0.06)
    ax.set_xlabel("時刻 [h]"); ax.set_ylabel("正味需要 [MW]"); ax.set_xlim(0, 24)
    ax.set_xticks(range(0, 25, 3)); ax.set_ylim(0, 1060); ax.grid(alpha=0.3)
    # 曲線の最大は 786 MW。上に空けた帯に凡例を置く（どの線とも重ならない）
    ax.legend(fontsize=11, frameon=False, loc="upper center", ncol=1)
    ax.set_title("正味需要が火力の最低出力を割ると、太陽光を絞るしかない", fontsize=11.5)
    savefig(fig, "ch15_duck.png"); plt.close(fig)
    nl600 = (demand - pv_shape * 600)[day].min()
    OUT["duck"] = (demand[day].min(), nl600)


# ============================================================ 9. 蓄電池の必要量
def fig_battery():
    Ks = np.array([60, 80, 100, 120, 150])
    dFmax = np.array([0.8, 1.0, 1.5])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    for dF, c in zip(dFmax, [C_ACC, C_MAIN, C_SEC]):
        Kreq = TRIP / dF
        need = np.maximum(Kreq - Ks, 0)
        a1.plot(Ks, need, "o-", color=c, lw=2.2, ms=5, label=f"許容 ΔF = {dF} Hz")
    a1.set_xlabel("太陽光導入後の系統定数 K [MW/Hz]"); a1.set_ylabel("蓄電池が補う K_bat [MW/Hz]")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title(f"K_bat = ΔP/|ΔF|max − K（ΔP = {TRIP:.0f} MW）", fontsize=11)
    for dF, c in zip(dFmax, [C_ACC, C_MAIN, C_SEC]):
        Kreq = TRIP / dF
        P = np.maximum(Kreq - Ks, 0) * dF
        a2.plot(Ks, P, "o-", color=c, lw=2.2, ms=5, label=f"許容 ΔF = {dF} Hz")
    a2.set_xlabel("太陽光導入後の系統定数 K [MW/Hz]"); a2.set_ylabel("蓄電池の出力 P_bat [MW]")
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("必要な出力（容量 kWh ではなく kW が効く）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch15_battery.png"); plt.close(fig)
    K400 = k_sys(400)
    OUT["battery"] = (K400, max(TRIP / 1.0 - K400, 0), max(TRIP / 1.0 - K400, 0) * 1.0)


# ============================================================ 10. 15 回のつながり
def fig_map():
    fig, ax = plt.subplots(figsize=(10.0, 4.6))
    ax.axis("off")
    # この図はスライド上でキャンバスを大きく縮めるので、文字が相対的に大きくなる分
    # ボックス幅を控えめにして隙間を広く取り、隣のボックスと文字が重ならないようにする
    # 説明文（what）も横幅が足りないので、行あたりの文字数を減らして隣の箱と重ならないようにする
    groups = [("Day 1", "（第1〜4回）", "エネルギー変換\n系統構成\nP,Q,Y_bus,直流法", C_SEC, 0.13),
              ("Day 2", "（第5〜8回）", "NR 法・鼻先曲線\n等面積法\nΔP = KΔF", C_MAIN, 0.37),
              ("Day 3", "（第9〜12回）", "インバータ\n気象・需要予測\n機械学習", C_WARM, 0.61),
              ("Day 4", "（第13〜15回）", "AI 解析\n最適化\n統合演習", C_ACC, 0.85)]
    BOX_W = 0.19
    for day, period, what, c, cx in groups:
        ax.add_patch(FancyBboxPatch((cx - BOX_W / 2, 0.46), BOX_W, 0.34, boxstyle="round,pad=0.012",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        # タイトルは横幅が足りないので「Day N」と「（第…回）」を 2 行に分けて隣の箱との重なりを防ぐ
        ax.text(cx, 0.735, f"{day}\n{period}", ha="center", va="center", fontsize=11, weight="bold",
                color=c, transform=ax.transAxes)
        ax.text(cx, 0.565, what, ha="center", va="center", fontsize=11, transform=ax.transAxes)
    targets = [("電圧", 0.10), ("線路容量・N-1", 0.35), ("周波数・安定度", 0.62), ("最低出力", 0.88)]
    for lab, x in targets:
        ax.add_patch(FancyBboxPatch((x - 0.095, 0.14), 0.19, 0.11, boxstyle="round,pad=0.008",
                                    transform=ax.transAxes, fc=C_LIGHT, ec=C_GREY, lw=1.4))
        ax.text(x, 0.195, lab, ha="center", va="center", fontsize=11, transform=ax.transAxes)
    for x0, x1 in [(0.13, 0.10), (0.37, 0.35), (0.61, 0.62), (0.85, 0.88)]:
        ax.annotate("", xy=(x1, 0.26), xytext=(x0, 0.45), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="->", color=C_GREY, lw=1.6))
    ax.text(0.5, 0.04, "15 回で学んだ道具が、そのまま 6 つの制約の計算になる", ha="center",
            fontsize=12, color=C_MAIN, transform=ax.transAxes)
    ax.set_title("この講義の全体像 — 道具と制約の対応", fontsize=12.5)
    savefig(fig, "ch15_map.png"); plt.close(fig)


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch15_analogy.png",
        left_title="樽（たとえ）", right_title="連系可能量（実物）",
        pairs=[("樽に入る水は一番低い板で決まる", "連系可能量＝6 つの上限の最小値"),
               ("高い板を伸ばしても水は増えない", "律速でない制約への対策は無駄"),
               ("低い板を伸ばすと次に低い板が効く", "対策すると律速が別の制約へ移る"),
               ("板は 6 枚", "電圧・線路容量・N-1・周波数・安定度・最低出力"),
               ("1 枚を伸ばす道具が別の板も伸ばすことがある", "蓄電池は周波数と最低出力の 2 枚を同時に伸ばす")],
        note="この対応が頭に入っていれば、6 制約の計算はすべて「樽の話」に翻訳できる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch15_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("連系可能量は系統の「性能」で、良い系統ほど大きい",
                "連系可能量は「いちばん弱い制約の位置」で決まる"),
               ("太陽光を増やせばその分だけ火力を止められる",
                "火力は最低出力と慣性の分だけ残す必要がある"),
               ("対策すれば必ず連系量が増える",
                "律速でない制約への対策は 1 MW も増やさない")],
        note="どれも「今の律速はどれか」を見ずに判断していることから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch15_deriv_hosting_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 制約はすべて満たす必要がある',
                '電圧・線路容量・N-1・周波数・安定度・最低出力',
                '6 つのうち 1 つでも破れば\n系統は運用できない'),
               ('② 各制約が許す最大量を求める',
                r"$P_1,\ P_2,\ \ldots,\ P_6$",
                '太陽光を 0 から増やしていき、\nその制約が最初に破れる量を上限とする'),
               ('③ 連系可能量は最小値',
                r"$P_{PV} = \min(P_1, P_2, \ldots, P_6)$",
                '最小値を与える制約が「律速」。\n対策はそこにしか効かない')],
            result='律速でない制約をいくら対策しても、1 MW も増えない')


if __name__ == "__main__":
    fig_system(); fig_limits_base(); fig_curves(); fig_hk(); fig_freq_response()
    fig_measures(); fig_measure_map(); fig_duck(); fig_battery(); fig_map()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    vmin, ldmax, ploss = OUT["base"]
    print(f"基準ケース: 最低電圧 {vmin:.3f} p.u.、最大利用率 {ldmax:.0f}%、損失 {ploss:.1f} MW")
    lim, mn, who = OUT["lim0"]
    for k, v in lim.items():
        print(f"  {k}: {v:.0f} MW")
    print(f"→ 連系可能量 {mn:.0f} MW（律速は {who}）")
    h0, h4, k0, k4 = OUT["hk"]
    print(f"H: {h0:.2f} → {h4:.2f} s（太陽光 400 MW）、K: {k0:.0f} → {k4:.0f} MW/Hz")
    for name, vals, m, w in OUT["measures"]:
        print(f"  対策「{name}」: {m:.0f} MW（律速 {w}）")
    dmin, nl600 = OUT["duck"]
    print(f"日負荷: 最小需要 {dmin:.0f} MW、太陽光 600 MW で正味需要 {nl600:.0f} MW（最低出力 {PMIN_TH:.0f} MW）")
    K400, kbat, pbat = OUT["battery"]
    fig_derivations()
    print(f"蓄電池: 太陽光 400 MW で K = {K400:.0f} MW/Hz、ΔF 1.0 Hz に抑えるには K_bat {kbat:.0f} MW/Hz（{pbat:.0f} MW）")
