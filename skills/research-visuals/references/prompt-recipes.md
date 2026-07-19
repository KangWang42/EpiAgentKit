# Imagegen 科研视觉提示词配方

先完成视觉简报和内容契约，再选择配方。提示词不是风格词堆砌；每个字段只写会改变结果的信息。提示词不设固定字数，以消除结构歧义且不重复为准。

## 目录

1. 通用视觉简报
2. 约束装配规则
3. 通用主提示词
4. PPT 主视觉或章节配图
5. 论文概念或科学教育插图
6. 精确流程、技术路线或图形摘要
7. 标书立项、创新或影响配图
8. 网页 hero 或登录侧栏
9. 网页卡片、内容插图或空状态
10. README 或技术文档正文内容图
11. 真实截图与成果预览
12. 报告封面或章节插图
13. 图类专属质量指标
14. 携图定向编辑与失败处理

## 1. 通用视觉简报

```text
Carrier: <PPT / paper / graphical abstract / grant / report / web>
Function: <解释关系 / 建立情境 / 提示功能 / 区分章节 / 突出创新 / 展示路径 / 形成识别>
Audience: <研究者 / 临床人员 / 评审专家 / 学生 / 公众>
Evidence class: <解释插图 / 精确结构图 / 装饰视觉；不得填写统计或原始科研图像>
Information role: <正文内容图 / 真实截图 / 氛围插图>
Source anchors: <文件、章节、小节、表图、results.yaml 键或已核验文献>
Primary message: <这张图只需要传达的一件事>
Rationale: <为什么图比文字、表格或已有图更清楚>
Subject: <真实对象、场景或关系>
Archetype: <单向主链 / 并行汇聚 / 总览加局部 / 证据复合 / 对照矩阵 / 时间或层级>
Visual language: <科学编辑插画 / 自然光纪实 / 纸艺档案 / 克制几何 / 编辑拼贴>
Composition: <比例、焦点、阅读方向、主体位置和层级>
Geometry and typography: <目标比例来自实际图位；可用宽度与节点/侧栏容量；正常字宽的中文字体；保持宽高比；禁止 condensed/narrow 字体、压缩字距和非等比缩放>
Template contract: <必须保留的比例/品牌/字体/色彩/安全区 | 允许按内容调整的结构/密度/图文比例>
Regions: <区域 ID | 比例位置 | 独立任务 | 内容>
Micro-visuals: <模块 ID | 与真实操作对应的微型图元；无则 none>
Icon strategy: <none / per-major-stage / semantic anchors only>
Icon map: <stage ID | literal metaphor or micro-visual | why it improves recognition>
Icon system: <L0/L1/L2/L3, outline/filled, stroke, corner, viewpoint, container, single-color logic>
Palette source: <现有模板或网页颜色；没有时为流程图指定两类语义主色，必要时增加第三类警示或关键状态色；主色相总数不超过三种，黑白灰中性色不计>
Material and lighting: <有语义的材质与自然光线>
Text (verbatim): <必须逐字呈现的短标签；无则写 none>
Text selection: <身份标签 | 必要关系/条件 | 少量消歧限定语 | 移到正文/图注/长描述的解释；每项说明删除后会造成什么歧义>
Safe zones: <标题、正文、按钮或裁切安全区>
Must include: <不可缺失元素>
Critical content: <事实、文字、数字、公式、身份、对象和关系>
Visual direction: <版式、间距、字体层级、配色、线宽、背景和视觉重心>
Type-specific constraints: <只加载一个或确有需要的图类约束块>
```

完整论文、项目或多图任务先按 `figure-planning.md` 建立来源到图件矩阵。每个采用候选分别保存 `Source anchors / Primary message / Rationale / Evidence class / Suggested aspect ratio`；不把整篇论文压成一段脱离来源的超长提示词，也不按章节数量机械生成图片。

计算模型、网络架构、模块详解、并行分支、跳连、反馈或张量流图需要更多表达词汇时，先读 `external/SOURCE.md`，再按关键词检索归档的上游提示词原文。只抽取与真实方法一致的布局和模块描述，并重新组装进本配方；不继承上游固定确认、字数、配色、平台或 API 要求。

