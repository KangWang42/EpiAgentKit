# Imagegen 科研视觉提示词模板

先明确图件要求和内容，再选择适用模板。提示词不是风格词堆砌；每个字段只写会改变结果的信息。提示词不设固定字数，以消除结构歧义且不重复为准。

本文件严格区分**图外规划**与**实际调用提示词**。第 1 节是内部规划工作表，不得整段复制给 imagegen。来源路径、采用理由、300 ppi 像素计算、验收日志和问题记录留在调用外；实际调用只装配第 2–3 节的五段最小包。长提示词本身不是失败原因，但重复约束、多个同义清单、一次并列多个修改目标和让模型从散文中推断精确图谱都会增加漂移。提示词只能提高遵循率，不能保证生成式模型完美复现生产级密集文字与拓扑；所有关键文字、节点和边仍须逐项检查。

## 目录

1. 通用图件要求
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
14. 根据原图定向修改与失败处理

## 1. 通用图件要求

```text
Carrier: <PPT / paper / graphical abstract / grant / report / web>
Function: <解释关系 / 建立情境 / 提示功能 / 区分章节 / 突出创新 / 展示路径 / 形成识别>
Audience: <研究者 / 临床人员 / 评审专家 / 学生 / 公众>
Evidence class: <解释插图 / 精确结构图 / 装饰视觉；不得填写统计或原始科研图像>
Information role: <正文内容图 / 真实截图 / 氛围插图>
Source material: <文件、章节、小节、表图、results.yaml 中的结果名称或已核验文献>
Primary message: <这张图只需要传达的一件事>
Figure title: <一个简短标题或 none；独立计算机方法图禁止副标题、覆盖标签、版本摘要、来源/实现说明和页脚句子>
Rationale: <为什么图比文字、表格或已有图更清楚>
Subject: <真实对象、场景或关系>
Archetype: <单向主链 / 并行汇聚 / 总览加局部 / 证据复合 / 对照矩阵 / 时间或层级>
Visual language: <科学编辑插画 / 自然光纪实 / 纸艺档案 / 克制几何 / 编辑拼贴>
Aesthetic system: <表面系统 | 主要区域分隔方式 | 颜色使用位置 | 容器深度 | 密度节奏>
Coverage mode: <完整架构 / 方法总览 / 模块详解 | 必须保留的层次 | 允许省略的内容>
Typography character: <中性/几何/略柔和/衬线点题；服从模板、语言覆盖与最终尺寸>
Composition: <比例、焦点、阅读方向、主体位置和层级>
Geometry and typography: <目标比例来自实际图位；可用宽度与节点/侧栏容量；正常字宽的中文字体；保持宽高比；禁止 condensed/narrow 字体、压缩字距和非等比缩放>
Raster resolution contract: <最终毫米尺寸 | 目标 ppi/dpi | 最低像素宽高 | 生成后读取实际像素与 DPI 元数据；提示词中的 300 dpi/print-ready/4K 不作为验收证据>
Natural canvas: <按正常标签、图元、内边距和连接估算的最小宽度 | 无既定图位时的自然比例 | 图位更窄时怎样重排或拆图>
Region shape map: <各区域适合横向/近方形/纵向的自然形状 | 哪些可以同排 | 出现高窄列或压缩图元时怎样改为双行、编辑分区或分区组合图>
Template requirements: <必须保留的比例/品牌/字体/色彩/安全区 | 允许按内容调整的结构/密度/图文比例>
Regions: <区域 ID | 比例位置 | 独立任务 | 内容>
Micro-visuals: <模块 ID | 与真实操作对应的微型图元；无则 none>
Representation identity: <必须保持的真实/写实/示意类型、关键微型图元、连续概率或热区含义、裁切、材质和已认可局部质量>
Flat-fill contract: <需要纯色的区域与有限色板 | 整块纯色底和网格描边 | 无渐变、白雾、中心高光、噪声、随机深浅、纹理或透明叠色；不适用写 none>
Icon strategy: <正式研究流程/研究设计/技术路线/病例流转/方法架构固定为 none；图形摘要、机制示意或科普/教学插图只有在大型图形对象承担真实内容编码时才记录例外>
Icon exception: <none，或大型对象 | 对应的真实对象/机制 | 删除后造成的内容损失>
Icon constraints: no emoji, pictogram, clip-art, decorative small icon, stage icon, node icon, result-document icon, or icon used as a bullet
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

完整论文、项目或多图任务先按 `figure-planning.md` 建立图件计划表，逐项写明每张候选图所依据的材料、核心信息、独立作用、采用理由、证据属性和建议比例。不把整篇论文压成一段脱离来源的超长提示词，也不按章节数量机械生成图片。

计算模型、网络架构、模块详解、并行分支、跳连、反馈或张量流图需要更多表达词汇时，先读 `external/SOURCE.md`，再按关键词检索归档的上游提示词原文。只抽取与真实方法一致的布局和模块描述，并重新写入本任务的提示词；不继承上游固定确认、字数、配色、平台或 API 要求。

## 2. 约束装配与最小调用包

每个最终提示词只保留三条永久约束：

1. 无水印或品牌伪造。
2. 无伪文字、随机界面文案或不可辨识标签。
3. 不擅自添加来源未提供的内容、数据、结论、对象或关系。

其余约束按图类加载，不把所有禁止项堆进每个提示词：

| 图类 | 只加载的专属约束 |
| --- | --- |
| 人物、临床或摄影场景 | 身份、姿态、手部、设备连接、真实光线；禁止多余肢体、错误设备和商业摆拍 |
| 科研流程、架构与密集图 | 精确文字、数字、公式、节点、边、方向、分支与汇合；正式流程固定 L0，禁止结构增删、交叉箭头、emoji、pictogram、clip-art、阶段/节点/结果小图标和装饰性科学符号 |
| README、技术文档与 skill 正文内容图 | 准确短标签、输入处理产物、结构关系、最终字号和窄屏显示；禁止把内容图做成无字插画 |
| 真实截图与成果预览 | 不进入 imagegen；实际运行或渲染，检查隐私、裁切、缩放、光标、通知和无关窗口 |
| 网页视觉 | 安全区、主体轮廓、负空间和响应式裁切；禁止伪 UI、烧录按钮文案和关键主体越出裁切区 |
| 科学教育插图 | 对象结构、层级、标签和证据边界；禁止无来源解剖、机制、分子和数据 |
| 封面与章节图 | 单一视觉命题、标题留白、印刷或投影适配；禁止多焦点、海报口号和拥挤细节 |

实际调用固定按 `USE → CONTENT LOCK → GRAPH OR LAYOUT → VISUAL DIRECTION → CONSTRAINTS` 五段装配。空字段直接省略，不再加第六个同义的 `MUST PRESERVE`、`Acceptance` 或 `Avoid` 清单。相同事实、节点、关系和约束只出现一次；精简提示词时先删除来源路径、采用理由、重复形容词、验收日志和不相关禁止项，不删除会改变图意的文字、节点、边、图片用途或单一修改目标。

图外继续保存完整事实清单、语义分辨率清单、图件计划表和验收表；它们是核验依据，不是模型输入。实际调用只把生成这张图所必需的内容压缩到五段中。精确图谱使用短 ID 和紧凑邻接表；同一 ID 与同一条关系只写一次，汇聚必须拆成多条有向边，不写 `A+B→C` 让模型自行解释。

计算机相关图件在“精确内容”之前先声明覆盖模式，并按来源建立不限层数的语义分辨率清单。完整架构提示词必须逐区列出所有会改变理解的内容和关系；高层阶段只能在真实需要时作为容器，不能成为把多个模块合并成一个大框的理由。空间不足时要求分区、多行主链、边缘辅助带、局部展开或拆图；不得用大片空白、均匀卡片、重阴影或减少节点换取“整洁”。

## 3. 通用五段调用模板

```text
USE
Create one <figure type> for <carrier and actual placement>. Purpose: <one message>. Audience: <reader>.

