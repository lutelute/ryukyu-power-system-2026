# -*- coding: utf-8 -*-
"""第5回 潮流計算の理論(2) ニュートン・ラフソン法 — スライド・ノート用の図を実計算から生成する
   python3 fig_ch05.py  → ../図/ch05_*.png
   3 母線系統は viz/newton.html と同じ（線路・指定値・電圧）。ヤコビアンは ΔV/V 形式（ノート 5.2.3）。
"""
import numpy as np
from pws_common import setup_japanese_font, savefig, build_ybus, newton_raphson, power_injection
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import LinearSegmentedColormap

# ---- 共通スタイル（スライドの terracotta パレットに合わせる）----
C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
CMAP = LinearSegmentedColormap.from_list("pws", ["#F2EFE6", C_LIGHT, C_SEC, C_MAIN])

# ---- 3 母線系統（viz/newton.html と同じ）----
LINES = [(1, 2, 0.02, 0.06, 0.030), (1, 3, 0.08, 0.24, 0.025), (2, 3, 0.06, 0.18, 0.020)]
BUS_TYPE = np.array([0, 1, 2])                      # 0=スラック, 1=PV, 2=PQ
P_SCH = np.array([0.0, 0.50, -1.00])
Q_SCH = np.array([0.0, 0.00, -0.40])
V_MAG = np.array([1.05, 1.02, 1.00])
Y3 = build_ybus(3, LINES)
TOL = 1e-8


# ============================================================ 共通の数値ルーチン
def jacobian_blocks(Ybus, V, theta, pvpq, pq):
    """ヤコビアン H, N, M, L（ΔV/V 形式。対角は P_i, Q_i で書ける）"""
    G, B = Ybus.real, Ybus.imag
    P, Q = power_injection(V, theta, Ybus)
    n1, n2 = len(pvpq), len(pq)
    H = np.zeros((n1, n1)); N = np.zeros((n1, n2)); M = np.zeros((n2, n1)); L = np.zeros((n2, n2))
    for a, i in enumerate(pvpq):
        for b, j in enumerate(pvpq):
            if i == j:
                H[a, b] = -Q[i] - B[i, i] * V[i] ** 2
            else:
                th = theta[i] - theta[j]
                H[a, b] = V[i] * V[j] * (G[i, j] * np.sin(th) - B[i, j] * np.cos(th))
        for b, j in enumerate(pq):
            if i == j:
                N[a, b] = P[i] + G[i, i] * V[i] ** 2
            else:
                th = theta[i] - theta[j]
                N[a, b] = V[i] * V[j] * (G[i, j] * np.cos(th) + B[i, j] * np.sin(th))
    for a, i in enumerate(pq):
        for b, j in enumerate(pvpq):
            if i == j:
                M[a, b] = P[i] - G[i, i] * V[i] ** 2
            else:
                th = theta[i] - theta[j]
                M[a, b] = -V[i] * V[j] * (G[i, j] * np.cos(th) + B[i, j] * np.sin(th))
        for b, j in enumerate(pq):
            if i == j:
                L[a, b] = Q[i] - B[i, i] * V[i] ** 2
            else:
                th = theta[i] - theta[j]
                L[a, b] = V[i] * V[j] * (G[i, j] * np.sin(th) - B[i, j] * np.cos(th))
    return H, N, M, L, P, Q


def nr_solve(Ybus, bus_type, P_sch, Q_sch, V0, th0, tol=TOL, max_iter=20):
    """初期値を指定できる NR 法。戻り値 (V, θ, 反復回数, 履歴, 収束したか)"""
    pv = np.where(bus_type == 1)[0]; pq = np.where(bus_type == 2)[0]
    pvpq = np.concatenate([pv, pq])
    V = np.array(V0, dtype=float); theta = np.array(th0, dtype=float); hist = []
    for it in range(max_iter + 1):
        H, N, M, L, P, Q = jacobian_blocks(Ybus, V, theta, pvpq, pq)
        mis = np.concatenate([P_sch[pvpq] - P[pvpq], Q_sch[pq] - Q[pq]])
        err = np.abs(mis).max(); hist.append(err)
        if err < tol:
            return V, theta, it, hist, True
        if it == max_iter or not np.isfinite(err) or err > 1e6:
            break
        J = np.block([[H, N], [M, L]])
        try:
            dx = np.linalg.solve(J, mis)
        except np.linalg.LinAlgError:
            break
        theta[pvpq] += dx[:len(pvpq)]
        V[pq] *= (1 + dx[len(pvpq):])
    return V, theta, it, hist, False


def gauss_seidel(Ybus, bus_type, P_sch, Q_sch, V_mag, tol=TOL, max_iter=500, accel=1.0):
    """ガウス・ザイデル法。履歴は各掃引後の最大電力ミスマッチ（NR と同じ物差し）"""
    n = len(bus_type)
    V = np.where(bus_type == 0, V_mag, 1.0).astype(complex)
    V[bus_type == 1] = V_mag[bus_type == 1]
    Q = np.array(Q_sch, dtype=float)
    pvpq = np.where(bus_type > 0)[0]; pq = np.where(bus_type == 2)[0]; hist = []
    for it in range(max_iter):
        for i in range(n):
            if bus_type[i] == 0:
                continue
            if bus_type[i] == 1:
                Q[i] = -np.imag(np.conj(V[i]) * (Ybus[i] @ V))
            s = Ybus[i] @ V - Ybus[i, i] * V[i]
            Vn = ((P_sch[i] - 1j * Q[i]) / np.conj(V[i]) - s) / Ybus[i, i]
            Vn = V[i] + accel * (Vn - V[i])
            if bus_type[i] == 1:
                Vn = V_mag[i] * Vn / abs(Vn)
            V[i] = Vn
        P, Qc = power_injection(np.abs(V), np.angle(V), Ybus)
        err = max(np.abs(P_sch[pvpq] - P[pvpq]).max(), np.abs(Q_sch[pq] - Qc[pq]).max())
        hist.append(err)
        if err < tol:
            return V, it + 1, hist
    return V, max_iter, hist


