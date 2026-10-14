// 从游戏的 app.min.js 里提取 I18n 词典（西语 -> 英语），写成 es_en.json
// 用法: node parse.js app.min.js [out.json]
// 游戏 JS 已被 javascript-obfuscator 混淆：部分字符串被替换成字符串表解码调用 _0xXXXX(0x123)，
// 所以要把顶部的字符串表 + 解码函数拿出来真跑一遍，再求值词典对象字面量。
const fs = require('fs');
const s = fs.readFileSync(process.argv[2], 'utf8');
const out = process.argv[3] || 'es_en.json';

// 从 s[i]（开括号）开始做括号匹配，跳过字符串
function matchBrace(i) {
  const open = s[i], close = { '{': '}', '(': ')', '[': ']' }[open];
  let depth = 0;
  for (; i < s.length; i++) {
    const c = s[i];
    if (c === '"' || c === "'" || c === '`') {
      for (i++; s[i] !== c; i++) if (s[i] === '\\') i++;
    } else if (c === open) depth++;
    else if (c === close && --depth === 0) return i + 1;
  }
  throw new Error('unbalanced');
}
function fnDecl(name) {
  const i = s.indexOf('function ' + name + '(');
  if (i < 0) throw new Error('no ' + name);
  return s.slice(i, matchBrace(s.indexOf('{', i)));
}

// 解码函数名：词典所在的 I18n 模块里 const _0xabc=a0_0xXXXX
const add = s.indexOf("['I18n']['add']({");
if (add < 0) throw new Error("找不到 ['I18n']['add']({ —— 游戏打包方式又变了");
const decName = /function (a0_0x[0-9a-f]+)\(_0x\w+,_0x\w+\)\{const _0x\w+=(a0_0x[0-9a-f]+)\(\)/.exec(s);
const [, dec, arr] = decName;
// 顶部的字符串表轮转 IIFE：(function(..){...}(arr,0x...));
const rot = s.slice(0, matchBrace(0)) + ';';
const decode = new Function(fnDecl(arr) + fnDecl(dec) + rot + 'return ' + dec + ';')();

// 求值从 s[i] 开始的对象/数组字面量，里面的 _0xabc(0x123) 都当字符串表解码
function literal(i) {
  const text = s.slice(i, matchBrace(i));
  const aliases = [...new Set([...text.matchAll(/(_0x[0-9a-f]+)\(0x[0-9a-f]+\)/g)].map((m) => m[1]))];
  return new Function(...aliases, 'return ' + text)(...aliases.map(() => decode));
}
const dict = literal(add + "['I18n']['add'](".length);

const ents = Object.entries(dict);
fs.writeFileSync(out, '{\n' + ents.map(([k, v]) => JSON.stringify(k) + ': ' + JSON.stringify(v)).join(',\n') + '\n}', 'utf8');
console.log(ents.length, 'entries,', ents.filter(([k]) => k.includes('{x}')).length, 'templates');

// 更新日志（「更新内容」窗口）：G.CHANGELOG=[{d, title:[es,en], new/chg/fix:[[es,en],...]}]，
// 渲染在 translate="no" 里、按语言取下标，不走 I18n。只导出英文原文，译文在 changelog_zh.json
const cl = s.indexOf("['CHANGELOG']=[");
if (cl < 0) throw new Error("找不到 ['CHANGELOG']=[");
const log = literal(cl + "['CHANGELOG']=".length);
const lines = [];
for (const day of log) {
  if (day.title) lines.push(day.title[1]);
  for (const k of Object.keys(day)) if (Array.isArray(day[k]) && Array.isArray(day[k][0])) for (const p of day[k]) lines.push(p[1]);
}
fs.writeFileSync('changelog_en.json', JSON.stringify(lines, null, 0).replace(/","/g, '",\n"'), 'utf8');
console.log(log.length, 'changelog days,', lines.length, 'lines -> changelog_en.json');
