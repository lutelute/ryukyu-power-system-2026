# -*- coding: utf-8 -*-
"""数式を「注釈つきの図」として描くヘルパ（全回で使う）

marp-pptx の equation 型は記号欄が数式フォントで崩れるため、
数式そのものを matplotlib で描き、色分け・引き出し線・読み下しを付けた
1 枚の図にして figure-story で見せる。

    from pws_eqfig import eq_figure
    eq_figure("ch08_eq_kdf.png",
              title="ΔP = KΔF",
              latex=r"$\\Delta P = K\\,\\Delta F$",
              terms=[("ΔP", "需給アンバランス [MW]", "発電が余れば正、足りなければ負", C_ACC),
                     ("K",  "系統定数 [MW/Hz]",      "周波数 1 Hz あたり何 MW 動くか", C_MAIN),
                     ("ΔF", "周波数偏差 [Hz]",        "発電不足なら負（下がる）",      C_SEC)],
              read="需給の食い違いを系統の硬さで割ると、周波数のずれになる。",
              note="単位は %MW/0.1Hz が実務の標準。K = %K × S / 10。")
"""
import numpy as np
from pws_common import setup_japanese_font, savefig

plt = setup_japanese_font()
from matplotlib.patches import FancyBboxPatch

C_MAIN, C_ACC, C_SEC, C_GREY, C_LIGHT = "#7C332A", "#B85042", "#5C7268", "#6E6A60", "#DCD8CC"
C_WARM, C_BLUE = "#B3812F", "#2F6DB3"


def eq_figure(fname, latex, terms, read=None, note=None, title=None,
              eq_size=34, width=11.0, height=5.4, extra=None):
    """数式 + 記号の対応表を 1 枚の図にする

    latex : matplotlib mathtext で描ける数式（$...$）
    terms : [(記号, 名前, 説明, 色), ...] 3〜5 個
    read  : 数式の読み下し（1 文）
    note  : 補足（1 文、任意）
    extra : ax を受け取って追加描画する関数（任意）
    """
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    y_eq = 0.80 if title else 0.84
    if title:
        ax.text(0.5, 0.95, title, ha="center", va="top", fontsize=15,
                color=C_MAIN, weight="bold")
    # 数式（中央・大きく）
    ax.text(0.5, y_eq, latex, ha="center", va="center", fontsize=eq_size, color="#1A1A17")

    # 読み下し
    y = y_eq - 0.18
    if read:
        ax.add_patch(FancyBboxPatch((0.06, y - 0.055), 0.88, 0.10,
                                    boxstyle="round,pad=0.012", fc="#F2EFE6",
                                    ec=C_LIGHT, lw=1.2, transform=ax.transAxes))
        ax.text(0.5, y, "読み下し：" + read, ha="center", va="center",
                fontsize=13, color="#1A1A17")
        y -= 0.16

    # 記号の対応（カード状に横並び）
    n = len(terms)
    w = 0.88 / n
    for i, (sym, name, desc, col) in enumerate(terms):
        x = 0.06 + i * w
        ax.add_patch(FancyBboxPatch((x + 0.008, y - 0.30), w - 0.016, 0.30,
                                    boxstyle="round,pad=0.010", fc="#FBFAF6",
                                    ec=col, lw=1.8, transform=ax.transAxes))
        ax.text(x + w / 2, y - 0.055, sym, ha="center", va="center",
                fontsize=20, color=col, weight="bold")
        ax.text(x + w / 2, y - 0.135, name, ha="center", va="center",
                fontsize=11.5, color="#1A1A17")
        ax.text(x + w / 2, y - 0.225, desc, ha="center", va="center",
                fontsize=10, color=C_GREY, wrap=True)

    if note:
        ax.text(0.5, 0.035, note, ha="center", va="center", fontsize=11, color=C_MAIN)

    if extra is not None:
        extra(ax)

    savefig(fig, fname)
    plt.close(fig)


