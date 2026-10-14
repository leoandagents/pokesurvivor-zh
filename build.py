import json, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

es_en = json.load(open('es_en.json', encoding='utf-8'))
zh = {}
for i in range(4):
    zh.update(json.load(open(f'zh{i}.json', encoding='utf-8')))
mons = json.load(open('mons_zh.json', encoding='utf-8'))
extra = {k: v for k, v in json.load(open('extra_zh.json', encoding='utf-8')).items() if not k.startswith('_')}
# 更新日志：changelog_en.json 由 parse.js 导出，译文在 changelog_zh.json；没译的条目照原样显示英文
log = json.load(open('changelog_zh.json', encoding='utf-8'))
log_missing = [l for l in json.load(open('changelog_en.json', encoding='utf-8')) if l not in log]

# 校验：词条全覆盖、{x} 数量一致
assert set(zh) == set(es_en), (set(es_en) - set(zh), set(zh) - set(es_en))
bad = [k for k in zh if k.count('{x}') != zh[k].count('{x}')]
assert not bad, bad

HEADER = """// ==UserScript==
// @name         PokéSurvivor 中文
// @namespace    pokesurvivor-zh
// @version      1.10
// @description  把 PokéSurvivor 的界面、招式、宝可梦名换成简体中文（挂在游戏自带的翻译系统上）
// @match        https://pokesurvivor.com/*
// @match        https://www.pokesurvivor.com/*
// @run-at       document-start
// @grant        none
// @updateURL    https://raw.githubusercontent.com/leoandagents/pokesurvivor-zh/main/pokesurvivor-zh.user.js
// @downloadURL  https://raw.githubusercontent.com/leoandagents/pokesurvivor-zh/main/pokesurvivor-zh.user.js
// ==/UserScript==
"""