def fdlf_matrices(lines, n_bus, Ybus, pvpq, pq):
    """高速デカップル法の B′（直列 X のみ）と B″（Y_bus の虚部）"""
    Yx = build_ybus(n_bus, [(f, t, 0.0, x, 0.0) for f, t, r, x, b in lines])
    Bp = -Yx.imag[np.ix_(pvpq, pvpq)]
    Bpp = -Ybus.imag[np.ix_(pq, pq)]
    return Bp, Bpp


def fast_decoupled(Ybus, lines, n_bus, bus_type, P_sch, Q_sch, V_mag, tol=TOL, max_iter=100):
    pv = np.where(bus_type == 1)[0]; pq = np.where(bus_type == 2)[0]
    pvpq = np.concatenate([pv, pq])
    Bp, Bpp = fdlf_matrices(lines, n_bus, Ybus, pvpq, pq)
    V = np.array(V_mag, dtype=float); theta = np.zeros(n_bus); hist = []
    for it in range(max_iter + 1):
        P, Q = power_injection(V, theta, Ybus)
        dP = P_sch[pvpq] - P[pvpq]; dQ = Q_sch[pq] - Q[pq]
        err = max(np.abs(dP).max(), np.abs(dQ).max()); hist.append(err)
        if err < tol or it == max_iter:
            return V, theta, it, hist
        theta[pvpq] += np.linalg.solve(Bp, dP / V[pvpq])          # P–θ 半反復
        P, Q = power_injection(V, theta, Ybus)
        dQ = Q_sch[pq] - Q[pq]
        V[pq] += np.linalg.solve(Bpp, dQ / V[pq])                 # Q–V 半反復
    return V, theta, max_iter, hist


def iters_to(hist, tol, offset=0):
    """履歴が tol を初めて下回る反復回数（offset: GS は掃引 1 回目が index 0）"""
    for k, e in enumerate(hist):
        if e < tol:
            return k + offset
    return None


# ============================================================ 1. 1 変数ニュートン法（接線の図）
def fig_newton1d():
    f = lambda t: 5 * np.sin(t) - 0.8
    df = lambda t: 5 * np.cos(t)
    th_star = np.arcsin(0.16)
    ths = [0.0]
    for _ in range(4):
        ths.append(ths[-1] - f(ths[-1]) / df(ths[-1]))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.3), gridspec_kw={"width_ratios": [1.5, 1]})
    t = np.linspace(-0.08, 0.32, 300)
    a1.plot(t, f(t), color=C_MAIN, lw=2.4, label="f(θ) = 5 sin θ − 0.8")
    a1.axhline(0, color=C_GREY, lw=0.8)
    for k, c in [(0, C_BLUE), (1, C_WARM)]:
        tk = ths[k]; tt = np.linspace(tk - 0.02, ths[k + 1] + 0.02, 50)
        a1.plot(tt, f(tk) + df(tk) * (tt - tk), color=c, lw=1.6, ls="--", label=f"θ{k} での接線（傾き f′ = {df(tk):.3f}）")
        a1.scatter([tk], [f(tk)], color=c, s=50, zorder=4)
        a1.plot([ths[k + 1], ths[k + 1]], [0, f(ths[k + 1])], color=c, lw=0.9, ls=":")
    a1.scatter([ths[1], ths[2]], [0, 0], color=[C_BLUE, C_WARM], s=45, zorder=5)
    a1.annotate(f"θ₀ = 0\nf = {f(0):.3f}", (0, f(0)), xytext=(-0.07, -0.55), fontsize=11, color=C_BLUE)
    a1.annotate(f"θ₁ = {ths[1]:.3f}", (ths[1], 0), xytext=(0.17, 0.25), fontsize=11, color=C_BLUE,
                arrowprops=dict(arrowstyle="->", color=C_BLUE, lw=0.8))
    a1.annotate(f"f(θ₁) = {f(ths[1]):.4f}", (ths[1], f(ths[1])), xytext=(0.03, 0.12), fontsize=11, color=C_WARM,
                arrowprops=dict(arrowstyle="->", color=C_WARM, lw=0.8))
    a1.annotate(f"θ₂ = {ths[2]:.5f}\n厳密解 {th_star:.5f}", (ths[2], 0), xytext=(0.2, -0.35), fontsize=11, color=C_MAIN,
                arrowprops=dict(arrowstyle="->", color=C_MAIN, lw=0.8))
    a1.set_xlim(-0.08, 0.32); a1.set_ylim(-1.0, 0.8); a1.set_xlabel("位相角 θ [rad]"); a1.set_ylabel("残差 f(θ) = 5 sin θ − P_spec")
    a1.grid(alpha=0.3); a1.legend(frameon=False, fontsize=11, loc="upper left")
    a1.set_title("接線が 0 になる点へ跳ぶ：θ₀ = 0 → 0.160 → 0.16069", fontsize=11)
    err = [abs(x - th_star) for x in ths]
    a2.bar(range(len(err)), [max(e, 1e-17) for e in err], color=[C_BLUE, C_WARM, C_MAIN, C_MAIN, C_MAIN], width=0.6)
    a2.set_yscale("log"); a2.set_ylim(1e-17, 1)
    for k, e in enumerate(err):
        a2.text(k, max(e, 1e-17) * 3, f"{e:.1e}" if e > 1e-16 else "≈ 0", ha="center", fontsize=11)
    a2.set_xticks(range(len(err))); a2.set_xlabel("反復回数 ν"); a2.set_ylabel("誤差 |θ_ν − θ*|")
    a2.set_title("誤差の指数が 1 → 3 → 6 → 12 と倍々に減る", fontsize=11); a2.grid(axis="y", alpha=0.3)
    fig.tight_layout(); savefig(fig, "ch05_newton1d.png"); plt.close(fig)
    return ths, [f(x) for x in ths], [df(x) for x in ths], th_star