## 2. 约束装配规则

每个最终提示词只保留三条永久约束：

1. 无水印或品牌伪造。
2. 无伪文字、随机界面文案或不可辨识标签。
3. 不擅自添加来源未提供的内容、数据、结论、对象或关系。

其余约束按图类加载，不把所有禁止项堆进每个提示词：

| 图类 | 只加载的专属约束 |
| --- | --- |
| 人物、临床或摄影场景 | 身份、姿态、手部、设备连接、真实光线；禁止多余肢体、错误设备和商业摆拍 |
| 科研流程、架构与密集图 | 精确文字、数字、公式、节点、边、方向、分支与汇合；禁止结构增删、交叉箭头和装饰性科学符号 |
| README、技术文档与 skill 正文内容图 | 准确短标签、输入处理产物、结构关系、最终字号和窄屏显示；禁止把内容图做成无字插画 |
| 真实截图与成果预览 | 不进入 imagegen；实际运行或渲染，检查隐私、裁切、缩放、光标、通知和无关窗口 |
| 网页视觉 | 安全区、主体轮廓、负空间和响应式裁切；禁止伪 UI、烧录按钮文案和关键主体越出裁切区 |
| 科学教育插图 | 对象结构、层级、标签和证据边界；禁止无来源解剖、机制、分子和数据 |
| 封面与章节图 | 单一视觉命题、标题留白、印刷或投影适配；禁止多焦点、海报口号和拥挤细节 |

提示词按 `精确内容 → 结构关系 → 视觉方向 → 图类禁止项 → 验收条件` 分块。相同约束只出现一次；压缩提示词时先删除重复形容词和不相关禁止项，不删除内容锁、结构 inventory、图片角色或验收条件。

## 3. 通用主提示词

```text
Act as a scientific visual editor and academic art director.
Create one complete image for the carrier and function below. Choose the visual treatment from the research content and surrounding layout; do not apply a generic “scientific” style.

<插入视觉简报>

Build one clear focal point, a stable visual hierarchy, and purposeful negative space. Match detail density to the final display size. Derive scientific credibility from the actual subject, evidence workflow, field setting, instrument, document, or mechanism, not from decorative science symbols.

Treat any template as an adjustable constraint system. Preserve only the locked dimensions, brand, typography, palette, safe zones, and required components; reshape regions, reading order, hierarchy, density, whitespace, and text-image balance to fit the actual content topology.

Preserve natural geometry: use regular-width CJK typography with normal glyph proportions, keep circles circular and squares square, and never solve layout pressure with condensed fonts, compressed tracking, or non-uniform scaling. Derive the aspect ratio from the final carrier, not from a reference image. If the nodes, arrows, gaps, and side regions do not fit at natural widths, reflow the structure before rendering.

Permanent constraints: no watermark or false branding; no pseudo-text or random interface copy; do not add content, data, conclusions, objects, labels, or relationships absent from the supplied source.

Append only the relevant type-specific constraint block from Section 2, with no duplicate constraints.
```

## 4. PPT 主视觉或章节配图

```text
Use case: scientific-educational or photorealistic-natural
Carrier: academic PPT, <全页 16:9 / 实际图片区比例>
Function: establish context for <主题> without repeating the slide title
Composition: one dominant subject on <left/right>; reserve clean negative space on <opposite side> for native slide title and body; subject faces or moves toward the slide interior
Text (verbatim): none; no title, caption, labels, page number, or interface text inside the image
Constraints: remain legible when projected; moderate contrast; integrate with <模板背景与配色>
Avoid: poster advertising, dark atmospheric crop, generic laboratory scene, decorative bokeh, excessive depth of field
```

## 5. 论文概念或科学教育插图

