"""第4回 ノードアドミタンス行列・電力方程式・直流法潮流"""
import numpy as np
from pws_common import build_ybus, power_injection

np.set_printoptions(precision=4, suppress=True)
print("=" * 62); print("第4回 デモ1: ノードアドミタンス行列の構築"); print("=" * 62)
lines = [(1, 2, 0.02, 0.06, 0.030), (1, 3, 0.08, 0.24, 0.025),
         (2, 3, 0.06, 0.18, 0.020)]
Y = build_ybus(3, lines)
print("  Y_bus =")
for row in Y:
    print("    [" + ", ".join(f"{v.real:8.4f}{v.imag:+8.4f}j" for v in row) + "]")
print(f"\n  検算1 対称性 |Y - Y^T| の最大値: {np.abs(Y - Y.T).max():.2e}")
print("  検算2 各行の和（充電容量分だけ虚部が残るはず）:")
for i, s in enumerate(Y.sum(axis=1), start=1):
    print(f"    行{i}: {s.real:+.6f}{s.imag:+.6f}j")

print()
print("=" * 62); print("第4回 デモ2: 系統規模と疎性"); print("=" * 62)
# ブランチ数は実系統の実績値（IEEE標準ケース）と、その外挿を使う
#   IEEE14: 20 ブランチ, IEEE118: 186 ブランチ → おおむね 1.4〜1.6 n
cases = [(14, 20, "IEEE 14"), (118, 186, "IEEE 118"),
         (1000, 1500, "中規模系統"), (10000, 15000, "大規模系統")]
print(f"  {'母線数':>8} {'ブランチ数':>10} {'非零要素':>12} {'全要素':>15} {'密度':>10}  系統")
for n, nl, label in cases:
    nnz = n + 2*nl; tot = n**2
    print(f"  {n:8d} {nl:10d} {nnz:12,d} {tot:15,d} {nnz/tot:9.4%}  {label}")
print("  → 規模が大きいほど疎になる（10000母線で 99.94% が零）")
print("\n  計算量（LU分解）の比較:")
print(f"  {'母線数':>8} {'密行列 O(n^3)':>18} {'疎行列 O(n^1.4)':>18} {'高速化':>12}")
for n in [14, 118, 1000, 10000]:
    print(f"  {n:8d} {n**3:18,.0f} {n**1.4:18,.0f} {n**3/n**1.4:11,.0f}x")

print()
print("=" * 62); print("第4回 デモ3: 電力方程式による注入電力の計算"); print("=" * 62)
V = np.array([1.05, 1.02, 0.98]); theta = np.deg2rad([0.0, -2.5, -5.1])
P, Q = power_injection(V, theta, Y)
print(f"  {'ノード':>6} {'V[p.u.]':>10} {'θ[deg]':>9} {'P[p.u.]':>10} {'Q[p.u.]':>10}")
for i in range(3):
    print(f"  {i+1:6d} {V[i]:10.4f} {np.rad2deg(theta[i]):9.2f} {P[i]:10.4f} {Q[i]:10.4f}")
print(f"\n  有効電力の総和（= 系統損失）: {P.sum():.5f} p.u. = {P.sum()*100:.2f} MW")
print(f"  無効電力の総和              : {Q.sum():.5f} p.u.")

print()
print("=" * 62); print("第4回 デモ4: 直流法潮流計算（教科書 例題4.4 に対応）"); print("=" * 62)
# ノード1から1.0、ノード2から0.8 供給。x12=0.8, x13=0.5, x23=1.0
x12, x13, x23 = 0.8, 0.5, 1.0
Amat = np.array([[-1/x12 - 1/x13, -1/x13 + 1/x13],  # 後で正しく組む
                 [0, 0]], dtype=float)
# 正しく: ノード1: 1.0 = (0-d2)/x12 + (0-d3)/x13
#         ノード2: 0.8 = (d2-0)/x12 + (d2-d3)/x23
A = np.array([[-1/x12, -1/x13],
              [1/x12 + 1/x23, -1/x23]])
b = np.array([1.0, 0.8])
d2, d3 = np.linalg.solve(A, b)
print(f"  δ2 = {d2:.4f} rad ({np.rad2deg(d2):.2f}°)")
print(f"  δ3 = {d3:.4f} rad ({np.rad2deg(d3):.2f}°)")
P12 = (0 - d2)/x12; P13 = (0 - d3)/x13; P23 = (d2 - d3)/x23
print(f"\n  P12 = {P12:.4f} p.u.（負ならノード2→1）")
print(f"  P13 = {P13:.4f} p.u.")
print(f"  P23 = {P23:.4f} p.u.")
print(f"\n  検算 ノード1 流出 = P12 + P13 = {P12+P13:.4f}（供給 1.0 と一致）")
print(f"       ノード2 流出 = -P12 + P23 = {-P12+P23:.4f}（供給 0.8 と一致）")
print(f"       ノード3 流入 = P13 + P23 = {P13+P23:.4f}（需要 1.8 と一致）")
print("\n第4回 完了")
