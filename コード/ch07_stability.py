"""第7回 電力系統の安定度 — 等面積法・動揺方程式・慣性低下"""
import numpy as np
from scipy.integrate import solve_ivp
from pws_common import setup_japanese_font, savefig, equal_area, F_N
plt = setup_japanese_font()

P_max, P_m, H, f0 = 2.0, 0.8, 4.0, F_N
w0 = 2*np.pi*f0

print("=" * 66); print("第7回 デモ1: 等面積法"); print("=" * 66)
d0_deg, dcr_deg, t_cr = equal_area(P_max, P_m, H, f0)
delta0, delta_cr = np.deg2rad(d0_deg), np.deg2rad(dcr_deg)
delta_max = np.pi - delta0
print(f"  初期相差角   δ0     = {d0_deg:6.2f}°")
print(f"  臨界除去角   δ_cr   = {dcr_deg:6.2f}°")
print(f"  最大振れ角   δ_max  = {np.rad2deg(delta_max):6.2f}°")
print(f"  臨界除去時間 t_cr   = {t_cr*1000:6.1f} ms ({t_cr*f0:.1f} サイクル)")
A1 = P_m*(delta_cr - delta0)
A2 = P_max*(np.cos(delta_cr) - np.cos(delta_max)) - P_m*(delta_max - delta_cr)
print(f"  検算: S_A = {A1:.6f}, S_B = {A2:.6f}, 差 = {abs(A1-A2):.2e}")

d = np.linspace(0, np.pi, 500)
fig, ax = plt.subplots(figsize=(9, 5.5))
ax.plot(np.rad2deg(d), P_max*np.sin(d), lw=2, label="$P_e = P_{max}\\sin\\delta$")
ax.axhline(P_m, color="k", ls="--", label=f"$P_m$ = {P_m}")
d1 = np.linspace(delta0, delta_cr, 200)
ax.fill_between(np.rad2deg(d1), 0, P_m, color="red", alpha=0.35, label="加速エネルギー $S_A$")
d2 = np.linspace(delta_cr, delta_max, 200)
ax.fill_between(np.rad2deg(d2), P_m, P_max*np.sin(d2), color="blue", alpha=0.35, label="減速エネルギー $S_B$")
for x, lab, c in [(delta0, "$\\delta_0$", "green"), (delta_cr, "$\\delta_{cr}$", "red"),
                  (delta_max, "$\\delta_{max}$", "blue")]:
    ax.axvline(np.rad2deg(x), color=c, ls=":", alpha=0.8)
    ax.text(np.rad2deg(x), -0.16, lab, ha="center", color=c, fontsize=11)
ax.set_xlabel("相差角 $\\delta$ [deg]"); ax.set_ylabel("電力 [p.u.]")
ax.set_title(f"等面積法（$t_{{cr}}$ = {t_cr*1000:.0f} ms）")
ax.set_ylim(-0.28, 2.2); ax.legend(loc="upper right"); ax.grid(alpha=0.3)
savefig(fig, "ch07_equal_area.png"); plt.close(fig)

print()
print("=" * 66); print("第7回 デモ2: 動揺方程式の数値積分"); print("=" * 66)
D = 0.5
def swing(t, y, t_clear):
    delta, dw = y
    Pe = 0.0 if t < t_clear else P_max*np.sin(delta)
    return [dw, (w0/(2*H))*(P_m - Pe - D*dw/w0)]

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
print(f"  {'除去時間[ms]':>13} {'最大δ[deg]':>12} {'判定':>8}")
for t_clear, color in [(0.10, "#2a9d8f"), (0.20, "#e9c46a"),
                       (0.24, "#f4a261"), (0.30, "#e63946")]:
    sol = solve_ivp(swing, (0, 5), [delta0, 0.0], t_eval=np.linspace(0, 5, 3000),
                    args=(t_clear,), rtol=1e-8, atol=1e-10, max_step=0.001)
    d_deg = np.rad2deg(sol.y[0])
    stable = d_deg.max() < 180 and np.isfinite(d_deg).all()
    print(f"  {t_clear*1000:13.0f} {d_deg.max():12.1f} {'安定' if stable else '脱調':>8}")
    lab = f"$t_c$={t_clear*1000:.0f} ms " + ("(安定)" if stable else "(脱調)")
    axes[0].plot(sol.t, d_deg, color=color, lw=2, label=lab)
    axes[1].plot(d_deg, sol.y[1]*60/(2*np.pi), color=color, lw=1.5, label=lab)
print(f"  → 理論の t_cr = {t_cr*1000:.0f} ms を境に安定/脱調が分かれる")
axes[0].axhline(180, color="k", ls="--", alpha=0.6, label="180°（脱調の目安）")
axes[0].set_xlabel("時間 [s]"); axes[0].set_ylabel("相差角 $\\delta$ [deg]")
axes[0].set_title("時間応答"); axes[0].legend(fontsize=9); axes[0].grid(alpha=0.3)
axes[0].set_ylim(0, 400)
axes[1].set_xlabel("$\\delta$ [deg]"); axes[1].set_ylabel("速度偏差 [Hz]")
axes[1].set_title("位相平面（安定なら渦を巻いて収束）")
axes[1].legend(fontsize=9); axes[1].grid(alpha=0.3); axes[1].set_xlim(0, 400)
savefig(fig, "ch07_swing.png"); plt.close(fig)

print()
print("=" * 66); print("第7回 デモ3: 慣性低下が t_cr に与える影響"); print("=" * 66)
H_range = np.linspace(0.5, 8.0, 200)
t_cr_range = np.array([equal_area(P_max, P_m, h, f0)[2] for h in H_range])
fig, ax = plt.subplots(figsize=(8.5, 5))
ax.plot(H_range, t_cr_range*1000, lw=2.5, color="#264653")
ax.axhline(70, color="r", ls="--", alpha=0.8, label="実際の保護時間 70 ms（リレー20＋遮断器50）")
print(f"  {'H [s]':>7} {'t_cr [ms]':>11} {'サイクル':>10} {'余裕':>8}")
for h, label in [(6.0, "従来系統"), (4.0, "現在"), (2.0, "再エネ50%"), (1.0, "再エネ大量")]:
    t = equal_area(P_max, P_m, h, f0)[2]
    ax.plot(h, t*1000, "o", ms=9, color="#e63946")
    ax.annotate(f"{label}\n{t*1000:.0f} ms", (h, t*1000),
                textcoords="offset points", xytext=(8, 8), fontsize=9)
    print(f"  {h:7.1f} {t*1000:11.1f} {t*f0:10.2f} {(t*1000-70)/(t*1000)*100:7.1f}%")
ax.set_xlabel("系統慣性定数 $H_{sys}$ [s]"); ax.set_ylabel("臨界故障除去時間 $t_{cr}$ [ms]")
ax.set_title("$t_{cr} \\propto \\sqrt{H}$ : 慣性が下がると保護に許される時間が短くなる")
ax.legend(); ax.grid(alpha=0.3)
savefig(fig, "ch07_inertia.png"); plt.close(fig)
print("\n第7回 完了")