# ============================================================ 2. GS vs NR のミスマッチ履歴
def fig_gs_vs_nr():
    V_nr, th_nr, it_nr, h_nr = newton_raphson(Y3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, tol=TOL)
    res = {}
    for a in (1.0, 1.6):
        res[a] = gauss_seidel(Y3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, accel=a)
    fig, ax = plt.subplots(figsize=(8.8, 4.6))
    for a, c, m in [(1.0, C_SEC, "o"), (1.6, C_WARM, "^")]:
        V_gs, it_gs, h = res[a]
        ax.semilogy(range(1, len(h) + 1), h, marker=m, ms=4, lw=1.4, color=c,
                    label=f"ガウス・ザイデル法 α = {a}：{it_gs} 回（1 次収束）")
    ax.semilogy(range(len(h_nr)), h_nr, marker="s", ms=7, lw=2.2, color=C_MAIN,
                label=f"ニュートン・ラフソン法：{it_nr} 回（2 次収束）")
    ax.axhline(TOL, color=C_ACC, ls="--", lw=1.2); ax.text(18, TOL / 6, r"収束判定 ε = $10^{-8}$", ha="center", fontsize=11, color=C_ACC)
    for k in range(1, 4):
        ax.annotate(f"{h_nr[k]:.1e}", (k, h_nr[k]), xytext=(10, -12), textcoords="offset points", fontsize=11, color=C_MAIN, ha="left")
    ax.set_xlim(-0.5, 32); ax.set_ylim(1e-17, 3)
    ax.set_xlabel("反復回数 ν"); ax.set_ylabel("最大ミスマッチ max(|ΔP|, |ΔQ|) [p.u.]")
    ax.grid(alpha=0.3, which="both"); ax.legend(frameon=False, fontsize=11, loc="upper right")
    ax.set_title("同じ 3 母線系統：対数軸で GS は直線、NR は急降下", fontsize=11.5)
    savefig(fig, "ch05_gs_vs_nr.png"); plt.close(fig)
    return (V_nr, th_nr, it_nr, h_nr), res


# ============================================================ 3. 収束次数（e_{ν+1} vs e_ν）
def fig_order(h_nr, h_gs):
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    e = np.logspace(-9, 0.3, 50)
    ax.loglog(e, 0.3 * e, color=C_GREY, lw=1, ls=":", label=r"傾き 1（$e_{\nu+1} = \rho\, e_\nu$、1 次収束）")
    ax.loglog(e, 0.06 * e ** 2, color=C_GREY, lw=1, ls="--", label=r"傾き 2（$e_{\nu+1} = C\, e_\nu^2$、2 次収束）")
    g = np.array(h_gs); g = g[g > 1e-14]
    ax.loglog(g[:-1], g[1:], "o", ms=4, color=C_SEC, label="ガウス・ザイデル法（α = 1.0）")
    n = np.array(h_nr); n = n[n > 1e-14]
    ax.loglog(n[:-1], n[1:], "s", ms=8, color=C_MAIN, label="ニュートン・ラフソン法")
    for k in range(len(n) - 1):
        ax.annotate(f"ν = {k}→{k+1}", (n[k], n[k + 1]), xytext=(8, -12), textcoords="offset points", fontsize=11, color=C_MAIN)
    ax.set_xlim(1e-9, 2); ax.set_ylim(1e-17, 1)
    ax.set_xlabel(r"今回の誤差 $e_\nu$（最大ミスマッチ）"); ax.set_ylabel(r"次回の誤差 $e_{\nu+1}$")
    ax.grid(alpha=0.3, which="both"); ax.legend(frameon=False, fontsize=11, loc="upper left")
    savefig(fig, "ch05_order.png"); plt.close(fig)


# ============================================================ 4. case14 のヤコビアン（H N M L のヒートマップ）
def fig_jacobian_blocks():
    import pandapower as pp
    import pandapower.networks as pn
    net = pn.case14(); pp.runpp(net, numba=False)
    ppci = net._ppc["internal"]
    Ybus = ppci["Ybus"].toarray(); Vc = ppci["V"]
    pv = np.array(ppci["pv"], dtype=int); pq = np.array(ppci["pq"], dtype=int)
    pvpq = np.concatenate([pv, pq])
    H, N, M, L, P, Q = jacobian_blocks(Ybus, np.abs(Vc), np.angle(Vc), pvpq, pq)
    J = np.block([[H, N], [M, L]])
    n1, n2 = len(pvpq), len(pq)
    fn = lambda A: np.linalg.norm(A, "fro")
    norms = dict(H=fn(H), N=fn(N), M=fn(M), L=fn(L))
    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    im = ax.imshow(np.abs(J), cmap=CMAP, vmin=0, vmax=np.percentile(np.abs(J)[np.abs(J) > 0], 97))
    ax.axhline(n1 - 0.5, color="#1A1A17", lw=1.4); ax.axvline(n1 - 0.5, color="#1A1A17", lw=1.4)
    for (r, c, name, key) in [(n1 / 2, n1 / 2, "H = ∂P/∂θ", "H"), (n1 / 2, n1 + n2 / 2, "N = V∂P/∂V", "N"),
                              (n1 + n2 / 2, n1 / 2, "M = ∂Q/∂θ", "M"), (n1 + n2 / 2, n1 + n2 / 2, "L = V∂Q/∂V", "L")]:
        ax.text(c - 0.5, r - 0.5, f"{name}\n‖·‖ = {norms[key]:.1f}", ha="center", va="center", fontsize=11, weight="bold",
                color="#1A1A17", bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="none", alpha=0.75))
    ax.set_xticks([n1 / 2 - 0.5, n1 + n2 / 2 - 0.5]); ax.set_xticklabels([f"Δθ（{n1} 列）", f"ΔV/V（{n2} 列）"])
    ax.set_yticks([n1 / 2 - 0.5, n1 + n2 / 2 - 0.5]); ax.set_yticklabels([f"ΔP\n（{n1} 行）", f"ΔQ\n（{n2} 行）"])
    ax.tick_params(length=0)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label("|要素| [p.u.]")
    nz = (np.abs(J) > 1e-9).sum()
    ax.set_title(f"IEEE 14 母線のヤコビアン {J.shape[0]}×{J.shape[1]}（非零 {nz/J.size*100:.0f}%）：対角ブロック H, L が濃い", fontsize=11)
    savefig(fig, "ch05_jacobian_blocks.png"); plt.close(fig)
    return norms, J.shape, nz / J.size, n1, n2, len(pv), len(pq)


