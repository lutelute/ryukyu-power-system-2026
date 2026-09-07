// tools/test-ex.mjs — 演習ページ ex/chNN.html の問題生成器を Node で検証する。
//   node tools/test-ex.mjs ch08          # 1 回分
//   node tools/test-ex.mjs all           # 全部
// 検査項目: 生成が例外なく走る／answers の value が有限／tol・abs が妥当／steps が 2 つ以上／
//           「答えを見る」で入る 4 桁丸め値が採点を通る（許容誤差が狭すぎない）／20 シードで NaN が出ない
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const targets = (!args.length || args[0] === 'all')
  ? fs.readdirSync(path.join(ROOT, 'ex')).filter(f => /^ch\d\d\.html$/.test(f)).map(f => f.slice(0, 4)).sort()
  : args.map(a => a.replace(/\.html$/, ''));

let failed = 0;
for (const ch of targets) {
  const file = path.join(ROOT, 'ex', ch + '.html');
  if (!fs.existsSync(file)) { console.log(`✗ ${ch}: ex/${ch}.html がありません`); failed++; continue; }
  const html = fs.readFileSync(file, 'utf8');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).filter(s => s.includes('EX.page'));
  if (scripts.length !== 1) { console.log(`✗ ${ch}: EX.page を呼ぶ <script> が ${scripts.length} 個（1 個であること）`); failed++; continue; }

  const sandbox = { window: {}, console, Math, Number, JSON, String, Array, Object, isFinite, parseFloat };
  sandbox.window.window = sandbox.window;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'viz', 'site.js'), 'utf8'), sandbox);
  vm.runInContext(fs.readFileSync(path.join(ROOT, 'ex', 'ex.js'), 'utf8'), sandbox);
  let spec = null;
  sandbox.window.EX.page = s => { spec = s; };
  sandbox.EX = sandbox.window.EX; sandbox.SITE = sandbox.window.SITE;
  try { vm.runInContext(scripts[0], sandbox, { filename: file }); } catch (e) { console.log(`✗ ${ch}: スクリプト実行エラー: ${e.message}`); failed++; continue; }
  if (!spec) { console.log(`✗ ${ch}: EX.page が呼ばれていません`); failed++; continue; }
  const expectedCh = +ch.slice(2);
  if (spec.ch !== expectedCh) { console.log(`✗ ${ch}: spec.ch=${spec.ch}（${expectedCh} であること）`); failed++; }
  if (!Array.isArray(spec.problems) || spec.problems.length < 3) { console.log(`✗ ${ch}: problems が 3 問未満`); failed++; continue; }

  const { mulberry32 } = sandbox.window.EX;
  const errs = [];
  spec.problems.forEach((p, i) => {
    if (!p.id) errs.push(`問${i + 1}: id がない`);
    if (!p.title) errs.push(`問${i + 1}: title がない`);
    const seen = new Set();
    for (let seed = 1; seed <= 20; seed++) {
      let g;
      try { g = p.gen(mulberry32(seed * 7919 + i)); } catch (e) { errs.push(`問${i + 1} seed${seed}: gen 例外 ${e.message}`); break; }
      if (!g || typeof g.q !== 'string' || !g.q.trim()) errs.push(`問${i + 1} seed${seed}: q がない`);
      if (!Array.isArray(g.answers) || !g.answers.length) { errs.push(`問${i + 1} seed${seed}: answers が空`); continue; }
      if (!Array.isArray(g.steps) || g.steps.length < 2) errs.push(`問${i + 1} seed${seed}: steps が 2 つ未満`);
      g.answers.forEach((a, k) => {
        if (typeof a.value !== 'number' || !isFinite(a.value)) { errs.push(`問${i + 1} seed${seed} 答${k + 1}(${a.label}): value=${a.value}`); return; }
        if (!a.label) errs.push(`問${i + 1} 答${k + 1}: label がない`);
        const tol = a.tol === undefined ? 0.02 : a.tol;
        const tolAbs = Math.max(a.abs || 0, tol * Math.abs(a.value));
        if (tolAbs <= 0) errs.push(`問${i + 1} seed${seed} 答${k + 1}(${a.label}): 許容誤差 0（value=${a.value}。abs を指定）`);
        const shown = Number(a.value.toPrecision(4));
        if (Math.abs(shown - a.value) > tolAbs + 1e-12) errs.push(`問${i + 1} seed${seed} 答${k + 1}(${a.label}): 4 桁表示値 ${shown} が許容誤差 ${tolAbs} を外れる`);
        if (String(g.steps.join(' ')).includes('NaN')) errs.push(`問${i + 1} seed${seed}: steps に NaN`);
      });
      seen.add(g.answers.map(a => a.value.toPrecision(3)).join(','));
    }
    if (seen.size < 3) errs.push(`問${i + 1}: 20 シードで答えの組が ${seen.size} 通りしかない（数値が変わっていない）`);
  });
  const uniq = errs.filter((e, k) => errs.indexOf(e) === k);
  if (uniq.length) { failed++; console.log(`✗ ${ch}: ${spec.problems.length} 問, 問題 ${uniq.length} 件`); uniq.slice(0, 12).forEach(e => console.log('    - ' + e)); }
  else {
    const g = spec.problems[0].gen(mulberry32(7919));
    console.log(`✓ ${ch}: ${spec.problems.length} 問 OK（例: 問1 ${g.answers.map(a => a.label + '=' + Number(a.value.toPrecision(4)) + (a.unit ? ' ' + a.unit : '')).join(', ')}）`);
  }
}
if (failed) { console.log(`\n${failed} 回分に問題あり`); process.exitCode = 1; } else console.log('\nすべて OK');