```text
Use case: scientific-educational
Carrier: paper figure, <single-column / double-column / graphical abstract>
Function: explain <核心命题>
Subject: <真实对象和支持元素>
Composition: white or publication-compatible background; one focal mechanism; limited supporting elements; clear reading order; safe margin against cropping
Text (verbatim): <逐字短标签> or none
Constraints: no figure number, title, or long caption; preserve object hierarchy and evidence boundaries; suitable for final print size
Avoid: sci-fi glow, decorative molecular structures, cartoon anatomy, colorful card wall, fake plots
```

## 6. 精确流程、技术路线或图形摘要

```text
Use case: infographic-diagram
Carrier: <PPT / paper / grant / report>
Function: show the exact path from <start> to <end>
Reading order: <left to right / top to bottom>
Nodes: <ID | exact label | level | visual object>
Edges: <source ID -> target ID | direction | relation>
Regions: <区域 ID | 比例位置 | 独立贡献；删除无贡献区域>
Micro-visuals: <仅填写与真实输入、操作或输出对应的波形/频谱/矩阵/网格/关系图元>
Icon strategy: <默认 none；需要时按 diagram-iconography.md 给出 0–4 个语义锚点>
Icon map: <node ID | literal metaphor | semantic contribution>
Text (verbatim): use only the supplied labels and numbers, exactly once
Terminology: every label must come from the source, protocol, or a verified domain term; do not invent abbreviations, compound labels, workflow jargon, colloquial actions, or literal translations
Composition: <target ratio from the actual carrier>; clear main path; branches close to their source; no crossing arrows; adequate label spacing; if a single row cannot preserve natural label width, use a two-row chain, grouped phases, top-to-bottom layout, or move explanations outside the main path
Geometry and typography: regular-width Chinese sans-serif with natural glyph proportions; node width follows the longest line plus visible horizontal padding; preserve the output aspect ratio; no condensed/narrow font, compressed tracking, horizontally squeezed text, stretched icons, or non-uniform scaling
Palette: use two semantic hues by default and a third only for a real warning, failure, abnormal state, adverse outcome, or essential key state; never exceed three chromatic hues; neutrals do not count; do not default to blue-and-white
Constraints: node and edge counts must match the contract; no added, merged, inferred, or omitted steps; approved icons use one coherent family and remain secondary to labels and arrows; no title, legend, or decorative icon
Avoid: card wall, random 3D symbols, gradients, duplicate nodes, ambiguous arrowheads
```

总览加局部结构只展开一个真正需要解释的模块，并用明确调用线连接母图与局部图。模块内微型图元必须表达真实操作；不得用伪统计图、无数值坐标、随机热图或通用占位图填空。

对样本纳排、CONSORT、病例流转和包含数字的图，逐项比对全部数字、原因和分支。错误时只用 imagegen 修正完整成图；适用的 Image 2 必须用于至少一轮定向修正，两轮定向修正后再整图重生成，仍不准确才把 `svg-diagrams` 作为最终回退。

### 科研技术路线补充

生成论文、PPT、标书或报告技术路线前，先按 `research-figure-patterns.md` 锁定以下内容：

```text
Research object and sources: <人群、队列、数据库、暴露、结局或外部数据>
Collection and time structure: <检测、设备、随访、空间匹配或重复测量>
Eligibility and QC: <纳排、清洗、缺失、异常、对齐和质量控制>
Variable or feature construction: <暴露、结局、中介、协变量、指标或信号特征>
Question-method pairs: <研究问题或估计对象 -> 对应方法；逐条列出>
Validation and robustness: <交叉/外部验证、分层、敏感性、替代定义或消融>
Outputs: <效应估计、风险预测、机制路径、解释或交付成果>
Icon anchors: <none，或 2–4 个与真实输入、处理、验证、输出对应的简单锚点>
```

主阅读方向只选一种，阶段控制在 4–7 个。多源数据先汇入整合节点，平行研究问题从共同分析集分叉，最终汇入验证或输出。不得只罗列模型名，也不得省略研究对象、质量控制和结果输出。

## 7. 标书立项、创新或影响配图

