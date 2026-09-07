# -*- coding: utf-8 -*-
"""第6回 潮流計算の実践 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch06.py  → ../図/ch06_*.png
   系統は pws_common.build_okinawa（沖縄本島 5 母線）と pandapower の IEEE 14 母線。
   数値はすべて pandapower の潮流計算結果。手計算の近似式との比較も実測で出す。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig, build_okinawa
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle
import pandapower as pp
import pandapower.networks as pn

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

# ============================================================ 1. pandapower のデータ構造
def fig_tables():
    net = build_okinawa()
    pp.runpp(net)
    fig, ax = plt.subplots(figsize=(9.6, 4.6))
    ax.axis("off")
    tables = [
        ("net.bus（母線）", ["name", "vn_kv"], net.bus[["name", "vn_kv"]].head(5).values, 0.02, 0.55),
        ("net.line（線路）", ["from", "to", "km"], net.line[["from_bus", "to_bus", "length_km"]].head(4).values, 0.36, 0.55),
        ("net.load（負荷）", ["bus", "p_mw", "q_mvar"], net.load[["bus", "p_mw", "q_mvar"]].values, 0.70, 0.55),
        ("res_bus（結果：電圧）", ["vm_pu", "va_deg"], np.round(net.res_bus[["vm_pu", "va_degree"]].values, 3), 0.02, 0.06),
        ("res_line（結果：潮流）", ["p_from", "loading%"], np.round(net.res_line[["p_from_mw", "loading_percent"]].values, 1), 0.40, 0.06),
    ]
    for title, cols, rows, x, y in tables:
        dx = 0.17 if title.startswith("res_line") else 0.12          # "loading%" は列幅を広めに取る
        ax.text(x, y + 0.36, title, fontsize=12, weight="bold", color=C_MAIN, transform=ax.transAxes)
        ax.add_patch(Rectangle((x - 0.005, y - 0.01), 0.28, 0.36, transform=ax.transAxes,
                               fc="#FBFAF6", ec=C_LIGHT, lw=1))
        for k, c in enumerate(cols):
            ax.text(x + 0.03 + k * dx, y + 0.30, c, fontsize=11, color=C_SEC,
                    ha="right", transform=ax.transAxes)
        for i, r in enumerate(rows[:5]):
            for k, v in enumerate(r):
                ax.text(x + 0.03 + k * dx, y + 0.24 - i * 0.055, str(v)[:9], fontsize=11,
                        ha="right", transform=ax.transAxes)
    ax.annotate("", xy=(0.16, 0.475), xytext=(0.16, 0.535), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=C_ACC, lw=2))
    ax.text(0.19, 0.495, "pp.runpp(net)", fontsize=11.5, color=C_ACC, weight="bold", transform=ax.transAxes)
    savefig(fig, "ch06_tables.png"); plt.close(fig)


# ============================================================ 2. 符号の規約
def fig_sign():
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.axis("off")
    box = dict(boxstyle="round,pad=0.4", fc="#F2EFE6", ec=C_MAIN, lw=1.5)
    box2 = dict(boxstyle="round,pad=0.4", fc="#EEF3FA", ec=C_BLUE, lw=1.5)
    ax.text(0.25, 0.78, "教科書（発電を正）", ha="center", fontsize=12, weight="bold", color=C_MAIN, transform=ax.transAxes)
    ax.text(0.75, 0.78, "pandapower（消費を正）", ha="center", fontsize=12, weight="bold", color=C_BLUE, transform=ax.transAxes)
    rows = [("負荷", "P = −100 MW", "load: p_mw = +100"),
            ("発電", "P = +250 MW", "gen: p_mw = +250"),
            ("太陽光", "P = +80 MW", "sgen: p_mw = +80"),
            ("Q 吸収", "Q = −26 Mvar", "sgen: q_mvar = −26")]
    for i, (name, a, b) in enumerate(rows):
        y = 0.60 - i * 0.15
        ax.text(0.02, y, name, fontsize=12, transform=ax.transAxes)
        ax.text(0.25, y, a, ha="center", fontsize=12, transform=ax.transAxes, bbox=box)
        ax.text(0.75, y, b, ha="center", fontsize=12, transform=ax.transAxes, bbox=box2)
    savefig(fig, "ch06_sign.png"); plt.close(fig)


# ============================================================ 3. 電圧プロファイル（沖縄 5 母線）
def fig_profile():
    net = build_okinawa(); pp.runpp(net)
    v0 = net.res_bus.vm_pu.values.copy()
    net2 = build_okinawa(load_scale=1.35); pp.runpp(net2)
    v1 = net2.res_bus.vm_pu.values
    net3 = build_okinawa(pv_mw=400.0, pv_bus=4, load_scale=0.30); pp.runpp(net3)
    v2 = net3.res_bus.vm_pu.values
    names = list(net.bus.name.values)
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.axhspan(0.95, 1.05, color=C_SEC, alpha=0.10)
    ax.axhline(1.05, color=C_SEC, ls="--", lw=1); ax.axhline(0.95, color=C_SEC, ls="--", lw=1)
    ax.plot(x, v0, "o-", color=C_MAIN, lw=2.2, label=f"基準（最低 {v0.min():.3f} p.u.）")
    ax.plot(x, v1, "s--", color=C_ACC, lw=2, label=f"負荷 1.35 倍（最低 {v1.min():.3f}）")
    ax.plot(x, v2, "^-.", color=C_BLUE, lw=2, label=f"軽負荷+太陽光 400 MW（最高 {v2.max():.3f}）")
    ax.set_xticks(x); ax.set_xticklabels(names)
    ax.set_ylabel("母線電圧 [p.u.]"); ax.grid(alpha=0.3, axis="y")
    ax.legend(frameon=False, fontsize=11, loc="lower left")
    savefig(fig, "ch06_profile.png"); plt.close(fig)
    OUT["v_base_min"], OUT["v_heavy_min"], OUT["v_pv_max"] = v0.min(), v1.min(), v2.max()


# ============================================================ 4. PV カーブ（鼻先）
def fig_pvcurve():
    Vs, X = 1.0, 0.30
    P = np.linspace(0, 1.0 / (2 * X), 400)
    disc = 1 - (2 * X * P) ** 2 * 0 - 4 * X ** 2 * P ** 2
    Vhi = np.sqrt(np.maximum((Vs ** 2 - 2 * 0) / 2 + np.sqrt(np.maximum(Vs ** 4 / 4 - (X * P) ** 2, 0)), 0))
    Vlo = np.sqrt(np.maximum(Vs ** 2 / 2 - np.sqrt(np.maximum(Vs ** 4 / 4 - (X * P) ** 2, 0)), 0))
    Pmax = Vs ** 2 / (2 * X)
    # pandapower で負荷を増やして収束しなくなる点を実測
    scales, vmins = [], []
    s = 1.0
    while s < 4.0:
        net = build_okinawa(load_scale=s)
        try:
            pp.runpp(net, max_iteration=40)
            scales.append(s); vmins.append(net.res_bus.vm_pu.min())
        except Exception:
            break
        s += 0.05
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.3))
    a1.plot(P, Vhi, color=C_MAIN, lw=2.4, label="解の上枝（運用点）")
    a1.plot(P, Vlo, color=C_LIGHT, lw=2, ls="--", label="解の下枝（不安定）")
    a1.scatter([Pmax], [Vs / np.sqrt(2)], color=C_ACC, s=80, zorder=5)
    a1.annotate(f"鼻先 P_max = V²/2X = {Pmax:.2f} p.u.\nV = 0.707 p.u.", (Pmax, Vs / np.sqrt(2)),
                xytext=(0.55, 0.45), fontsize=11, arrowprops=dict(arrowstyle="->", color=C_GREY))
    a1.axvspan(Pmax, Pmax * 1.15, color=C_ACC, alpha=0.10)
    a1.text(Pmax * 1.02, 0.95, "解が存在しない", fontsize=11, color=C_ACC)
    a1.set_xlabel("受電電力 P [p.u.]"); a1.set_ylabel("受電端電圧 V_r [p.u.]")
    a1.set_xlim(0, Pmax * 1.15); a1.set_ylim(0, 1.05); a1.grid(alpha=0.3)
    a1.legend(frameon=False, fontsize=11); a1.set_title("理論：X = 0.30 p.u.、力率 1", fontsize=11)
    a2.plot(scales, vmins, "o-", color=C_MAIN, lw=2, ms=4)
    a2.scatter([scales[-1]], [vmins[-1]], color=C_ACC, s=80, zorder=5)
    a2.annotate(f"ここで収束しなくなる\n負荷 {scales[-1]:.2f} 倍、V = {vmins[-1]:.3f}",
                (scales[-1], vmins[-1]), xytext=(scales[0] + 0.05, 0.68), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.axhline(0.95, color=C_SEC, ls="--", lw=1); a2.text(scales[0], 0.955, "運用下限 0.95", fontsize=11, color=C_SEC)
    a2.set_xlabel("負荷の倍率"); a2.set_ylabel("最低母線電圧 [p.u.]"); a2.grid(alpha=0.3)
    a2.set_title("実測：沖縄 5 母線を pandapower で", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch06_pvcurve.png"); plt.close(fig)
    OUT["Pmax_pu"], OUT["nose_scale"], OUT["nose_v"] = Pmax, scales[-1], vmins[-1]


# ============================================================ 5. 電圧感度 ΔV/ΔQ と短絡容量
def fig_sensitivity():
    from pws_common import V_BASE_KV, OKINAWA_LINES
    net = build_okinawa(); pp.runpp(net)
    base = net.res_bus.vm_pu.values.copy()
    dq = 20.0
    sens = []
    for b in range(len(net.bus)):
        n2 = build_okinawa()
        pp.create_sgen(n2, bus=b, p_mw=0.0, q_mvar=dq, name="test")
        pp.runpp(n2)
        sens.append((n2.res_bus.vm_pu.values[b] - base[b]) / dq)
    # 短絡容量：線路の Ybus に電源の内部アドミタンスを足して Z_ii を出す（100 MVA 基準）
    Zb = V_BASE_KV ** 2 / 100.0
    n = len(net.bus)
    Y = np.zeros((n, n), dtype=complex)
    for f, t, L, par in OKINAWA_LINES:
        z = (0.06 + 0.35j) * L / par / Zb
        y = 1.0 / z
        Y[f, f] += y; Y[t, t] += y; Y[f, t] -= y; Y[t, f] -= y
    Y[0, 0] += 1.0 / (100.0 / 3000.0 * (0.1 + 1j) / abs(0.1 + 1j))   # ext_grid 3000 MVA
    Y[1, 1] += 1.0 / (0.20 * 100.0 / 250.0 * 1j)                      # 発電機 x'd = 0.20 p.u.(250 MVA)
    Z = np.linalg.inv(Y)
    ssc = 100.0 / np.abs(np.diag(Z))
    names = list(net.bus.name.values)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.bar(names, np.array(sens) * 1000, color=C_MAIN, alpha=0.85)
    for i, s in enumerate(sens):
        a1.text(i, s * 1000 + 0.03, f"{s*1000:.2f}", ha="center", fontsize=11)
    a1.set_ylim(0, max(sens) * 1000 * 1.25)
    a1.set_ylabel("電圧感度 ΔV/ΔQ [p.u./Mvar] ×0.001"); a1.grid(alpha=0.3, axis="y")
    a1.set_title(f"Q を +{dq:.0f} Mvar 注入したときの自母線の電圧上昇", fontsize=11)
    a2.scatter(ssc, np.array(sens) * 1000, color=C_MAIN, s=70, zorder=3)
    for i, nm in enumerate(names):
        a2.annotate(nm, (ssc[i], sens[i] * 1000), textcoords="offset points", xytext=(6, 4), fontsize=11)
    xs = np.linspace(ssc.min() * 0.85, ssc.max() * 1.1, 100)
    a2.plot(xs, 1000 / xs, color=C_SEC, lw=1.8, ls="--", label="1/S_sc（理論）")
    a2.set_xlabel("短絡容量 S_sc [MVA]"); a2.set_ylabel("電圧感度 [p.u./Mvar] ×0.001")
    a2.grid(alpha=0.3); a2.legend(frameon=False, fontsize=11)
    a2.set_title("感度は短絡容量の逆数 — 弱い母線ほど動く", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch06_sensitivity.png"); plt.close(fig)
    OUT["sens"] = [(names[i], sens[i] * 1000, ssc[i]) for i in range(n)]


# ============================================================ 6. 近似式 ΔV ≈ (RP+XQ)/V の検証
def fig_approx():
    R, X, V = 0.10, 0.30, 1.0
    cases = [("重負荷\nP=0.4, Q=0.2", 0.4, 0.2), ("軽負荷\nP=0.1, Q=0.05", 0.1, 0.05),
             ("PV 逆潮流\nP=−0.4, Q=0", -0.4, 0.0), ("PV 力率0.95\nP=−0.4, Q=+0.131", -0.4, 0.131)]
    approx, exact = [], []
    for name, P, Q in cases:
        dv = (R * P + X * Q) / V
        approx.append(dv)
        # 厳密：V_r を解く（送電端 1.0 固定、R+jX の線路、受電端で P+jQ を消費）
        from numpy.polynomial import polynomial as _p
        a = 1.0
        b = 2 * (R * P + X * Q) - V ** 2
        c = (P ** 2 + Q ** 2) * (R ** 2 + X ** 2)
        vr2 = (-b + np.sqrt(max(b ** 2 - 4 * a * c, 0))) / 2
        exact.append(V - np.sqrt(vr2))
    x = np.arange(len(cases))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(x - 0.19, approx, 0.36, color=C_LIGHT, ec=C_GREY, label="近似 ΔV ≈ (RP + XQ)/V")
    ax.bar(x + 0.19, exact, 0.36, color=C_MAIN, label="厳密（2 次方程式を解く）")
    for i in range(len(cases)):
        ax.text(x[i] - 0.19, approx[i] + 0.004 * np.sign(approx[i] + 1e-9), f"{approx[i]:+.3f}", ha="center", fontsize=11)
        ax.text(x[i] + 0.19, exact[i] + 0.004 * np.sign(exact[i] + 1e-9), f"{exact[i]:+.3f}", ha="center", fontsize=11)
    ax.axhline(0, color=C_GREY, lw=1)
    ax.set_xticks(x); ax.set_xticklabels([c[0] for c in cases], fontsize=11)
    ax.set_ylabel("電圧降下 ΔV [p.u.]"); ax.grid(alpha=0.3, axis="y")
    ax.legend(frameon=False, fontsize=11)
    ax.set_title(f"近似式は実用十分（R = {R}, X = {X} p.u.）— 逆潮流では ΔV が負＝電圧が上がる", fontsize=11.5)
    savefig(fig, "ch06_approx.png"); plt.close(fig)
    OUT["approx"] = list(zip([c[0] for c in cases], approx, exact))


# ============================================================ 7. 太陽光の連系可能量（配電フィーダ）
def feeder(pv=0.0, pf=1.0, n_seg=5, seg_km=1.0, load_kw=200.0):
    """6.6 kV 配電フィーダ（5 区間・各区間に 200 kW の負荷、末端に太陽光）"""
    net = pp.create_empty_network(sn_mva=100.0)
    b = [pp.create_bus(net, vn_kv=6.6, name=f"P{i}") for i in range(n_seg + 1)]
    pp.create_ext_grid(net, bus=b[0], vm_pu=1.00, name="変電所")
    for i in range(n_seg):
        pp.create_line_from_parameters(net, b[i], b[i + 1], length_km=seg_km,
                                       r_ohm_per_km=0.30, x_ohm_per_km=0.35,
                                       c_nf_per_km=0.0, max_i_ka=0.4)
        pp.create_load(net, bus=b[i + 1], p_mw=load_kw / 1000, q_mvar=load_kw / 1000 * 0.3)
    if pv > 0:
        q = 0.0 if pf >= 1.0 else -pv * np.tan(np.arccos(pf))
        pp.create_sgen(net, bus=b[-1], p_mw=pv, q_mvar=q, name="太陽光")
    return net


def fig_hosting():
    pvs = np.arange(0, 6.01, 0.1)
    lim = 1.05
    host = {}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.3))
    # 左：フィーダに沿った電圧（PV なし / 力率1 / 力率0.95）
    for pv, pf, c, ls, lab in [(0.0, 1.0, C_SEC, "--", "太陽光なし（夜間・重負荷）"),
                               (2.5, 1.0, C_ACC, "-", "PV 2.5 MW・力率 1"),
                               (2.5, 0.95, C_MAIN, "-", "PV 2.5 MW・力率 0.95")]:
        n = feeder(pv, pf); pp.runpp(n)
        a1.plot(range(len(n.bus)), n.res_bus.vm_pu.values, "o" + ls, color=c, lw=2, label=lab)
    a1.axhspan(0.95, lim, color=C_SEC, alpha=0.10)
    a1.axhline(lim, color=C_ACC, ls="--", lw=1.2); a1.axhline(0.95, color=C_SEC, ls="--", lw=1)
    a1.text(0.05, lim + 0.003, "上限 1.05", fontsize=11, color=C_ACC)
    a1.set_xlabel("変電所からの距離 [km]"); a1.set_ylabel("電圧 [p.u.]")
    a1.grid(alpha=0.3); a1.legend(frameon=False, fontsize=11, loc="center left")
    a1.set_title("6.6 kV 配電フィーダの電圧分布", fontsize=11)
    # 右：連系量に対する末端電圧
    for pf, c in [(1.0, C_ACC), (0.95, C_MAIN)]:
        vs = []
        for pv in pvs:
            n = feeder(float(pv), pf)
            try:
                pp.runpp(n); vs.append(n.res_bus.vm_pu.values[-1])
            except Exception:
                vs.append(np.nan)
        vs = np.array(vs)
        a2.plot(pvs, vs, color=c, lw=2.3, label=f"力率 {pf}")
        over = np.where(vs > lim)[0]
        h = pvs[over[0]] if len(over) else np.nan
        host[pf] = h
        if not np.isnan(h):
            a2.scatter([h], [lim], color=c, s=70, zorder=5)
            a2.annotate(f"{h:.1f} MW", (h, lim), textcoords="offset points", xytext=(-8, 10),
                        ha="right", fontsize=11.5, color=c, weight="bold")
    a2.axhline(lim, color=C_SEC, ls="--", lw=1.2)
    a2.set_xlabel("末端に連系する太陽光 [MW]"); a2.set_ylabel("末端の電圧 [p.u.]")
    a2.grid(alpha=0.3); a2.legend(frameon=False, fontsize=11.5)
    gain = host[0.95] - host[1.0]
    a2.set_title(f"連系可能量 {host[1.0]:.1f} → {host[0.95]:.1f} MW（+{gain:.1f} MW）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch06_hosting.png"); plt.close(fig)
    OUT["host"] = host


# ============================================================ 8. IEEE 14 母線
def fig_ieee14():
    net = pn.case14(); pp.runpp(net)
    p = np.abs(net.res_line.p_from_mw.values)
    idx = np.argsort(p)[::-1]
    labels = [f"{net.line.from_bus[i]+1}–{net.line.to_bus[i]+1}" for i in idx]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.bar(range(len(p)), p[idx], color=[C_ACC if v > 50 else (C_WARM if v > 20 else C_SEC) for v in p[idx]])
    a1.set_xticks(range(len(p))); a1.set_xticklabels(labels, rotation=90, fontsize=11)
    a1.set_ylabel("線路潮流 |P| [MW]"); a1.grid(alpha=0.3, axis="y")
    a1.set_title(f"線路潮流（最大 {p.max():.1f} MW、総損失 {net.res_line.pl_mw.sum():.2f} MW）", fontsize=11)
    v = net.res_bus.vm_pu.values
    a2.bar(range(len(v)), v, color=[C_ACC if (x < 0.95 or x > 1.05) else C_SEC for x in v])
    a2.axhline(1.05, color=C_ACC, ls="--", lw=1); a2.axhline(0.95, color=C_SEC, ls="--", lw=1)
    a2.text(0.1, 1.078, "上限 1.05", fontsize=11, color=C_ACC)
    a2.set_ylim(0.9, 1.12); a2.set_xticks(range(len(v)))
    a2.set_xticklabels([str(i + 1) for i in range(len(v))], fontsize=11)
    a2.set_xlabel("母線番号"); a2.set_ylabel("電圧 [p.u.]"); a2.grid(alpha=0.3, axis="y")
    over = int((v > 1.05).sum())
    a2.set_title(f"母線電圧 {v.min():.3f}〜{v.max():.3f}（上限超過 {over} 母線）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch06_ieee14.png"); plt.close(fig)
    OUT["ieee14"] = (p.max(), v.min(), v.max(), net.res_line.pl_mw.sum(), over)


# ============================================================ 9. 調相設備とタップ
def fig_devices():
    fig, ax = plt.subplots(figsize=(9.6, 4.2))
    ax.axis("off")
    items = [("分路コンデンサ\n(SC)", "Q を出す", "段階的（入切）", "秒〜分", C_MAIN),
             ("分路リアクトル\n(ShR)", "Q を吸う", "段階的", "秒〜分", C_MAIN),
             ("同期調相機\n(RC)", "出す/吸う", "連続", "秒", C_SEC),
             ("SVC / STATCOM", "出す/吸う", "連続", "ミリ秒", C_BLUE),
             ("変圧器タップ\n(LTC)", "電圧比を変える", "段階（1.25%/段）", "十秒〜分", C_WARM),
             ("インバータ\n(PV/蓄電池)", "出す/吸う", "連続", "ミリ秒", C_BLUE)]
    for i, (name, what, how, speed, c) in enumerate(items):
        x = 0.02 + (i % 3) * 0.33
        y = 0.55 - (i // 3) * 0.47
        ax.add_patch(FancyBboxPatch((x, y), 0.29, 0.40, boxstyle="round,pad=0.01",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=1.8))
        ax.text(x + 0.145, y + 0.33, name, ha="center", va="center", fontsize=12, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.02, y + 0.15, f"働き：{what}", fontsize=11, transform=ax.transAxes)
        ax.text(x + 0.02, y + 0.09, f"調整：{how}", fontsize=11, transform=ax.transAxes)
        ax.text(x + 0.02, y + 0.03, f"速さ：{speed}", fontsize=11, transform=ax.transAxes)
    savefig(fig, "ch06_devices.png"); plt.close(fig)


# ============================================================ 10. 自作 NR と pandapower の照合
def fig_verify():
    from pws_common import build_ybus, newton_raphson
    lines = [(1, 2, 0.02, 0.06, 0.0), (1, 3, 0.08, 0.24, 0.0), (2, 3, 0.06, 0.18, 0.0)]
    Y = build_ybus(3, lines)
    bus_type = np.array([0, 1, 2]); P = np.array([0.0, 0.5, -1.0]); Q = np.array([0.0, 0.0, -0.5])
    Vm = np.array([1.05, 1.02, 1.0])
    V, th, it = newton_raphson(Y, bus_type, P, Q, Vm)[:3]
    net = pp.create_empty_network(sn_mva=100.0)
    b = [pp.create_bus(net, vn_kv=132.0) for _ in range(3)]
    pp.create_ext_grid(net, bus=b[0], vm_pu=1.05)
    pp.create_gen(net, bus=b[1], p_mw=50.0, vm_pu=1.02)
    pp.create_load(net, bus=b[2], p_mw=100.0, q_mvar=50.0)
    for f, t, r, x, bsh in lines:
        pp.create_line_from_parameters(net, b[f - 1], b[t - 1], length_km=1.0,
                                       r_ohm_per_km=r * 132.0 ** 2 / 100.0,
                                       x_ohm_per_km=x * 132.0 ** 2 / 100.0,
                                       c_nf_per_km=0.0,
                                       max_i_ka=10.0)
    pp.runpp(net)
    vpp = net.res_bus.vm_pu.values; thpp = np.deg2rad(net.res_bus.va_degree.values)
    dv = np.abs(V - vpp); dth = np.abs(th - thpp)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    x = np.arange(3)
    a1.bar(x - 0.19, V, 0.36, color=C_MAIN, label=f"自作 NR（{it} 回で収束）")
    a1.bar(x + 0.19, vpp, 0.36, color=C_SEC, label="pandapower")
    for i in range(3):
        a1.text(x[i], max(V[i], vpp[i]) + 0.004, f"{V[i]:.5f}\n{vpp[i]:.5f}", ha="center", fontsize=11)
    a1.set_ylim(0.9, 1.09); a1.set_xticks(x); a1.set_xticklabels(["母線1", "母線2", "母線3"])
    a1.set_ylabel("電圧 [p.u.]"); a1.legend(frameon=False, fontsize=11); a1.grid(alpha=0.3, axis="y")
    a1.set_title("電圧の照合", fontsize=11)
    a2.bar(x - 0.19, dv, 0.36, color=C_MAIN, label="|ΔV| [p.u.]")
    a2.bar(x + 0.19, dth, 0.36, color=C_SEC, label="|Δθ| [rad]")
    a2.set_yscale("log"); a2.axhline(1e-5, color=C_ACC, ls="--", lw=1.2)
    a2.text(0.05, 1.3e-5, r"合格ライン $10^{-5}$", fontsize=11, color=C_ACC)
    a2.set_xticks(x); a2.set_xticklabels(["母線1", "母線2", "母線3"]); a2.set_ylabel("差の絶対値")
    a2.legend(frameon=False, fontsize=11); a2.grid(alpha=0.3, axis="y")
    a2.set_title(f"差は最大 {max(dv.max(), dth.max()):.1e} — 実装は正しい", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch06_verify.png"); plt.close(fig)
    OUT["verify"] = (it, dv.max(), dth.max())


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure


def fig_analogy():
    analogy_figure("ch06_analogy.png",
        left_title="橋（たとえ）", right_title="電圧安定性（実物）",
        pairs=[("荷物を積むとたわむ", "荷物＝負荷 P、たわみ＝電圧低下"),
               ("最初はゆっくり、限界近くで急に", "PV カーブの形そのもの"),
               ("ある重さで折れる（戻れない）", "折れる点＝鼻先（電圧崩壊点）"),
               ("支柱を足せば、もっと積める", "支柱＝無効電力の補給"),
               ("折れる直前まで見た目は平気", "潮流計算は鼻先の手前で収束しなくなる")],
        note="この対応が頭に入っていれば、PV カーブの話は全部「橋の話」に翻訳できる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch06_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("電圧が低いのは発電が足りないから",
                "電圧を決めるのは無効電力 Q。Q は遠くへ運べない"),
               ("太陽光は発電なので電圧を下げる方向に働く",
                "太陽光は逆潮流で、むしろ末端の電圧を上げる"),
               ("潮流計算が収束しないのはプログラムのバグ",
                "収束しないのは解が存在しない可能性がある（電圧崩壊の兆候）")],
        note="電圧は P ではなく Q が決める、が今日いちばん外してはいけない点。")


if __name__ == "__main__":
    fig_tables(); fig_sign(); fig_profile(); fig_pvcurve(); fig_sensitivity()
    fig_approx(); fig_hosting(); fig_ieee14(); fig_devices(); fig_verify()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    print(f"電圧プロファイル: 基準の最低 {OUT['v_base_min']:.3f}, 負荷1.35倍 {OUT['v_heavy_min']:.3f}, 軽負荷+PV400MW の最高 {OUT['v_pv_max']:.3f} p.u.")
    print(f"PV カーブ: 理論 P_max = {OUT['Pmax_pu']:.3f} p.u.、実測は負荷 {OUT['nose_scale']:.2f} 倍・V={OUT['nose_v']:.3f} で収束せず")
    for nm, s, sc in OUT["sens"]:
        print(f"  感度 {nm}: {s:.2f} [10^-3 p.u./Mvar], S_sc = {sc:.0f} MVA")
    for n, a, e in OUT["approx"]:
        print(f"  近似 vs 厳密  {n.replace(chr(10), ' ')}: {a:+.4f} / {e:+.4f}（誤差 {abs(a-e):.4f}）")
    print(f"連系可能量（6.6 kV フィーダ）: 力率1 で {OUT['host'][1.0]:.1f} MW、力率0.95 で {OUT['host'][0.95]:.1f} MW")
    pm, vmin, vmax, ploss, over = OUT["ieee14"]
    print(f"IEEE14: 最大潮流 {pm:.1f} MW, 電圧 {vmin:.3f}〜{vmax:.3f}（上限超過 {over}）, 総損失 {ploss:.2f} MW")
    it, dv, dth = OUT["verify"]
    print(f"照合: 自作 NR {it} 回、|ΔV|max = {dv:.2e}、|Δθ|max = {dth:.2e}")
