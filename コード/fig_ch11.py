# -*- coding: utf-8 -*-
"""第11回 電力需要予測（統計的手法）— スライド・ノート用の図を実計算から生成する
   python3 fig_ch11.py  → ../図/ch11_*.png
   需要データは pws_common.make_okinawa_demand（2 年・1 時間刻み）を使い、
   分解・度日・重回帰・評価指標・時系列分割をすべて実データで計算する。
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
from pws_common import setup_japanese_font, savefig, make_okinawa_demand, thi_index
from pws_eqfig import analogy_figure, derivation_figure
plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch, Rectangle

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": C_GREY, "axes.labelcolor": "#1A1A17", "figure.dpi": 100})
OUT = {}

DF = make_okinawa_demand()
if hasattr(DF, "columns"):
    COLS = list(DF.columns)
else:
    COLS = None


def get(col, alt=None):
    if COLS is None:
        return None
    for c in [col] + (alt or []):
        if c in COLS:
            return np.asarray(DF[c].values, dtype=float)
    return None


T_IDX = DF.index if hasattr(DF, "index") else None
Y = get("demand", ["demand_mw", "load_mw", "P"])
TA = get("temp", ["temp_c", "temperature", "T"])
RH = get("humidity", ["rh", "RH", "humid"])
HOUR = np.array([t.hour for t in T_IDX], dtype=float)
DOW = np.array([t.dayofweek for t in T_IDX], dtype=float)
DOY = np.array([t.dayofyear for t in T_IDX], dtype=float)
WEEKDAY = (DOW < 5).astype(float)


# ============================================================ 1. 需要の分解
def fig_decompose():
    n = len(Y)
    days = n // 24
    daily = Y[:days * 24].reshape(days, 24).mean(axis=1)
    # savefig() はこの図をスライドの箱（高さ約 68%）に合わせて縮めてから保存する。
    # pt 指定のタイトル・目盛りは縮小後もそのままの大きさなので、通常より広めの
    # pad / h_pad を明示して、縮小後に隣の段と競合しないよう先に余白を確保しておく
    fig, axes = plt.subplots(4, 1, figsize=(9.6, 6.2), sharex=False)
    # 縦長の日本語 ylabel（例:「日平均 [MW]」）は回転すると 1 段の高さを超えて
    # 上端で欠ける。単位だけ「MW」に絞り、内容はタイトル側にすでに書いてあるものを使う
    axes[0].plot(np.arange(days) / 365.25, daily, color=C_MAIN, lw=1.0)
    axes[0].set_ylabel("MW")
    axes[0].set_title("① 2 年分の日平均需要（年周期がはっきり見える）", fontsize=11, loc="left")
    axes[0].grid(alpha=0.3)  # xlabel は直下の②と共通なので②側にだけ付ける
    w = 365
    trend = np.convolve(daily, np.ones(w) / w, mode="same")
    axes[1].plot(np.arange(days) / 365.25, daily - trend, color=C_SEC, lw=1.0)
    axes[1].set_ylabel("MW"); axes[1].set_xlabel("経過年数"); axes[1].grid(alpha=0.3)
    axes[1].set_title("② トレンドを引いた残り（夏と冬に山）", fontsize=11, loc="left")
    wk = np.array([daily[i::7].mean() for i in range(7)])
    axes[2].bar(["月", "火", "水", "木", "金", "土", "日"], wk - wk.mean(), color=C_WARM)
    axes[2].set_ylabel("MW"); axes[2].grid(alpha=0.3, axis="y")
    axes[2].set_title("③ 曜日ごとの平均のずれ（休日は低い）", fontsize=11, loc="left")
    prof = Y[:days * 24].reshape(days, 24)
    axes[3].plot(range(24), prof.mean(axis=0), color=C_ACC, lw=2.4)
    axes[3].fill_between(range(24), np.percentile(prof, 10, axis=0), np.percentile(prof, 90, axis=0),
                         color=C_ACC, alpha=0.18)
    axes[3].set_ylabel("MW"); axes[3].set_xlabel("時刻 [h]"); axes[3].grid(alpha=0.3)
    axes[3].set_xticks(range(0, 24, 3))
    axes[3].set_title("④ 時刻ごとの平均（帯は 10〜90 パーセンタイル）", fontsize=11, loc="left")
    for ax in axes:
        # 縮小後は 1 段の高さが目盛り数字 2 個ぶんも無く、間引いても数字同士が重なる。
        # 具体的な MW 値は横の fs-points（平均・最大・差）に書いてあるので、
        # ここでは目盛りの数字は消し、山の形（グリッド線）だけを見せる
        ax.tick_params(axis="y", labelleft=False)
    # savefig() での縮小率（このボックスだと約 0.68 倍）のぶん、pt 指定のフォントは
    # 縮小後に見かけ上ふくらむ。その分を見込んで pad を通常よりかなり広めに取る
    fig.tight_layout(pad=1.6, h_pad=2.0)
    savefig(fig, "ch11_decompose.png"); plt.close(fig)
    OUT["mean"], OUT["peak"] = Y.mean(), Y.max()
    OUT["wk_gap"] = wk[:5].mean() - wk[5:].mean()


# ============================================================ 2. 需要と気温（V 字）
def fig_temp_scatter():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.3))
    mask = (HOUR >= 9) & (HOUR <= 21)
    a1.scatter(TA[mask], Y[mask], s=3, alpha=0.15, color=C_SEC)
    bins = np.arange(np.floor(TA.min()), np.ceil(TA.max()) + 1, 1.0)
    cent, med = [], []
    for b in bins[:-1]:
        m = mask & (TA >= b) & (TA < b + 1)
        if m.sum() > 20:
            cent.append(b + 0.5); med.append(np.median(Y[m]))
    a1.plot(cent, med, "o-", color=C_MAIN, lw=2.4, ms=5, label="1 °C ごとの中央値")
    a1.set_xlabel("気温 [°C]"); a1.set_ylabel("需要 [MW]（9〜21 時）")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False)
    a1.set_title("需要と気温は V 字（冷房と暖房）", fontsize=11)
    # 基準温度の探索
    T0s = np.arange(14, 27, 0.5)
    r2 = []
    for T0 in T0s:
        cdd = np.maximum(TA - T0, 0); hdd = np.maximum(T0 - TA, 0)
        X = np.column_stack([np.ones_like(Y), cdd, hdd, WEEKDAY])
        beta, *_ = np.linalg.lstsq(X, Y, rcond=None)
        pred = X @ beta
        r2.append(1 - ((Y - pred) ** 2).sum() / ((Y - Y.mean()) ** 2).sum())
    r2 = np.array(r2)
    best = T0s[int(np.argmax(r2))]
    a2.plot(T0s, r2, "o-", color=C_MAIN, lw=2.2, ms=4)
    a2.scatter([best], [r2.max()], color=C_ACC, s=90, zorder=5)
    a2.annotate(f"最適 T₀ = {best:.1f} °C\nR² = {r2.max():.3f}", (best, r2.max()),
                xytext=(best - 5.5, r2.max() - 0.06), fontsize=11.5, color=C_ACC,
                arrowprops=dict(arrowstyle="->", color=C_GREY))
    a2.set_xlabel("度日の基準温度 T₀ [°C]"); a2.set_ylabel("決定係数 R²")
    a2.grid(alpha=0.3)
    fig.tight_layout(); savefig(fig, "ch11_temp_scatter.png"); plt.close(fig)
    OUT["T0"], OUT["r2_best"] = best, r2.max()


# ============================================================ 3. 度日と THI
def fig_degree_thi():
    T0 = OUT.get("T0", 22.0)
    cdd = np.maximum(TA - T0, 0)
    hdd = np.maximum(T0 - TA, 0)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    t = np.linspace(5, 38, 300)
    a1.plot(t, np.maximum(t - T0, 0), color=C_ACC, lw=2.6, label=f"CDD = max(T − {T0:.0f}, 0)")
    a1.plot(t, np.maximum(T0 - t, 0), color=C_BLUE, lw=2.6, label=f"HDD = max({T0:.0f} − T, 0)")
    a1.axvline(T0, color=C_GREY, ls=":", lw=1.4)
    a1.text(T0 + 0.4, 13, f"基準 {T0:.0f} °C", fontsize=11.5, color=C_GREY)
    a1.set_xlabel("気温 [°C]"); a1.set_ylabel("度日 [°C]"); a1.grid(alpha=0.3)
    a1.legend(fontsize=11, frameon=False); a1.set_title("V 字を 2 本の直線に分ける", fontsize=11)
    if RH is not None:
        thi = thi_index(TA, RH)
        m = (HOUR >= 12) & (HOUR <= 18)
        a2.scatter(thi[m], Y[m], s=3, alpha=0.15, color=C_SEC)
        cc_thi = np.corrcoef(thi[m], Y[m])[0, 1]
        cc_t = np.corrcoef(TA[m], Y[m])[0, 1]
        z = np.polyfit(thi[m], Y[m], 1)
        xs = np.linspace(thi[m].min(), thi[m].max(), 50)
        a2.plot(xs, np.polyval(z, xs), color=C_MAIN, lw=2.4)
        a2.set_xlabel("不快指数 THI"); a2.set_ylabel("需要 [MW]（12〜18 時）")
        a2.grid(alpha=0.3)
        a2.set_title(f"THI との相関 {cc_thi:.3f}（気温だけなら {cc_t:.3f}）", fontsize=11)
        OUT["corr"] = (cc_thi, cc_t)
    fig.tight_layout(); savefig(fig, "ch11_degree_thi.png"); plt.close(fig)


# ============================================================ 4. 重回帰の当てはめ
def build_X(T0):
    cdd = np.maximum(TA - T0, 0); hdd = np.maximum(T0 - TA, 0)
    cols = [np.ones_like(Y), cdd, hdd, WEEKDAY]
    for k in (1, 2, 3):
        cols += [np.sin(2 * np.pi * k * HOUR / 24), np.cos(2 * np.pi * k * HOUR / 24)]
    cols += [np.sin(2 * np.pi * DOY / 365.25), np.cos(2 * np.pi * DOY / 365.25)]
    return np.column_stack(cols)


def fig_regression():
    T0 = OUT.get("T0", 22.0)
    X = build_X(T0)
    n = len(Y)
    ntr = int(n * 0.7)
    beta, *_ = np.linalg.lstsq(X[:ntr], Y[:ntr], rcond=None)
    pred = X @ beta
    err = Y[ntr:] - pred[ntr:]
    mae = np.abs(err).mean(); rmse = np.sqrt((err ** 2).mean())
    mape = np.abs(err / Y[ntr:]).mean() * 100
    # ベースライン：前週同曜日同時刻
    base = np.full(n, np.nan)
    base[168:] = Y[:-168]
    be = Y[ntr:] - base[ntr:]
    brmse = np.sqrt(np.nanmean(be ** 2))
    ss = 1 - rmse / brmse
    i0 = ntr + 24 * 30
    sl = slice(i0, i0 + 24 * 7)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9.6, 5.4), gridspec_kw={"height_ratios": [1.4, 1]})
    hrs = np.arange(24 * 7) / 24
    a1.plot(hrs, Y[sl], color=C_MAIN, lw=2.2, label="実績")
    a1.plot(hrs, pred[sl], color=C_SEC, lw=1.8, ls="--", label="重回帰の予測")
    a1.plot(hrs, base[sl], color=C_LIGHT, lw=1.6, ls=":", label="前週同曜日（ベースライン）")
    a1.set_ylabel("需要 [MW]"); a1.set_xlabel("経過日数（検証期間の 1 週間）")
    a1.grid(alpha=0.3); a1.legend(fontsize=11, frameon=False, ncol=3, loc="upper center")
    a1.set_title(f"重回帰の当てはめ（学習 70%・検証 30%）  MAE {mae:.1f} MW / RMSE {rmse:.1f} MW / MAPE {mape:.2f}%", fontsize=11)
    a2.bar(["前週同曜日", "重回帰"], [brmse, rmse], color=[C_LIGHT, C_MAIN], width=0.45)
    for i, v in enumerate([brmse, rmse]):
        a2.text(i, v + 1, f"{v:.1f} MW", ha="center", fontsize=11, weight="bold")
    a2.set_ylabel("検証 RMSE [MW]"); a2.grid(alpha=0.3, axis="y")
    a2.set_ylim(0, brmse * 1.35)
    a2.set_title(f"Skill Score = 1 − {rmse:.1f}/{brmse:.1f} = {ss:.3f}（正なら価値がある）", fontsize=11)
    # savefig() での縮小ぶん pt 指定の文字が縮小後に相対的にふくらむため、
    # 上段の xlabel と下段のタイトルが重ならないよう段間を広めに取る。
    # 外側の pad も合わせて広げないと、下段の縦書き ylabel が下端で欠ける
    fig.tight_layout(pad=1.4, h_pad=2.5); savefig(fig, "ch11_regression.png"); plt.close(fig)
    OUT["reg"] = (mae, rmse, mape, brmse, ss)
    OUT["beta"] = beta
    return X, beta, ntr, pred


# ============================================================ 5. 係数の意味
def fig_coefficients():
    beta = OUT["beta"]
    names = ["定数項", "CDD [MW/°C]", "HDD [MW/°C]", "平日ダミー [MW]"]
    vals = list(beta[:4])
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    colors = [C_GREY, C_ACC, C_BLUE, C_WARM]
    bars = ax.barh(names[::-1], vals[::-1], color=colors[::-1])
    for b, v in zip(bars, vals[::-1]):
        ax.text(v + np.sign(v) * max(abs(np.array(vals))) * 0.02, b.get_y() + b.get_height() / 2,
                f"{v:+.1f}", va="center", fontsize=11, weight="bold")
    ax.axvline(0, color=C_GREY, lw=1)
    ax.set_xlabel("回帰係数"); ax.grid(alpha=0.3, axis="x")
    ax.set_title("係数がそのまま読める — 気温 1 °C で何 MW、平日は何 MW 高いか", fontsize=11.5)
    savefig(fig, "ch11_coefficients.png"); plt.close(fig)
    OUT["coef"] = dict(zip(names, vals))


# ============================================================ 6. 誤差指標の違い
def fig_metrics():
    rng = np.random.default_rng(2)
    e_small = rng.normal(0, 20, 200)
    e_out = e_small.copy(); e_out[50] = 250
    sets = [("外れ値なし", e_small), ("外れ値 1 点あり", e_out)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    for ax, (lab, e) in zip((a1, a2), sets):
        mae = np.abs(e).mean(); rmse = np.sqrt((e ** 2).mean())
        ax.hist(e, bins=30, color=C_SEC, alpha=0.7)
        ax.axvline(mae, color=C_MAIN, lw=2.2, label=f"MAE = {mae:.1f}")
        ax.axvline(rmse, color=C_ACC, lw=2.2, label=f"RMSE = {rmse:.1f}")
        ax.set_xlabel("誤差 [MW]"); ax.set_ylabel("度数"); ax.grid(alpha=0.3, axis="y")
        ax.legend(fontsize=11.5, frameon=False)
        ax.set_title(f"{lab}（RMSE/MAE = {rmse/mae:.2f}）", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch11_metrics.png"); plt.close(fig)
    OUT["ratio"] = (np.sqrt((sets[0][1] ** 2).mean()) / np.abs(sets[0][1]).mean(),
                    np.sqrt((sets[1][1] ** 2).mean()) / np.abs(sets[1][1]).mean())


# ============================================================ 7. 時系列分割 vs ランダム分割
def fig_split():
    T0 = OUT.get("T0", 22.0)
    X = build_X(T0)
    n = len(Y)
    rng = np.random.default_rng(0)
    # ランダム分割（誤り）：隣の時刻が学習に入る
    idx = rng.permutation(n)
    tr, te = idx[:int(n * 0.7)], idx[int(n * 0.7):]
    b1, *_ = np.linalg.lstsq(X[tr], Y[tr], rcond=None)
    rmse_rand = np.sqrt(((Y[te] - X[te] @ b1) ** 2).mean())
    # 時系列分割（正しい）
    ntr = int(n * 0.7)
    b2, *_ = np.linalg.lstsq(X[:ntr], Y[:ntr], rcond=None)
    rmse_ts = np.sqrt(((Y[ntr:] - X[ntr:] @ b2) ** 2).mean())
    # ラグ特徴量を入れるとランダム分割が極端に良く見える
    lag = np.full(n, np.nan); lag[1:] = Y[:-1]
    X2 = np.column_stack([X, np.nan_to_num(lag, nan=Y.mean())])
    b3, *_ = np.linalg.lstsq(X2[tr], Y[tr], rcond=None)
    rmse_rand_lag = np.sqrt(((Y[te] - X2[te] @ b3) ** 2).mean())
    b4, *_ = np.linalg.lstsq(X2[:ntr], Y[:ntr], rcond=None)
    rmse_ts_lag = np.sqrt(((Y[ntr:] - X2[ntr:] @ b4) ** 2).mean())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.6, 4.2))
    a1.axis("off")
    a1.add_patch(Rectangle((0.05, 0.60), 0.63, 0.16, transform=a1.transAxes, fc=C_MAIN, alpha=0.55))
    a1.add_patch(Rectangle((0.68, 0.60), 0.27, 0.16, transform=a1.transAxes, fc=C_SEC, alpha=0.55))
    a1.text(0.36, 0.68, "学習（過去）", ha="center", va="center", fontsize=11, color="white", weight="bold", transform=a1.transAxes)
    a1.text(0.81, 0.68, "検証（未来）", ha="center", va="center", fontsize=11, color="white", weight="bold", transform=a1.transAxes)
    a1.text(0.5, 0.82, "○ 時系列分割（正しい）", ha="center", fontsize=12, color=C_MAIN, weight="bold", transform=a1.transAxes)
    rng2 = np.random.default_rng(1)
    for i in range(45):
        x = 0.05 + i * 0.02
        c = C_MAIN if rng2.random() < 0.7 else C_SEC
        a1.add_patch(Rectangle((x, 0.22), 0.018, 0.16, transform=a1.transAxes, fc=c, alpha=0.55))
    a1.text(0.5, 0.44, "✗ ランダム分割（未来が学習に混ざる）", ha="center", fontsize=12, color=C_ACC, weight="bold", transform=a1.transAxes)
    a1.text(0.5, 0.10, "隣の時刻はほぼ同じ値 → 答えを見ながら学ぶことになる", ha="center", fontsize=11.5, color=C_GREY, transform=a1.transAxes)
    labels = ["時系列分割\n（基本の特徴量）", "ランダム分割\n（基本の特徴量）", "時系列分割\n（1 時間前を追加）", "ランダム分割\n（1 時間前を追加）"]
    vals = [rmse_ts, rmse_rand, rmse_ts_lag, rmse_rand_lag]
    cols = [C_MAIN, C_ACC, C_MAIN, C_ACC]
    bars = a2.bar(labels, vals, color=cols)
    for b, v in zip(bars, vals):
        a2.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}", ha="center", fontsize=12, weight="bold")
    a2.set_ylabel("検証 RMSE [MW]"); a2.grid(alpha=0.3, axis="y"); a2.tick_params(axis="x", labelsize=8.5)
    a2.set_title("ラグを入れるとランダム分割だけ極端に良く見える", fontsize=11)
    fig.tight_layout(); savefig(fig, "ch11_split.png"); plt.close(fig)
    OUT["split"] = (rmse_ts, rmse_rand, rmse_ts_lag, rmse_rand_lag)


# ============================================================ 8. 自己相関
def fig_acf():
    y = Y - Y.mean()
    lags = np.arange(0, 24 * 15)
    ac = np.array([1.0 if l == 0 else np.corrcoef(y[:-l], y[l:])[0, 1] for l in lags])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(lags / 24, ac, color=C_MAIN, lw=1.6)
    for d in range(1, 15):
        ax.axvline(d, color=C_LIGHT, lw=0.8, zorder=0)
    for l, lab, c in [(24, "24 h（日周期）", C_ACC), (168, "168 h（週周期）", C_WARM)]:
        ax.scatter([l / 24], [ac[l]], color=c, s=80, zorder=5)
        ax.annotate(f"{lab}\nr = {ac[l]:.3f}", (l / 24, ac[l]), textcoords="offset points",
                    xytext=(8, 10), fontsize=11.5, color=c)
    ax.axhline(0, color=C_GREY, lw=1)
    ax.set_xlabel("ラグ [日]"); ax.set_ylabel("自己相関"); ax.grid(alpha=0.3)
    savefig(fig, "ch11_acf.png"); plt.close(fig)
    OUT["acf"] = (ac[24], ac[168])


# ============================================================ 9. 残差の診断
def fig_residual():
    T0 = OUT.get("T0", 22.0)
    X = build_X(T0)
    n = len(Y); ntr = int(n * 0.7)
    beta, *_ = np.linalg.lstsq(X[:ntr], Y[:ntr], rcond=None)
    res = Y[ntr:] - X[ntr:] @ beta
    ta = TA[ntr:]; hr = HOUR[ntr:]
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(11.2, 3.8))
    a1.hist(res, bins=40, color=C_SEC, alpha=0.75)
    a1.axvline(0, color=C_MAIN, lw=2)
    a1.set_xlabel("残差 [MW]"); a1.set_ylabel("度数"); a1.grid(alpha=0.3, axis="y")
    a1.set_title(f"分布（平均 {res.mean():+.1f}、標準偏差 {res.std():.1f}）", fontsize=12)
    a2.scatter(ta, res, s=3, alpha=0.15, color=C_SEC)
    bins = np.arange(np.floor(ta.min()), np.ceil(ta.max()) + 1, 2.0)
    cx, cy = [], []
    for b in bins[:-1]:
        m = (ta >= b) & (ta < b + 2)
        if m.sum() > 20: cx.append(b + 1); cy.append(res[m].mean())
    a2.plot(cx, cy, "o-", color=C_MAIN, lw=2)
    a2.axhline(0, color=C_ACC, lw=1.5, ls="--")
    a2.set_xlabel("気温 [°C]"); a2.set_ylabel("残差 [MW]"); a2.grid(alpha=0.3)
    a2.set_title("気温に対する偏り（0 に近いほど良い）", fontsize=12)
    hm = [res[hr == h].mean() for h in range(24)]
    a3.bar(range(24), hm, color=[C_ACC if abs(v) > 8 else C_SEC for v in hm])
    a3.axhline(0, color=C_MAIN, lw=1.5)
    a3.set_xlabel("時刻 [h]"); a3.set_ylabel("残差の平均 [MW]"); a3.set_xticks(range(0, 24, 4))
    a3.grid(alpha=0.3, axis="y")
    a3.set_title("時刻ごとの偏り", fontsize=12)
    fig.tight_layout(); savefig(fig, "ch11_residual.png"); plt.close(fig)
    OUT["res_std"] = res.std()


# ============================================================ 10. 予備力への翻訳
def fig_reserve():
    _, rmse, _, brmse, _ = OUT["reg"]
    rng = np.random.default_rng(4)
    err = rng.normal(0, rmse, 20000)
    qs = [80, 90, 95, 99]
    vals = [np.percentile(np.abs(err), q) for q in qs]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
    a1.hist(err, bins=60, color=C_SEC, alpha=0.7, density=True)
    for q, v, c in zip(qs, vals, [C_WARM, C_MAIN, C_ACC, "#5A1F19"]):
        a1.axvline(v, color=c, lw=2, label=f"{q}% が収まる ±{v:.0f} MW")
    a1.set_xlabel("予測誤差 [MW]"); a1.set_ylabel("確率密度"); a1.grid(alpha=0.3)
    a1.legend(fontsize=11, frameon=False)
    a1.set_title(f"予測誤差の分布（σ = RMSE = {rmse:.1f} MW）", fontsize=11)
    bars = a2.bar([f"{q}%" for q in qs], vals, color=[C_WARM, C_MAIN, C_ACC, "#5A1F19"])
    for b, v in zip(bars, vals):
        a2.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.0f}", ha="center", fontsize=11, weight="bold")
    a2.set_ylabel("必要な予備力 [MW]"); a2.set_xlabel("カバーしたい確率")
    a2.grid(alpha=0.3, axis="y")
    fig.tight_layout(); savefig(fig, "ch11_reserve.png"); plt.close(fig)
    OUT["reserve"] = dict(zip(qs, vals))


# ============================================================ 11. たとえ話 — 体温調節と電力需要
def fig_analogy():
    analogy_figure("ch11_analogy.png",
        left_title="体（たとえ）", right_title="電力需要（実物）",
        pairs=[("暑ければ汗をかき、寒ければ震えて体温を調節する", "気温反応＝冷房と暖房の V 字（度日 CDD/HDD）"),
               ("快適な温度から離れるほど、体の反応は強くなる", "距離の指標＝度日は快適な基準温度からの隔たり"),
               ("平日と休日では、生活のリズムが違う", "曜日効果＝平日と休日で需要が変わるダミー変数"),
               ("朝起きて夜寝る、体内時計のリズムがある", "日内変動＝朝から昼にかけてピークが立つ 1 日の波"),
               ("昨日の暑さが、今日の体にも残っている", "蓄熱効果＝前日の気温が今日の需要に残るラグ")],
        note="この対応が頭に入っていれば、需要の式は全部「体温調節の話」に翻訳できる。")


# ============================================================ 12. よくある誤解
def fig_myth():
    analogy_figure("ch11_myth.png",
        left_title="× よくある誤解", right_title="○ 正しい理解",
        pairs=[("モデルが複雑なほど、当たる",
                "当たりの 9 割は特徴量（気温・曜日・時刻）が決める"),
               ("学習データと検証データは、ランダムに分ければよい",
                "時系列は未来を混ぜず、必ず前週同曜日と比べる"),
               ("検証精度が高ければ、良いモデル",
                "良すぎる結果は、まずリークを疑う")],
        note="モデルを複雑にする前に、特徴量の設計と検証の設計を疑う。")


# ==================================================== 導出の段階開示（1 手ずつ出す 3 枚組）
def fig_derivations():
    """文字だけだった導出スライドを、1 手ずつ出す図版に置き換えるための図"""
    for i in (1, 2, 3):
        derivation_figure(f"ch11_deriv_split_{i}.png", reveal=i, width=11.8, height=5.8,
            steps=[('① 時系列は隣が似ている',
                r"$\rho(1\ \mathrm{h}) \approx 1$",
                '1 時間前との相関はほぼ 1。ランダムに\n分けると、検証の隣が学習に入る'),
               ('② それは実質的に答えを見ている',
                'リーク（情報の漏れ）',
                '未来の情報が学習に混ざると、\n検証精度は現実より良く出る'),
               ('③ だから時間順に切る',
                r"$41.7 \to 36.1\ \mathrm{MW}$",
                'ランダム分割は RMSE を 14% 過小に見せる。\n運用では出ない性能である')],
            result='過去で学び、未来で試す。時系列ではこれが唯一の分け方')


if __name__ == "__main__":
    fig_decompose(); fig_temp_scatter(); fig_degree_thi(); fig_regression(); fig_coefficients()
    fig_metrics(); fig_split(); fig_acf(); fig_residual(); fig_reserve()
    fig_analogy(); fig_myth()
    print("\n===== スライドに書く数値 =====")
    print(f"需要データ: {len(Y):,} 時間、平均 {OUT['mean']:.0f} MW、最大 {OUT['peak']:.0f} MW、平日と休日の差 {OUT['wk_gap']:.0f} MW")
    print(f"度日の最適基準温度 T0 = {OUT['T0']:.1f} °C（R² = {OUT['r2_best']:.3f}）")
    if "corr" in OUT:
        print(f"相関: THI {OUT['corr'][0]:.3f} vs 気温 {OUT['corr'][1]:.3f}")
    mae, rmse, mape, brmse, ss = OUT["reg"]
    print(f"重回帰: MAE {mae:.1f} MW、RMSE {rmse:.1f} MW、MAPE {mape:.2f}%")
    print(f"  ベースライン（前週同曜日）RMSE {brmse:.1f} MW → Skill Score {ss:.3f}")
    for k, v in OUT["coef"].items():
        print(f"  係数 {k}: {v:+.2f}")
    print(f"RMSE/MAE 比: 外れ値なし {OUT['ratio'][0]:.2f} → 1 点あり {OUT['ratio'][1]:.2f}")
    ts, rd, tsl, rdl = OUT["split"]
    fig_derivations()
    print(f"分割: 時系列 {ts:.1f} / ランダム {rd:.1f} MW、ラグ追加で 時系列 {tsl:.1f} / ランダム {rdl:.1f} MW")
    print(f"自己相関: 24 h {OUT['acf'][0]:.3f}、168 h {OUT['acf'][1]:.3f}")
    print(f"残差の標準偏差 {OUT['res_std']:.1f} MW")
    print(f"予備力: " + "、".join(f"{k}% → {v:.0f} MW" for k, v in OUT["reserve"].items()))