# ============================================================ 5. ‖N‖/‖H‖, ‖M‖/‖L‖ vs X/R
def fig_xr_ratio():
    ratios = np.linspace(1.0, 15.0, 29)
    rN, rM = [], []
    pvpq = np.array([1, 2]); pq = np.array([2])
    for rho in ratios:
        ln = [(f, t, x / rho, x, b) for f, t, r, x, b in LINES]
        Y = build_ybus(3, ln)
        V, th, it, h = newton_raphson(Y, BUS_TYPE, P_SCH, Q_SCH, V_MAG, tol=TOL)
        H, N, M, L, P, Q = jacobian_blocks(Y, V, th, pvpq, pq)
        fn = lambda A: np.linalg.norm(A, "fro")
        rN.append(fn(N) / fn(H)); rM.append(fn(M) / fn(L))
    rN, rM = np.array(rN), np.array(rM)
    fig, ax = plt.subplots(figsize=(8.6, 4.5))
    ax.axvspan(1, 2, color=C_WARM, alpha=0.12); ax.text(1.5, 0.62, "配電線\nR ≈ X", ha="center", fontsize=11, color=C_WARM)
    ax.axvspan(5, 15, color=C_SEC, alpha=0.10); ax.text(10, 0.46, "架空送電線 X/R = 5〜15", ha="center", fontsize=11, color=C_SEC)
    ax.plot(ratios, rN, color=C_MAIN, lw=2.2, marker="o", ms=4)
    ax.plot(ratios, rM, color=C_BLUE, lw=2.2, marker="s", ms=4)
    ax.text(15.3, rN[-1], "‖N‖/‖H‖\n（∂P/∂V の相対的な大きさ）", ha="left", va="center", fontsize=11, color=C_MAIN)
    ax.text(15.3, rM[-1], "‖M‖/‖L‖\n（∂Q/∂θ の相対的な大きさ）", ha="left", va="center", fontsize=11, color=C_BLUE)
    k3 = np.argmin(abs(ratios - 3)); k10 = np.argmin(abs(ratios - 10))
    for k, dx in [(k3, 0.4), (k10, 0.4)]:
        ax.scatter([ratios[k]] * 2, [rN[k], rM[k]], color=[C_MAIN, C_BLUE], s=60, zorder=4)
        ax.annotate(f"X/R = {ratios[k]:.0f}：{rN[k]:.2f} / {rM[k]:.2f}", (ratios[k], max(rN[k], rM[k])),
                    xytext=(ratios[k] + dx, max(rN[k], rM[k]) + 0.10), fontsize=11, color="#1A1A17")
    ax.axhline(0.1, color=C_GREY, lw=0.9, ls=":"); ax.text(14.9, 0.115, "0.1", ha="right", fontsize=11, color=C_GREY)
    ax.set_xlim(1, 15); ax.set_ylim(0, 0.7); ax.set_xlabel("線路の X/R 比"); ax.set_ylabel("非対角ブロックの相対ノルム")
    ax.grid(alpha=0.3)
    ax.set_title("X ≫ R ほど N, M が小さい：高速デカップル法が効く条件（3 母線系統）", fontsize=11.5)
    fig.subplots_adjust(right=0.66)          # 右端の直接ラベルの場所をあける
    savefig(fig, "ch05_xr_ratio.png"); plt.close(fig)
    return ratios[k3], rN[k3], rM[k3], ratios[k10], rN[k10], rM[k10]