BODY = r"""
(function () {
  'use strict';
  // 游戏只认 es/en；非 es 时才启用翻译层（含 canvas fillText 钩子），所以强制 en
  try { localStorage.setItem('ps.lang', 'en'); } catch (e) {}
  if (window.__psZh) return;
  window.__psZh = true;

  const ZH = __ZH__;      // 西语原文 -> 中文
  const EN = __EN__;      // 英文译文 -> 中文（页面上已经是英文时用）
  const MONS = __MONS__;  // 宝可梦名 -> 中文
  const TPL = __TPL__;    // [西语或英文模板, 中文模板]，含 {x}
  const EXTRA = __EXTRA__;  // 游戏词典里没有的词（性格名、增益缩写、等级前缀、地区名），见 extra_zh.json
  const LOG = __LOG__;      // 更新日志英文 -> 中文，见 changelog_zh.json

  // ① 早注入：游戏写法 G['I18n']=(...)(); G['I18n']['add']({西语:英语})，在 add 里把英文译文换成中文。
  // 游戏 JS 已混淆，G 是 IIFE 局部变量、不在 window 上，变量名每次打包都变；
  // 所以在 Object.prototype 上放 I18n 的 setter：G 自己没有 I18n 属性，赋值时会落到这里，this 就是 G。
  const hook = (v) => {
    if (v && typeof v.add === 'function' && !v.__zh) {
      const orig = v.add;
      let first = true;
      v.add = function (dict) {
        const m = {};
        for (const k in dict) m[k] = Object.prototype.hasOwnProperty.call(ZH, k) ? ZH[k] : dict[k];
        if (first) {
          for (const k in MONS) if (!(k in m)) m[k] = MONS[k];
          first = false;
        }
        return orig.call(this, m);
      };
      v.__zh = 'early';
    }
    return v;
  };
  Object.defineProperty(Object.prototype, 'I18n', {
    configurable: true,
    set(v) {
      Object.defineProperty(this, 'I18n', { value: hook(v), writable: true, configurable: true, enumerable: true });
      if (v && typeof v.add === 'function') delete Object.prototype.I18n;
    },
  });

  // ② 自带翻译层，早晚注入都启用：
  //   - 晚注入（Tampermonkey 在 iframe 里常见，如 pokesurvivor.org/play/）：拿不到 I18n，全靠这一层；
  //     这时它排在游戏的 canvas 钩子前面，收到的可能是西语原文，也可能是游戏已经翻好的英文，两种都要认。
  //   - 早注入：canvas 钩子装在游戏之前、被游戏包在外面，只处理游戏翻完还剩的英文
  //     （游戏的句中词替换把汉字也算字母，「闪光Moltres」这种拼接替换不了）。
  const UI = new Map(Object.entries(Object.assign({}, LOG, EN, ZH)));  // translate="no" 里只认这些整句
  const MAP = new Map(Object.entries(Object.assign({}, EXTRA, MONS, LOG, EN, ZH)));
  // 游戏在英文模式下直接写死、不走 I18n 的句式（多在 translate="no" 里）
  const PERIOD = { 'today': '今日', 'this week': '本周', 'this month': '本月', 'this year': '今年', 'of all time': '历史' };
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const MODE = '(solo|group)(?: with (.+?))?', PER = '(today|this week|this month|this year|of all time)';
  const mode = (m, mon) => (m === 'solo' ? '单人' : '组队') + (mon ? '（' + tr(mon) + '）' : '');
  const RULES = [
    [new RegExp("^You're not in the top 50 " + MODE + ' ' + PER + ' yet\\. Your exact rank is in All-time\\.$'),
      (_, m, mon, p) => '你还没进入' + PERIOD[p] + mode(m, mon) + '榜前 50 名。确切排名请看「历史」榜。'],
    [new RegExp('^Your best ' + MODE + ' rank ' + PER + ':$'), (_, m, mon, p) => '你' + PERIOD[p] + '的' + mode(m, mon) + '最佳排名：'],
    [new RegExp("^You don't have a " + MODE + ' record ' + PER + ' yet\\.$'), (_, m, mon, p) => '你' + PERIOD[p] + '还没有' + mode(m, mon) + '记录。'],
    [new RegExp('^(\\d{1,2}) (' + MONTHS.join('|') + ') (\\d{4})$'), (_, d, mo, y) => y + '年' + (MONTHS.indexOf(mo) + 1) + '月' + d + '日'],
    [/^(\d+) d (\d+) h$/, (_, d, h) => d + ' 天 ' + h + ' 小时'],
    [/^(\d+) h (\d+) min$/, (_, h, m) => h + ' 小时 ' + m + ' 分'],
    [/^(\d+) h$/, (_, h) => h + ' 小时'],
    [/^(\d+) min$/, (_, m) => m + ' 分钟'],
  ];
  const rule = (core) => { for (const [re, f] of RULES) if (re.test(core)) return core.replace(re, f); };
  const LOW = new Map();
  for (const [k, v] of MAP) if (!LOW.has(k.toLowerCase())) LOW.set(k.toLowerCase(), v);
  const esc = (p) => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  // 模板：{x} 处的内容递归翻译；字面部分越长越先匹配
  const TPLS = TPL.map(([src, zh]) => {
    const re = '^' + src.split('{x}').map(esc).join('([\\s\\S]+?)') + '$';
    return { re: new RegExp(re), reI: new RegExp(re, 'i'), zh, n: src.replace(/\{x\}/g, '').length };
  }).sort((a, b) => b.n - a.n);
  // 句中词：整句和模板都没命中时，把句子里认识的词（宝可梦名、招式、≥4 字母的词条）逐个替换。
  // 边界只看拉丁字母：汉字、数字紧挨着也能替换（「闪光Moltres」「Nv.1」）。
  const LATIN = 'A-Za-zÀ-ɏ';
  const short = new Set(Object.keys(Object.assign({}, MONS, EXTRA)).map((k) => k.toLowerCase()));
  const words = [...LOW.keys()].filter((k) => !k.includes('{x}') && /[a-z]/.test(k) && (k.length >= 4 || /\s/.test(k) || short.has(k)));
  const WORDS = new RegExp('(?<![' + LATIN + '])(' + words.sort((a, b) => b.length - a.length).map(esc).join('|') + ')(?![' + LATIN + '])', 'gi');
  const HAS_LATIN = new RegExp('[A-Za-zÀ-ɏ]');

  const tr1 = (core) => {
    const caps = core === core.toUpperCase();  // 游戏会把全大写标题照原样大写输出
    let r = MAP.get(core);
    if (r === undefined && caps) r = LOW.get(core.toLowerCase());
    if (r !== undefined) return r;
    if ((r = rule(core)) !== undefined) return r;
    for (const t of TPLS) {
      const m = (caps ? t.reI : t.re).exec(core);
      if (!m) continue;
      let i = 1;
      return t.zh.replace(/\{x\}/g, () => { const c = m[i++]; return c === undefined ? '' : tr(c); });
    }
    // 游戏翻完的中文里还嵌着英文时间单位（「17 h 19 min后刷新」）
    return core.replace(WORDS, (w) => LOW.get(w.toLowerCase()) || w)
      .replace(/\b(\d+) d (\d+) h\b/g, '$1 天 $2 小时').replace(/\b(\d+) h (\d+) min\b/g, '$1 小时 $2 分')
      .replace(/\b(\d+) h\b/g, '$1 小时').replace(/\b(\d+) min\b/g, '$1 分钟');
  };
  const cache = new Map();
  const tr = (s) => {
    if (typeof s !== 'string' || !HAS_LATIN.test(s)) return s;
    let r = cache.get(s);
    if (r !== undefined) return r;
    const m = /^(\s*)([\s\S]*?)(\s*)$/.exec(s), core = m[2].replace(/\s+/g, ' ');
    const t = core && tr1(core);
    r = !t ? s : m[1] + t + m[3];
    if (cache.size > 5000) cache.clear();
    cache.set(s, r);
    return r;
  };

  const P = CanvasRenderingContext2D.prototype;
  for (const fn of ['fillText', 'strokeText', 'measureText']) {
    const g = P[fn];
    P[fn] = function (a, ...r) { return g.call(this, tr(a), ...r); };
  }
  const oc = window.confirm, oa = window.alert;
  window.confirm = (a) => oc.call(window, tr(a));
  window.alert = (a) => oa.call(window, tr(a));

  const ATTRS = ['placeholder', 'title', 'alt', 'aria-label'];
  const skip = (el) => !el || (el.closest && el.closest('[translate="no"], script, style, code, noscript'));
  // translate="no" 多是玩家昵称，但游戏也会往里塞 T('Invitado')、更新日志、排行榜提示：只做整句精确匹配和固定句式
  const noTr = (v) => {
    const t = v.trim().replace(/\s+/g, ' ');
    if (!t) return v;
    const r = UI.get(t) ?? rule(t);
    return r === undefined ? v : v.replace(v.trim(), r);
  };
  const doText = (n) => {
    const el = n.parentElement;
    if (!el || (el.closest && el.closest('script, style, code, noscript'))) return;
    const v = n.nodeValue, r = skip(el) ? noTr(v) : tr(v);
    if (r !== v) n.nodeValue = r;
  };
  const doAttr = (el) => {
    if (!el.getAttribute || skip(el)) return;
    for (const k of ATTRS) {
      const v = el.getAttribute(k);
      if (v) { const r = tr(v); if (r !== v) el.setAttribute(k, r); }
    }
  };
  const walk = (root) => {
    if (root.nodeType === 3) return doText(root);
    if (root.nodeType !== 1) return;
    doAttr(root);
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    let n;
    while ((n = w.nextNode())) n.nodeType === 3 ? doText(n) : doAttr(n);
  };
  const start = () => {
    delete Object.prototype.I18n;  // 游戏 JS 是 defer，到这里还没截获说明是晚注入，撤掉 setter
    walk(document.body);
    document.title = tr(document.title);
    new MutationObserver((ms) => {
      for (const m of ms) {
        if (m.type === 'characterData') doText(m.target);
        else if (m.type === 'attributes') doAttr(m.target);
        else m.addedNodes.forEach(walk);
      }
    }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  };
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', start) : start();
})();
"""

