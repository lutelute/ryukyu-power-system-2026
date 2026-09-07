"""第2回 電力システムの構成 — 送電電圧と損失、系統構成の信頼度"""
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()

print("=" * 60); print("第2回 デモ1: 送電電圧レベルと損失率"); print("=" * 60)
P, length, r_per_km, pf = 1000e6, 200.0, 0.03, 0.95
R = r_per_km * length
V_levels = np.array([66, 110, 154, 275, 500]) * 1e3

print(f"  {'電圧[kV]':>9} {'電流[A]':>10} {'損失[MW]':>11} {'損失率[%]':>11}")
loss_rates = []
for V in V_levels:
    I = P / (np.sqrt(3) * V * pf)
    loss = 3 * I**2 * R
    rate = loss / P * 100
    loss_rates.append(rate)
    print(f"  {V/1e3:9.0f} {I:10.0f} {loss/1e6:11.2f} {rate:11.2f}")
print("  → 66 kV では損失が送電電力を超え、物理的に送電不可能")

fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.plot(V_levels / 1e3, loss_rates, "o-", lw=2, ms=8, color="#e63946")
for v, lr in zip(V_levels / 1e3, loss_rates):
    ax.annotate(f"{lr:.1f}%", (v, lr), textcoords="offset points",
                xytext=(6, 6), fontsize=9)
ax.set_xlabel("送電電圧 [kV]"); ax.set_ylabel("損失率 [%]")
ax.set_title(f"送電損失率 vs 電圧（{P/1e6:.0f} MW を {length:.0f} km 送電）")
ax.set_yscale("log"); ax.grid(alpha=0.3, which="both")
savefig(fig, "ch02_loss_vs_voltage.png"); plt.close(fig)

print()
print("=" * 60); print("第2回 デモ2: 放射状 vs ループ の供給信頼度"); print("=" * 60)
rng = np.random.default_rng(42)
N, p_fail = 200_000, 0.01
radial = (rng.random((N, 3)) > p_fail).all(axis=1)
loop   = (rng.random((N, 2)) > p_fail).any(axis=1)
print(f"  放射状（3本直列）: 供給成功率 {radial.mean():.5f} "
      f"（理論値 {(1-p_fail)**3:.5f}）")
print(f"  ループ（2経路）  : 供給成功率 {loop.mean():.5f} "
      f"（理論値 {1-p_fail**2:.5f}）")
print(f"  年間停電時間: 放射状 {(1-radial.mean())*8760*60:7.1f} 分/年")
print(f"              ループ {(1-loop.mean())*8760*60:7.1f} 分/年")
print(f"  → ループ化で停電時間が約 {(1-radial.mean())/(1-loop.mean()):.0f} 分の1")
print("\n第2回 完了")
