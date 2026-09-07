"""第1回 エネルギー変換の基礎 — カルノー効率と風力の3乗則"""
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()

print("=" * 60); print("第1回 デモ1: 発電方式ごとの効率比較"); print("=" * 60)
plants = [("汽力(超臨界)", 566, 33, 0.42),
          ("コンバインドサイクル", 1600, 33, 0.62),
          ("原子力(PWR)", 325, 33, 0.34)]
names, carnot, actual = [], [], []
for name, t_h, t_l, eta in plants:
    T_H, T_L = t_h + 273.15, t_l + 273.15
    names.append(name); carnot.append(1 - T_L / T_H); actual.append(eta)
    print(f"  {name:<22} カルノー {1-T_L/T_H:6.1%} / 実機 {eta:5.1%} "
          f"→ 達成率 {eta/(1-T_L/T_H):5.1%}")

x = np.arange(len(names))
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.bar(x - 0.2, carnot, 0.4, label="カルノー効率（理論上限）", color="#8ecae6")
ax.bar(x + 0.2, actual, 0.4, label="実機の総合効率", color="#fb8500")
for i, (c, a) in enumerate(zip(carnot, actual)):
    ax.text(i - 0.2, c + 0.012, f"{c:.1%}", ha="center", fontsize=9)
    ax.text(i + 0.2, a + 0.012, f"{a:.1%}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
ax.set_ylabel("効率"); ax.set_ylim(0, 1.0)
ax.set_title("理論上限と実機効率の差")
ax.legend(); ax.grid(axis="y", alpha=0.3)
savefig(fig, "ch01_carnot.png"); plt.close(fig)

print()
print("=" * 60); print("第1回 デモ2: 風力の3乗則とベッツの限界"); print("=" * 60)
rho, D, Cp, BETZ = 1.225, 90.0, 0.45, 16 / 27
A = np.pi * (D / 2) ** 2
u = np.linspace(0, 25, 300)
P_wind = 0.5 * rho * A * u**3 / 1e6
P_rated, u_in, u_out = 3.0, 3.0, 25.0
P_turbine = np.clip(P_wind * Cp, 0, P_rated)
P_turbine[(u < u_in) | (u > u_out)] = 0.0

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(u, P_wind, "--", label="風の全エネルギー ($u^3$ に比例)")
ax.plot(u, P_wind * BETZ, "--", label=f"ベッツの限界 ({BETZ:.3f})")
ax.plot(u, P_turbine, lw=2.5, label=f"実機 ($C_p$={Cp}, 定格{P_rated} MW)")
ax.axvline(u_in, color="gray", ls=":"); ax.axvline(u_out, color="gray", ls=":")
ax.text(u_in + 0.3, 8.5, "カットイン", fontsize=9)
ax.text(u_out - 5.5, 8.5, "カットアウト", fontsize=9)
ax.set_xlabel("風速 $u_w$ [m/s]"); ax.set_ylabel("出力 [MW]")
ax.set_ylim(0, 10); ax.set_title("風力発電の出力特性")
ax.legend(fontsize=9); ax.grid(alpha=0.3)
savefig(fig, "ch01_wind.png"); plt.close(fig)

for us in [5, 10, 12, 15]:
    print(f"  風速 {us:2d} m/s → 出力 {min(0.5*rho*A*us**3*Cp/1e6, P_rated):5.2f} MW")
print(f"\n  風速 10→12 m/s で出力は {(12/10)**3:.3f} 倍（3乗則）")
print("\n第1回 完了")