# 英文 -> 中文；英文恰好也是某条西语 key 时让给西语那条。
# 多条西语对应同一英文时，¡/¿ 开头的感叹/疑问句式排后面（「¡Nivel」=升级横幅 和「Nivel」=等级 英文都是 Level）
en_zh = {}
for k, en in sorted(es_en.items(), key=lambda kv: kv[0][:1] in '¡¿'):
    if en and en != k and en not in es_en and en not in en_zh:
        en_zh[en] = zh[k]

# 模板：西语原文和英文译文各一份（英文的 {x} 个数对不上就不要）
tpl = []
for k, en in es_en.items():
    if '{x}' in k:
        tpl.append([k, zh[k]])
        if en != k and en.count('{x}') == k.count('{x}'):
            tpl.append([en, zh[k]])

body = (BODY.replace('__ZH__', json.dumps(zh, ensure_ascii=False))
        .replace('__EN__', json.dumps(en_zh, ensure_ascii=False))
        .replace('__MONS__', json.dumps(mons, ensure_ascii=False))
        .replace('__TPL__', json.dumps(tpl, ensure_ascii=False))
        .replace('__EXTRA__', json.dumps(extra, ensure_ascii=False))
        .replace('__LOG__', json.dumps(log, ensure_ascii=False)))
out = 'pokesurvivor-zh.user.js'
open(out, 'w', encoding='utf-8').write(HEADER + body)
print('ok', len(zh), 'ui entries,', len(mons), 'mons,', len(tpl), 'templates,', len(log), 'changelog,', len(HEADER + body), 'chars')
if log_missing:
    print(f'⚠ 更新日志有 {len(log_missing)} 条没译（补进 changelog_zh.json）：')
    for l in log_missing: print('  ', l)
