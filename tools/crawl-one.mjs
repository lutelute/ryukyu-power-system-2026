// tools/crawl-one.mjs — 1 ページを実ブラウザで開き、全スライドを通しクリックして壊れていないか見る。
//
// 教材を 1 本書いている最中に、いちばん回数を使うツール。
//   1) リポジトリ直下で:  python3 -m http.server 8000
//   2) 別ターミナルで:    node tools/crawl-one.mjs viz/example-gradient.html [8000]
//
// 見るもの: console error / 未捕捉例外 / リクエスト失敗。
// 「見た目が正しいか」は測れないので、これが通ったら必ず自分の目でも 1 周する。
import { chromium } from 'playwright';

const path = process.argv[2];
const port = process.argv[3] || '8000';
if (!path) { console.error('使い方: node tools/crawl-one.mjs viz/<slug>.html [port]'); process.exit(1); }

const url = `http://localhost:${port}/${path.replace(/^\//, '')}`;
const errs = [];

const browser = await chromium.launch();
const page = await (await browser.newContext()).newPage();
page.on('console', m => { if (m.type() === 'error') errs.push('[console] ' + m.text()); });
page.on('pageerror', e => errs.push('[pageerror] ' + e.message));
page.on('requestfailed', r => errs.push('[requestfailed] ' + r.url()));

await page.goto(url, { waitUntil: 'networkidle' });
await page.waitForTimeout(800);

// 全スライドを通しでクリックし、各 draw() を 1 度は実行させる。
// 「次へ」が disabled になったら最後まで来た合図。
let clicks = 0;
for (let i = 0; i < 40; i++) {
  const btn = page.locator('#nextBtn');
  if (await btn.count() === 0) break;
  if (await btn.isDisabled()) break;
  await btn.click();
  clicks++;
  await page.waitForTimeout(180);
}
// 章タブも一通り踏む（章の先頭スライドで別の分岐が走ることがある）
const tabs = page.locator('.stepper .stp');
for (let i = 0; i < await tabs.count(); i++) { await tabs.nth(i).click(); await page.waitForTimeout(200); }

const slides = await page.locator('.explain .lbl').textContent().catch(() => '');
await browser.close();

console.log(`${path}  — 「次へ」${clicks} 回 / ${slides || 'ラベル取得不可'}`);
if (errs.length) { console.error('✗ NG\n' + errs.join('\n')); process.exit(1); }
console.log('✓ OK — console error・例外・失敗リクエストなし');