# ============================================================ 6. 高速デカップル法のフロー（NR との対比）
def fig_fdlf_flow(it_nr, it_fd):
    fig, ax = plt.subplots(figsize=(10, 5.2)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5.2)

    def box(x, y, w, h, text, fc="#F2EFE6", ec=C_MAIN, fs=9.5, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", fc=fc, ec=ec, lw=1.4))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color="#1A1A17", weight=weight)

    def arrow(p, q, color=C_GREY, style="-|>", cs="arc3,rad=0"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, color=color, lw=1.3, connectionstyle=cs))

    # ---- 左：ニュートン・ラフソン法
    ax.text(2.3, 5.0, f"ニュートン・ラフソン法（この系統 {it_nr} 回）", ha="center", fontsize=11.5, weight="bold", color=C_MAIN)
    box(0.5, 4.05, 3.4, 0.55, "初期値 V = 1, θ = 0（フラットスタート）")
    box(0.5, 3.2, 3.4, 0.55, "ミスマッチ ΔP, ΔQ を計算")
    box(0.5, 2.35, 3.4, 0.55, "ヤコビアン J を作り直す（毎回）", fc="#E8C9C3", ec=C_ACC)
    box(0.5, 1.5, 3.4, 0.55, "J Δx = Δf を LU 分解して解く（毎回）", fc="#E8C9C3", ec=C_ACC)
    box(0.5, 0.65, 3.4, 0.55, "θ += Δθ,  V *= (1 + ΔV/V)")
    for y in (4.05, 3.2, 2.35, 1.5):
        arrow((2.2, y), (2.2, y - 0.3))
    arrow((3.9, 0.92), (3.9, 3.47), cs="arc3,rad=-0.4")
    ax.text(4.65, 2.2, "収束まで\n3〜5 回", ha="left", va="center", fontsize=11, color=C_GREY)
    # ---- 右：高速デカップル法
    ax.text(7.5, 5.0, f"高速デカップル法（この系統 {it_fd} 回）", ha="center", fontsize=11.5, weight="bold", color=C_SEC)
    box(5.6, 4.05, 3.6, 0.55, "B′, B″ を 1 回だけ作り LU 分解（定数）", fc="#DCE6E1", ec=C_SEC, weight="bold")
    box(5.6, 3.2, 3.6, 0.55, "B′ Δθ = ΔP/V を代入だけで解く")
    box(5.6, 2.35, 3.6, 0.55, "θ += Δθ")
    box(5.6, 1.5, 3.6, 0.55, "B″ ΔV = ΔQ/V を代入だけで解く")
    box(5.6, 0.65, 3.6, 0.55, "V += ΔV → 判定 max(|ΔP|, |ΔQ|) < ε")
    for y in (4.05, 3.2, 2.35, 1.5):
        arrow((7.4, y), (7.4, y - 0.3))
    arrow((9.2, 0.92), (9.2, 3.47), cs="arc3,rad=-0.4", color=C_SEC)
    ax.text(9.35, 2.2, "収束まで\n10〜20 回\n（1 回が軽い）", ha="left", va="center", fontsize=11, color=C_SEC)
    ax.text(5.0, 0.15, "赤の箱＝毎回やり直す重い処理。高速デカップル法はそれを 1 回で済ませ、反復は代入だけにする",
            ha="center", fontsize=11, color=C_GREY)
    savefig(fig, "ch05_fdlf_flow.png"); plt.close(fig)


# ============================================================ 7. 収束判定閾値と反復回数
def fig_tolerance():
    tols = np.logspace(-2, -12, 11)
    _, _, _, h_nr = newton_raphson(Y3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, tol=1e-14, max_iter=20)
    _, _, h_gs = gauss_seidel(Y3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, tol=1e-13, max_iter=1000)
    _, _, _, h_fd = fast_decoupled(Y3, LINES, 3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, tol=1e-13, max_iter=300)
    n_nr = [iters_to(h_nr, t, 0) for t in tols]
    n_gs = [iters_to(h_gs, t, 1) for t in tols]
    n_fd = [iters_to(h_fd, t, 0) for t in tols]
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    ax.plot(tols, n_gs, marker="o", ms=5, lw=1.8, color=C_SEC, label="ガウス・ザイデル法（α = 1.0）")
    ax.plot(tols, n_fd, marker="^", ms=6, lw=1.8, color=C_BLUE, label="高速デカップル法")
    ax.plot(tols, n_nr, marker="s", ms=7, lw=2.4, color=C_MAIN, label="ニュートン・ラフソン法")
    ax.set_xscale("log"); ax.invert_xaxis()
    for t, n in zip(tols[::2], n_nr[::2]):
        ax.text(t, n - 1.3, str(n), ha="center", fontsize=11, color=C_MAIN, weight="bold")
    ax.axvline(1e-6, color=C_GREY, lw=0.9, ls=":"); ax.text(1e-6, 1.0, r"既定 ε = $10^{-6}$", ha="center", va="bottom", fontsize=11, color=C_GREY)
    ax.set_xlabel("収束判定閾値 ε（右へ行くほど厳しい）"); ax.set_ylabel("必要な反復回数")
    ax.set_ylim(0, max(n_gs) + 3); ax.grid(alpha=0.3, which="both"); ax.legend(frameon=False, fontsize=11, loc="upper left")
    ax.set_title(r"ε を $10^{-2}$ から $10^{-12}$ に厳しくしても、NR 法は数回しか増えない", fontsize=11.5)
    savefig(fig, "ch05_tolerance.png"); plt.close(fig)
    return tols, n_nr, n_gs, n_fd


