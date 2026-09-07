// tools/build-notes.mjs — ノート/*.md と 記号表.md・教科書対応.md を notes/*.html に変換する。
//   node tools/build-notes.mjs
// ・数式は KaTeX を Node 側で描画（実行時に JS も fetch も不要 → file:// で開ける）
// ・Markdown は marked。数式とコードは先に退避してから変換する
// ・ナビ／前後リンク／演習リンクは viz/site.js の cats から生成（順路が 1 箇所で決まる）
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const CAND = [path.join(path.dirname(fileURLToPath(import.meta.url)), "node_modules"), process.env.HOME + "/Documents/GitHub/Noda_model/node_modules", process.env.HOME + "/Documents/GitHub/tool_dev_SGNB/marginalia/node_modules"];
function req(name) { for (const d of CAND) { try { return require(path.join(d, name)); } catch (e) {} } throw new Error(name + " が見つかりません"); }
const katex = req("katex");
const { marked } = req("marked");

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'ノート');
const OUT = path.join(ROOT, 'notes');
fs.mkdirSync(OUT, { recursive: true });

// ---- site.js を読む（ブラウザ用ファイルを Node で評価）----
const win = {};
new Function('window', fs.readFileSync(path.join(ROOT, 'viz', 'site.js'), 'utf8'))(win);
const SITE = win.SITE;
const FLAT = [];
SITE.cats.forEach((c, ci) => c.items.forEach(p => FLAT.push({ ...p, day: c.name, dayIndex: ci })));
// 第 n 回 → FLAT[n-1]（cats の順路＝回の順）

