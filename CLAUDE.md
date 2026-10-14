# PokéSurvivor 汉化

Tampermonkey 用户脚本，把 pokesurvivor.com 的界面/招式/宝可梦名/更新日志换成简体中文。
**产物 `pokesurvivor-zh.user.js` 是 build.py 生成的，不要手改**——改译文改 json，再跑构建。

## 文件
- `es_en.json` / `changelog_en.json`：`parse.js` 从游戏 `app.min.js` 提取的原文（西语→英语词典、更新日志英文），不手改
- `zh0~3.json`：西语 key → 中文，必须与 `es_en.json` 的 key 完全一致（build.py 有断言），`{x}` 占位数要对上
- `mons_zh.json`：宝可梦名；`extra_zh.json`：游戏词典里没有的零散词；`changelog_zh.json`：更新日志英文 → 中文
- `build.py`：校验 + 拼出 user.js（版本号、@updateURL 在 HEADER 里）

## 游戏更新后的同步流程
```bash
curl -sL -o app.min.js https://pokesurvivor.com/js/app.min.js   # 已 gitignore
node parse.js app.min.js es_en.json
python build.py
```
- build.py 断言失败 = 词典新增/删除了词条：按报错把新增 key 的中文补进 `zh3.json`（删除的 key 从 zh*.json 去掉）
- 输出 "⚠ 更新日志有 N 条没译" → 把列出的英文补进 `changelog_zh.json`
- parse.js 报"找不到 ['I18n']['add']" = 游戏打包方式变了，需要重新分析 app.min.js

## 发布
- 每次改动都要把 build.py HEADER 里的 `@version` 加一（如 1.10 → 1.11），否则 Tampermonkey 不会自动更新
- 重新 `python build.py`，`node --check pokesurvivor-zh.user.js` 过语法，提交并推送 main
- 用户端通过 @updateURL（raw.githubusercontent.com 的 main 分支）自动更新，所以 main 上的 user.js 必须始终是能用的构建产物

## 云端会话注意
- 需要能访问 pokesurvivor.com 下载 app.min.js；云环境网络若被限制，要在环境设置里放行该域名
