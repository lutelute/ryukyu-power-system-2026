// ===== 全ページが読み込む唯一の共有 JS =====
//
// 各ページは末尾で <script src="site.js"></script><script src="nav.js"></script> を読むだけ。
// ここ 1 ファイルで全ページに効くので、「全ページに ○○ を足したい」は原則ここに書く
//   （個別ページを N 回編集しない ＝ このプロジェクトで最も効く運用ルール）。
//
// 担当している 6 つの仕事：
//   ① 数式の見た目を教科書品質に（.eq / .frac / .rad / .read 読み下し）
//   ② アクセシビリティの底上げ（コントラスト・フォーカス可視化・reduced-motion）
//   ③ カテゴリ折りたたみナビの注入（site.js の SITE.cats から生成）
//   ④ 図と言葉の同期（.ref → 'hl' イベント）
//   ⑤ canvas の代替テキスト・ステッパーのキーボード操作
//   ⑥ 学習順路フッター（← 前のテーマ／次のテーマ →）
//
// スタイルはすべて head 末尾への <style> 注入＝「後勝ち」で入れる。
// これにより、各ページの inline <style> や theme.css より確実に優先される。
(function () {
  const CFG = window.SITE || { cats: [], home: '../', pinned: [] };
  const cats = CFG.cats || [];
  // 現在ページのファイル名（'gradient.html' など）。ディレクトリ直アクセスは index.html 扱い。
  const cur = (location.pathname.split('/').pop() || 'index.html');

  // ===== ① 数式の見た目を全ページ一括で改善 =====
  // 各ページの inline `.eq{font-family:mono}` を body .eq の詳細度で上書きし、セリフ＋斜体変数に。
  (function injectMath() {
    if (document.getElementById('mathfmt')) return;
    const css =
      'body .eq{font-family:"STIX Two Math","Cambria Math","TeX Gyre Termes Math",Georgia,"Times New Roman",serif;font-size:15.5px;letter-spacing:.2px;line-height:2.05;}'
      + '.eq i,.eq var,.mvar{font-style:italic;}'
      + '.eq b{font-weight:600;}'
      + '.eq .op{font-style:normal;padding:0 .12em;opacity:.85;}'
      // 分数 <span class="frac"><span>分子</span><span>分母</span></span>
      + '.frac{display:inline-flex;flex-direction:column;vertical-align:-0.55em;text-align:center;margin:0 .22em;line-height:1.22;}'
      + '.frac>span:first-child{border-bottom:1.4px solid currentColor;padding:0 .45em 1px;}'
      + '.frac>span:last-child{padding:1px .45em 0;}'
      // 根号 <span class="rad">x</span>
      + '.rad{border-top:1.4px solid currentColor;padding:0 .3em;margin-left:.06em;}'
      + '.rad::before{content:"\\221A";margin-left:-.52em;margin-right:.02em;}'
      + '.mvec{font-weight:600;font-style:italic;}'
      // 読み下し行 <span class="read">読み：…</span> — 数式の意味を日本語で添える（必須部品）
      + '.eq .read{display:block;font-family:var(--gothic,sans-serif);font-size:11.5px;font-style:normal;color:var(--ink-3,#6e6a60);letter-spacing:.02em;line-height:1.7;margin-top:3px;border-top:1px dashed var(--rule,#dcd8cc);padding-top:3px;}'
      + '.eq .read i,.eq .read b{font-style:normal;font-weight:700;color:var(--ink-2,#52504a);}';
    const s = document.createElement('style');
    s.id = 'mathfmt'; s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  })();

  // ===== ② アクセシビリティ底上げ =====
  (function injectA11yStyles() {
    if (document.getElementById('a11yfmt')) return;
    const css =
      // 二次テキストのコントラスト：#928f84 は背景 #faf8f1 上で約 3.0:1（AA 未満）→ 約 5:1 に。
      ':root{--faint:#6e6a60;--ink-3:#6e6a60;}'
      // キーボードフォーカスの可視化（マウス操作では出さない）
      + ':focus-visible{outline:2px solid var(--accent,#1f9e8a);outline-offset:2px;border-radius:2px;}'
      + '.stp:focus-visible{outline-offset:-2px;}'
      // 前庭障害への配慮：CSS のアニメ/トランジションを抑制
      + '@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important;}}';
    const s = document.createElement('style');
    s.id = 'a11yfmt'; s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  })();
  // canvas 内の requestAnimationFrame は CSS では止まらないので、各ページが参照できるフラグを公開。
  // 各ページの draw 側で「真ならアニメを飛ばして最終状態を描く」を実装すること。
  try { window.__prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches; }
  catch (e) { window.__prefersReducedMotion = false; }

  // ===== ③ ナビ（カテゴリ折りたたみ）の見た目 =====
  // 色は var(--x, フォールバック) で受ける（theme.css を読んでいないページでも壊れない）。
  (function injectNavStyles() {
    if (document.getElementById('navfmt')) return;
    const css =
      '.nav{font-size:11px;line-height:1.7;letter-spacing:.03em;}'
      + '.nav .navhead{margin-bottom:8px;}'
      + '.nav .navhead a,.nav .navhead b{margin-right:16px;font-weight:600;text-decoration:none;color:var(--ink-2,#52504a);}'
      + '.nav .navhead a:hover{color:var(--ink,#1a1a17);text-decoration:underline;}'
      + '.nav .navhead b{color:var(--ink,#1a1a17);}'
      // 上段＝均一な分野タイル列（領域マップ）
      + '.nav .navcats{display:flex;flex-wrap:wrap;gap:5px;}'
      + '.nav button.navcat{font-family:inherit;font-size:11px;letter-spacing:.03em;color:var(--ink-2,#52504a);background:var(--panel,#fff);border:1px solid var(--rule,#dcd8cc);border-radius:2px;padding:3px 9px;cursor:pointer;white-space:nowrap;}'
      + '.nav button.navcat:hover{color:var(--ink,#1a1a17);border-color:var(--ink-3,#928f84);}'
      + '.nav button.navcat[aria-selected="true"]{color:var(--ink,#1a1a17);font-weight:700;border-color:var(--ink,#1a1a17);background:var(--panel-2,#f2efe6);}'
      + '.nav button.navcat.cur{box-shadow:inset 3px 0 0 var(--accent,#1f9e8a);padding-left:11px;}'
      + '.nav .navcat-n{color:var(--faint,#6e6a60);font-weight:400;letter-spacing:0;margin-left:1px;}'
      // 下段＝選択中分野の手法パネル
      + '.nav .navpanel{margin-top:7px;padding-top:6px;border-top:1px solid var(--rule,#dcd8cc);white-space:normal;color:var(--faint,#6e6a60);}'
      + '.nav .navpanel-cat{color:var(--ink,#1a1a17);font-weight:700;}'
      + '.nav .navpanel-arw{color:var(--ink-3,#928f84);margin:0 7px 0 4px;}'
      + '.nav .navpanel-hint{color:var(--faint,#6e6a60);font-style:italic;}'
      + '.nav .navpanel a{color:var(--ink-2,#52504a);text-decoration:none;white-space:nowrap;}'
      + '.nav .navpanel a:hover{color:var(--ink,#1a1a17);text-decoration:underline;}'
      + '.nav .navpanel .cur{color:var(--ink,#1a1a17);font-weight:700;white-space:nowrap;}'
      + '.nav .navpanel .sep{color:var(--faint,#6e6a60);margin:0 2px;}'
      // ページ末尾の学習順路フッター
      + '.navfoot{display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap;margin-top:30px;padding-top:12px;border-top:1px solid var(--rule,#dcd8cc);font-size:12.5px;letter-spacing:.02em;}'
      + '.navfoot a{text-decoration:none;}'
      + '.navfoot .navfoot-prev{color:var(--ink-3,#6e6a60);}'
      + '.navfoot .navfoot-next{color:var(--accent,#1f9e8a);font-weight:700;}'
      + '.navfoot a:hover{text-decoration:underline;color:var(--ink,#1a1a17);}';
    const s = document.createElement('style');
    s.id = 'navfmt'; s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
  })();

  // ===== ④ 図と言葉の同期 =====
  // 説明文に <span class="ref" data-hl="key">語</span> と書くと、ホバー/タップで
  // document に 'hl' イベント（detail = key / null）が飛ぶ。ページ側は
  //   document.addEventListener('hl', e => { HL = e.detail; draw_(); })
  // で受け、draw 内で該当部位を強調する。未対応ページでは単なる強調表示として無害。
  (function injectRefSync() {
    if (document.getElementById('reffmt')) return;
    const css =
      '.ref{border-bottom:1.5px dashed var(--accent,#1f9e8a);cursor:help;color:var(--ink,#1a1a17);font-weight:600;}'
      + '.ref:hover,.ref.on{background:rgba(31,158,138,0.16);border-bottom-style:solid;}';
    const s = document.createElement('style');
    s.id = 'reffmt'; s.textContent = css;
    (document.head || document.documentElement).appendChild(s);
    window.__hlKey = null;
    let lockEl = null; // タップ（クリック）で固定した .ref
    function fire(key) {
      window.__hlKey = key || null;
      try { document.dispatchEvent(new CustomEvent('hl', { detail: window.__hlKey })); } catch (e) { /* 旧環境 */ }
    }
    document.addEventListener('mouseover', function (e) {
      const r = e.target && e.target.closest ? e.target.closest('.ref') : null;
      if (r && !lockEl) fire(r.dataset.hl);
    });
    document.addEventListener('mouseout', function (e) {
      const r = e.target && e.target.closest ? e.target.closest('.ref') : null;
      if (r && !lockEl) fire(null);
    });
    document.addEventListener('click', function (e) {
      const r = e.target && e.target.closest ? e.target.closest('.ref') : null;
      if (!r) { if (lockEl) { lockEl.classList.remove('on'); lockEl = null; fire(null); } return; }
      if (lockEl === r) { r.classList.remove('on'); lockEl = null; fire(null); }
      else { if (lockEl) lockEl.classList.remove('on'); lockEl = r; r.classList.add('on'); fire(r.dataset.hl); }
    });
  })();

  // ===== ナビの描画 =====
  function tileHtml(cat, i, active, isCur) {
    return '<button class="navcat' + (isCur ? ' cur' : '') + '" role="tab" data-i="' + i + '"'
      + ' aria-selected="' + (active ? 'true' : 'false') + '" tabindex="' + (active ? '0' : '-1') + '">'
      + cat.name + '<span class="navcat-n">·' + cat.items.length + '</span>'
      + '</button>';
  }
  function catItemsHtml(cat) {
    return cat.items.map(function (p) {
      if (p.href === cur) return '<b class="cur">' + p.label + '</b>';
      return '<a href="' + p.href + '">' + p.label + '</a>';
    }).join(' <span class="sep">·</span> ');
  }
  function panelHtml(idx) {
    if (idx < 0) return '<span class="navpanel-hint">分野を選ぶと手法が並びます。</span>';
    return '<span class="navpanel-cat">' + cats[idx].name + '</span>'
      + '<span class="navpanel-arw">›</span> ' + catItemsHtml(cats[idx]);
  }

  function render() {
    const el = document.querySelector('.nav');
    if (!el) return;
    let curCat = -1;
    cats.forEach(function (c, i) {
      if (c.items.some(function (p) { return p.href === cur; })) curCat = i;
    });
    const pinned = (CFG.pinned || []).map(function (p) {
      return p.href === cur ? '<b>' + p.label + '</b>' : '<a href="' + p.href + '">' + p.label + '</a>';
    }).join('');
    const head = '<div class="navhead"><a href="' + (CFG.home || '../') + '">▲ 地図（トップ）</a>' + pinned + '</div>';
    const tiles = cats.map(function (c, i) { return tileHtml(c, i, i === curCat, i === curCat); }).join('');
    el.innerHTML = head
      + '<div class="navcats" role="tablist" aria-label="分野">' + tiles + '</div>'
      + '<div class="navpanel">' + panelHtml(curCat) + '</div>';

    // タイルのクリック／←→キーで下パネルを切り替え（イベント委譲・1 回だけ束縛）
    if (!el.dataset.navbound) {
      el.dataset.navbound = '1';
      const activate = function (btn, focus) {
        el.querySelectorAll('.navcat').forEach(function (b) { b.setAttribute('aria-selected', 'false'); b.setAttribute('tabindex', '-1'); });
        btn.setAttribute('aria-selected', 'true'); btn.setAttribute('tabindex', '0');
        const panel = el.querySelector('.navpanel');
        if (panel) panel.innerHTML = panelHtml(+btn.getAttribute('data-i'));
        if (focus) btn.focus();
      };
      el.addEventListener('click', function (e) {
        const btn = e.target && e.target.closest ? e.target.closest('.navcat') : null;
        if (btn && el.contains(btn)) activate(btn, false);
      });
      el.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
        const btn = e.target && e.target.closest ? e.target.closest('.navcat') : null;
        if (!btn || !el.contains(btn)) return;
        e.preventDefault();
        const list = Array.prototype.slice.call(el.querySelectorAll('.navcat'));
        const next = list[list.indexOf(btn) + (e.key === 'ArrowRight' ? 1 : -1)];
        if (next) activate(next, true);
      });
    }
  }

  // ===== ⑤ DOM 強化：canvas の代替テキスト＋ステッパーのキーボード操作 =====
  function enhanceA11y() {
    const title = ((document.querySelector('h1') || {}).textContent || document.title || '可視化').trim();
    document.querySelectorAll('canvas').forEach(function (cv) {
      if (!cv.getAttribute('role')) cv.setAttribute('role', 'img');
      if (!cv.getAttribute('aria-label')) cv.setAttribute('aria-label', title + ' — 図（Canvas による可視化）');
    });
    // div 製ステッパーを role=tablist/tab 化し、Enter/Space/矢印で操作可能に。
    // innerHTML を作り直すページ／class だけ差し替えるページの両方に追従する。
    function decorate(stepper) {
      if (stepper.getAttribute('role') !== 'tablist') stepper.setAttribute('role', 'tablist');
      stepper.querySelectorAll('.stp').forEach(function (stp) {
        stp.setAttribute('role', 'tab');
        if (stp.getAttribute('tabindex') === null) stp.setAttribute('tabindex', '0');
        stp.setAttribute('aria-selected', stp.classList.contains('active') ? 'true' : 'false');
        if (stp.dataset.a11y) return;            // ハンドラ付与は 1 度だけ（冪等）
        stp.dataset.a11y = '1';
        stp.addEventListener('keydown', function (e) {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); stp.click(); }
          else if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
            e.preventDefault();
            const list = Array.prototype.slice.call(stepper.querySelectorAll('.stp'));
            const next = list[list.indexOf(stp) + (e.key === 'ArrowRight' ? 1 : -1)];
            if (next) next.focus();
          }
        });
      });
    }
    document.querySelectorAll('.stepper').forEach(function (stepper) {
      decorate(stepper);
      // 付与するのは role/aria-*/tabindex/data-* のみ（class は書かない）→ 自己再発火しない
      try {
        new MutationObserver(function () { decorate(stepper); })
          .observe(stepper, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
      } catch (e) { /* 監視できない環境でも初期装飾は効く */ }
    });
  }

  // ===== ⑥ 学習順路フッター =====
  // SITE.cats のフラット順＝学習順路。「読み終えたら次はどこへ」をページ下端に出す。
  // ステップ UI の「次へ」との混同を避けるため文言は「次のテーマ」。順路に無いページには出さない。
  function injectFooterNav() {
    if (document.querySelector('.navfoot')) return;
    const flat = [];
    cats.forEach(function (c) { c.items.forEach(function (p) { flat.push(p); }); });
    const idx = flat.map(function (p) { return p.href; }).indexOf(cur);
    if (idx < 0) return;
    const prev = flat[idx - 1], next = flat[idx + 1];
    const el = document.createElement('div');
    el.className = 'navfoot';
    el.innerHTML =
      (prev ? '<a class="navfoot-prev" href="' + prev.href + '">← 前のテーマ：' + prev.label + '</a>' : '<span></span>')
      + (next ? '<a class="navfoot-next" href="' + next.href + '">次のテーマ：' + next.label + ' →</a>'
        : '<a class="navfoot-next" href="' + (CFG.home || '../') + '">🎉 全テーマ完走 — 地図に戻る →</a>');
    (document.querySelector('.wrap') || document.body).appendChild(el);
  }

  function init() { render(); enhanceA11y(); injectFooterNav(); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
