# -*- coding: utf-8 -*-
"""第9回 インバータと系統連系 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch09.py  → ../図/ch09_*.png
   PWM は搬送波と変調波の比較で実際に波形を作り、DFT でスペクトルと THD を出す。
   合成慣性の効果は第8回と同じ周波数応答モデル（RK4）に仮想慣性の項を足して比べる。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}
F1, VDC = 60.0, 600.0


def pwm(m, mf, n=200000, cycles=1):
    """正弦波 PWM の相電圧（中性点基準、±Vdc/2）を作る"""
    t = np.linspace(0, cycles / F1, n, endpoint=False)
    ref = m * np.sin(2 * np.pi * F1 * t)
    fc = mf * F1
    carrier = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * fc * t))   # 三角波（±1）
    v = np.where(ref > carrier, VDC / 2, -VDC / 2)
    return t, ref, carrier, v


def harmonics(v, t, hmax=60):
    """1 周期の波形から高調波振幅（相電圧）を DFT で取り出す"""
    n = len(v)
    V = np.fft.rfft(v) / n * 2
    freqs = np.fft.rfftfreq(n, t[1] - t[0])
    amp = np.abs(V)
    idx = [int(round(h * F1 / (freqs[1]))) for h in range(1, hmax + 1)]
    return np.array([amp[i] if i < len(amp) else 0.0 for i in idx])


def thd(amps):
    return np.sqrt(np.sum(amps[1:] ** 2)) / amps[0] * 100


# ============================================================ 1. PWM の作り方
def fig_pwm():
    t, ref, car, v = pwm(0.9, 21)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.4, 5.0), sharex=True,
                                 gridspec_kw={"height_ratios": [1, 1]})
    ms = t * 1000
    a1.plot(ms, car, color=C_LIGHT, lw=1.2, label="搬送波（三角波 1,260 Hz）")
    a1.plot(ms, ref, color=C_MAIN, lw=2.2, label="変調波（正弦波 60 Hz、m = 0.9）")
    a1.fill_between(ms, -1.05, 1.05, where=ref > car, color=C_ACC, alpha=0.10)
    a1.set_ylabel("振幅（規格化）"); a1.set_ylim(-1.15, 1.65); a1.grid(alpha=0.3)
    a1.legend(fontsize=11, frameon=False, ncol=2, loc="upper center")
    a1.set_title("正弦波 PWM：変調波が搬送波より上なら ON、下なら OFF", fontsize=12)
    a2.plot(ms, v, color=C_ACC, lw=1.2, label="インバータの出力（±Vdc/2 の矩形）")
    a2.plot(ms, 0.9 * VDC / 2 * np.sin(2 * np.pi * F1 * t), color=C_MAIN, lw=2.4,
            label=f"基本波 m·Vdc/2 = {0.9*VDC/2:.0f} V")
    a2.set_xlabel("時間 [ms]"); a2.set_ylabel("相電圧 [V]"); a2.grid(alpha=0.3)
    a2.legend(fontsize=11, frameon=False, loc="upper right"); a2.set_ylim(-430, 500)
    fig.tight_layout(); savefig(fig, "ch09_pwm.png"); plt.close(fig)


# ============================================================ 2. スペクトルと THD
def fig_spectrum():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.2), sharey=True)
    res = {}
    for ax, mf, c in [(a1, 21, C_MAIN), (a2, 99, C_SEC)]:
        t, _, _, v = pwm(0.9, mf, n=400000)
        amp = harmonics(v, t, hmax=140)
        h = np.arange(1, len(amp) + 1)
        rel = amp / amp[0] * 100
        ax.bar(h, rel, color=[C_ACC if k == 0 else c for k in range(len(h))], width=0.8)
        res[mf] = (thd(amp), amp[0])
        ax.axvline(mf, color=C_WARM, ls="--", lw=1.2)
        ax.text(mf + 2, 60, f"m_f = {mf}\n付近に山", fontsize=11, color=C_WARM)
        ax.set_xlabel("高調波次数"); ax.set_xlim(0, 140); ax.grid(alpha=0.3, axis="y")
        ax.set_title(f"m_f = {mf}（f_sw = {mf*60:,.0f} Hz）  THD = {res[mf][0]:.1f}%", fontsize=11)
    a1.set_ylabel("基本波に対する振幅 [%]"); a1.set_ylim(0, 110)
    fig.tight_layout(); savefig(fig, "ch09_spectrum.png"); plt.close(fig)
    OUT["thd"] = {k: v[0] for k, v in res.items()}
    OUT["v1"] = res[21][1]


# ============================================================ 3. 変調率と出力電圧
def fig_modulation():
    ms = np.linspace(0.1, 1.4, 60)
    v1, v1_theory = [], []
    for m in ms:
        t, _, _, v = pwm(m, 45, n=180000)
        amp = harmonics(v, t, hmax=3)
        v1.append(amp[0])
        v1_theory.append(min(m, 1.0) * VDC / 2)
    v1 = np.array(v1)
    vll = v1 / np.sqrt(2) * np.sqrt(3)
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.plot(ms, v1, "o-", color=C_MAIN, ms=3, lw=2, label="実測（DFT の基本波振幅）")
    ax.plot(ms[ms <= 1.0], np.array(v1_theory)[ms <= 1.0], "--", color=C_SEC, lw=2, label="理論 m·Vdc/2（線形領域）")
    ax.axvline(1.0, color=C_ACC, lw=1.4, ls=":")
    ax.axvspan(1.0, 1.4, color=C_ACC, alpha=0.08)
    ax.text(1.02, 130, "過変調領域\n（低次高調波が出る）", fontsize=11, color=C_ACC)
    m09 = np.argmin(np.abs(ms - 0.9))
    ax.scatter([ms[m09]], [v1[m09]], color=C_ACC, s=70, zorder=5)
    ax.annotate(f"m = 0.9 → {v1[m09]:.0f} V（相・振幅）\n線間実効値 {vll[m09]:.0f} V",
                (ms[m09], v1[m09]), xytext=(0.15, 300), fontsize=11,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    ax.set_xlabel("変調率 m"); ax.set_ylabel("基本波の相電圧振幅 [V]")
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="lower right")
    ax.set_ylim(0, 380)
    ax.set_title(f"変調率と出力電圧（Vdc = {VDC:.0f} V）— m が 1 以下なら比例", fontsize=11.5)
    savefig(fig, "ch09_modulation.png"); plt.close(fig)
    OUT["v1_09"], OUT["vll_09"] = v1[m09], vll[m09]


# ============================================================ 4. dq 変換
def fig_dq():
    t = np.linspace(0, 2 / F1, 1000)
    w = 2 * np.pi * F1
    ia = np.cos(w * t - 0.3); ib = np.cos(w * t - 0.3 - 2 * np.pi / 3); ic = np.cos(w * t - 0.3 + 2 * np.pi / 3)
    theta = w * t
    d = 2 / 3 * (ia * np.cos(theta) + ib * np.cos(theta - 2 * np.pi / 3) + ic * np.cos(theta + 2 * np.pi / 3))
    q = -2 / 3 * (ia * np.sin(theta) + ib * np.sin(theta - 2 * np.pi / 3) + ic * np.sin(theta + 2 * np.pi / 3))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.0))
    a1.plot(t * 1000, ia, color=C_MAIN, lw=2, label="a 相")
    a1.plot(t * 1000, ib, color=C_SEC, lw=2, label="b 相")
    a1.plot(t * 1000, ic, color=C_WARM, lw=2, label="c 相")
    a1.set_xlabel("時間 [ms]"); a1.set_ylabel("電流 [p.u.]"); a1.grid(alpha=0.3)
    a1.legend(fontsize=11, frameon=False, ncol=3, loc="upper center"); a1.set_ylim(-1.5, 1.9)
    a1.set_title("三相の交流量（時間で変わる）", fontsize=11)
    a2.plot(t * 1000, d, color=C_MAIN, lw=2.4, label=f"d 軸（有効分）→ 一定 {d[-1]:.3f}")
    a2.plot(t * 1000, q, color=C_ACC, lw=2.4, label=f"q 軸（無効分）→ 一定 {q[-1]:.3f}")
    a2.set_xlabel("時間 [ms]"); a2.set_ylabel("dq 電流 [p.u.]"); a2.grid(alpha=0.3)
    a2.legend(fontsize=11, frameon=False); a2.set_ylim(-1.0, 1.3)
    a2.set_title("回転座標に乗せると直流量になる → PI 制御が使える", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch09_dq.png"); plt.close(fig)


# ============================================================ 5. フォロイング vs フォーミング
def fig_gfl_gfm():
    fig, ax = plt.subplots(figsize=(9.6, 4.0))
    ax.axis("off")
    for x, title, sub, items, c in [
        (0.03, "グリッドフォロイング（GFL）", "電流源として振る舞う",
         ["PLL で系統電圧の位相に追従", "指令どおりの電流を流す", "系統が無いと動けない",
          "慣性なし・現在の主流", "系統が弱いと不安定"], C_SEC),
        (0.52, "グリッドフォーミング（GFM）", "電圧源として振る舞う",
         ["自分で周波数と電圧を作る", "ドループで複数台が分担", "系統が無くても立ち上がる",
          "慣性を模擬できる", "ブラックスタートが可能"], C_MAIN)]:
        ax.add_patch(FancyBboxPatch((x, 0.06), 0.45, 0.80, boxstyle="round,pad=0.015",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=2))
        ax.text(x + 0.225, 0.78, title, ha="center", fontsize=12.5, weight="bold", color=c, transform=ax.transAxes)
        ax.text(x + 0.225, 0.70, sub, ha="center", fontsize=12, color=C_GREY, transform=ax.transAxes)
        for i, it in enumerate(items):
            ax.text(x + 0.03, 0.60 - i * 0.105, "・" + it, fontsize=12, transform=ax.transAxes)
    ax.set_title("インバータの 2 つの性格 — 「合わせ手」か「指揮者」か", fontsize=12.5)
    savefig(fig, "ch09_gfl_gfm.png"); plt.close(fig)


# ============================================================ 6. Volt-Var 制御
def fig_voltvar():
    v = np.linspace(0.92, 1.08, 400)
    q = np.piecewise(v, [v < 0.96, (v >= 0.96) & (v < 0.99), (v >= 0.99) & (v <= 1.01),
                         (v > 1.01) & (v <= 1.04), v > 1.04],
                     [0.33, lambda x: 0.33 * (0.99 - x) / 0.03, 0.0,
                      lambda x: -0.33 * (x - 1.01) / 0.03, -0.33])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.plot(v, q, color=C_MAIN, lw=2.6)
    a1.axhline(0, color=C_LIGHT, lw=1); a1.axvspan(0.99, 1.01, color=C_SEC, alpha=0.12)
    a1.text(1.0, 0.26, "不感帯", ha="center", fontsize=11.5, color=C_SEC)
    a1.text(0.925, 0.40, "Q を出す（電圧を上げる）", fontsize=11, color=C_WARM)
    a1.text(1.075, -0.40, "Q を吸う（電圧を下げる）", fontsize=11, color=C_ACC, ha="right")
    a1.set_xlabel("連系点の電圧 [p.u.]"); a1.set_ylabel("無効電力 Q [p.u.]（発電を正）")
    a1.grid(alpha=0.3); a1.set_ylim(-0.45, 0.45)
    a1.set_title("Volt-Var 特性（力率 0.95 相当の折れ線）", fontsize=11)
    # 効果：第6回と同じ 6.6 kV 配電フィーダを pandapower で解く
    import pandapower as pp
    def feeder(pv, pf):
        net = pp.create_empty_network(sn_mva=100.0)
        b = [pp.create_bus(net, vn_kv=6.6) for _ in range(6)]
        pp.create_ext_grid(net, bus=b[0], vm_pu=1.00)
        for i in range(5):
            pp.create_line_from_parameters(net, b[i], b[i + 1], length_km=1.0, r_ohm_per_km=0.30,
                                           x_ohm_per_km=0.35, c_nf_per_km=0.0, max_i_ka=0.4)
            pp.create_load(net, bus=b[i + 1], p_mw=0.2, q_mvar=0.06)
        if pv > 0:
            q = 0.0 if pf >= 1 else -pv * np.tan(np.arccos(pf))
            pp.create_sgen(net, bus=b[-1], p_mw=pv, q_mvar=q)
        pp.runpp(net)
        return net.res_bus.vm_pu.values[-1]
    pv = np.linspace(0, 6.0, 61)
    host = {}
    for pf, c, lab in [(1.0, C_ACC, "力率 1"), (0.95, C_MAIN, "力率 0.95（Q 吸収）")]:
        vs = np.array([feeder(float(p), pf) for p in pv])
        a2.plot(pv, vs, color=c, lw=2.3, label=lab)
        over = np.where(vs > 1.05)[0]
        if len(over):
            h = pv[over[0]]; host[pf] = h
            a2.scatter([h], [1.05], color=c, s=60, zorder=5)
            a2.annotate(f"{h:.1f} MW", (h, 1.05), textcoords="offset points", xytext=(3, 7),
                        fontsize=11, color=c, weight="bold")
    OUT["host_vv"] = host
    a2.axhline(1.05, color=C_SEC, ls="--", lw=1.2)
    a2.text(0.05, 1.052, "上限 1.05", fontsize=11, color=C_SEC)
    a2.set_xlabel("末端に連系する太陽光 [MW]"); a2.set_ylabel("末端電圧 [p.u.]")
    a2.set_ylim(0.96, 1.14)
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("第6回の電圧問題への答え", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch09_voltvar.png"); plt.close(fig)


# ============================================================ 7. 合成慣性の効果
def response_vi(S=1500.0, H=2.0, dP=-250.0, pctK=1.0, Tg=8.0, Kl_share=0.3,
                Hv=0.0, tau_v=0.2, t_end=20.0, dt=0.005):
    """第8回の周波数応答に合成慣性（df/dt を測って出す・遅れ tau_v）を足す"""
    F0 = 60.0
    K = pctK * 10.0 / 100.0 * S
    Kl, Kg = K * Kl_share, K * (1 - Kl_share)
    n = int(t_end / dt)
    f, pg, pv, dfdt_meas = F0, 0.0, 0.0, 0.0
    ts, fs, pvs = [0.0], [F0], [0.0]
    for i in range(n):
        df = f - F0
        dfdt = F0 / (2 * H * S) * (dP + pg - Kl * df + pv)
        dfdt_meas += (dfdt - dfdt_meas) * dt / tau_v      # 測定の遅れ（一次遅れ）
        pv_target = -2 * Hv * S / F0 * dfdt_meas
        pv += (pv_target - pv) * dt / 0.05                # 出力の応答（速い）
        pg += (-Kg * df - pg) / Tg * dt
        f += dfdt * dt
        ts.append((i + 1) * dt); fs.append(f); pvs.append(pv)
    return np.array(ts), np.array(fs), np.array(pvs)


def fig_synthetic_inertia():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.8, 4.3))
    res = {}
    for Hv, c, lab in [(0.0, C_ACC, "合成慣性なし（H = 2.0 s）"),
                       (1.5, C_WARM, "合成慣性 H_v = 1.5 s"),
                       (3.0, C_MAIN, "合成慣性 H_v = 3.0 s")]:
        t, f, pv = response_vi(Hv=Hv)
        a1.plot(t, f, color=c, lw=2.3, label=f"{lab}  nadir {f.min():.2f} Hz")
        a2.plot(t, pv, color=c, lw=2.3, label=lab)
        res[Hv] = (f.min(), (f[1] - f[0]) / 0.005, pv.max())
    a1.axhline(59.0, color=C_SEC, ls="--", lw=1.2)
    a1.text(11, 59.03, "UFR 59.0 Hz", fontsize=11, color=C_SEC)
    a1.set_xlabel("時間 [s]"); a1.set_ylabel("周波数 [Hz]"); a1.set_xlim(0, 20); a1.set_ylim(57.0, 60.2)
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False, loc="lower right")
    a1.set_title("合成慣性で最低点が浅くなる", fontsize=11)
    a2.set_xlabel("時間 [s]"); a2.set_ylabel("合成慣性の出力 [MW]"); a2.set_xlim(0, 20)
    a2.grid(alpha=0.3); a2.legend(fontsize=11, frameon=False)
    a2.set_title("蓄えたエネルギーを数秒だけ吐き出す", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch09_synthetic_inertia.png"); plt.close(fig)
    OUT["vi"] = res


# ============================================================ 8. 合成慣性の遅れの影響
def fig_delay():
    fig, ax = plt.subplots(figsize=(8.8, 4.3))
    for tau, c, lab in [(0.05, C_MAIN, "遅れ 50 ms"), (0.2, C_WARM, "遅れ 200 ms"), (0.5, C_ACC, "遅れ 500 ms")]:
        t, f, _ = response_vi(Hv=3.0, tau_v=tau)
        ax.plot(t, f, color=c, lw=2.3, label=f"{lab}  nadir {f.min():.2f} Hz")
    t0, f0, _ = response_vi(Hv=0.0)
    ax.plot(t0, f0, color=C_LIGHT, lw=2, ls="--", label=f"合成慣性なし  nadir {f0.min():.2f} Hz")
    ax.set_xlabel("時間 [s]"); ax.set_ylabel("周波数 [Hz]"); ax.set_xlim(0, 12); ax.set_ylim(57.2, 60.15)
    ax.grid(alpha=0.3); ax.legend(fontsize=11, frameon=False, loc="lower right")
    ax.set_title("測ってから出すので遅れる — 遅いほど効果が薄れる（真の慣性との差）", fontsize=11.5)
    savefig(fig, "ch09_delay.png"); plt.close(fig)


# ============================================================ 9. 単独運転検出
def fig_islanding():
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.axis("off")
    ax.plot([0.06, 0.30], [0.62, 0.62], color="#1A1A17", lw=2.5, transform=ax.transAxes)
    ax.plot([0.06, 0.06], [0.45, 0.79], color="#1A1A17", lw=5, transform=ax.transAxes)
    ax.text(0.06, 0.86, "変電所", ha="center", fontsize=12, transform=ax.transAxes)
    ax.plot([0.30], [0.62], marker="x", ms=18, mew=3.5, color=C_ACC, transform=ax.transAxes)
    ax.text(0.30, 0.72, "遮断器が開く\n（上位系統から切り離される）", ha="center", fontsize=11.5, color=C_ACC, transform=ax.transAxes)
    ax.plot([0.34, 0.90], [0.62, 0.62], color="#1A1A17", lw=2.5, transform=ax.transAxes)
    for x, lab, c in [(0.50, "太陽光\n(PCS)", C_MAIN), (0.70, "負荷", C_WARM), (0.86, "作業員", C_ACC)]:
        ax.plot([x, x], [0.40, 0.62], color="#1A1A17", lw=2, transform=ax.transAxes)
        ax.add_patch(FancyBboxPatch((x - 0.055, 0.20), 0.11, 0.20, boxstyle="round,pad=0.008",
                                    transform=ax.transAxes, fc="#FBFAF6", ec=c, lw=1.8))
        ax.text(x, 0.30, lab, ha="center", va="center", fontsize=11.5, color=c, transform=ax.transAxes)
    ax.text(0.60, 0.08, "発電と消費がたまたま釣り合うと、切り離された後も送電が続く（単独運転）",
            ha="center", fontsize=11, color=C_MAIN, transform=ax.transAxes)
    ax.text(0.60, 0.90, "危険：①作業員の感電 ②電圧・周波数が外れて機器が壊れる ③再閉路で位相がずれたまま突き合わせる",
            ha="center", fontsize=11.5, color=C_ACC, transform=ax.transAxes)
    ax.set_title("単独運転検出はなぜ必須か", fontsize=12)
    savefig(fig, "ch09_islanding.png"); plt.close(fig)


# ============================================================ 10. LCL フィルタ
def fig_lcl():
    L1, L2, Cf = 1.5e-3, 0.6e-3, 15e-6
    f = np.logspace(1, 5, 2000)
    w = 2 * np.pi * f
    # インバータ電圧 → 系統側電流の伝達（簡略：無損失）
    num = 1.0
    den = w * (L1 + L2) * (1 - w ** 2 * (L1 * L2 / (L1 + L2)) * Cf)
    H = np.abs(num / den)
    fres = 1 / (2 * np.pi) * np.sqrt((L1 + L2) / (L1 * L2 * Cf))
    HL = 1 / (w * (L1 + L2))
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    ax.loglog(f, H, color=C_MAIN, lw=2.4, label="LCL フィルタ")
    ax.loglog(f, HL, color=C_LIGHT, lw=2, ls="--", label="L フィルタのみ（−20 dB/dec）")
    ax.axvline(fres, color=C_ACC, lw=1.5, ls=":")
    ax.text(fres * 1.7, 1e-2, f"共振 {fres/1000:.1f} kHz\n（制動が要る）", fontsize=11, color=C_ACC)
    ax.axvline(60, color=C_SEC, lw=1.2, ls=":"); ax.text(64, 1e-4, "基本波 60 Hz", fontsize=11, color=C_SEC)
    ax.axvline(21 * 60, color=C_WARM, lw=1.2, ls=":"); ax.text(21 * 60 * 1.08, 1e-4, "m_f = 21", fontsize=11, color=C_WARM)
    ax.set_xlabel("周波数 [Hz]"); ax.set_ylabel("電圧 → 電流のゲイン（相対）")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=11, frameon=False)
    ax.set_xlim(10, 1e5); ax.set_ylim(1e-6, 1e1)
    ax.set_title("LCL フィルタ：高い周波数を −60 dB/dec で落とす（L 単体より小型）", fontsize=11.5)
    savefig(fig, "ch09_lcl.png"); plt.close(fig)
    OUT["fres"] = fres


# ============================================================ 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch09_analogy.png",
        left_title="合唱（たとえ）", right_title="インバータ（実物）",
        pairs=[("合わせ手は周りの声を聞いて合わせて歌う", "グリッドフォロイング（GFL）：PLL で系統電圧の位相に追従する"),
               ("誰も歌っていないと合わせられない", "系統が無いと動けない。だから単独運転を検出して止める"),
               ("指揮者は自分でテンポと音程を決める", "グリッドフォーミング（GFM）：自分で周波数と電圧を作る"),
               ("指揮者が 2 人いると喧嘩する", "複数台の GFM はドループ制御で出力を分担する"),
               ("声量は大きいが体重はない", "合成慣性は速く応答するが、真の慣性 H は無い")],
        note="崩れる点：合唱は「合わせる」だけだが、インバータは電流の大きさと位相を数万分の 1 秒ごとに決めている。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch09_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("インバータは正弦波を「増幅」して出す",
                "矩形パルスの ON/OFF の幅を変え、その平均として正弦波を作っている"),
               ("合成慣性があれば同期発電機と同じ働きをする",
                "合成慣性は df/dt を測ってから出すので遅れ、続けるには蓄電などのエネルギー源が要る"),
               ("スイッチング周波数を上げれば高調波は消える",
                "高調波の総量は大きくは減らない。消えるのではなく、フィルタで落としやすい高い周波数へ移る")],
        note="どれも「回転体があるかのように振る舞わせている」という制御の正体を見落としたことから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch09_deriv_pwm_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 1 スイッチング周期の平均を見る',
                r"$\bar{v} \propto m\,\sin\omega t$",
                '三角波なら ON の時間の割合は\n変調波の値に線形に比例する'),
               ('② 相電圧の基本波',
                r"$\hat{V}_1 = m\,\dfrac{V_{dc}}{2}$",
                '振れ幅は ±V_dc/2。変調率 m が\nその何割まで使うかを決める'),
               ('③ 線間の実効値に直す',
                r"$V_{LL} = \dfrac{\sqrt{3}}{\sqrt{2}}\,m\,\dfrac{V_{dc}}{2} \approx 0.612\,m\,V_{dc}$",
                '600 V・m = 0.9 なら 328 V。\n400 V 系統には少し足りない')],
            result='直流電圧が足りなければ、いくら変調しても交流電圧は出ない')


if __name__ == "__main__":
    fig_pwm(); fig_spectrum(); fig_modulation(); fig_dq(); fig_gfl_gfm()
    fig_voltvar(); fig_synthetic_inertia(); fig_delay(); fig_islanding(); fig_lcl()
    fig_analogy(); fig_myth()
    fig_derivations()
    print("\n===== スライドに書く数値 =====")
    print(f"Vdc = {VDC:.0f} V、m = 0.9 → 相電圧の基本波振幅 {OUT['v1_09']:.0f} V、線間実効値 {OUT['vll_09']:.0f} V")
    for mf, v in OUT["thd"].items():
        print(f"  m_f = {mf}: THD = {v:.1f}%（{mf*60:,.0f} Hz スイッチング）")
    for Hv, (nad, roco, pmax) in OUT["vi"].items():
        print(f"  合成慣性 H_v = {Hv}: nadir = {nad:.2f} Hz, 初期 RoCoF = {roco:.2f} Hz/s, 最大出力 = {pmax:.0f} MW")
    print(f"LCL の共振周波数 = {OUT['fres']:.0f} Hz")
    print(f"Volt-Var の連系可能量: {OUT.get('host_vv')}")
