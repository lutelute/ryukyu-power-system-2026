# -*- coding: utf-8 -*-
"""図の中の小さすぎる fontsize を底上げする

図はスライド上で「描いたときの pt のまま」表示される（savefig がキャンバスを
縮めるため）。つまり図の中で fontsize=9 と書けば、投影しても 9 pt にしかならない。
13.33 inch 幅のスライドで 9 pt は、後ろの席から読めない。

    python3 tools/lift-fontsize.py --check ch08   # 変わる箇所を見るだけ
    python3 tools/lift-fontsize.py ch08           # 書き換える
    python3 tools/lift-fontsize.py                # 全回
"""
import glob, os, re, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLOOR = 11.0


def lift(f):
    """11 pt を下限に、1.5 pt 持ち上げる（大小の順序は保つ）"""
    return round(max(FLOOR, f + 1.5), 1)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    pat = args[0] if args else "ch*"
    total = 0
    for py in sorted(glob.glob(os.path.join(BASE, "コード", f"fig_{pat}.py"))):
        src = open(py, encoding="utf-8").read()
        n = [0]

        def rep(m):
            f = float(m.group(1))
            if f >= FLOOR:
                return m.group(0)
            n[0] += 1
            v = lift(f)
            return f"fontsize={v:g}"

        out = re.sub(r"fontsize=([\d.]+)", rep, src)
        if n[0]:
            total += n[0]
            print(f"{os.path.basename(py)}: {n[0]} 箇所")
            if not check:
                open(py, "w", encoding="utf-8").write(out)
    print(f"合計 {total} 箇所" + ("（--check なので書き換えていない）" if check else "を底上げした"))


if __name__ == "__main__":
    main()