def derivation_figure(fname, steps, title=None, width=11.0, height=5.6, result=None,
                     reveal=None):
    """導出を 3〜4 段の帯で描く（sections + build の図版）

    steps : [(見出し, 式(latex または文字列), 説明), ...]
    result: 最後に強調する結論（任意）
    reveal: 何段目まで見せるか（1 起点）。指定すると、それより先の段と結論を
            薄く（ゴースト）描く。1, 2, 3 と変えた図を並べれば、スライドの
            段階開示になる。None なら全部を濃く描く。
    """
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    def alpha_of(i):
        """i 段目（0 起点）の濃さ。まだ出していない段は薄く"""
        return 1.0 if reveal is None or i < reveal else 0.16
    if title:
        ax.text(0.5, 0.96, title, ha="center", va="top", fontsize=15, color=C_MAIN, weight="bold")
    n = len(steps)
    top = 0.86 if title else 0.94
    bottom = 0.16 if result else 0.06
    h = (top - bottom) / n
    cols = [C_SEC, C_WARM, C_MAIN, C_ACC]
    for i, (head, eq, desc) in enumerate(steps):
        y = top - i * h
        a = alpha_of(i)
        ax.add_patch(FancyBboxPatch((0.04, y - h + 0.02), 0.92, h - 0.035,
                                    boxstyle="round,pad=0.008", fc="#FBFAF6",
                                    ec=cols[i % 4], lw=1.6, alpha=a, transform=ax.transAxes))
        ax.add_patch(FancyBboxPatch((0.045, y - h + 0.025), 0.035, h - 0.045,
                                    boxstyle="round,pad=0.004", fc=cols[i % 4],
                                    ec="none", alpha=a, transform=ax.transAxes))
        ax.text(0.0625, y - h / 2 + 0.01, str(i + 1), ha="center", va="center",
                fontsize=15, color="white", weight="bold", alpha=a)
        ax.text(0.095, y - 0.035, head, ha="left", va="top", fontsize=12.5,
                color=cols[i % 4], weight="bold", alpha=a)
        ax.text(0.42, y - h / 2 + 0.005, eq, ha="center", va="center",
                fontsize=17, color="#1A1A17", alpha=a)
        ax.text(0.70, y - h / 2 + 0.005, desc, ha="left", va="center",
                fontsize=10.5, color=C_GREY, alpha=a)
        if i < n - 1:
            ax.annotate("", xy=(0.5, y - h + 0.012), xytext=(0.5, y - h + 0.030),
                        xycoords="axes fraction",
                        arrowprops=dict(arrowstyle="-|>", color=C_GREY, lw=1.6,
                                        alpha=min(a, alpha_of(i + 1))))
    if result:
        ar = 1.0 if reveal is None or reveal >= n else 0.16
        ax.add_patch(FancyBboxPatch((0.04, 0.025), 0.92, 0.105,
                                    boxstyle="round,pad=0.010", fc=C_MAIN,
                                    ec="none", alpha=0.90 * ar, transform=ax.transAxes))
        if isinstance(result, tuple):          # (数式, 添え書き) で渡すと 2 段に描く
            eq_r, note_r = result
            ax.text(0.065, 0.078, eq_r, ha="left", va="center", fontsize=17,
                    color="white", alpha=ar)
            ax.text(0.945, 0.078, note_r, ha="right", va="center", fontsize=12.5,
                    color="white", weight="bold", alpha=ar)
        else:
            ax.text(0.5, 0.078, result, ha="center", va="center", fontsize=14,
                    color="white", weight="bold", alpha=ar)
    savefig(fig, fname)
    plt.close(fig)


def worked_example(fname, given, steps, answer, title=None, width=11.0, height=5.6):
    """例題を「与件 → 手順 → 答え」の 1 枚に描く

    given  : [(ラベル, 値), ...] 3〜4 個
    steps  : [(手順名, 式, 結果), ...] 3〜4 個
    answer : 強調する答え（40 字以内を推奨）
    """
    fig, ax = plt.subplots(figsize=(width, height))
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    if title:
        ax.text(0.5, 0.975, title, ha="center", va="top", fontsize=15, color=C_MAIN, weight="bold")

    top, bottom = (0.90 if title else 0.97), 0.26
    # 与件（左の箱）— 内容の数に合わせて高さを決める
    ng = len(given)
    ax.add_patch(FancyBboxPatch((0.03, bottom), 0.235, top - bottom,
                                boxstyle="round,pad=0.012", fc="#F2EFE6",
                                ec=C_SEC, lw=1.6, transform=ax.transAxes))
    ax.text(0.1475, top - 0.045, "与えられた条件", ha="center", va="center",
            fontsize=12, color=C_SEC, weight="bold")
    gy0, gh = top - 0.115, (top - bottom - 0.145) / max(ng, 1)
    for i, (lab, val) in enumerate(given):
        y = gy0 - i * gh
        ax.text(0.055, y, lab, ha="left", va="center", fontsize=10, color=C_GREY)
        ax.text(0.055, y - 0.048, val, ha="left", va="center", fontsize=12.5, color="#1A1A17")

    # 手順（右）
    n = len(steps)
    h = (top - bottom) / n
    cols = [C_SEC, C_WARM, C_MAIN, C_ACC]
    for i, (name, eq, res) in enumerate(steps):
        y = top - i * h
        c = cols[i % 4]
        ax.add_patch(FancyBboxPatch((0.29, y - h + 0.018), 0.68, h - 0.034,
                                    boxstyle="round,pad=0.008", fc="#FBFAF6",
                                    ec=c, lw=1.4, transform=ax.transAxes))
        ax.text(0.317, y - h / 2 + 0.009, f"{i+1}", ha="center", va="center",
                fontsize=14, color=c, weight="bold")
        ax.text(0.342, y - 0.038, name, ha="left", va="center", fontsize=11, color=c, weight="bold")
        ax.text(0.342, y - h + 0.075, eq, ha="left", va="center", fontsize=12.5, color="#1A1A17")
        if res:
            ax.text(0.955, y - h / 2 + 0.009, res, ha="right", va="center",
                    fontsize=15, color=c, weight="bold")

    # 答え
    ax.add_patch(FancyBboxPatch((0.03, 0.035), 0.94, 0.175, boxstyle="round,pad=0.012",
                                fc=C_MAIN, ec="none", alpha=0.92, transform=ax.transAxes))
    fs = 15 if len(answer) <= 38 else (13 if len(answer) <= 48 else 11.5)
    ax.text(0.5, 0.122, answer, ha="center", va="center", fontsize=fs,
            color="white", weight="bold")
    savefig(fig, fname)
    plt.close(fig)

