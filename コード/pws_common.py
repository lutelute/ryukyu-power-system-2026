"""
pws_common.py — 講義全体で共有するユーティリティ

電力エネルギーシステム解析の基礎と応用
第1〜15回のサンプルコードが共通で使う関数をまとめたもの。

使い方:
    from pws_common import setup_japanese_font, build_okinawa, make_okinawa_demand
"""
from __future__ import annotations
import os
import warnings
import logging

# pandapower の numba 未導入警告を抑制（学習用途では速度は問題にならない）
warnings.filterwarnings("ignore", message=".*numba.*")
logging.getLogger("pandapower").setLevel(logging.ERROR)
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- 図の設定
FIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "図")


def setup_japanese_font():
    """matplotlib で日本語を表示できるようにする（環境に応じて自動選択）"""
    import matplotlib
    matplotlib.use("Agg")                    # 画面がなくても動くようにする
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    available = {f.name for f in fm.fontManager.ttflist}
    for cand in ["Hiragino Sans", "Yu Gothic", "Noto Sans CJK JP",
                 "IPAexGothic", "Hiragino Maru Gothic Pro", "MS Gothic"]:
        if cand in available:
            plt.rcParams["font.family"] = cand
            break
    plt.rcParams["axes.unicode_minus"] = False   # マイナス記号の文字化け対策
    # 投影を前提にした文字の大きさ（スライドに貼ると縮むので、図の側で大きめに描く）
    plt.rcParams.update({
        "font.size": 14,
        "axes.titlesize": 15,
        "axes.labelsize": 14,
        "xtick.labelsize": 13,
        "ytick.labelsize": 13,
        "legend.fontsize": 12.5,
        "figure.titlesize": 16,
        "lines.linewidth": 2.4,
        "axes.linewidth": 1.2,
    })
    return plt


# スライド上で図に与えられる箱 (幅, 高さ) [inch]（tools/fig-scale.py が作る）
_SCALE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fig_scale.json")
try:
    import json as _json
    with open(_SCALE_PATH, encoding="utf-8") as _f:
        FIG_WIDTH_ON_SLIDE = _json.load(_f)
except Exception as _e:                  # 読めなければ縮小なしになる。黙って通さない
    FIG_WIDTH_ON_SLIDE = {}
    warnings.warn(f"fig_scale.json を読めませんでした（図は縮小されません）: {_e}")


def savefig(fig, name, dpi=None):
    """図を ../図/ に保存する

    figure-story のように小さく置かれる図は、キャンバスを縮めてから保存する。
    フォントの pt は変わらないので、スライド上での文字の見かけの大きさが揃う。
    """
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    box = FIG_WIDTH_ON_SLIDE.get(name)
    if box:
        w, h = fig.get_size_inches()
        k = max(0.45, min(1.0, box[0] / w, box[1] / h))   # 縮めすぎない
        if k < 0.995:
            fig.set_size_inches(w * k, h * k)
    if dpi is None:
        dpi = 200 if box and box[0] < 9.0 else 150
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    print(f"  [図を保存] {os.path.relpath(path, os.getcwd())}")
    return path


# ------------------------------------------------- 沖縄本島系統（簡略モデル）
S_BASE_MVA = 1500.0      # 系統容量 [MVA]
V_BASE_KV  = 132.0       # 基準電圧 [kV]
F_N        = 60.0        # 定格周波数 [Hz]
H_SYS      = 4.5         # 系統慣性定数 [s]
PCT_K      = 1.0         # 系統定数 [%MW/0.1Hz]

OKINAWA_BUSES = ["具志川", "牧港", "那覇", "中部", "北部"]
OKINAWA_LOADS = {2: (400.0, 160.0), 3: (350.0, 140.0), 4: (150.0, 60.0)}
# 132 kV のルート (from, to, 亘長 km, 回線数)。中枢は 4 回線、北部へ向かう末端は 1 回線。
# 1 回線だけでは 900 MW を送れず潮流計算が発散するため、実系統相当の回線数を持たせている。
OKINAWA_LINES = [(0, 1, 15.0, 4), (1, 2, 25.0, 4), (2, 3, 20.0, 3),
                 (3, 4, 35.0, 1), (0, 4, 45.0, 1)]


