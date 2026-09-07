// tools/sync-intuition.mjs — スライド/chNN.md の「直感」スライド（一言・事例・たとえ話・地図・なぜそう考えるか）を
// ノート/chNN_*.md の冒頭「## まず直感で（3 分でつかむ）」節に流し込む（マーカー間を置換。何度でも実行可）。
//   node tools/sync-intuition.mjs          # 全部
//   node tools/sync-intuition.mjs ch08     # 1 回分
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const only = process.argv.slice(2);
const strip = s => s.replace(/<[^>]+>/g, '').replace(/==([^=]+)==/g, '**$1**').trim();
const clean = s => strip(s).replace(/\s*\n\s*/g, ' ');

for (const md of fs.readdirSync(path.join(ROOT, 'スライド')).filter(f => /^ch\d\d\.md$/.test(f)).sort()) {
  const ch = md.slice(0, 4);
  if (only.length && !only.includes(ch)) continue;
  const deck = fs.readFileSync(path.join(ROOT, 'スライド', md), 'utf8');
  const slides = deck.split(/\n---\n/).map(s => s.trim());
  const byClass = c => slides.filter(s => s.startsWith(`<!-- _class: ${c} -->`));
  const note = s => { const m = s.match(/<!-- note:\s*([\s\S]*?)-->/); return m ? clean(m[1]) : ''; };

  const statement = byClass('statement')[0];
  const oneLiner = statement ? clean(statement.replace(/<!--[\s\S]*?-->/g, '')) : '';

  const sec = byClass('sections')[0] || '';
  const cases = [...sec.matchAll(/<span class="sec-title">([\s\S]*?)<\/span>\s*<span class="sec-body">([\s\S]*?)<\/span>/g)]
    .map(m => ({ title: clean(m[1]), body: clean(m[2]) }));
  const caseNote = note(sec);

  const cols = byClass('cols-2')[0] || '';
  const colParts = cols.split(/<div>\s*\n/).slice(1).map(p => p.split('</div>')[0]);
  const colTitle = p => (p.match(/###\s*(.+)/) || [, ''])[1].trim();
  const colItems = p => [...p.matchAll(/^- (.+)$/gm)].map(m => clean(m[1]));
  const analogyTitle = clean((cols.match(/^# (.+)$/m) || [, ''])[1]).replace(/^たとえ話\s*[—-]\s*/, '');
  const analogyNote = note(cols);

  const agenda = byClass('agenda')[0] || '';
  const map = [...agenda.matchAll(/^\d+\.\s+(.+)$/gm)].map(m => clean(m[1]));

  const blocks = byClass('blocks')[0] || '';
  const whys = [...blocks.matchAll(/<div class="bk (\w+)">\s*<span class="bk-title">([\s\S]*?)<\/span>\s*<span class="bk-body">([\s\S]*?)<\/span>/g)]
    .map(m => ({ kind: m[1], title: clean(m[2]), body: clean(m[3]) }));

  const n = +ch.slice(2);
  const out = [];
  out.push('<!-- intuition:start（tools/sync-intuition.mjs が スライド/' + md + ' から生成。直接編集せずスライドを直す）-->');
  out.push('> **✍ 演習**：[`ex/' + ch + '.html`](../ex/' + ch + '.html) — 学籍番号ごとに数値が変わる問題。採点・途中式つき。');
  out.push('> **📊 スライド**：`スライド/' + ch + '.pptx`（講義用）');
  out.push('', '---', '', '## まず直感で（3 分でつかむ）', '');
  if (oneLiner) out.push('> **📌 一言でいうと**：' + oneLiner, '');
  if (colParts.length === 2) {
    out.push('> **🪄 たとえ話：' + analogyTitle + '**', '>');
    out.push('> | ' + colTitle(colParts[0]) + ' | ' + colTitle(colParts[1]) + ' |', '> |:--|:--|');
    const a = colItems(colParts[0]), b = colItems(colParts[1]);
    for (let i = 0; i < Math.max(a.length, b.length); i++) out.push('> | ' + (a[i] || '') + ' | ' + (b[i] || '') + ' |');
    if (analogyNote) out.push('>', '> ' + analogyNote);
    out.push('');
  }
  for (const c of cases) out.push('> **📰 事例：' + c.title + '**', '> ' + c.body, '');
  if (caseNote) out.push('> **🤔 この回の式で読むと**：' + caseNote, '');
  for (const w of whys) out.push('> **' + (w.kind === 'alert' ? '⚠ ' : '🤔 ') + w.title + '**', '> ' + w.body, '');
  if (map.length) out.push('**この回の地図**：' + map.map((m, i) => 'Ⅰ Ⅱ Ⅲ Ⅳ Ⅴ'.split(' ')[i] + ' ' + m).join(' → '), '');
  out.push('<!-- intuition:end -->');
  const block = out.join('\n');

  const noteFile = fs.readdirSync(path.join(ROOT, 'ノート')).find(f => f.startsWith(ch + '_'));
  if (!noteFile) { console.log('✗ ' + ch + ': ノートが見つからない'); continue; }
  const p = path.join(ROOT, 'ノート', noteFile);
  let s = fs.readFileSync(p, 'utf8');
  if (s.includes('<!-- intuition:start')) {
    s = s.replace(/<!-- intuition:start[\s\S]*?<!-- intuition:end -->/, block);
  } else {
    // 🖥 動くインフォグラフ の引用ブロックの直後（次の '---' 行の直前）に挿入
    const i = s.indexOf('> **🖥 動くインフォグラフ**');
    const j = i >= 0 ? s.indexOf('\n---', i) : -1;
    if (j < 0) { console.log('✗ ' + ch + ': 🖥 ブロックが無い'); continue; }
    s = s.slice(0, j + 1) + '\n' + block + '\n' + s.slice(j + 1);
  }
  fs.writeFileSync(p, s);
  console.log('✓ ' + ch + ': 一言 ' + (oneLiner ? 1 : 0) + ', 事例 ' + cases.length + ', たとえ ' + (colParts.length === 2 ? 1 : 0) + ', なぜ ' + whys.length + ', 地図 ' + map.length);
}