# ============================================================ 8. PV 母線の Q 限界
def fig_qlimit(q_max=0.30):
    # 左：母線 2 の Q–V 曲線（電圧指定値を保つのに必要な Q）
    vset = np.linspace(0.96, 1.08, 25)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4))
    for k, c in [(1.0, C_SEC), (1.5, C_BLUE), (2.0, C_MAIN)]:
        qs = []
        for v in vset:
            Vm = V_MAG.copy(); Vm[1] = v
            V, th, it, h = newton_raphson(Y3, BUS_TYPE, P_SCH * np.array([1, 1, k]), Q_SCH * np.array([1, 1, k]), Vm, tol=TOL)
            P, Q = power_injection(V, th, Y3); qs.append(Q[1])
        a1.plot(vset, qs, color=c, lw=2, label=f"負荷 {k:.1f} 倍")
    a1.axhline(q_max, color=C_ACC, ls="--", lw=1.4); a1.text(0.962, q_max + 0.02, f"Q_max = {q_max:.2f} p.u.", fontsize=11, color=C_ACC)
    a1.axvline(1.02, color=C_GREY, lw=0.9, ls=":"); a1.text(1.021, -0.55, "指定 V₂ = 1.02", fontsize=11, color=C_GREY)
    a1.set_xlabel("母線 2 の電圧指定値 V₂ [p.u.]"); a1.set_ylabel("必要な無効電力 Q₂ [p.u.]")
    a1.set_xlim(0.96, 1.08); a1.grid(alpha=0.3); a1.legend(frameon=False, fontsize=11, loc="upper left")
    a1.set_title("Q–V 曲線：電圧を上げるほど、負荷が重いほど Q が要る", fontsize=12)
    # 右：負荷を増やすと Q₂ が上限に当たり、PV → PQ に切り替わって V₂ が下がる
    ks = np.linspace(0.5, 2.4, 39); q2, v2, switched = [], [], []
    k_sw = None
    for k in ks:
        Ps, Qs = P_SCH * np.array([1, 1, k]), Q_SCH * np.array([1, 1, k])
        V, th, it, h = newton_raphson(Y3, BUS_TYPE, Ps, Qs, V_MAG, tol=TOL)
        P, Q = power_injection(V, th, Y3)
        if Q[1] <= q_max:
            q2.append(Q[1]); v2.append(V[1]); switched.append(False)
        else:                                   # Q 限界違反 → Q₂ を上限に固定して PQ 母線として解き直す
            if k_sw is None:
                k_sw = k
            bt = np.array([0, 2, 2]); Qs2 = Qs.copy(); Qs2[1] = q_max
            V, th, it, h = newton_raphson(Y3, bt, Ps, Qs2, V_MAG, tol=TOL)
            q2.append(q_max); v2.append(V[1]); switched.append(True)
    q2, v2, switched = np.array(q2), np.array(v2), np.array(switched)
    a2.plot(ks, q2, color=C_MAIN, lw=2.2, label="Q₂（発電機の無効電力出力）")
    a2.axhline(q_max, color=C_ACC, ls="--", lw=1.2)
    a2.set_xlabel("母線 3 の負荷倍率"); a2.set_ylabel("Q₂ [p.u.]", color=C_MAIN); a2.set_ylim(-0.6, 0.5)
    a3 = a2.twinx(); a3.plot(ks, v2, color=C_BLUE, lw=2.2, label="V₂（母線 2 の電圧）"); a3.set_ylabel("V₂ [p.u.]", color=C_BLUE)
    a3.set_ylim(0.90, 1.05); a3.spines["right"].set_visible(True)
    if k_sw is not None:
        a2.axvspan(k_sw, ks[-1], color=C_LIGHT, alpha=0.5)
        a2.text((k_sw + ks[-1]) / 2, 0.42, "PQ に切替\n（V₂ を保てない）", ha="center", fontsize=11, color="#1A1A17")
        a2.text((0.5 + k_sw) / 2, 0.42, "PV 母線（V₂ = 1.02 一定）", ha="center", fontsize=11, color="#1A1A17")
        a2.axvline(k_sw, color=C_ACC, lw=1)
    h1, l1 = a2.get_legend_handles_labels(); h2, l2 = a3.get_legend_handles_labels()
    a2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=11, loc="lower left"); a2.grid(alpha=0.3)
    a2.set_title("負荷を増やすと Q₂ が上限に当たり、電圧が落ち始める", fontsize=12)
    fig.tight_layout(); savefig(fig, "ch05_qlimit.png"); plt.close(fig)
    return k_sw, v2[-1], ks[-1]


# ============================================================ 9. 初期値の良し悪しと収束
def fig_initial_guess():
    f = lambda t: 5 * np.sin(t) - 0.8
    df = lambda t: 5 * np.cos(t)
    th_star = np.arcsin(0.16)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw={"width_ratios": [1, 1.15]})
    # 左：1 変数。出発点 θ₀ ごとに「どの解に着くか」と「何回かかるか」
    t0s = np.linspace(-3.0, 6.0, 361); roots, its = [], []
    for t0 in t0s:
        x = t0; n = None
        for k in range(60):
            if abs(f(x)) < 1e-10:
                n = k; break
            if abs(df(x)) < 1e-12:
                break
            x = x - f(x) / df(x)
        roots.append(x if n is not None else np.nan); its.append(n if n is not None else np.nan)
    roots, its = np.array(roots), np.array(its)
    near = np.isclose(roots, th_star, atol=1e-6)
    a1.scatter(t0s[near], its[near], s=9, color=C_MAIN, label=f"θ* = {th_star:.4f}（求めたい解）に着く")
    a1.scatter(t0s[~near], its[~near], s=9, color=C_WARM, label="別の解（θ* + 2πk, π − θ* …）に着く")
    a1.axvspan(-0.5, 0.8, color=C_SEC, alpha=0.12); a1.text(0.15, 20.5, "フラットスタート\nθ₀ = 0 の近傍", ha="center", fontsize=11, color=C_SEC)
    for x in (np.pi / 2, -np.pi / 2, 3 * np.pi / 2):
        a1.axvline(x, color=C_GREY, lw=0.8, ls=":")
    a1.text(np.pi / 2 + 0.15, 13.5, "f′ = 0（接線が水平）\n→ 跳び先が遠くへ飛ぶ", fontsize=11, color=C_GREY)
    a1.set_xlim(-3, 6); a1.set_ylim(0, 30); a1.set_xlabel("出発点 θ₀ [rad]"); a1.set_ylabel("収束までの反復回数")
    a1.grid(alpha=0.3); a1.legend(frameon=False, fontsize=11, loc="upper left")
    a1.set_title("1 変数：遠い出発点は別の解へ跳ぶ", fontsize=12)
    # 右：3 母線。初期値 (V₃⁰, θ⁰) ごとの NR 反復回数
    v0s = np.linspace(0.2, 1.8, 33); t0s2 = np.deg2rad(np.linspace(-150, 150, 31))
    grid = np.full((len(v0s), len(t0s2)), np.nan)
    V_ref, th_ref, _, _, _ = nr_solve(Y3, BUS_TYPE, P_SCH, Q_SCH, V_MAG, np.zeros(3))
    for i, v0 in enumerate(v0s):
        for j, t0 in enumerate(t0s2):
            V0 = V_MAG.copy(); V0[2] = v0; th0 = np.array([0.0, t0, t0])
            V, th, it, h, ok = nr_solve(Y3, BUS_TYPE, P_SCH, Q_SCH, V0, th0, max_iter=25)
            if ok and abs(V[2] - V_ref[2]) < 1e-4 and abs(th[2] - th_ref[2]) < 1e-4:
                grid[i, j] = it
    im = a2.imshow(grid, origin="lower", aspect="auto", cmap=CMAP, vmin=2, vmax=12,
                   extent=[np.rad2deg(t0s2[0]), np.rad2deg(t0s2[-1]), v0s[0], v0s[-1]])
    a2.set_facecolor("#1A1A17")
    a2.scatter([0], [1.0], marker="*", s=180, color="white", edgecolor=C_MAIN, zorder=5)
    a2.text(8, 1.04, "フラットスタート", fontsize=11, color="white")
    cb = fig.colorbar(im, ax=a2, fraction=0.045, pad=0.02); cb.set_label("反復回数（黒＝正しい解に着かない）")
    a2.set_xlabel("初期位相 θ₂⁰ = θ₃⁰ [deg]"); a2.set_ylabel("初期電圧 V₃⁰ [p.u.]")
    a2.set_title("3 母線：正常運転の解は 1.0∠0° のすぐ近くにある", fontsize=12)
    fig.tight_layout(); savefig(fig, "ch05_initial_guess.png"); plt.close(fig)
    ok_frac = np.isfinite(grid).mean()
    return ok_frac, np.nanmax(grid), float(np.nanmin(grid))


