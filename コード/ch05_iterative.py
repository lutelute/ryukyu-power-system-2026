"""第5回 反復解法 — ガウス・ザイデル法とニュートン・ラフソン法の比較"""
import numpy as np
from pws_common import setup_japanese_font, savefig, build_ybus, newton_raphson
plt = setup_japanese_font()


def gauss_seidel(Ybus, bus_type, P_sch, Q_sch, V_mag,
                 tol=1e-8, max_iter=2000, accel=1.6):
    """ガウス・ザイデル法（第5回 5.2.1 節）"""
    n = len(bus_type)
    V = np.where(bus_type == 0, V_mag, 1.0).astype(complex)
    V[bus_type == 1] = V_mag[bus_type == 1]
    Q = np.array(Q_sch, dtype=float)
    history = []
    for it in range(max_iter):
        V_prev = V.copy()
        for i in range(n):
            if bus_type[i] == 0:
                continue
            if bus_type[i] == 1:                       # PV: Q を推定
                Q[i] = -np.imag(np.conj(V[i]) * (Ybus[i, :] @ V))
            sum_YV = Ybus[i, :] @ V - Ybus[i, i]*V[i]
            V_new = ((P_sch[i] - 1j*Q[i]) / np.conj(V[i]) - sum_YV) / Ybus[i, i]
            V_new = V[i] + accel*(V_new - V[i])        # 加速
            if bus_type[i] == 1:                       # PV: 大きさを戻す
                V_new = V_mag[i] * V_new/abs(V_new)
            V[i] = V_new
        err = np.abs(V - V_prev).max()
        history.append(err)
        if err < tol:
            return V, it+1, history
    return V, max_iter, history


lines = [(1, 2, 0.02, 0.06, 0.030), (1, 3, 0.08, 0.24, 0.025),
         (2, 3, 0.06, 0.18, 0.020)]
Y = build_ybus(3, lines)
bus_type = np.array([0, 1, 2])
P_sch = np.array([0.0, 0.50, -1.00])
Q_sch = np.array([0.0, 0.00, -0.40])
V_mag = np.array([1.05, 1.02, 1.00])

print("=" * 62); print("第5回 デモ1: ガウス・ザイデル法"); print("=" * 62)
V_gs, it_gs, hist_gs = gauss_seidel(Y, bus_type, P_sch, Q_sch, V_mag)
print(f"  {it_gs} 回の反復で収束（1次収束）")
print(f"  {'ノード':>6} {'|V|[p.u.]':>11} {'θ[deg]':>9}")
for i in range(3):
    print(f"  {i+1:6d} {abs(V_gs[i]):11.6f} {np.rad2deg(np.angle(V_gs[i])):9.4f}")

print()
print("=" * 62); print("第5回 デモ2: ニュートン・ラフソン法"); print("=" * 62)
V_nr, th_nr, it_nr, hist_nr = newton_raphson(Y, bus_type, P_sch, Q_sch, V_mag,
                                             verbose=True)
print(f"\n  {it_nr} 回の反復で収束（2次収束）")
print(f"  {'ノード':>6} {'|V|[p.u.]':>11} {'θ[deg]':>9}")
for i in range(3):
    print(f"  {i+1:6d} {V_nr[i]:11.6f} {np.rad2deg(th_nr[i]):9.4f}")

print("\n  ミスマッチの推移（誤差の指数部が倍々になる = 2次収束）:")
for k, e in enumerate(hist_nr):
    print(f"    反復 {k}: {e:.3e}")

print()
print("=" * 62); print("第5回 デモ3: 収束特性の比較"); print("=" * 62)
print(f"  ガウス・ザイデル法: {it_gs:4d} 回")
print(f"  ニュートン・ラフソン法: {it_nr:4d} 回")
print(f"  反復回数の比: {it_gs/max(it_nr,1):.1f} 倍")
print(f"\n  両手法の解の一致:")
print(f"    |V| の最大差: {np.abs(np.abs(V_gs) - V_nr).max():.2e}")
print(f"    θ  の最大差: {np.abs(np.angle(V_gs) - th_nr).max():.2e}")

fig, ax = plt.subplots(figsize=(8, 5))
ax.semilogy(range(1, len(hist_gs)+1), hist_gs, "o-", ms=2.5,
            label=f"ガウス・ザイデル法（{it_gs} 回, 1次収束）")
ax.semilogy(range(1, len(hist_nr)+1), hist_nr, "s-", ms=8, lw=2,
            label=f"ニュートン・ラフソン法（{it_nr} 回, 2次収束）")
ax.axhline(1e-8, color="r", ls="--", alpha=0.6, label="収束判定 $\\varepsilon=10^{-8}$")
ax.set_xlabel("反復回数 $\\nu$"); ax.set_ylabel("最大ミスマッチ")
ax.set_title("潮流計算の収束特性の比較")
ax.legend(); ax.grid(alpha=0.3, which="both")
savefig(fig, "ch05_convergence.png"); plt.close(fig)
print("\n第5回 完了")