CONTENT LOCK
Exact text: <quoted short labels, each once, or none>.
Must include: <facts, objects, numbers, formulas, states>.
Do not infer: <unsupported content>.

GRAPH OR LAYOUT
<For an exact graph: NODES, EDGES, optional GROUPS, reading direction, merge/branch placement>.
<For an illustration: SUBJECTS, PLACEMENT, SAFE ZONES, framing>.

VISUAL DIRECTION
<one surface system; one region-separation method; semantic color carriers; shallow container depth; density rhythm; natural-width type and undistorted geometry>.

CONSTRAINTS
<only the relevant type-specific constraints>; no watermark or false branding; no extra or pseudo-text; no unsupported content or relationships.
```

五段标题只是稳定分隔符，不要求每段写成长段落。普通插图通常只需数句；精确架构图可以因节点和边较多而变长，但不得重复同一内容。`GRAPH OR LAYOUT` 二选一：精确关系图写图谱，摄影或编辑插图写主体与空间，不把两套字段同时堆入。

调用参数与提示词分开处理。工具允许选择质量时，密集标签、复杂信息图和最终成品优先比较 `medium` 与 `high`，不能用形容词替代质量参数。论文要求 300 ppi 时，先按最终毫米尺寸计算最低像素，再请求满足尺寸的输出并读取实际像素和 DPI 元数据；不要把 `300 dpi`、`4K` 或 `print-ready` 当作能改变真实像素的提示词。工具未暴露尺寸或质量参数时，生成后按实际文件验收，未达到就如实报告。

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
USE
Create one exact infographic diagram for <carrier and actual placement>. Purpose: show <start> to <end>. Reading: <left-to-right / top-to-bottom>.

CONTENT LOCK
Exact text: <quoted labels and numbers, each once>.
Must include: <verified objects, states, formulas and outputs>.
Do not infer: any step, abbreviation, value or relationship not listed below.

GRAPH OR LAYOUT
NODES: input="<label>"; M00="<label>"; M01="<label>"; output="<label>".
EDGES: input>M00; M00>M01; M01>output.
GROUPS: <group ID={member IDs}, only for real containment; otherwise omit>.
Render labels, not IDs. Draw every listed edge once with one unambiguous arrowhead. Keep branches beside their source and merges beside their target. If one row compresses labels, use two rows or unequal editorial regions.

VISUAL DIRECTION
<target ratio>; <surface and region separation>; two semantic hues, with a third only for a real exceptional state; regular-width type; natural node width; undistorted shapes; formal research flow uses text, numbering, boundaries and arrows only; verified method micro-visuals only when they encode actual input, transformation or output; <flat-fill contract when applicable>.

CONSTRAINTS
Node and edge counts must match the lists; no added, duplicated, merged, inferred or omitted nodes or edges; no crossing arrows; no emoji, pictogram, clip-art, stage icon, node icon, result-document icon or decorative small symbol; no condensed type, non-uniform scaling, card wall, random scientific symbols, watermark, extra title, legend or pseudo-text.
```