# ============================================================ 10. 例題用：フラットスタートの 1 反復（3 母線）
def first_iteration():
    pvpq = np.array([1, 2]); pq = np.array([2])
    V = V_MAG.copy(); th = np.zeros(3)
    H, N, M, L, P, Q = jacobian_blocks(Y3, V, th, pvpq, pq)
    mis = np.concatenate([P_SCH[pvpq] - P[pvpq], Q_SCH[pq] - Q[pq]])
    J = np.block([[H, N], [M, L]]); dx = np.linalg.solve(J, mis)
    Bp, Bpp = fdlf_matrices(LINES, 3, Y3, pvpq, pq)
    return P, Q, mis, H, N, M, L, dx, Bp, Bpp


# ==================================================== 11. たとえ話の対応表
from pws_eqfig import analogy_figure, derivation_figure


def fig_analogy():
    analogy_figure("ch05_analogy.png",
        left_title="霧の坂道（たとえ）", right_title="ニュートン・ラフソン法（実物）",
        pairs=[("見えるのは足元の傾きだけ", "傾き＝ヤコビアン（1 階微分）"),
               ("傾きの方向へ、傾きが急なら大きく進む", r"修正量 $\Delta x = -J^{-1} f(x)$"),
               ("谷底に近づくほど歩幅は自然に小さくなる", "誤差が 2 乗で縮む（2 次収束）"),
               ("手探りで一歩ずつ下りるやり方もある", "手探り＝ガウス・ザイデル法（遅い）"),
               ("出発点が悪いと隣の谷へ行く", "出発点＝フラットスタート（V=1、θ=0）")],
        note="この対応が頭に入っていれば、式は全部「谷を下る話」に翻訳できる。")


# ==================================================== 12. よくある誤解
def fig_myth():
    analogy_figure("ch05_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("母線が増えれば NR 法の反復回数も増える",
                "NR 法の回数は規模によらず 3〜5 回。母線数は式に出てこない"),
               ("収束判定を厳しくすると反復が何倍にもなる",
                r"2 次収束なので ε を $10^{-2}$ から" + "\n" + r"$10^{-12}$ にしても 2 → 4 回しか増えない"),
               ("潮流計算が収束しないのはプログラムのバグ",
                "収束しないのは「解が存在しない」（電圧崩壊に近い）か初期値が悪いせいかもしれない")],
        note="どれも「反復回数を決めているのは何か」を取り違えたことから来ている。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch05_deriv_quad_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① テイラー展開で 1 次まで取る',
                r"$f(x+\Delta x) \approx f(x) + f'(x)\,\Delta x$",
                '2 次以降を捨てると f′Δx = −f。\n多変数では f′ が行列 J になる'),
               ('② 捨てた項が、そのまま次の誤差になる',
                r"$e_{n+1} \approx \dfrac{f''}{2f'}\,e_n^{2}$",
                '1 次の項は接線で消え、残るのは\n誤差の 2 乗に比例する項だけ'),
               ('③ 桁が倍々に増える',
                r"$10^{-2} \to 10^{-4} \to 10^{-8} \to 10^{-16}$",
                '1e-8 まで 4 回、1e-16 でも 5 回。\n母線数は式に出てこない')],
            result='規模によらず 3〜5 回で収束する。これが 2 次収束の正体')

    for i in (1, 2, 3):
        derivation_figure(f"ch05_deriv_jacobian_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 何を何で微分するか',
                r"$H = \dfrac{\partial P}{\partial \theta}, \quad L = V\dfrac{\partial Q}{\partial V}$",
                '未知数は (θ, V)、式は (ΔP, ΔQ)。\n4 つのブロック H, N, M, L に分かれる'),
               ('② 非対角（i ≠ j）',
                r"$H_{ij} = V_iV_j\,(G_{ij}\sin\theta_{ij} - B_{ij}\cos\theta_{ij})$",
                '∂θ_ij/∂θ_j = −1 なので、出てくるのは\nQ_i の j 番目の項そのもの'),
               ('③ 対角（i = j）',
                r"$H_{ii} = -Q_i - B_{ii}V_i^{2}, \quad L_{ii} = Q_i - B_{ii}V_i^{2}$",
                '対角は P_i, Q_i で書ける。ミスマッチ計算の\n値をそのまま使い回せる')],
            result='ヤコビアンは新しい計算ではなく、潮流の式を微分しただけ')