def _wrap_ja(text, n):
    """日本語を n 文字で折り返す（すでに改行があればそれを尊重する）

    日本語はどこでも折り返せるので幅で切る。ただし行頭に句読点・閉じ括弧が
    来ないように 1 文字ぶんずらす。半角は 0.55 文字として数える。
    """
    if "\n" in text:
        return text
    NG_HEAD = "、。）」』】・％%!?！？"
    out, line, w = [], "", 0.0
    for ch in text:
        cw = 0.55 if ord(ch) < 0x3000 else 1.0
        if w + cw > n and line:
            if ch in NG_HEAD:                 # 行頭に置けない字は前の行に残す
                line += ch
                out.append(line); line, w = "", 0.0
                continue
            out.append(line); line, w = "", 0.0
        line += ch; w += cw
    if line:
        out.append(line)
    return "\n".join(out)


def analogy_figure(fname, left_title, right_title, pairs, note=None,
                   width=12.4, height=5.8, left_color=None, right_color=None,
                   fontsize=13):
    """たとえ話と実物の対応を、左右 2 列 + 矢印の 1 枚にする

    left_title  : 左列の見出し（たとえ話の側。例「天秤」）
    right_title : 右列の見出し（実物の側。例「電力系統」）
    pairs       : [(左の文, 右の文), ...] 4〜6 個。右は「◯◯＝用語」の形が読みやすい
    note        : 下に置く 1 文（任意）
    """
    lc = left_color or C_SEC
    rc = right_color or C_MAIN
    fig = plt.figure(figsize=(width, height))
    ax = fig.add_axes([0, 0, 1, 1])       # 図いっぱいに描く（座標＝図の割合）
    ax.axis("off"); ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    n = len(pairs)
    top, bottom = 0.86, (0.10 if note else 0.03)
    h = (top - bottom) / n
    lx, lw = 0.03, 0.415
    rx, rw = 0.555, 0.415

    for x, w, t, c in [(lx, lw, left_title, lc), (rx, rw, right_title, rc)]:
        ax.add_patch(FancyBboxPatch((x, top + 0.025), w, 0.085,
                                    boxstyle="round,pad=0.010", fc=c, ec="none",
                                    alpha=0.92, transform=ax.transAxes))
        ax.text(x + w / 2, top + 0.068, t, ha="center", va="center",
                fontsize=15, color="white", weight="bold")

    for i, (lft, rgt) in enumerate(pairs):
        y = top - i * h
        ncol = lw * width * 72 / fontsize * 0.90        # 1 行に入る全角文字数
        for x, w, txt, c, fc in [(lx, lw, _wrap_ja(lft, ncol), lc, "#F2EFE6"),
                                 (rx, rw, _wrap_ja(rgt, ncol), rc, "#FBFAF6")]:
            ax.add_patch(FancyBboxPatch((x, y - h + 0.018), w, h - 0.036,
                                        boxstyle="round,pad=0.008", fc=fc,
                                        ec=c, lw=1.5, transform=ax.transAxes))
            ax.text(x + w / 2, y - h / 2 + 0.008, txt, ha="center", va="center",
                    fontsize=fontsize, color="#1A1A17", transform=ax.transAxes,
                    linespacing=1.45)
        ax.annotate("", xy=(rx - 0.012, y - h / 2 + 0.008),
                    xytext=(lx + lw + 0.012, y - h / 2 + 0.008),
                    xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color=rc, lw=2.0))

    if note:
        ax.text(0.5, 0.045, note, ha="center", va="center", fontsize=12.5,
                color=C_MAIN, weight="bold")
    savefig(fig, fname)
    plt.close(fig)
