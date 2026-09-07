"""第6回 潮流計算の実践 — 自作NRとpandapowerの照合、IEEE14、PVカーブ、太陽光導入"""
import numpy as np
import pandapower as pp
import pandapower.networks as pn
from pws_common import setup_japanese_font, savefig, build_ybus, newton_raphson
plt = setup_japanese_font()

# ============================================================
print("=" * 66); print("第6回 演習1: 自作ニュートン法と pandapower の照合"); print("=" * 66)
S_BASE, V_BASE = 100.0, 132.0
Z_BASE = V_BASE**2 / S_BASE

net = pp.create_empty_network(f_hz=60.0, sn_mva=S_BASE)
buses = [pp.create_bus(net, vn_kv=V_BASE, name=f"Bus {i+1}") for i in range(3)]
pp.create_ext_grid(net, bus=buses[0], vm_pu=1.05)
pp.create_gen(net, bus=buses[1], p_mw=50.0, vm_pu=1.02)
pp.create_load(net, bus=buses[2], p_mw=100.0, q_mvar=40.0)

line_pu = [(0, 1, 0.02, 0.06, 0.030), (0, 2, 0.08, 0.24, 0.025),
           (1, 2, 0.06, 0.18, 0.020)]
for f, t, r_pu, x_pu, b_half in line_pu:
    L = 1.0
    b_siemens = 2 * b_half / Z_BASE                    # 線路全体の B [S]
    c_nf = b_siemens / (2 * np.pi * 60.0) * 1e9 / L    # -> nF/km
    pp.create_line_from_parameters(
        net, from_bus=buses[f], to_bus=buses[t], length_km=L,
        r_ohm_per_km=r_pu * Z_BASE / L, x_ohm_per_km=x_pu * Z_BASE / L,
        c_nf_per_km=c_nf, max_i_ka=2.0, name=f"L{f+1}-{t+1}")
pp.runpp(net, algorithm="nr", tolerance_mva=1e-10)

print("  【pandapower】")
print(f"  {'ノード':>6} {'|V|[p.u.]':>11} {'θ[deg]':>10}")
for i in range(3):
    print(f"  {i+1:6d} {net.res_bus.vm_pu[i]:11.6f} {net.res_bus.va_degree[i]:10.4f}")

Y = build_ybus(3, [(f+1, t+1, r, x, b) for f, t, r, x, b in line_pu])
V_own, th_own, iters, _ = newton_raphson(
    Y, np.array([0, 1, 2]),
    np.array([0.0, 50.0/S_BASE, -100.0/S_BASE]),
    np.array([0.0, 0.0, -40.0/S_BASE]),
    np.array([1.05, 1.02, 1.00]))
print("\n  【自作ニュートン法】")
print(f"  {'ノード':>6} {'|V|[p.u.]':>11} {'θ[deg]':>10}")
for i in range(3):
    print(f"  {i+1:6d} {V_own[i]:11.6f} {np.rad2deg(th_own[i]):10.4f}")

dv = np.abs(net.res_bus.vm_pu.values - V_own).max()
dt = np.abs(net.res_bus.va_degree.values - np.rad2deg(th_own)).max()
print(f"\n  差分: |V| {dv:.2e} p.u.,  θ {dt:.2e} deg")
print(f"  → {'✅ 実装は正しい（1e-5 以下）' if dv < 1e-5 else '❌ 要デバッグ'}")

# ============================================================
print()
print("=" * 66); print("第6回 演習2: IEEE 14 母線系統"); print("=" * 66)
net = pn.case14()
print(f"  母線 {len(net.bus)} / 線路 {len(net.line)} / 変圧器 {len(net.trafo)} "
      f"/ 発電機 {len(net.gen)}(PV) / 負荷 {len(net.load)}")
pp.runpp(net)
print(f"\n  電圧範囲: {net.res_bus.vm_pu.min():.4f} 〜 {net.res_bus.vm_pu.max():.4f} p.u.")
out = net.res_bus[(net.res_bus.vm_pu > 1.05) | (net.res_bus.vm_pu < 0.95)]
if len(out):
    print(f"  運用範囲(0.95-1.05)外の母線: {list(out.index)} "
          f"→ 値 {[round(v,4) for v in out.vm_pu]}")
print(f"  最大線路負荷率: {net.res_line.loading_percent.max():.2f} % "
      f"(線路 {net.res_line.loading_percent.idxmax()})")
print("  ※ IEEE 14 の標準データは線路容量が大きく設定されており、負荷率は低い")

p_gen = net.res_ext_grid.p_mw.sum() + net.res_gen.p_mw.sum()
p_load = net.res_load.p_mw.sum()
p_loss = net.res_line.pl_mw.sum() + net.res_trafo.pl_mw.sum()
print(f"\n  総発電 {p_gen:8.3f} MW / 総負荷 {p_load:8.3f} MW")
print(f"  総損失 {p_loss:8.3f} MW ({p_loss/p_load*100:.2f} %)")
print(f"  収支誤差 {p_gen - p_load - p_loss:.2e} MW（0 になるはず）")

