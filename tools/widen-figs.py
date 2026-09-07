# -*- coding: utf-8 -*-
"""横長の図が載っている figure-story スライドを figure-full に移す

figure-story の図は本文領域の 58%（約 7.1 inch）までしか使えない。
2 枚並びのグラフ（縦横比 2.1 以上）をそこへ入れると、図の中の文字が
投影で読めない大きさに縮む。そういう図はスライド 1 枚を丸ごと使う。

移すときに失われる要素は次のように残す:
  h2「読み方｜…」と fs-conclusion → キャプション（1 行にまとめる）
  fs-points の箇条書き            → 講師ノート

    python3 tools/widen-figs.py --check        # 対象を数えるだけ
    python3 tools/widen-figs.py               # 全回を書き換える
    python3 tools/widen-figs.py ch08          # 1 回だけ
"""
import glob, os, re, sys
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIO = 2.1

def aspect(img):
    p = os.path.join(BASE, "図", img)
    if not os.path.exists(p):
        return None
    w, h = Image.open(p).size
    return w / h


def multi_panel():
    """グラフを 2 枚以上並べている図の名前を集める

    複数のパネルを 7.1 inch に押し込むと、どのパネルも読めない大きさになる。
    そういう図はスライド 1 枚を丸ごと使う。
    """
    names = set()
    for py in sorted(glob.glob(os.path.join(BASE, "コード", "fig_ch*.py"))):
        src = open(py, encoding="utf-8").read()
        for m in re.finditer(r"\ndef (\w+)\(.*?\):(.*?)(?=\ndef |\Z)", src, re.S):
            body = m.group(2)
            n = 1
            for a, b in re.findall(r"subplots\(\s*(\d+)\s*,\s*(\d+)", body):
                n = max(n, int(a) * int(b))
            for a, b in re.findall(r"add_gridspec\(\s*(\d+)\s*,\s*(\d+)", body):
                n = max(n, int(a) * int(b))
            if n > 1:
                names.update(re.findall(r'savefig\(fig,\s*"([^"]+)"', body))
    return names


MULTI = multi_panel()

def convert(block):
    m = re.search(r"!\[[^\]]*\]\(\.\./図/([^)]+)\)", block)
    if not m:
        return None
    img = m.group(1)
    a = aspect(img)
    if a is None or (a < RATIO and img not in MULTI):
        return None
    h2 = re.search(r"^## (.+)$", block, re.M)
    pts = re.search(r'<div class="fs-points">\n(.*?)\n</div>', block, re.S)
    concl = re.search(r'<div class="fs-conclusion">(.*?)</div>', block, re.S)
    note = re.search(r"<!--\s*note:\s*(.*?)\s*-->", block, re.S)

    lead = h2.group(1).strip() if h2 else ""
    lead = re.sub(r"^読み方｜", "", lead).strip()
    tail = concl.group(1).strip() if concl else ""
    cap = "　".join(x for x in (lead, tail) if x)

    bullets = []
    if pts:
        for ln in pts.group(1).splitlines():
            ln = ln.strip()
            if ln.startswith("- "):
                bullets.append(re.sub(r"\*\*(.+?)\*\*", r"\1", ln[2:]).strip())
    notes = [note.group(1).strip()] if note else []
    if bullets:
        notes.append("図の要点：" + "／".join(bullets))

    out = block
    out = out.replace("<!-- _class: figure-story -->", "<!-- _class: figure-full -->")
    out = re.sub(r"<!--\s*_side:\s*\w+\s*-->\n?", "", out)
    out = re.sub(r"^## .+\n\n?", "", out, count=1, flags=re.M)
    out = re.sub(r'<div class="fs-points">\n.*?\n</div>\n\n?', "", out, flags=re.S)
    out = re.sub(r'<div class="fs-conclusion">.*?</div>\n\n?', "", out, flags=re.S)
    out = re.sub(r"<!--\s*note:.*?-->\n?", "", out, flags=re.S)
    out = re.sub(r"!\[[^\]]*\]\((\.\./図/[^)]+)\)", r"![w:1150](\1)", out)
    out = out.rstrip("\n") + "\n"
    if cap:
        out += f'\n<div class="caption">{cap}</div>\n'
    if notes:
        out += f"\n<!-- note: {'　'.join(notes)} -->\n"
    return out

def main():
    check = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pat = args[0] if args else "ch*"
    total = 0
    for md in sorted(glob.glob(os.path.join(BASE, "スライド", f"{pat}.md"))):
        txt = open(md, encoding="utf-8").read()
        blocks = txt.split("\n---\n")
        n = 0
        for i, b in enumerate(blocks):
            if "_class: figure-story" not in b:
                continue
            nb = convert(b)
            if nb:
                blocks[i] = nb
                n += 1
        if n and not check:
            open(md, "w", encoding="utf-8").write("\n---\n".join(blocks))
        if n:
            print(f"{os.path.basename(md)}: {n} 枚を figure-full へ")
        total += n
    print(f"合計 {total} 枚" + ("（--check なので書き換えていない）" if check else ""))

if __name__ == "__main__":
    main()