邻接表中同一 ID 只定义一次，同一边只列一次。两条路径汇入同一节点时写成 `M06>M12; M11>M12`，不能写成 `M06+M11>M12`。若标签、公式和拓扑在五段包中仍过密，先重排；只有用户要求多个用途、图位确需拆图或单图无法在最终尺寸成立时，才规划职责明确的“架构沟通图”“接口审计图”等多图成果，不得删边、缩窄节点或依靠提示词重复强调来硬塞。

总览加局部结构只放大一个真正需要解释的部分，并用明确的引导线连接总体图中的位置与局部放大图。局部图中的小型图形必须表达真实操作；不得用伪统计图、无数值坐标、随机热图或通用占位图填空。

对样本纳排、CONSORT、病例流转和包含数字的图，逐项比对全部数字、原因和分支。错误时只用 imagegen 修改完整成图；用户已经提供且确有帮助的可选参考图可在任一轮使用，不为使用参考图单独增加一轮。最多定向修改两轮；第二次修改后保存当前结果，分别披露内容硬伤和审美问题，再由用户决定是否继续，不自动重生整图或改用 SVG。

### 科研技术路线补充

生成论文、PPT、标书或报告技术路线前，先按 `research-figure-patterns.md` 确认以下内容：

```text
Research object and sources: <人群、队列、数据库、暴露、结局或外部数据>
Collection and time structure: <检测、设备、随访、空间匹配或重复测量>
Eligibility and QC: <纳排、清洗、缺失、异常、对齐和质量控制>
Variable or feature construction: <暴露、结局、中介、协变量、指标或信号特征>
Question-method pairs: <研究问题或估计对象 -> 对应方法；逐条列出>
Validation and robustness: <交叉/外部验证、分层、敏感性、替代定义或消融>
Outputs: <效应估计、风险预测、机制路径、解释或交付成果>
Icon strategy: none; no emoji, pictogram, clip-art, stage icon, node icon or result-document icon
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
Template requirements: preserve the native copy and control safe zone; adapt subject scale, crop, visual weight, and background extension to the actual message
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

正文内容图不是无字功能插画。先按 `scenario-playbook.md` 确认输入、处理、产物和需要准确呈现的文字，再使用：

```text
Use case: infographic-diagram
Carrier: README / project documentation / tutorial / skill example, <target ratio and rendered width>
Information role: <正文内容图>
Function: explain <workflow / architecture / skill capability / before-after / result path>
Source material: <README section / SKILL.md / actual command / rendered artifact>
Core claim: <读者脱离图注仍应理解的一句话>
Archetype: <单向主链 / 并行汇聚 / 对照矩阵 / 层级 / 时间>
Nodes: <ID | exact label | role | visual object>
Edges: <source -> target | direction | relation>
Text (verbatim): <通过来源核验和删除测试后保留的必要标题、节点、数字和状态；指定语言、出现次数和层级>
Text selection: keep only <identity labels / non-obvious relation or branch conditions / critical state / selected disambiguating qualifier>; move <definitions / rationale / methods detail / limitations / sources> to native text or a long description
Text hierarchy: <optional figure title | stage heading | node label | relation term | optional qualifier>; do not give every node a subtitle
Template requirements: preserve <ratio, brand, typography, palette, safe zones>; adapt <regions, reading order, weights, density, whitespace, text-image ratio> to the content
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