def build_okinawa(pv_mw=0.0, pv_pf=1.0, pv_bus=4, load_scale=1.0):
    """沖縄本島系統の簡略モデルを作る（第6回・第15回で使用）

    pv_mw    : 太陽光の容量 [MW]
    pv_pf    : 太陽光インバータの力率（1.0=力率1、0.95=進み）
    pv_bus   : 太陽光の連系ノード（0始まり）
    load_scale: 負荷の倍率
    """
    import pandapower as pp
    net = pp.create_empty_network(f_hz=F_N, sn_mva=100.0)
    buses = [pp.create_bus(net, vn_kv=V_BASE_KV, name=n) for n in OKINAWA_BUSES]

    pp.create_ext_grid(net, bus=buses[0], vm_pu=1.02, name="具志川",
                       min_p_mw=-500.0, max_p_mw=800.0,
                       min_q_mvar=-300.0, max_q_mvar=300.0,
                       s_sc_max_mva=3000.0, rx_max=0.1)   # 短絡計算（calc_sc）用
    pp.create_gen(net, bus=buses[1], p_mw=250.0, vm_pu=1.01, name="牧港",
                  min_p_mw=60.0, max_p_mw=400.0,
                  min_q_mvar=-120.0, max_q_mvar=150.0)

    for b, (p, q) in OKINAWA_LOADS.items():
        pp.create_load(net, bus=buses[b], p_mw=p * load_scale,
                       q_mvar=q * load_scale, name=OKINAWA_BUSES[b])

    for f, t, length, par in OKINAWA_LINES:
        pp.create_line_from_parameters(
            net, from_bus=buses[f], to_bus=buses[t], length_km=length,
            r_ohm_per_km=0.06, x_ohm_per_km=0.35, c_nf_per_km=9.0,
            max_i_ka=1.2, parallel=par, name=f"L{f+1}-{t+1}")

    if pv_mw > 0:
        q = 0.0 if pv_pf >= 1.0 else -pv_mw * np.tan(np.arccos(pv_pf))
        pp.create_sgen(net, bus=buses[pv_bus], p_mw=pv_mw, q_mvar=q,
                       name="太陽光")
    return net


