"""第3回 基本量と等価回路 — 瞬時電力・π型等価回路・P-δ/Q-V 分離"""
import numpy as np
from pws_common import setup_japanese_font, savefig
plt = setup_japanese_font()

print("=" * 62); print("第3回 デモ1: 瞬時電力の分解（無効電力の可視化）"); print("=" * 62)
f, V, I = 60.0, 1.0, 1.0
phi = np.deg2rad(30)
t = np.linspace(0, 2 / f, 1000, endpoint=False)   # 整数周期でサンプリング
w = 2 * np.pi * f
v = np.sqrt(2) * V * np.cos(w * t)
i = np.sqrt(2) * I * np.cos(w * t - phi)
p = v * i
P, Q = V * I * np.cos(phi), V * I * np.sin(phi)
p_act = P * (1 + np.cos(2 * w * t))
p_rea = Q * np.sin(2 * w * t)
print(f"  P = {P:.4f} p.u.,  Q = {Q:.4f} p.u.,  S = {V*I:.4f} p.u.")
print(f"  p(t) の実測平均 = {p.mean():.4f}  （P と一致するはず）")
print(f"  p(t) < 0 の時間割合 = {(p<0).mean()*100:.1f} %（電源へ戻る時間）")

fig, axes = plt.subplots(2, 1, figsize=(9, 6.5), sharex=True)
axes[0].plot(t*1000, v, label="$v(t)$"); axes[0].plot(t*1000, i, label="$i(t)$")
axes[0].set_ylabel("電圧・電流 [p.u.]")
axes[0].set_title(f"力率角 $\\phi$ = {np.rad2deg(phi):.0f}° （力率 {np.cos(phi):.3f} 遅れ）")
axes[0].legend(loc="upper right"); axes[0].grid(alpha=0.3)
axes[1].plot(t*1000, p, "k", lw=2, label="瞬時電力 $p(t)$")
axes[1].plot(t*1000, p_act, "--", label=f"有効分（平均 P={P:.3f}）")
axes[1].plot(t*1000, p_rea, "--", label=f"無効分（平均 0, 振幅 Q={Q:.3f}）")
axes[1].axhline(P, color="r", ls=":", label=f"$P$ = {P:.3f}")
axes[1].axhline(0, color="gray", lw=0.5)
axes[1].fill_between(t*1000, p, 0, where=(p < 0), color="red", alpha=0.25,
                     label="$p<0$: 電源へ返る")
axes[1].set_xlabel("時間 [ms]"); axes[1].set_ylabel("電力 [p.u.]")
axes[1].legend(loc="upper right", fontsize=8); axes[1].grid(alpha=0.3)
savefig(fig, "ch03_instantaneous_power.png"); plt.close(fig)

print()
print("=" * 62); print("第3回 デモ2: π型等価回路の四端子定数とフェランチ効果"); print("=" * 62)
f, length = 60.0, 200.0
r, x_l, c = 0.030, 0.35, 0.0090e-6
Z = (r + 1j*x_l) * length
Y = 1j * 2*np.pi*f * c * length
A = D = 1 + Z*Y/2; B = Z; C = Y*(1 + Z*Y/4)
print(f"  Z = {Z:.3f} ohm")
print(f"  Y = {Y.imag:.6f}j S")
print(f"  A = D = {A:.6f}")
print(f"  B = {B:.3f} ohm")
print(f"  C = {C:.8f} S")
print(f"  検算 AD - BC = {A*D - B*C:.10f}  （1 になるはず）")

# 送電端電圧を一定に保ったとき、受電端がどうなるかを見る
Vs = 275e3/np.sqrt(3)                      # 送電端 相電圧（線間 275 kV）
Vr_nl = Vs / A                             # 無負荷（Ir=0）: Vs = A*Vr より
print(f"\n  【無負荷時】送電端 {abs(Vs)/1e3:.2f} kV → 受電端 {abs(Vr_nl)/1e3:.2f} kV")
print(f"  受電端/送電端 = {abs(Vr_nl)/abs(Vs):.4f}")
print(f"  → {'フェランチ効果あり（受電端の方が高い）' if abs(Vr_nl)>abs(Vs) else 'フェランチ効果なし'}")

# 定格負荷時: Vs = A*Vr + B*Ir, Ir = conj(S/3/Vr) を反復で解く
S_load = 300e6 + 1j*100e6
Vr_l = Vs
for _ in range(60):
    Ir = np.conj(S_load/3 / Vr_l)
    Vr_l = (Vs - B*Ir) / A
print(f"  【負荷 300MW+j100Mvar】受電端 {abs(Vr_l)/1e3:.2f} kV, "
      f"電圧降下率 {(abs(Vs)-abs(Vr_l))/abs(Vs)*100:.2f} %")

print()
print("=" * 62); print("第3回 デモ3: P-δ / Q-V の分離"); print("=" * 62)
X = 0.20
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
delta = np.linspace(0, np.pi, 400)
for Vs in [0.95, 1.00, 1.05]:
    axes[0].plot(np.rad2deg(delta), Vs*1.0/X*np.sin(delta),
                 label=f"$V_s$={Vs:.2f}, $V_r$=1.00")
axes[0].axvline(90, color="r", ls="--", alpha=0.7)
axes[0].text(92, 1.0, "定態安定限界\n$\\delta=90°$", color="r", fontsize=9)
axes[0].set_xlabel("相差角 $\\delta$ [deg]"); axes[0].set_ylabel("$P$ [p.u.]")
axes[0].set_title("$P = \\frac{V_sV_r}{X}\\sin\\delta$ : 相差角が支配")
axes[0].legend(fontsize=9); axes[0].grid(alpha=0.3)
Vs_range = np.linspace(0.90, 1.10, 200)
for d_deg in [0, 10, 20]:
    d = np.deg2rad(d_deg)
    axes[1].plot(Vs_range, (Vs_range*1.0*np.cos(d) - 1.0)/X, label=f"$\\delta$={d_deg}°")
axes[1].axhline(0, color="gray", lw=0.8); axes[1].axvline(1.0, color="gray", lw=0.8, ls=":")
axes[1].set_xlabel("送電端電圧 $V_s$ [p.u.]"); axes[1].set_ylabel("$Q$ [p.u.]")
axes[1].set_title("$Q$ : 電圧の大きさの差が支配")
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3)
savefig(fig, "ch03_pdelta_qv.png"); plt.close(fig)
print(f"  X = {X} p.u. のとき最大送電電力 P_max = {1.0/X:.2f} p.u.")
print(f"  δ=30° での送電電力 P = {1.0/X*np.sin(np.deg2rad(30)):.3f} p.u.")
print("\n第3回 完了")