| 图片类型 | 必须保持准确的内容 | 通过条件 |
| --- | --- | --- |
| 科研流程与架构图 | 文字、数字、公式、节点、边、方向、分支、汇合与几何完整性 | 关键文字与结构 100% 一致，无裁切或重叠，正常中文字宽和形状比例，页面与缩略图尺度可读 |
| 人物或临床场景 | 身份、姿态、手部、设备连接和真实光线 | 身份与设备关系不漂移，解剖和物理合理，光线符合场景 |
| 网页视觉 | 安全区、响应式裁切、主体轮廓和负空间 | 桌面与移动裁切保留主体，文字/按钮区干净，轮廓清楚 |
| README / 技术文档内容图 | 文字、输入处理产物、结构关系、模板适配和最终字号 | 脱离图注可理解，标签逐字准确，窄屏仍可读，未机械套版 |
| 真实截图 / 成果预览 | 真实状态、隐私、裁切、缩放和证明目标 | 与实际产物一致，无敏感信息、无关窗口或生成式伪 UI |
| 科学教育插图 | 对象结构、层级、标签和证据边界 | 无虚构结构或机制，标签与层级准确，抽象程度符合受众 |
| 封面与章节图 | 单一视觉命题、标题留白和印刷适配 | 主体一眼可辨，留白可用，印刷/投影无脏色和细节噪声 |

不要把流程图的逐字标签规则强加给无文字摄影，也不要把摄影的光线、景深和材质要求套到技术路线图。图类指标决定 acceptance checks；通用美学只能排在精确内容与最终显示可读性之后。