# ------------------------------------------------------- 需要データ（第11回）
def make_okinawa_demand(start="2024-01-01", periods=24 * 365 * 2, seed=42):
    """沖縄本島系統を模した需要データ（1時間値）を生成する

    第11回で定義し、第12回・第15回でも使う。
    冷房主体・高湿度という沖縄の特徴を反映している。
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=periods, freq="h")
    doy, hour, dow = idx.dayofyear.values, idx.hour.values, idx.dayofweek.values

    # 気温（那覇: 年平均 23.5°C、年較差が小さい）
    T = (23.5 - 6.0 * np.cos(2 * np.pi * (doy - 25) / 365)
         - 3.0 * np.cos(2 * np.pi * (hour - 14) / 24)
         + rng.normal(0, 1.5, periods))
    # 相対湿度（夏に高い）
    RH = np.clip(74 + 8 * np.sin(2 * np.pi * (doy - 100) / 365)
                 + rng.normal(0, 6, periods), 40, 98)
    THI = thi_index(T, RH)

    base    = 700.0
    daily   = (180 * np.sin(2 * np.pi * (hour - 9) / 24)
               + 90 * np.sin(4 * np.pi * (hour - 7) / 24))
    weekly  = np.where(dow >= 5, -70.0, 0.0)
    cooling = 14.0 * np.maximum(THI - 70, 0) ** 1.25     # 冷房（非線形）
    heating = 4.0 * np.maximum(16 - T, 0)                # 暖房（沖縄は僅少）
    trend   = np.linspace(0, 25, periods)
    noise   = rng.normal(0, 22, periods)

    y = base + daily + weekly + cooling + heating + trend + noise
    return pd.DataFrame({"demand": np.maximum(y, 300.0),
                         "temp": T, "humidity": RH, "thi": THI}, index=idx)


def thi_index(T_air, RH):
    """不快指数 THI（第11回 11.2.2 節）"""
    return 0.81 * T_air + 0.01 * RH * (0.99 * T_air - 14.3) + 46.3


# ------------------------------------------------- 太陽光・風力（第10回）
def solar_position(doy, hour, lat_deg, lon_deg, tz=9.0):
    """太陽の天頂角 [deg] と時角 [deg] を返す（簡易 NOAA アルゴリズム）"""
    lat = np.deg2rad(lat_deg)
    decl = np.deg2rad(23.45) * np.sin(2 * np.pi * (284 + doy) / 365)
    B = 2 * np.pi * (doy - 81) / 364
    eot = 9.87 * np.sin(2 * B) - 7.53 * np.cos(B) - 1.5 * np.sin(B)   # 均時差[min]
    solar_time = hour + (4 * (lon_deg - 15 * tz) + eot) / 60
    omega = np.deg2rad(15 * (solar_time - 12))
    cos_z = (np.sin(lat) * np.sin(decl)
             + np.cos(lat) * np.cos(decl) * np.cos(omega))
    return np.rad2deg(np.arccos(np.clip(cos_z, -1, 1))), np.rad2deg(omega)


def clear_sky_ghi(doy, hour, lat=26.21, lon=127.68):
    """晴天時の全天日射量 [W/m^2]（Haurwitz モデル）"""
    zen, _ = solar_position(doy, hour, lat, lon)
    cos_z = np.cos(np.deg2rad(zen))
    cos_z = np.where(cos_z > 0, cos_z, 0.0)
    with np.errstate(divide="ignore", over="ignore"):
        ghi = 1098 * cos_z * np.exp(-0.059 / np.maximum(cos_z, 1e-6))
    return np.where(cos_z > 0, ghi, 0.0)


def pv_power(G_poa, T_air, p_rated_kw=1000.0,
             gamma=-0.004, noct=45.0, eta_sys=0.82):
    """PVWatts 型の太陽光出力モデル（第10回 10.2.4 節）

    G_poa [W/m^2], T_air [degC] -> (出力[kW], セル温度[degC])
    """
    G_poa = np.asarray(G_poa, dtype=float)
    T_cell = np.asarray(T_air, dtype=float) + (noct - 20) / 800 * G_poa
    p = p_rated_kw * (G_poa / 1000) * (1 + gamma * (T_cell - 25)) * eta_sys
    return np.maximum(p, 0.0), T_cell


def wind_shear(u_ref, z=90.0, z_ref=10.0, alpha=0.14):
    """べき法則によるハブ高さ風速の補正（第10回 10.2.5 節）"""
    return np.asarray(u_ref, dtype=float) * (z / z_ref) ** alpha


def wind_power_curve(u, p_rated=3.0, u_in=3.0, u_rated=12.0, u_out=25.0):
    """風車のパワーカーブ [MW]（第10回 10.2.5 節）"""
    u = np.atleast_1d(np.asarray(u, dtype=float))
    p = np.zeros_like(u)
    mid = (u >= u_in) & (u < u_rated)
    p[mid] = p_rated * ((u[mid] ** 3 - u_in ** 3) /
                        (u_rated ** 3 - u_in ** 3))
    p[(u >= u_rated) & (u <= u_out)] = p_rated
    return p if p.size > 1 else float(p[0])


# --------------------------------------------- 動特性（第7回・第8回）
def system_constant(capacity_mw=S_BASE_MVA, pct_k_per_01hz=PCT_K):
    """系統定数 K [MW/Hz]（%MW/0.1Hz から換算）"""
    return pct_k_per_01hz / 100 * capacity_mw * 10


def rocof(delta_p_mw, h_sys=H_SYS, s_sys=S_BASE_MVA, f_n=F_N):
    """周波数変化率 dF/dt [Hz/s]（第8回 8.2.6 節）"""
    return f_n * delta_p_mw / (2 * h_sys * s_sys)


def equal_area(p_max=2.0, p_m=1.0, h=4.0, f_n=F_N):
    """等面積法（第7回 7.2.6 節）

    戻り値: (delta0[deg], delta_cr[deg], t_cr[s])
    三相短絡（故障中 Pe=0）、故障除去後は元の曲線に復帰する場合。
    """
    w0 = 2 * np.pi * f_n
    d0 = np.arcsin(np.clip(p_m / p_max, -1, 1))
    cos_cr = p_m / p_max * (np.pi - 2 * d0) - np.cos(d0)
    d_cr = np.arccos(np.clip(cos_cr, -1, 1))
    t_cr = np.sqrt(4 * h * (d_cr - d0) / (w0 * p_m))
    return np.rad2deg(d0), np.rad2deg(d_cr), t_cr


# ------------------------------------------------------- 潮流計算（第4回）
def build_ybus(n_bus, lines, shunts=None):
    """ノードアドミタンス行列を作る（第4回 4.2.1 節）

    lines : [(from, to, R, X, B_half), ...]  ノード番号は 1 始まり
    """
    Y = np.zeros((n_bus, n_bus), dtype=complex)
    for f, t, r, x, b_half in lines:
        i, j = f - 1, t - 1
        y = 1.0 / complex(r, x)
        Y[i, j] -= y
        Y[j, i] -= y
        Y[i, i] += y + 1j * b_half
        Y[j, j] += y + 1j * b_half
    if shunts:
        for bus, ys in shunts.items():
            Y[bus - 1, bus - 1] += ys
    return Y


def power_injection(V, theta, Ybus):
    """電力方程式から注入電力を計算する（第4回 4.2.3 節）"""
    Vc = np.asarray(V) * np.exp(1j * np.asarray(theta))
    S = Vc * np.conj(Ybus @ Vc)
    return S.real, S.imag


def newton_raphson(Ybus, bus_type, P_sch, Q_sch, V_mag,
                   tol=1e-8, max_iter=20, verbose=False):
    """ニュートン・ラフソン法による潮流計算（第5回 5.3.2 節）

    bus_type: 0=スラック, 1=PV指定, 2=PQ指定
    戻り値: (V, theta, 反復回数, 収束履歴)
    """
    Ybus = np.asarray(Ybus)
    G, B = Ybus.real, Ybus.imag
    bus_type = np.asarray(bus_type)
    pv = np.where(bus_type == 1)[0]
    pq = np.where(bus_type == 2)[0]
    pvpq = np.concatenate([pv, pq])

    V = np.array(V_mag, dtype=float)
    theta = np.zeros(len(bus_type))          # フラットスタート
    history = []

    for it in range(max_iter):
        P, Q = power_injection(V, theta, Ybus)
        mismatch = np.concatenate([np.asarray(P_sch)[pvpq] - P[pvpq],
                                   np.asarray(Q_sch)[pq] - Q[pq]])
        err = np.abs(mismatch).max() if mismatch.size else 0.0
        history.append(err)
        if verbose:
            print(f"    反復 {it}: 最大ミスマッチ = {err:.3e}")
        if err < tol:
            return V, theta, it, history

        n1, n2 = len(pvpq), len(pq)
        H = np.zeros((n1, n1)); N = np.zeros((n1, n2))
        M = np.zeros((n2, n1)); L = np.zeros((n2, n2))

        for a, i in enumerate(pvpq):
            for b, j in enumerate(pvpq):
                if i == j:
                    H[a, b] = -Q[i] - B[i, i] * V[i] ** 2
                else:
                    th = theta[i] - theta[j]
                    H[a, b] = V[i]*V[j]*(G[i, j]*np.sin(th) - B[i, j]*np.cos(th))
            for b, j in enumerate(pq):
                if i == j:
                    N[a, b] = P[i] + G[i, i] * V[i] ** 2
                else:
                    th = theta[i] - theta[j]
                    N[a, b] = V[i]*V[j]*(G[i, j]*np.cos(th) + B[i, j]*np.sin(th))
        for a, i in enumerate(pq):
            for b, j in enumerate(pvpq):
                if i == j:
                    M[a, b] = P[i] - G[i, i] * V[i] ** 2
                else:
                    th = theta[i] - theta[j]
                    M[a, b] = -V[i]*V[j]*(G[i, j]*np.cos(th) + B[i, j]*np.sin(th))
            for b, j in enumerate(pq):
                if i == j:
                    L[a, b] = Q[i] - B[i, i] * V[i] ** 2
                else:
                    th = theta[i] - theta[j]
                    L[a, b] = V[i]*V[j]*(G[i, j]*np.sin(th) - B[i, j]*np.cos(th))

        J = np.block([[H, N], [M, L]])
        dx = np.linalg.solve(J, mismatch)
        theta[pvpq] += dx[:n1]
        if n2:
            V[pq] *= (1 + dx[n1:])
    return V, theta, max_iter, history


if __name__ == "__main__":
    print("pws_common.py セルフテスト")
    print("-" * 46)
    Y = build_ybus(3, [(1, 2, 0.02, 0.06, 0.030),
                       (1, 3, 0.08, 0.24, 0.025),
                       (2, 3, 0.06, 0.18, 0.020)])
    print("Y_bus 対称性の誤差:", np.abs(Y - Y.T).max())
    V, th, it, _ = newton_raphson(
        Y, np.array([0, 1, 2]),
        np.array([0.0, 0.50, -1.00]), np.array([0.0, 0.0, -0.40]),
        np.array([1.05, 1.02, 1.00]))
    print(f"NR法: {it} 回で収束, |V| = {np.round(V, 5)}")
    d0, dcr, tcr = equal_area(p_max=2.0, p_m=0.8, h=4.0)
    print(f"等面積法: δ0={d0:.2f}°, δcr={dcr:.2f}°, t_cr={tcr*1000:.1f} ms")
    print(f"系統定数 K = {system_constant():.0f} MW/Hz")
    print(f"RoCoF(-250MW) = {rocof(-250.0):.3f} Hz/s")
    print("OK")
