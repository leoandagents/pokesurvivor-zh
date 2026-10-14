# PokéSurvivor 中文

[PokéSurvivor](https://pokesurvivor.com/) 简体中文汉化脚本（Tampermonkey / Violentmonkey 用户脚本）。
汉化界面、招式、宝可梦名和「更新内容」窗口，不改游戏本身，不需要登录。

## 安装

### 1. 装脚本管理器（只需一次）

| 浏览器 | 扩展 |
|---|---|
| Chrome / Edge | [Tampermonkey](https://www.tampermonkey.net/)（Chrome 应用商店 / Edge 加载项里搜 Tampermonkey） |
| Firefox | Tampermonkey 或 Violentmonkey |
| 安卓手机 | 用 Firefox 或 Edge 手机版，再装 Tampermonkey |
| iPhone / iPad | Safari + 「Tampermonkey」或「Userscripts」App |

**Chrome / Edge 必做**：新版浏览器默认不让扩展运行用户脚本，不开这个开关脚本不会生效——
- Chrome：地址栏打开 `chrome://extensions` → 找到 Tampermonkey 点「详情」→ 打开 **「允许运行用户脚本」**（旧版 Chrome 没这个开关时，改为打开右上角「开发者模式」）
- Edge：`edge://extensions` → 打开左侧 **「开发人员模式」**

### 2. 安装汉化脚本

点开下面这个链接，Tampermonkey 会弹出安装页，点 **「安装」**：

<https://raw.githubusercontent.com/leoandagents/pokesurvivor-zh/main/pokesurvivor-zh.user.js>

### 3. 开玩

打开（或刷新）<https://pokesurvivor.com/>，界面就是中文了。

## 更新

脚本自带自动更新，Tampermonkey 会定期检查新版本。想立刻更新：Tampermonkey 图标 → 「管理面板」→ 勾选本脚本 → 「检查更新」，或直接再点一次上面的安装链接。

## 常见问题

- **装了还是英文/西语**：检查 Chrome 的「允许运行用户脚本」或 Edge 的「开发人员模式」开了没有；Tampermonkey 图标上应该显示数字 1（表示脚本在这个页面生效），然后刷新页面。
- **游戏更新后出现个别英文**：游戏新增的文字还没翻译，等脚本更新即可。