```text
Use case: scientific-educational or infographic-diagram
Carrier: grant proposal, page-width <3:2 / 4:3>
Function: help reviewers understand <significance / gap / innovation / approach / impact>
Primary message: <一个可在数秒内理解的命题>
Composition: one dominant comparison or pathway; short reading distance; large visual units; readable at 100% page zoom and in grayscale print
Text (verbatim): <必要短标签> or none
Constraints: distinguish established evidence, proposed work, and expected impact visually without presenting proposed outcomes as existing findings
Avoid: promotional slogan, futuristic promise, decorative laboratory montage, dense micro-text, unsupported causal arrows
```

## 8. 网页 hero 或登录侧栏

```text
Use case: scientific-educational, editorial illustration, or photorealistic-natural
Carrier: website <desktop hero / mobile hero / login side panel>, <target ratio>
Function: establish the product or research domain while supporting native page copy and controls
Composition: keep the main subject inside the crop-safe zone; reserve clean negative space at <location>; background may extend for responsive cropping
Text (verbatim): none; no headline, body copy, button label, logo, or fake UI text inside the image
Constraints: match the existing site palette and visual language; the actual subject must be inspectable; avoid dark or blurred stock imagery
Template contract: preserve the native copy and control safe zone; adapt subject scale, crop, visual weight, and background extension to the actual message
Avoid: generic SaaS gradient, floating dashboard cards, decorative orb, pseudo-interface, unrelated science symbols, cinematic darkness
```

桌面与移动端构图差异明显时分别生成，不要求同一张图兼容所有裁切。

## 9. 网页卡片、内容插图或空状态

```text
Use case: scientific-educational or editorial illustration
Carrier: website <feature card / article illustration / empty state>, <1:1 / 4:3>
Function: communicate <单一功能或状态>
Composition: one strong silhouette and at most one supporting object; generous padding; recognizable at <目标像素>
Text (verbatim): none
Constraints: harmonize with adjacent cards without repeating an identical template; no control icon replacement when the interface already uses an icon library
Avoid: complex scene, small texture, pseudo-text, plastic 3D badge, random background shapes
```

## 10. README 或技术文档正文内容图

正文内容图不是无字功能插画。先按 `scenario-playbook.md` 锁定输入、处理、产物和真实文字，再使用：

```text
Use case: infographic-diagram
Carrier: README / project documentation / tutorial / skill example, <target ratio and rendered width>
Information role: <正文内容图>
Function: explain <workflow / architecture / skill capability / before-after / result path>
Source anchors: <README section / SKILL.md / actual command / rendered artifact>
Core claim: <读者脱离图注仍应理解的一句话>
Archetype: <单向主链 / 并行汇聚 / 对照矩阵 / 层级 / 时间>
Nodes: <ID | exact label | role | visual object>
Edges: <source -> target | direction | relation>
Text (verbatim): <通过来源核验和删除测试后保留的必要标题、节点、数字和状态；指定语言、出现次数和层级>
Text selection: keep only <identity labels / non-obvious relation or branch conditions / critical state / selected disambiguating qualifier>; move <definitions / rationale / methods detail / limitations / sources> to native text or a long description
Text hierarchy: <optional figure title | stage heading | node label | relation term | optional qualifier>; do not give every node a subtitle
Template contract: preserve <ratio, brand, typography, palette, safe zones>; adapt <regions, reading order, weights, density, whitespace, text-image ratio> to the content
Composition: large labels readable at the final rendered width; one clear reading direction; native section heading may replace a duplicate long in-image title; reflow long single-row processes instead of widening the canvas or narrowing nodes
Geometry and typography: derive the ratio from the rendered content column; keep regular-width CJK glyphs and aspect-locked shapes; no condensed font or non-uniform resize
Constraints: include every label required to understand the content and no text that merely repeats an icon, position, native section heading, caption, or neighboring label; no pseudo-text; no added capability, result, command, UI state, or relationship
Avoid: textless decorative illustration, generic feature cards, fake UI, tiny labels, repeated icons, template-driven card wall
```

Skill 示例至少呈现 `输入 → 能力或处理 → 可复核产物`。若要证明真实界面、命令或文件外观，转到下一节的真实截图路线，不生成似真替代图。