# ============================================================
print()
print("=" * 66); print("第6回 演習3: PVカーブ（負荷増加と電圧崩壊）"); print("=" * 66)
base = pn.case14()
p0, q0 = base.load.p_mw.copy(), base.load.q_mvar.copy()
scales, v_min, converged_max = [], [], 0.0
for k in np.arange(1.0, 5.01, 0.02):
    n2 = pn.case14()
    n2.load.p_mw, n2.load.q_mvar = p0 * k, q0 * k
    try:
        pp.runpp(n2, max_iteration=50)
        scales.append(k); v_min.append(n2.res_bus.vm_pu.min()); converged_max = k
    except pp.LoadflowNotConverged:
        break
print(f"  収束した最大負荷倍率: {converged_max:.2f} 倍")
print(f"  そのときの最低電圧  : {v_min[-1]:.4f} p.u.")
i95 = next((i for i, v in enumerate(v_min) if v < 0.95), None)
if i95:
    print(f"  電圧が 0.95 を割る倍率: {scales[i95]:.2f} 倍")

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(scales, v_min, "o-", ms=3, label="系統最低電圧")
ax.axhline(0.95, color="r", ls="--", alpha=0.7, label="運用下限 0.95 p.u.")
ax.axvline(converged_max, color="k", ls=":", alpha=0.7,
           label=f"収束限界 {converged_max:.2f} 倍")
ax.set_xlabel("負荷倍率"); ax.set_ylabel("母線電圧 [p.u.]")
ax.set_title("PV カーブ（負荷増加に伴う電圧低下）")
ax.legend(); ax.grid(alpha=0.3)
savefig(fig, "ch06_pv_curve.png"); plt.close(fig)

# ============================================================
print()
print("=" * 66); print("第6回 演習4: 太陽光導入の影響"); print("=" * 66)
PV_BUSES = [9, 10, 11, 12, 13]
ratios, vmax_l, vmin_l, loss_l = [], [], [], []
for ratio in np.arange(0.0, 2.01, 0.05):
    n3 = pn.case14()
    pv_each = n3.load.p_mw.sum() * ratio / len(PV_BUSES)
    for b in PV_BUSES:
        pp.create_sgen(n3, bus=b, p_mw=pv_each, q_mvar=0.0)
    try:
        pp.runpp(n3)
        ratios.append(ratio*100); vmax_l.append(n3.res_bus.vm_pu.max())
        vmin_l.append(n3.res_bus.vm_pu.min()); loss_l.append(n3.res_line.pl_mw.sum())
    except pp.LoadflowNotConverged:
        break
i_min = int(np.argmin(loss_l))
print(f"  {'導入率[%]':>10} {'最高電圧':>10} {'最低電圧':>10} {'損失[MW]':>10}")
for j in range(0, len(ratios), 8):
    print(f"  {ratios[j]:10.0f} {vmax_l[j]:10.4f} {vmin_l[j]:10.4f} {loss_l[j]:10.3f}")
print(f"\n  損失が最小になる導入率: {ratios[i_min]:.0f} % （損失 {loss_l[i_min]:.3f} MW）")
print(f"  → 導入率が低いうちは損失が減り、逆潮流が大きくなると再び増える")

fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
axes[0].plot(ratios, vmax_l, "o-", ms=3, label="系統最高電圧")
axes[0].plot(ratios, vmin_l, "s-", ms=3, label="系統最低電圧")
axes[0].axhline(1.05, color="r", ls="--", alpha=0.7, label="運用上限 1.05")
axes[0].axhline(0.95, color="r", ls="--", alpha=0.7)
axes[0].set_xlabel("太陽光導入率 [% of 総需要]"); axes[0].set_ylabel("電圧 [p.u.]")
axes[0].set_title("太陽光導入率と母線電圧"); axes[0].legend(fontsize=9); axes[0].grid(alpha=0.3)
axes[1].plot(ratios, loss_l, "o-", ms=3, color="#d62828")
axes[1].plot(ratios[i_min], loss_l[i_min], "k*", ms=14, label="損失最小")
axes[1].set_xlabel("太陽光導入率 [%]"); axes[1].set_ylabel("送電損失 [MW]")
axes[1].set_title("太陽光導入率と送電損失"); axes[1].legend(); axes[1].grid(alpha=0.3)
savefig(fig, "ch06_pv_penetration.png"); plt.close(fig)

# 電圧プロファイル
net = pn.case14(); pp.runpp(net)
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.bar(net.res_bus.index + 1, net.res_bus.vm_pu, color="#457b9d")
ax.axhline(1.05, color="r", ls="--", label="上限 1.05")
ax.axhline(0.95, color="r", ls="--", label="下限 0.95")
ax.set_ylim(0.9, 1.12); ax.set_xlabel("母線番号"); ax.set_ylabel("電圧 [p.u.]")
ax.set_title("IEEE 14 母線系統の電圧プロファイル")
ax.legend(); ax.grid(axis="y", alpha=0.3)
savefig(fig, "ch06_voltage_profile.png"); plt.close(fig)
print("\n第6回 完了")
