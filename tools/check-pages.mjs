// tools/check-pages.mjs — 全ページの静的健全性チェック。`node tools/check-pages.mjs` で実行（CI でも走る）。
//
// 見るのは 2 つだけ。依存パッケージなし・Node 標準のみで動く（＝いつでも走らせられる）。
//   ① リンク切れ — href / src が指すローカルファイルが実在するか
//   ② インライン <script> の JS 構文 — node --check で構文エラーを検出
//      （HTML コメント内の <script> は除去してから判定する）
//
// 実ブラウザでの実行時エラー確認は tools/crawl-pages.mjs（Playwright）が担当。
// この 2 本で「壊れたページを公開してしまう」事故はほぼ止まる。
import { readFileSync, readdirSync, existsSync, writeFileSync, mkdtempSync, rmSync, statSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join, dirname, resolve, extname } from 'node:path';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SCAN_DIRS = ['.', 'viz', 'notes', 'ex'];          // ページを置くディレクトリ。増やしたらここに足す
const SKIP = /^(https?:|mailto:|data:|javascript:|#|\/\/)/;

let failed = 0;
const ok = m => console.log('  ok   ' + m);
const fail = m => { console.error('  FAIL ' + m); failed++; };

// ---- 対象 HTML の収集 ----
const pages = [];
for (const d of SCAN_DIRS) {
  const abs = join(root, d);
  if (!existsSync(abs)) continue;
  for (const f of readdirSync(abs)) {
    if (extname(f) !== '.html') continue;
    const p = join(abs, f);
    if (statSync(p).isFile()) pages.push(p);
  }
}
if (pages.length === 0) { console.error('走査対象の HTML が見つかりません'); process.exit(1); }

// ---- ① リンク切れ ----
// <script> の "中身" は対象外。JS が組み立てる href（'viz/' + p.href など）は静的に追えないため。
// 開始タグは残すので <script src="..."> の実在チェックは効いたままになる。
for (const page of pages) {
  const html = readFileSync(page, 'utf8').replace(/(<script[^>]*>)[\s\S]*?<\/script>/gi, '$1</script>');
  const rel = page.slice(root.length + 1);
  for (const m of html.matchAll(/(?:href|src)\s*=\s*"([^"]+)"/g)) {
    const raw = m[1].trim();
    if (!raw || SKIP.test(raw)) continue;
    let target = raw.split('#')[0].split('?')[0];
    if (!target) continue;
    try { target = decodeURIComponent(target); } catch (e) {}   // 日本語パス（%E5%9B%B3 = 図）を戻す
    let abs = resolve(dirname(page), target);
    if (target.endsWith('/')) abs = join(abs, 'index.html');
    if (!existsSync(abs)) fail(`${rel} → リンク切れ: ${raw}`);
  }
}
ok(`リンク整合性 — ${pages.length} ページ走査`);

// ---- ② インライン <script> の構文 ----
const tmp = mkdtempSync(join(tmpdir(), 'checkpages-'));
let scripts = 0;
try {
  for (const page of pages) {
    const rel = page.slice(root.length + 1);
    // HTML コメントを先に落とす（コメントアウトされた <script> を拾わないため）
    const html = readFileSync(page, 'utf8').replace(/<!--[\s\S]*?-->/g, '');
    let i = 0;
    for (const m of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)) {
      const attrs = m[1] || '', code = m[2];
      if (/\ssrc\s*=/i.test(attrs)) continue;          // 外部ファイル参照はここでは見ない
      if (!code.trim()) continue;
      const isModule = /type\s*=\s*"module"/i.test(attrs);
      const file = join(tmp, `p${scripts}_${i++}.${isModule ? 'mjs' : 'js'}`);
      writeFileSync(file, code);
      const r = spawnSync(process.execPath, ['--check', file], { encoding: 'utf8' });
      if (r.status !== 0) fail(`${rel} → JS 構文エラー\n${(r.stderr || '').split('\n').slice(0, 6).join('\n')}`);
      scripts++;
    }
  }
} finally { rmSync(tmp, { recursive: true, force: true }); }
ok(`JS 構文 — インライン script ${scripts} 本を node --check`);

console.log(failed ? `\n✗ ${failed} 件失敗` : `\n✓ 全 ${pages.length} ページ合格（リンク・構文）`);
process.exit(failed ? 1 : 0);
