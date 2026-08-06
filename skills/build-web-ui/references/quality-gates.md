# 性能、SEO、无障碍与浏览器验收

## 目录

- [性能](#性能)
- [技术 SEO 与页面边界](#技术-seo-与页面边界)
- [WCAG 2.2 AA](#wcag-22-aa)
- [浏览器验收矩阵](#浏览器验收矩阵)
- [真实手机视口](#真实手机视口)
- [每个场景的统一证据](#每个场景的统一证据)
- [键盘、触控与状态](#键盘触控与状态)
- [静态审计脚本](#静态审计脚本)
- [浏览器审计脚本](#浏览器审计脚本)
- [官方依据](#官方依据)

## 性能

以真实用户 Core Web Vitals 的第 75 百分位为目标：LCP 不高于 2.5 秒、INP 不高于 200 毫秒、CLS 不高于 0.1。开发环境和 Lighthouse 是诊断工具，不冒充线上字段数据。

1. 让主内容和 LCP 资源在初始 HTML 可发现。不要懒加载 LCP 图；仅对确有必要的少数关键资源使用高优先级。
2. 为图片声明 `width`/`height` 或稳定 `aspect-ratio`，使用与显示尺寸匹配的 `srcset`/`sizes`，优先 AVIF/WebP 并保留合适回退。首屏外资源使用原生懒加载。
3. 缩小客户端 JavaScript，删除未使用依赖，按路由或交互边界拆分；公开内容优先静态或服务端渲染。避免用 JavaScript 重现原生 HTML/CSS 已能完成的行为。
4. 字体使用 WOFF2、必要字重和字符子集，设置可靠回退与 `font-display`。只有首屏确定使用的关键字体才预加载。
5. 对稳定资源使用内容哈希和长期缓存；HTML 与动态数据使用符合更新频率的策略。压缩文本资源，避免把大图、完整字体或重复库塞入首屏。

## 技术 SEO 与页面边界

先分类页面：公开且应索引、公开但不应索引、需要登录、后台或临时预览。公开页与后台页分别验收，不把同一套 SEO 要求机械应用到两者。

- 每个可索引页面使用准确且独立的 title、meta description、canonical、语言和一个主 H1；正文层级与标题含义一致。
- 让重要内容以文本存在于 DOM，使用语义 HTML 和真实 `<a href>` 链接。单页应用的独立内容或状态需要稳定 URL。
- sitemap 只包含规范、公开、成功响应页面；lastmod 来自真实内容变化。robots.txt 管抓取，不代替 `noindex` 或登录保护。
- 结构化数据只声明页面真实提供且搜索引擎支持的类型；验证 JSON-LD 与页面可见内容一致，不虚构评分、作者、价格或组织信息。
- 登录、账户、管理、搜索结果、预览和私密页面按产品边界使用 `noindex` 或鉴权，不放入 sitemap。
- 发布后核验实际抓取版本，并监控 4xx、5xx、重定向链、重复标题与 canonical 冲突。

## WCAG 2.2 AA

- 保证键盘可完成核心任务，焦点顺序符合视觉顺序，焦点样式可见且不被固定头部、浮层或 cookie 条遮挡。
- 使用原生 button、a、input、select、textarea 和 dialog；自定义控件必须补齐名称、角色、状态、键盘和焦点管理。
- 每个表单控件有持久可见标签；错误与控件关联，动态状态通过适当的 `aria-live` 告知，不只改变颜色。
- 普通文字对比度至少 4.5:1，大号文字至少 3:1；非文字控件、焦点和传达状态的图形按适用要求至少 3:1。允许浏览器缩放和文本重排，不设置 `user-scalable=no`。
- 关键配色记录实际前景色、背景色、对比度和阈值。半透明、渐变、背景图、混合模式和 hover/focus 等状态应在实际最不利背景上检查；自动工具跳过或近似计算的组合不能直接判为合格。
- 交互目标满足 WCAG 2.2 的最小目标尺寸或间距例外；移动端优先使用更宽裕的触控面积。
- 图片根据功能提供准确 alt；装饰图使用空 alt。视频有字幕或等价内容，图表有文字摘要或数据表。
- 支持 `prefers-reduced-motion`，避免闪烁、自动播放和无法暂停的连续动画。

## 浏览器验收矩阵

先从页面合同选代表场景。至少包含：

- 所有主要公开页面；
- 登录页和至少一个后台列表、详情或编辑页；
- 首屏与至少一个锚点、滚动深处或任务中间状态；
- 真实长标题、长正文、筛选/表单、空、错、加载、成功、弹窗和权限状态中适用的项目；
- 约 1440 像素桌面布局视口与 390 像素手机布局视口；已有暗色模式时增加对应组合。

页面较多时可以按共享模板和组件抽样，但每个独立布局、鉴权边界和高风险交互至少有一个代表页面。单张首页截图不能覆盖整站。

## 真实手机视口

浏览器外窗宽度不等于页面布局视口。Windows Chrome 使用 `--window-size=390` 时，外窗或无头窗口可能仍被钳到更宽的布局视口，再把画面裁成 390 像素；这会制造假溢出，也会漏掉只在真正窄屏触发的断点。

1. 使用 CDP `Emulation.setDeviceMetricsOverride`、浏览器自动化的设备上下文或真实设备，把布局视口明确设为目标宽度。
2. 每个场景记录 `window.innerWidth`、`document.documentElement.clientWidth`、`document.documentElement.scrollWidth` 和 `document.body.scrollWidth`。
3. 手机仿真中只有 `innerWidth` 与 `clientWidth` 接近目标值时，截图才可作为该移动端宽度证据；超过 1 像素的差异先解释设备缩放或错误仿真。桌面 `clientWidth` 可以因垂直滚动条比 `innerWidth` 小，需记录差值并结合溢出判断，不把正常滚动条报成横向布局失败。
4. 横向溢出使用 `max(documentElement.scrollWidth, body.scrollWidth) > clientWidth + 1` 判断，并同时人工检查祖先 `overflow: hidden` 造成的标题、导航、阴影或控件裁切。
5. 记录 `devicePixelRatio`、URL、页面状态和截图文件，使机器报告与图片能够对应。

随附 `audit_browser.py` 使用现有 Chromium 和 CDP 设置布局视口；找不到兼容浏览器时明确报告，不能自行安装，也不能退回外窗窄截图后声称等价。

## 每个场景的统一证据

机器报告至少包含：

- URL、标题、布局视口、滚动宽度和横向溢出；
- H1 数量、重复 ID、缺失 alt 和破图；
- 控制台 error、未捕获脚本异常、HTTP 400 及以上响应和网络加载失败；
- 截图路径与截图时的滚动位置；
- 自动检查未覆盖或不能可靠判断的项目。

截图逐屏检查层级、对齐、折行、密度、视觉重心、字体回退、图片裁切、固定元素遮挡和安全区。深层截图应来自 URL 锚点、查询状态或可复现的交互步骤，不用手工拖到大致位置后只保存图片。

## 键盘、触控与状态

1. 用键盘完成核心任务，检查跳过链接、焦点顺序、可见焦点、Escape 关闭、焦点返回、表单错误和浏览器后退。
2. 检查 hover 之外的信息可发现性。触控设备不模拟 hover，重要内容改为常显、点按或展开。
3. 检查软键盘、滚动锁、固定头部、表格、代码块、对话框和浮层。状态变化不能只靠颜色。
4. 在减少动效下重新走核心路径；动效关闭后内容顺序、可见性和操作结果保持不变。

## 静态审计脚本

```powershell
python scripts/audit_static_html.py dist --root dist
python scripts/audit_static_html.py public/index.html --root public --json
python scripts/audit_static_html.py app/static/index.html --root app --strict
```

脚本检查 HTML 语言、viewport、title、description、canonical、H1、main、图片 alt 与尺寸、表单标签、重复 id、阻塞脚本、明显的 LCP 优先级冲突和本地资源存在性。动态路由、实际布局视口、视觉层级、真实对比度、控制台、网络、Core Web Vitals、结构化数据语义和业务流程仍需其它工具或人工检查。

## 浏览器审计脚本

```powershell
python scripts/audit_browser.py http://127.0.0.1:8000/ --output browser-audit
python scripts/audit_browser.py http://127.0.0.1:8000/ http://127.0.0.1:8000/archive#year-2024 --output browser-audit --viewports desktop=1440x1000,mobile=390x844
python scripts/audit_browser.py https://example.test/ --browser "C:\Program Files\Google\Chrome\Application\chrome.exe" --output browser-audit --strict
```

脚本只连接本次启动的本地 CDP 端口，默认输出每个 URL 与视口的 PNG 和一个 JSON 总报告。URL 可携带锚点或查询参数以复现深层状态。它不能替代登录步骤、键盘操作、对比度计算、真实触控、人工视觉审校、Lighthouse 或线上真实用户数据。

## 官方依据

- [Core Web Vitals 阈值与第 75 百分位](https://web.dev/articles/defining-core-web-vitals-thresholds)
- [优化 Largest Contentful Paint](https://web.dev/articles/optimize-lcp)
- [Google Search 开发者 SEO 指南](https://developers.google.com/search/docs/fundamentals/get-started-developers)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Chrome DevTools Protocol：Emulation](https://chromedevtools.github.io/devtools-protocol/tot/Emulation/)
- [Chrome DevTools Protocol：Page](https://chromedevtools.github.io/devtools-protocol/tot/Page/)
- [Chrome DevTools Protocol：Network](https://chromedevtools.github.io/devtools-protocol/tot/Network/)
- [Chrome DevTools Protocol：Runtime](https://chromedevtools.github.io/devtools-protocol/tot/Runtime/)