if __name__ == "__main__":
    ths, fs, dfs, th_star = fig_newton1d()
    (V_nr, th_nr, it_nr, h_nr), gs = fig_gs_vs_nr()
    fig_order(h_nr, gs[1.0][2])
    norms, shape, dens, n1, n2, npv, npq = fig_jacobian_blocks()
    x3, rN3, rM3, x10, rN10, rM10 = fig_xr_ratio()
    V_fd, th_fd, it_fd, h_fd = fast_decoupled(Y3, LINES, 3, BUS_TYPE, P_SCH, Q_SCH, V_MAG)
    fig_fdlf_flow(it_nr, it_fd)
    tols, n_nr, n_gs, n_fd = fig_tolerance()
    k_sw, v2_end, k_end = fig_qlimit()
    ok_frac, it_max, it_min = fig_initial_guess()
    P0, Q0, mis0, H0, N0, M0, L0, dx0, Bp, Bpp = first_iteration()
    fig_analogy(); fig_myth()
    fig_derivations()

    print("\n==== 主要な数値（スライドはこの値を使う）====")
    print("[1 変数] f(θ) = 5 sin θ − 0.8, θ₀ = 0")
    for k in range(3):
        print(f"  ν={k}: θ = {ths[k]:.5f}, f = {fs[k]:.5f}, f′ = {dfs[k]:.4f} → θ_{k+1} = {ths[k+1]:.5f}, 誤差 {abs(ths[k]-th_star):.2e}")
    print(f"  厳密解 asin(0.16) = {th_star:.6f}")
    print(f"[3 母線 NR] {it_nr} 回。履歴 " + " → ".join(f"{e:.2e}" for e in h_nr))
    print(f"  解 |V| = {np.round(V_nr, 5)}, θ = {np.round(np.rad2deg(th_nr), 3)} deg, P1 = {power_injection(V_nr, th_nr, Y3)[0][0]:.4f}, Q2 = {power_injection(V_nr, th_nr, Y3)[1][1]:.4f}")
    for a in (1.0, 1.6):
        print(f"[3 母線 GS α={a}] {gs[a][1]} 回（最大ミスマッチ < 1e-8）")
    print(f"[3 母線 FDLF] {it_fd} 回。履歴先頭 " + " → ".join(f"{e:.2e}" for e in h_fd[:6]))
    print(f"[フラットスタートの 1 反復] P = {np.round(P0, 4)}, Q = {np.round(Q0, 4)}")
    print(f"  ミスマッチ [ΔP2, ΔP3, ΔQ3] = {np.round(mis0, 4)}")
    print(f"  H = {np.round(H0, 3).tolist()}, N = {np.round(N0, 3).tolist()}, M = {np.round(M0, 3).tolist()}, L = {np.round(L0, 3).tolist()}")
    print(f"  修正量 [Δθ2, Δθ3, ΔV3/V3] = {np.round(dx0, 4)} → θ2 = {np.rad2deg(dx0[0]):.3f}°, θ3 = {np.rad2deg(dx0[1]):.3f}°, V3 = {1 + dx0[2]:.4f}")
    print(f"  B′ = {np.round(Bp, 3).tolist()}, B″ = {np.round(Bpp, 3).tolist()}")
    print(f"[case14 ヤコビアン] {shape[0]}×{shape[1]}（PV {npv}, PQ {npq}）, 非零 {dens*100:.0f}%, "
          f"‖H‖ = {norms['H']:.1f}, ‖N‖ = {norms['N']:.1f}, ‖M‖ = {norms['M']:.1f}, ‖L‖ = {norms['L']:.1f}, "
          f"‖N‖/‖H‖ = {norms['N']/norms['H']:.2f}, ‖M‖/‖L‖ = {norms['M']/norms['L']:.2f}")
    print(f"[X/R] X/R={x3:.0f}: ‖N‖/‖H‖ = {rN3:.2f}, ‖M‖/‖L‖ = {rM3:.2f} ／ X/R={x10:.0f}: {rN10:.2f}, {rM10:.2f}")
    print("[閾値と反復回数] ε: " + ", ".join(f"1e{int(np.log10(t))}" for t in tols))
    print("  NR  : " + ", ".join(str(n) for n in n_nr))
    print("  GS  : " + ", ".join(str(n) for n in n_gs))
    print("  FDLF: " + ", ".join(str(n) for n in n_fd))
    print(f"[Q 限界] Q_max = 0.30 で負荷 {k_sw:.2f} 倍から PQ に切替。負荷 {k_end:.1f} 倍で V2 = {v2_end:.4f}")
    k_last = None
    for k in np.arange(2.0, 3.0, 0.05):                 # Q₂ を上限に固定したまま負荷を増やし、解が無くなる点を探す
        Ps, Qs = P_SCH * np.array([1, 1, k]), np.array([0.0, 0.30, -0.40 * k])
        _, _, it, h = newton_raphson(Y3, np.array([0, 2, 2]), Ps, Qs, V_MAG, tol=TOL, max_iter=30)
        if h[-1] < TOL:
            k_last = k
        else:
            break
    print(f"  Q₂ = 0.30 固定で NR が収束する最大負荷 ≈ {k_last:.2f} 倍（それ以上は解が無く、収束しない）")
    print(f"[初期値] 3 母線グリッドで正しい解に着く割合 {ok_frac*100:.0f}%、反復 {it_min:.0f}〜{it_max:.0f} 回")
