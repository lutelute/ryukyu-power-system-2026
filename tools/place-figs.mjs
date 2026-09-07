// tools/place-figs.mjs — スライド/chNN.figs.json に従い、ノート/chNN_*.md の各節末尾に図と説明を置く（何度でも実行可）
//   node tools/place-figs.mjs ch01
// figs.json の形: [{ "after": "### 1.2.1", "file": "ch01_chain.png", "num": "図 1.1", "caption": "…" }, …]
//   after: この見出しで始まる節の末尾（次の見出しの直前）に置く
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ch = process.argv[2];
if (!ch) { console.error('usage: node tools/place-figs.mjs chNN'); process.exit(1); }
const spec = JSON.parse(fs.readFileSync(path.join(ROOT, 'スライド', ch + '.figs.json'), 'utf8'));
const noteFile = fs.readdirSync(path.join(ROOT, 'ノート')).find(f => f.startsWith(ch + '_'));
const p = path.join(ROOT, 'ノート', noteFile);
let s = fs.readFileSync(p, 'utf8');
// 既存の自動配置を除去
s = s.replace(/\n<!-- fig:([^ ]+) -->[\s\S]*?<!-- \/fig -->\n?/g, '\n');
const lines = s.split('\n');
let placed = 0;
for (const f of spec) {
  if (!fs.existsSync(path.join(ROOT, '図', f.file))) { console.log('✗ 図が無い: ' + f.file); continue; }
  const i = lines.findIndex(l => l.startsWith(f.after));
  if (i < 0) { console.log('✗ 見出しが無い: ' + f.after); continue; }
  // 次の見出し（同レベル以上）or 水平線 or 文末
  const lvl = (f.after.match(/^#+/) || ['###'])[0].length;
  let j = i + 1;
  while (j < lines.length) {
    const m = lines[j].match(/^(#+)\s/);
    if ((m && m[1].length <= lvl) || lines[j].trim() === '---') break;
    j++;
  }
  // 末尾の空行を飛ばして挿入
  let k = j; while (k > i + 1 && lines[k - 1].trim() === '') k--;
  const block = ['', `<!-- fig:${f.file} -->`, `![${f.num}](../図/${f.file})`, `*${f.num}　${f.caption}*`, '<!-- /fig -->'];
  lines.splice(k, 0, ...block);
  placed++;
}
fs.writeFileSync(p, lines.join('\n'));
console.log(`✓ ${ch}: ${placed}/${spec.length} 図を配置 → ${noteFile}`);