所有图类再做一次视觉系统检查：表面是否安静，区域分隔是否只使用必要手段，颜色是否落在有语义的元素上，容器是否过深，核心与辅助区域是否形成疏密节奏。检查结果不能推翻本表的内容准确和证据边界要求。

## 14. 根据原图定向修改、按内容重构与失败处理

需要保留原图视觉身份并修改、重绘或修正上一版时，附带待修改原图。用户只要求提取图中内容并彻底重构时，把原图作为内容来源图：先转写全部事实与关系，再按全新创作不附图生成，避免继续模仿其布局和审美。待修改路线中，所有需要附带的图片都有本地路径时用 `referenced_image_paths`；只能从近期对话取得图片时，使用能够覆盖全部必要图片的最小 `num_last_images_to_include`；不得同时设置两者。一种附图方式不能同时包含待修改原图和可选参考图时，优先附带待修改原图；参考图对修正确有帮助时再请用户重新附图。没有适用参考图时不额外寻找。

### 14.1 本次编辑需要确认的信息

先从实际论文、PPT、报告或网页解析图片目标，不按导出文件名或媒体序号猜测图号。以下字段只为当前任务填写，不把项目事实回写到这个通用模板文件：

```text
Target identity: <用户指向、图题/正文交叉引用、页面或段落位置>
Confirmed edit target: <经文档关系和渲染外观核对后的待修改原图>
Supporting sources: <支持本轮修改的正文、表图、results.yaml 中的结果名称或其它权威来源>
Instance-only facts: <本项目的精确标签、方法、阈值、比例、配色和修改范围>
Representation identity lock: <真实/写实/示意类型 | 必须保持的时相图、概率图、热区图、矩阵或其它关键微型图元 | 裁切、材质和已认可质量>
Carrier-managed text: <由 Word/PPT/网页/排版系统承担且不烧录进图片的图号、图题、标题或来源说明；无则 none>
```

### 14.2 图片角色

```text
Target image: the only image to edit; use it to verify all factual, scientific, structural, and identity content.
Content-source image: use it outside the generation call to transcribe and verify facts and relationships; do not attach it to a full redesign, and do not inherit its rejected layout, styling, aspect ratio, or visual grammar.
Optional reference image: use only when it has already been provided and materially helps the requested edit; borrow only its verified palette, spatial organization, reading direction, and line treatment.
Do not copy the optional reference image's objects, labels, data, layout errors, branding, scientific claims, canvas aspect ratio, narrow node geometry, condensed typography, or compression artifacts.
```

不为凑足图片数量寻找或生成参考图。用户已提供或指定且它确实能改善配色、布局或结构表达时才使用；使用时必须在提示词中保留以上作用说明。

### 14.3 不降质要求

```text
Use the attached target image to verify the edit.

Priority order:
1. factual and semantic fidelity
2. exact text, numbers, formulas, and identity
3. correct objects, nodes, arrows, and relationships
4. representation identity, key micro-visuals, crop, material, and approved local quality
5. readability at final display size
6. visual refinement

A more attractive image is not acceptable if any higher-priority item becomes worse.
Keep the original unchanged unless the candidate passes every acceptance check.
```

### 14.4 必须保持、可以调整和不得改变的内容

每轮只处理一个主要问题，并填写：

```text
USE
Edit the attached target image.
Change request: <单一、可观察的修改目标>.

CONTENT LOCK
MUST PRESERVE:
<不得改变的文字、数字、公式、对象、人物身份、节点、连线、方向和结论；真实/写实/示意类型、关键微型图元、裁切、材质和已认可质量>

GRAPH OR LAYOUT
<只列与本轮目标直接相关的位置、节点或区域；不重新讲述整张图>

VISUAL DIRECTION
MAY ADJUST:
<允许优化的版式、间距、字体层级、配色、线宽、背景和视觉重心>

CONSTRAINTS
MUST NOT CHANGE:
<不得添加、删除、纠正、推断、合并、替换或简化的内容>

Return one complete edited image, not a patch or explanation.
```

