// ex/ex.js — 演習エンジン（外部依存ゼロ・file:// で動く）
// 使い方: 各回の ex/chNN.html で EX.page({ ch: 8, intro: '…', problems: [ … ] }) を呼ぶ。
// 問題 1 件の形:
//   { id: 'k-def', title: '系統定数を求める', tags: ['8.2.5'],
//     gen(rng) { … return { given: [['系統容量 S', '1000 MW'], …], q: '問い（HTML）',
//                         answers: [{ key:'K', label:'K', unit:'MW/Hz', value: 100, tol: .02 }],
//                         steps: ['途中式 1（HTML）', …], insight: '一言（HTML）' }; } }
// ・数値は rng（mulberry32）からだけ作る。Math.random は使わない（学籍番号で再現できるため）
// ・tol は相対誤差（既定 2%）。0 付近の答えは abs（絶対誤差）を指定する
window.EX = (function () {
  'use strict';

  // ---------- 乱数（シード付き） ----------
  function mulberry32(a) {
    return function () {
      a |= 0; a = a + 0x6D2B79F5 | 0;
      let t = Math.imul(a ^ a >>> 15, 1 | a);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function hash(str) { // FNV-1a 32bit
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return h >>> 0;
  }
  const rint = (rng, lo, hi, step) => { step = step || 1; const n = Math.floor((hi - lo) / step + 1e-9); return lo + step * Math.floor(rng() * (n + 1)); };
  const pick = (rng, arr) => arr[Math.floor(rng() * arr.length)];
  const round = (v, step) => Math.round(v / step) * step;

  // ---------- 数値表示 ----------
  function fmt(v, d) {
    if (v === null || v === undefined || !isFinite(v)) return '—';
    if (typeof d === 'number') return Number(v.toFixed(d)).toLocaleString('ja-JP', { maximumFractionDigits: d, minimumFractionDigits: d });
    const a = Math.abs(v);
    if (a >= 10000) return Math.round(v).toLocaleString('ja-JP');
    if (a >= 1000) return v.toFixed(0);
    if (a >= 100) return v.toFixed(1);
    if (a >= 10) return v.toFixed(2);
    if (a >= 1) return v.toFixed(3);
    if (a === 0) return '0';
    return v.toPrecision(3);
  }
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // ---------- 保存（localStorage は file:// でも使える。無ければ黙って諦める） ----------
  const KEY = ch => 'ex.ch' + String(ch).padStart(2, '0');
  function load(ch) { try { return JSON.parse(localStorage.getItem(KEY(ch)) || '{}'); } catch (e) { return {}; } }
  function save(ch, st) { try { localStorage.setItem(KEY(ch), JSON.stringify(st)); } catch (e) {} }

  // ---------- ページ生成 ----------
  function page(spec) {
    const SITE = window.SITE || { cats: [] };
    const flat = []; SITE.cats.forEach((c, ci) => c.items.forEach(p => flat.push(Object.assign({ day: c.name, dayIndex: ci }, p))));
    const cur = flat[spec.ch - 1] || { label: '第' + spec.ch + '回', href: '', note: '', day: '' };
    const prev = flat[spec.ch - 2], next = flat[spec.ch];
    const st = load(spec.ch);
    let seedText = st.seed || '';
    let variant = 0;
    const root = document.getElementById('ex') || document.body.appendChild(Object.assign(document.createElement('div'), { id: 'ex' }));

    root.innerHTML = `
      <header class="top">
        <a class="home" href="../index.html">▲ 地図（トップ）</a>
        <span class="day">${esc(cur.day)}</span>
        <nav class="rounds">${flat.map((p, i) => `<a href="${p.ex}" class="${i === spec.ch - 1 ? 'on' : ''}" title="${esc(p.label)}">${i + 1}</a>`).join('')}</nav>
      </header>
      <div class="wrap">
        <h1>${esc(cur.label)} <span class="sub">演習</span></h1>
        <div class="chips">
          <a class="chip note" href="../notes/${cur.note}">📖 講義ノート</a>
          <a class="chip viz" href="../viz/${cur.href}">🖥 動く図</a>
          <a class="chip" href="../notes/symbols.html">記号表</a>
        </div>
        <p class="intro">${spec.intro || ''}</p>
        <div class="seedbox">
          <label>学籍番号（または好きな文字列）<input id="seed" type="text" placeholder="例: 245701A" value="${esc(seedText)}"></label>
          <button id="go" class="primary">この番号で出題</button>
          <button id="alt">別の数値で</button>
          <span class="score" id="score"></span>
        </div>
        <p class="hint">番号ごとに数値が変わります。答えを入力して「採点」。行き詰まったら「途中式」を開いてください。正解は 2% の誤差まで認めます。</p>
        <div id="problems"></div>
        <div class="pn">
          ${prev ? `<a class="pn-prev" href="${prev.ex}">← ${esc(prev.label)} の演習</a>` : '<span></span>'}
          ${next ? `<a class="pn-next" href="${next.ex}">${esc(next.label)} の演習 →</a>` : '<a class="pn-next" href="../index.html">🎉 全回の演習を完走 — 地図に戻る →</a>'}
        </div>
      </div>
      <footer class="bottom">数値はブラウザ内でその場で計算しています（サーバー通信なし）。採点結果はこの端末のブラウザにだけ保存されます。</footer>`;

    const $ = s => root.querySelector(s);
    const probsEl = $('#problems');
    let current = [];

    function build() {
      seedText = $('#seed').value.trim() || 'guest';
      const rngBase = hash(seedText + ':ch' + spec.ch + ':v' + variant);
      current = spec.problems.map((p, i) => {
        const rng = mulberry32(rngBase + i * 7919);
        const g = p.gen(rng);
        return Object.assign({ id: p.id || 'p' + i, title: p.title || '', tags: p.tags || [] }, g);
      });
      render();
    }

    function render() {
      const done = st.solved || {};
      probsEl.innerHTML = current.map((p, i) => `
        <section class="prob ${done[p.id] ? 'solved' : ''}" data-i="${i}">
          <div class="prob-h"><span class="pnum">問 ${spec.ch}-${i + 1}</span><span class="ptitle">${esc(p.title)}</span>
            ${p.tags.length ? `<span class="ptags">${p.tags.map(t => '<span>' + esc(t) + '</span>').join('')}</span>` : ''}
            <span class="pstat">${done[p.id] ? '✓ 正解済み' : ''}</span></div>
          ${p.given && p.given.length ? `<table class="given">${p.given.map(r => `<tr><th>${r[0]}</th><td>${r[1]}</td></tr>`).join('')}</table>` : ''}
          <div class="q">${p.q}</div>
          <div class="answers">${p.answers.map((a, k) => `
            <label class="ans" data-k="${k}"><span class="alabel">${a.label}</span>
              <input type="number" step="any" inputmode="decimal" placeholder="?">
              <span class="unit">${a.unit || ''}</span><span class="mark"></span></label>`).join('')}
          </div>
          <div class="btns">
            <button class="grade primary">採点</button>
            <button class="steps-btn">途中式を見る</button>
            <button class="reveal">答えを見る</button>
          </div>
          <div class="fb"></div>
          <ol class="steps" hidden>${(p.steps || []).map(s => `<li>${s}</li>`).join('')}</ol>
          ${p.insight ? `<div class="insight" hidden>💡 ${p.insight}</div>` : ''}
        </section>`).join('');
      updScore();
    }

    function updScore() {
      const done = st.solved || {}; const n = current.filter(p => done[p.id]).length;
      $('#score').textContent = n ? `正解済み ${n} / ${current.length}` : '';
    }

    function grade(sec) {
      const p = current[+sec.dataset.i]; let all = true, any = false;
      sec.querySelectorAll('.ans').forEach((lab, k) => {
        const a = p.answers[k]; const inp = lab.querySelector('input'); const m = lab.querySelector('.mark');
        const v = parseFloat(inp.value);
        if (isNaN(v)) { m.textContent = ''; lab.classList.remove('ok', 'ng'); all = false; return; }
        any = true;
        const tolAbs = Math.max(a.abs || 0, (a.tol === undefined ? 0.02 : a.tol) * Math.abs(a.value));
        const ok = Math.abs(v - a.value) <= tolAbs + 1e-12;
        lab.classList.toggle('ok', ok); lab.classList.toggle('ng', !ok);
        m.textContent = ok ? '○' : '×'; if (!ok) all = false;
      });
      const fb = sec.querySelector('.fb');
      if (!any) { fb.textContent = '数値を入力してください。'; fb.className = 'fb'; return; }
      if (all && sec.dataset.revealed) { fb.textContent = "合っています。ただし答えを見た後なので正解済みにはしません。「別の数値で」を押して自力で解いてみてください。"; fb.className = "fb"; return; }
      if (all) {
        st.solved = st.solved || {}; st.solved[p.id] = true; st.seed = seedText; st.updated = Date.now(); save(spec.ch, st);
        sec.classList.add('solved'); sec.querySelector('.pstat').textContent = '✓ 正解済み';
        fb.textContent = '正解です。'; fb.className = 'fb ok';
        const ins = sec.querySelector('.insight'); if (ins) ins.hidden = false;
      } else {
        fb.textContent = '× の欄を見直してください。単位（MW と p.u.、Hz と %）と符号の取り違えが多いです。'; fb.className = 'fb ng';
      }
      updScore();
    }

    function reveal(sec) {
      const p = current[+sec.dataset.i]; sec.dataset.revealed = "1";
      sec.querySelectorAll('.ans').forEach((lab, k) => { const a = p.answers[k]; lab.querySelector('input').value = Number(a.value.toPrecision(4)); lab.querySelector('.mark').textContent = '='; lab.classList.remove('ok', 'ng'); });
      sec.querySelector('.steps').hidden = false;
      const fb = sec.querySelector('.fb'); fb.textContent = '答えを表示しました（正解済みにはなりません）。「別の数値で」で再挑戦できます。'; fb.className = 'fb';
      const ins = sec.querySelector('.insight'); if (ins) ins.hidden = false;
    }

    root.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      const sec = b.closest('.prob');
      if (b.id === 'go') { variant = 0; build(); }
      else if (b.id === 'alt') { variant++; build(); }
      else if (b.classList.contains('grade')) grade(sec);
      else if (b.classList.contains('steps-btn')) { const s = sec.querySelector('.steps'); s.hidden = !s.hidden; b.textContent = s.hidden ? '途中式を見る' : '途中式を閉じる'; }
      else if (b.classList.contains('reveal')) reveal(sec);
    });
    root.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('.ans input')) grade(e.target.closest('.prob')); if (e.key === 'Enter' && e.target.id === 'seed') { variant = 0; build(); } });

    build();
  }

  return { page, fmt, rint, pick, round, mulberry32, hash, esc };
})();
