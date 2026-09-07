# -*- coding: utf-8 -*-
"""スライドの型ごとに、図をどれだけ縮めて描くかを決める（コード/fig_scale.json）

図はスライド上で型ごとに違う幅に置かれる。figure-story は本文領域の 58% が上限で、
9〜12 inch の figsize で描いた図をそこへ入れると、図の中の文字が投影で読めなくなる。
そこで「小さく置かれる図は、小さいキャンバスに同じ pt で描く」ことで、
スライド上での文字の見かけの大きさを揃える。

    python3 tools/fig-scale.py     → コード/fig_scale.json を書き出す
"""
import json, os, re, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 型ごとの「スライド上で図に与えられる箱（幅, 高さ）[inch]」
# 13.33 x 7.5 inch のスライドで、題・リード・キャプション・結論箱を引いた実寸。
BOX_ON_SLIDE = {
    "figure-full": (12.8, 5.9), "panorama": (12.4, 5.2),
    "figure": (7.6, 3.9), "diagram": (8.0, 4.2), "chart": (8.0, 4.2),
    "annotation": (8.0, 4.2), "figure-cols": (6.4, 4.4),
    "result": (7.0, 3.8), "result-dual": (5.6, 3.4),
    "figure-story": (7.1, 4.2), "title-figure": (6.6, 5.0),
    "gallery-img": (4.6, 3.0), "multi-result": (4.6, 3.0),
    "split-panel": (6.0, 4.6),
}
# graphical-abstract のパネル内の図は飾りとして小さく置かれるだけなので、
# 縮小の判断からは外す（同じ図が本編で大きく使われることが多い）。
SKIP = {"graphical-abstract"}
# 書き出すのは「スライド上での図の幅」そのもの。実際の縮小率は savefig が
# 図の figsize と突き合わせて決める（factor = 幅 / figsize の幅、上限 1.0）。

def main():
    scale = {}
    for md in sorted(glob.glob(os.path.join(BASE, "スライド", "ch*.md"))):
        txt = open(md, encoding="utf-8").read()
        for block in txt.split("\n---\n"):
            m = re.search(r"<!--\s*_class:\s*([\w-]+)\s*-->", block)
            cls = m.group(1) if m else "default"
            if cls in SKIP:
                continue
            for img in re.findall(r"!\[[^\]]*\]\(\.\./図/([^)]+)\)", block):
                box = BOX_ON_SLIDE.get(cls, (8.0, 4.2))
                # 同じ図が複数の型で使われたら、小さく置かれるほうに合わせる
                old = scale.get(img)
                scale[img] = box if old is None else (min(old[0], box[0]),
                                                     min(old[1], box[1]))
    out = os.path.join(BASE, "コード", "fig_scale.json")
    # 一時ファイルに書いてから差し替える。並行して図を作っている別のプロセスが
    # 書きかけのファイルを読んで「縮小なし」で保存してしまうのを防ぐ。
    tmp = out + f".tmp{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(scale, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, out)
    from collections import Counter
    print(f"{len(scale)} 枚 → {os.path.relpath(out, BASE)}")
    for b, n in sorted(Counter(map(tuple, scale.values())).items()):
        print(f"  箱 {b[0]} x {b[1]} inch : {n} 枚")

if __name__ == "__main__":
    main()