// ---- Markdown 前処理：コードと数式を退避 ----
function convert(md) {
  // ノート間・付録へのリンクを notes/ 内の HTML に付け替える（原稿は .md のまま）
  md = md.replace(/\]\((?:\.\.\/)?(?:ノート\/)?(ch\d\d)_[^)]*\.md(#[^)]*)?\)/g, ']($1.html$2)')
         .replace(/\]\((?:\.\.\/)?教科書対応\.md(#[^)]*)?\)/g, '](textbook.html$1)')
         .replace(/\]\((?:\.\.\/)?記号表\.md(#[^)]*)?\)/g, '](symbols.html$1)');
  const code = [], math = [];
  md = md.replace(/```[\s\S]*?```/g, m => { code.push(m); return `QQCODE${code.length - 1}QQ`; });
  md = md.replace(/`[^`\n]+`/g, m => { code.push(m); return `QQCODE${code.length - 1}QQ`; });
  md = md.replace(/\$\$([\s\S]+?)\$\$/g, (m, t) => { math.push({ t, d: true }); return `QQMATH${math.length - 1}QQ`; });
  md = md.replace(/\$([^$\n]+?)\$/g, (m, t) => { math.push({ t, d: false }); return `QQMATH${math.length - 1}QQ`; });
  md = md.replace(/\*\*([^*\n]+?)\*\*/g, (m, t) => '<strong>' + t + '</strong>');
  md = md.replace(/QQCODE(\d+)QQ/g, (m, i) => code[+i]);

  let html = marked.parse(md, { gfm: true, breaks: false });

  let errors = 0;
  html = html.replace(/QQMATH(\d+)QQ/g, (m, i) => {
    const { t, d } = math[+i];
    try {
      return katex.renderToString(t, { displayMode: d, throwOnError: true, strict: 'ignore', output: 'htmlAndMathml' });
    } catch (e) {
      errors++;
      console.warn('  [katex] ' + e.message.split('\n')[0] + '  ←  ' + t.slice(0, 60));
      return katex.renderToString(t, { displayMode: d, throwOnError: false, strict: 'ignore' });
    }
  });

  // 見出しに id を振り、目次を作る
  const toc = [];
  let n = 0;
  html = html.replace(/<h([23])>([\s\S]*?)<\/h\1>/g, (m, lv, inner) => {
    const id = 's' + (++n);
    toc.push({ lv: +lv, id, text: inner.replace(/<math[\s\S]*?<\/math>/g, '').replace(/<[^>]+>/g, '') });
    return `<h${lv} id="${id}">${inner}</h${lv}>`;
  });

  // 引用ブロックの先頭記号でコールアウト化
  const CLS = { '📰': 'case', '🪄': 'analogy', '🤔': 'why', '💡': 'tip', '⚠': 'warn', '🖥': 'viz', '✍': 'ex', '📌': 'key' };
  html = html.replace(/<blockquote>\s*<p>(<strong>)?\s*([📰🪄🤔💡⚠🖥✍📌])/gu, (m, strong, mark) =>
    `<blockquote class="callout ${CLS[mark]}">\n<p>${strong || ''}${mark}`);
  html = html.replace(/<blockquote>\s*<p>(<strong>)?\s*教科書対応/g, (m, strong) => `<blockquote class="callout textbook">\n<p>${strong || ''}教科書対応`);

  // 表は横スクロール枠に入れる
  html = html.replace(/<table>/g, '<div class="tbl"><table>').replace(/<\/table>/g, '</table></div>');
  return { html, toc, errors };
}

function esc(s) { return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }

function tocHtml(toc) {
  return '<nav class="toc" aria-label="目次"><div class="toc-h">この回の目次</div>'
    + toc.map(t => `<a class="lv${t.lv}" href="#${t.id}">${esc(t.text)}</a>`).join('') + '</nav>';
}

function page({ title, body, toc, n, extraHead = '' }) {
  const cur = n ? FLAT[n - 1] : null;
  const prev = n && n > 1 ? FLAT[n - 2] : null;
  const next = n && n < FLAT.length ? FLAT[n] : null;
  const chips = cur
    ? `<div class="chips"><span class="chip day">${esc(cur.day)}</span>`
      + `<a class="chip viz" href="../viz/${cur.href}">🖥 動く図で見る</a>`
      + `<a class="chip ex" href="../ex/${cur.ex}">✍ 演習で確かめる</a>`
      + `<a class="chip" href="symbols.html">記号表</a></div>`
    : `<div class="chips"><a class="chip" href="../index.html">▲ 地図（トップ）</a></div>`;
  const foot = cur
    ? `<div class="pn">${prev ? `<a class="pn-prev" href="${prev.note}">← ${esc(prev.label)}</a>` : '<span></span>'}`
      + `${next ? `<a class="pn-next" href="${next.note}">${esc(next.label)} →</a>` : '<a class="pn-next" href="../index.html">🎉 全 15 回を読了 — 地図に戻る →</a>'}</div>`
    : '';
  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${esc(title)} — 講義ノート</title>
<link rel="stylesheet" href="vendor/katex/katex.min.css">
<link rel="stylesheet" href="notes.css">${extraHead}
</head>
<body>
<header class="top">
  <a class="home" href="../index.html">▲ 地図（トップ）</a>
  <nav class="days">${SITE.cats.map((c, i) => `<span class="${cur && cur.dayIndex === i ? 'on' : ''}">${esc(c.name)}</span>`).join('')}</nav>
  <nav class="rounds">${FLAT.map((p, i) => `<a href="${p.note}" class="${cur && i === n - 1 ? 'on' : ''}" title="${esc(p.label)}">${i + 1}</a>`).join('')}</nav>
</header>
<div class="wrap">
  <main class="doc">
    ${chips}
    ${body}
    ${foot}
  </main>
  <aside class="side">${tocHtml(toc)}</aside>
</div>
<footer class="bottom">教科書：加藤・田岡『電力システム工学の基礎』 ／ 電力エネルギーシステム解析の基礎と応用 ／ 数式描画：KaTeX（同梱・MIT）</footer>
<script>
// 目次の現在位置ハイライト（外部依存なし・file:// で動く）
(function(){
  var links=[].slice.call(document.querySelectorAll('.toc a')); if(!links.length) return;
  var heads=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function upd(){ var y=window.scrollY+120, i=0; for(var k=0;k<heads.length;k++){ if(heads[k]&&heads[k].offsetTop<=y) i=k; }
    links.forEach(function(a,k){ a.classList.toggle('on',k===i); }); }
  window.addEventListener('scroll',upd,{passive:true}); upd();
})();
</script>
</body>
</html>`;
}

// ---- 15 回のノート ----
let total = 0, totalErr = 0;
const ONLY = process.argv.slice(2).filter(a => a !== "--only").map(a => a.replace(/\.html$|\.md$/, ""));
const files = fs.readdirSync(SRC).filter(f => /^ch\d\d_.*\.md$/.test(f)).filter(f => !ONLY.length || ONLY.includes(f.slice(0, 4))).sort();
for (const f of files) {
  const n = +f.slice(2, 4);
  const md = fs.readFileSync(path.join(SRC, f), 'utf8');
  const title = (md.match(/^#\s+(.+)$/m) || [, f])[1].replace(/\*\*/g, '');
  const { html, toc, errors } = convert(md);
  const outName = FLAT[n - 1].note;
  fs.writeFileSync(path.join(OUT, outName), page({ title, body: html, toc, n }));
  total++; totalErr += errors;
  console.log(`${f} → notes/${outName}  (${toc.length} 見出し, 数式エラー ${errors})`);
}

// ---- 付録：記号表・教科書対応 ----
for (const [src, out, title] of ONLY.length ? [] : [['記号表.md', 'symbols.html', '記号表'], ['教科書対応.md', 'textbook.html', '教科書対応']]) {
  const p = path.join(ROOT, src);
  if (!fs.existsSync(p)) continue;
  const md = fs.readFileSync(p, 'utf8');
  const { html, toc, errors } = convert(md);
  fs.writeFileSync(path.join(OUT, out), page({ title, body: html, toc, n: 0 }));
  totalErr += errors;
  console.log(`${src} → notes/${out}  (数式エラー ${errors})`);
}
console.log(`\n${total} ノート + 付録を生成。KaTeX エラー合計 ${totalErr}`);
if (totalErr) process.exitCode = 1;