## 11. 真实截图与成果预览

此场景不调用 imagegen 生成截图。先运行、打开或渲染实际产物，再执行：

```text
Proof target: <截图要证明的功能、步骤或产物>
Source artifact: <真实命令、界面、文档、PPT、表格、图件或交付包>
Required state: <必须可见的控件、命令、结果、页或文件>
Crop: <保留范围与最终比例>
Privacy: <必须隐藏的姓名、路径、账号、令牌、通知、历史和非公开数据>
Presentation: <主题、缩放、窗口尺寸、光标、弹窗与连续步骤>
Annotations: <none，或不遮盖原内容的必要编号/框线/箭头>
Acceptance: <与实际产物一致、最终尺寸可读、无敏感信息、无伪 UI>
```

代码与命令优先使用 README 原生代码块；只有需要证明运行环境、界面状态或最终外观时才截图。统计结果截图必须能回到真实代码和数据，正式结果图仍由 `publication-figures` 输出。

## 12. 报告封面或章节插图

```text
Use case: editorial illustration, paper collage, or photorealistic-natural
Carrier: report <cover / section image>, <portrait / 3:2 / 4:3>
Function: establish an editorial frame for <主题>
Composition: one focal subject; reserve native title area; controlled texture; clear edge against the page background
Text (verbatim): none; report title, date, version, and organization remain native document text
Constraints: professional, evidence-oriented, printable, and compatible with <页面配色>
Avoid: campaign poster, saturated marketing palette, dramatic spotlight, fake paper text, decorative clutter
```

## 13. 图类专属质量指标

| 图片类型 | 首要锁定内容 | 通过条件 |
| --- | --- | --- |
| 科研流程与架构图 | 文字、数字、公式、节点、边、方向、分支、汇合与几何完整性 | 关键文字与结构 100% 一致，无裁切或重叠，正常中文字宽和形状比例，页面与缩略图尺度可读 |
| 人物或临床场景 | 身份、姿态、手部、设备连接和真实光线 | 身份与设备关系不漂移，解剖和物理合理，光线符合场景 |
| 网页视觉 | 安全区、响应式裁切、主体轮廓和负空间 | 桌面与移动裁切保留主体，文字/按钮区干净，轮廓清楚 |
| README / 技术文档内容图 | 文字、输入处理产物、结构关系、模板适配和最终字号 | 脱离图注可理解，标签逐字准确，窄屏仍可读，未机械套版 |
| 真实截图 / 成果预览 | 真实状态、隐私、裁切、缩放和证明目标 | 与实际产物一致，无敏感信息、无关窗口或生成式伪 UI |
| 科学教育插图 | 对象结构、层级、标签和证据边界 | 无虚构结构或机制，标签与层级准确，抽象程度符合受众 |
| 封面与章节图 | 单一视觉命题、标题留白和印刷适配 | 主体一眼可辨，留白可用，印刷/投影无脏色和细节噪声 |

不要把流程图的逐字标签规则强加给无文字摄影，也不要把摄影的光线、景深和材质要求套到技术路线图。图类指标决定 acceptance checks；通用美学只能排在精确内容与载体可读性之后。

## 14. 携图定向编辑与失败处理

需要修改既有图片、根据既有图重绘或修正上一版时，携带当前编辑目标。所有待附图片都有本地路径时用 `referenced_image_paths`；近期对话能覆盖全部待附图片时用最小 `num_last_images_to_include`；不得同时设置两者。单一机制无法覆盖 Image 1 与必要 Image 2 时，省略非必要 Image 2；Image 2 对修正确有帮助时要求重新附图。适用的 Image 2 路径优先于 SVG。

### 14.1 运行时实例卡

先从载体解析真实目标，不按导出文件名或媒体序号猜测图号。以下字段只为当前任务填写，不把项目事实回写到本配方：

