// ===== サイト設定 — ここ 1 箇所を書き換えれば、全ページのナビと学習順路が変わる =====
// 電力エネルギーシステム解析の基礎と応用の動くインフォグラフ集。
// cats を上から順にフラットに並べたものが、そのまま推奨学習順路（第1回→第15回）。

window.SITE = {
  title: '電力エネルギーシステム解析 — 動くノート',
  home: '../',

  pinned: [],

  cats: [
    {
      name: 'Day 1 基礎と潮流計算入門', items: [
        { href: 'energy.html', note: 'ch01.html', ex: 'ch01.html', label: '第1回 エネルギー変換' },
        { href: 'grid.html', note: 'ch02.html', ex: 'ch02.html', label: '第2回 電力システムの構成' },
        { href: 'acpower.html', note: 'ch03.html', ex: 'ch03.html', label: '第3回 P と Q の分離' },
        { href: 'ybus.html', note: 'ch04.html', ex: 'ch04.html', label: '第4回 Y行列と直流法潮流' },
      ],
    },
    {
      name: 'Day 2 潮流とダイナミクス', items: [
        { href: 'newton.html', note: 'ch05.html', ex: 'ch05.html', label: '第5回 ニュートン・ラフソン法' },
        { href: 'voltage.html', note: 'ch06.html', ex: 'ch06.html', label: '第6回 電圧と無効電力' },
        { href: 'swing.html', note: 'ch07.html', ex: 'ch07.html', label: '第7回 等面積法と安定度' },
        { href: 'freq.html', note: 'ch08.html', ex: 'ch08.html', label: '第8回 周波数と需給バランス' },
      ],
    },
    {
      name: 'Day 3 インバータと予測', items: [
        { href: 'inverter.html', note: 'ch09.html', ex: 'ch09.html', label: '第9回 インバータと系統連系' },
        { href: 'weather.html', note: 'ch10.html', ex: 'ch10.html', label: '第10回 気象と再エネ出力' },
        { href: 'demand.html', note: 'ch11.html', ex: 'ch11.html', label: '第11回 電力需要予測' },
        { href: 'ml.html', note: 'ch12.html', ex: 'ch12.html', label: '第12回 機械学習で予測する' },
      ],
    },
    {
      name: 'Day 4 AI と統合演習', items: [
        { href: 'ai.html', note: 'ch13.html', ex: 'ch13.html', label: '第13回 AI × 系統解析' },
        { href: 'opf.html', note: 'ch14.html', ex: 'ch14.html', label: '第14回 経済負荷配分と OPF' },
        { href: 'island.html', note: 'ch15.html', ex: 'ch15.html', label: '第15回 沖縄系統・統合演習' },
      ],
    },
  ],
};