同一轮不得同时要求“修复全部文字、重排全部节点、改变配色并更换画风”。用户说“重新画图”但只点名纯色、噪声、文字或单条连线时，仍按局部编辑处理，不扩大成全图重构。后续轮次重新写明当前唯一修改目标和仍须保持的不变量，不用“同上”代替；已经在 `CONTENT LOCK` 写过的内容不再复制到 `CONSTRAINTS`。局部纯色修正需逐区写明目标色块，并明确每块为均匀不透明纯色，排除渐变、白雾、中心高光、噪声、随机深浅、纹理和透明叠色；同时锁定其余图元的表示身份和既有质量。

### 14.5 内容来源图重构模板

用户要求保留内容但明确重做布局或否定原图审美时使用：

```text
Use case: full redesign from a verified content-source image
Input handling: the source image has been transcribed outside this call; do not attach or imitate it
Verified fact inventory: <文字、数字、对象、节点、接口和结论>
Verified topology: <边、方向、分支、汇合、反馈和包含关系>
Coverage for this deliverable: <架构沟通 / 模块详解 / 算子审计 / 接口与导出约束 / 其它明确任务>
Information kept here: <完成该任务所需的全部信息>
Information kept in carrier text or separately requested figures: <不在本图硬塞的审计明细、长说明或来源>
New composition: <从任务与区域自然形状推导的全新布局>
Aesthetic direction: <独立于原图建立的表面、分隔、颜色使用位置、线条、文字层级和密度节奏>
Must not inherit: <被否定的原图栏数、卡片、比例、颜色、阴影、图标或阅读路径>
Acceptance: facts and topology match the transcribed source; composition independently succeeds; no visual anchoring to the rejected source
```

### 14.6 密集科研图定向编辑模板

下列清单先在调用外核对完整性；实际编辑提示词只抽取本轮唯一修改目标及其直接相关的不变量，按 14.4 的五段结构装配，不把整份审计表原样粘贴给 imagegen。

```text
Use case: high-fidelity scientific-figure edit
Input role: the target image is the only image to edit, not a style reference.

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

### 14.7 候选图与 HTTP 524

成功返回修改结果后，与待修改原图逐项比较并按 Section 13 核对。任何非目标文字、结构、图元、表示类型、裁切、材质或已认可质量发生漂移，都判定本轮失败并保留修改前版本。最多连续修改两轮；第二轮以上一轮结果为本轮待修改图片，但仍重复原图作用、参考图作用和四类编辑要求，并与最初原图核对。用户已经提供且确有帮助的参考图可以在任一轮使用，不为使用参考图单独增加一轮。第二次修改后停止自动修改、整图重生和绘制方式切换，把该图保存为当前结果。交付时分开说明：(1) 内容硬伤，包括错误、缺失、重复或关系漂移；(2) 表现身份漂移，包括写实/示意类型、关键微型图元、裁切、材质或既有质量变化；(3) 审美问题，包括比例、密度、对齐、留白、配色或局部失真；(4) 各问题对理解和使用的影响；随后询问用户是否继续修改。不可替代的用户原图始终保留。

HTTP 524 不计入候选图质量修正：

```text
First HTTP 524:
retry once with the same edit target and a compressed prompt; keep the image roles, structure inventory, MUST PRESERVE/MAY ADJUST/MUST NOT CHANGE requirements, and acceptance checks.

Second HTTP 524:
stop retrying; preserve the original; do not interpret timeout as a design failure; do not silently downgrade the model or switch to SVG/API.
```

imagegen 已成功返回但内容或美学仍不合格，不得据此改用 SVG。只有 imagegen 实际不可用、用户明确要求 SVG/矢量源、编辑现有 SVG 或交付格式强制矢量时才进入 `svg-diagrams`。不得用 Python、PPT/Word 文本框或 SVG 覆盖层补字，也不得以重新生成的图片冒充对原图修改成功。