```text
Target identity: <用户指向、图题/正文交叉引用、页面或段落位置>
Resolved Image 1: <经文档关系和渲染外观核对后的实际编辑目标>
Source anchors: <支持本轮修改的正文、表图、结果键或其它权威来源>
Instance-only facts: <本项目的精确标签、方法、阈值、比例、配色和修改范围>
Carrier-managed text: <由 Word/PPT/网页/排版系统承担且不烧录进图片的图号、图题、标题或来源说明；无则 none>
```

### 14.2 图片角色

```text
Image 1: edit target and acceptance baseline; preserve its factual, scientific, structural, and identity content.
Image 2: optional auxiliary reference; transfer only verified palette, spatial organization, reading direction, and line treatment.
Do not transfer Image 2 objects, labels, data, layout errors, branding, scientific claims, canvas aspect ratio, narrow node geometry, condensed typography, or compression artifacts.
```

不为凑足图片数量寻找或生成 Image 2。用户已提供或指定且它能改善视觉语言、布局节奏或结构表达时使用；使用 Image 2 时必须在提示词中保留以上角色声明。

### 14.3 不降质合同

```text
Baseline: Image 1 is the acceptance baseline.

Priority order:
1. factual and semantic fidelity
2. exact text, numbers, formulas, and identity
3. correct objects, nodes, arrows, and relationships
4. readability at final display size
5. visual refinement

A more attractive image is not acceptable if any higher-priority item becomes worse.
Keep the original unchanged unless the candidate passes every acceptance check.
```

### 14.4 LOCKED / FLEXIBLE / FORBIDDEN

每轮只锁定一个主要问题，并填写：

```text
Edit the attached target image.
Change request: <单一、可观察的修改目标>.

LOCKED:
<不得改变的文字、数字、公式、对象、人物身份、节点、连线、方向和结论>

FLEXIBLE:
<允许优化的版式、间距、字体层级、配色、线宽、背景和视觉重心>

FORBIDDEN:
<不得添加、删除、纠正、推断或合并的内容>

Return one complete edited image, not a patch or explanation.
```

### 14.5 密集科研图专用模板

```text
Use case: high-fidelity scientific-figure edit
Input role: Image 1 is the only edit target, not merely a style reference.

Structure inventory:
- stages: <数量>
- pathways: <数量>
- nodes: <数量>
- merges or branches: <逐项列出>
- output regions: <逐项列出>

Content lock:
- copy every technical label, number, unit, variable, formula, and footnote
- preserve every arrow, branch, merge, and decision condition
- ambiguous source text must be copied, never guessed

Visual freedom:
- typography, spacing, alignment, border weight, restrained palette, carrier-derived aspect ratio, and reflow needed to preserve natural label width
- no scientific-content changes

Acceptance:
- 100% critical-text accuracy
- 100% node and edge preservation
- no clipping or overlap
- regular-width CJK glyphs and undistorted circles/squares; no non-uniform scaling
- readable at page scale and thumbnail scale
```

### 14.6 候选图与 HTTP 524

成功返回候选图后，与 Image 1 全幅比较并按 Section 13 验收。最多连续两轮候选图质量修正；第二轮以上一轮候选为当前目标，但重复完整基线、角色和三段式合同。适用的 Image 2 可从首轮开始加入，尚未使用时必须占用其中至少一轮。可替代的生成稿仍失败时，才按完整内容合同纯文本整图重生一次；不可替代的用户原图保留原件。

HTTP 524 不计入候选图质量修正：

```text
First HTTP 524:
retry once with the same edit target and a compressed prompt; keep image roles, structure inventory, LOCKED/FLEXIBLE/FORBIDDEN, and acceptance checks.

Second HTTP 524:
stop retrying; preserve the original; do not interpret timeout as a design failure; do not silently downgrade the model or switch to SVG/API.
```

只有成功返回的候选图确实不满足内容精度要求，且 Image 1 定向编辑、适用的 Image 2 辅助修正和允许的整图重生成均已完成时，精确结构图才可把 SVG 作为最终回退；不得用 Python、PPT/Word 文本框或 SVG 覆盖层补字，也不得以重生图冒充修改成功。
