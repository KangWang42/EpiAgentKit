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
10. 报告封面或章节插图
11. 图类专属质量指标
12. 携图定向编辑与失败处理

## 1. 通用视觉简报

```text
Carrier: <PPT / paper / graphical abstract / grant / report / web>
Function: <解释关系 / 建立情境 / 提示功能 / 区分章节 / 突出创新 / 展示路径 / 形成识别>
Audience: <研究者 / 临床人员 / 评审专家 / 学生 / 公众>
Evidence class: <解释插图 / 精确结构图 / 装饰视觉；不得填写统计或原始科研图像>
Source anchors: <文件、章节、小节、表图、results.yaml 键或已核验文献>
Primary message: <这张图只需要传达的一件事>
Rationale: <为什么图比文字、表格或已有图更清楚>
Subject: <真实对象、场景或关系>
Archetype: <单向主链 / 并行汇聚 / 总览加局部 / 证据复合 / 对照矩阵 / 时间或层级>
Visual language: <科学编辑插画 / 自然光纪实 / 纸艺档案 / 克制几何 / 编辑拼贴>
Composition: <比例、焦点、阅读方向、主体位置和层级>
Regions: <区域 ID | 比例位置 | 独立任务 | 内容>
Micro-visuals: <模块 ID | 与真实操作对应的微型图元；无则 none>
Icon strategy: <none / per-major-stage / semantic anchors only>
Icon map: <stage ID | literal metaphor or micro-visual | why it improves recognition>
Icon system: <L0/L1/L2/L3, outline/filled, stroke, corner, viewpoint, container, single-color logic>
Palette source: <现有模板或网页颜色；没有时描述中性色与强调逻辑>
Material and lighting: <有语义的材质与自然光线>
Text (verbatim): <必须逐字呈现的短标签；无则写 none>
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
Composition: <target ratio>; clear main path; branches close to their source; no crossing arrows; adequate label spacing
Constraints: node and edge counts must match the contract; no added, merged, inferred, or omitted steps; approved icons use one coherent family and remain secondary to labels and arrows; no title, legend, or decorative icon
Avoid: card wall, random 3D symbols, gradients, duplicate nodes, ambiguous arrowheads
```

总览加局部结构只展开一个真正需要解释的模块，并用明确调用线连接母图与局部图。模块内微型图元必须表达真实操作；不得用伪统计图、无数值坐标、随机热图或通用占位图填空。

对样本纳排、CONSORT、病例流转和包含数字的图，逐项比对全部数字、原因和分支。错误时只用 imagegen 修正完整成图；两次定向修正后整图重生成，仍不准确才整图回退 `svg-diagrams`。

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

## 10. 报告封面或章节插图

```text
Use case: editorial illustration, paper collage, or photorealistic-natural
Carrier: report <cover / section image>, <portrait / 3:2 / 4:3>
Function: establish an editorial frame for <主题>
Composition: one focal subject; reserve native title area; controlled texture; clear edge against the page background
Text (verbatim): none; report title, date, version, and organization remain native document text
Constraints: professional, evidence-oriented, printable, and compatible with <页面配色>
Avoid: campaign poster, saturated marketing palette, dramatic spotlight, fake paper text, decorative clutter
```

## 11. 图类专属质量指标

| 图片类型 | 首要锁定内容 | 通过条件 |
| --- | --- | --- |
| 科研流程与架构图 | 文字、数字、公式、节点、边、方向、分支与汇合 | 关键文字与结构 100% 一致，无裁切或重叠，页面与缩略图尺度可读 |
| 人物或临床场景 | 身份、姿态、手部、设备连接和真实光线 | 身份与设备关系不漂移，解剖和物理合理，光线符合场景 |
| 网页视觉 | 安全区、响应式裁切、主体轮廓和负空间 | 桌面与移动裁切保留主体，文字/按钮区干净，轮廓清楚 |
| 科学教育插图 | 对象结构、层级、标签和证据边界 | 无虚构结构或机制，标签与层级准确，抽象程度符合受众 |
| 封面与章节图 | 单一视觉命题、标题留白和印刷适配 | 主体一眼可辨，留白可用，印刷/投影无脏色和细节噪声 |

不要把流程图的逐字标签规则强加给无文字摄影，也不要把摄影的光线、景深和材质要求套到技术路线图。图类指标决定 acceptance checks；通用美学只能排在精确内容与载体可读性之后。

## 12. 携图定向编辑与失败处理

需要修改既有图片、根据既有图重绘或修正上一版时，携带当前编辑目标。所有待附图片都有本地路径时用 `referenced_image_paths`；近期对话能覆盖全部待附图片时用最小 `num_last_images_to_include`；不得同时设置两者。单一机制无法覆盖 Image 1 与必要 Image 2 时，省略非必要 Image 2；风格迁移必要时要求重新附图。

### 12.1 图片角色

```text
Image 1: edit target and acceptance baseline; preserve its factual, scientific, structural, and identity content.
Image 2: optional style reference only; transfer palette, spacing rhythm, and line treatment.
Do not transfer Image 2 objects, labels, data, layout errors, or branding.
```

没有明确风格迁移需求时不附 Image 2。使用 Image 2 时必须在提示词中保留以上角色声明。

### 12.2 不降质合同

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

### 12.3 LOCKED / FLEXIBLE / FORBIDDEN

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

### 12.4 密集科研图专用模板

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
- typography, spacing, alignment, border weight, and restrained palette
- no scientific-content changes

Acceptance:
- 100% critical-text accuracy
- 100% node and edge preservation
- no clipping or overlap
- readable at page scale and thumbnail scale
```

### 12.5 候选图与 HTTP 524

成功返回候选图后，与 Image 1 全幅比较并按 Section 11 验收。最多连续两轮候选图质量修正；第二轮以上一轮候选为当前目标，但重复完整基线、角色和三段式合同。可替代的生成稿仍失败时，才按完整内容合同纯文本整图重生一次；不可替代的用户原图保留原件。

HTTP 524 不计入候选图质量修正：

```text
First HTTP 524:
retry once with the same edit target and a compressed prompt; keep image roles, structure inventory, LOCKED/FLEXIBLE/FORBIDDEN, and acceptance checks.

Second HTTP 524:
stop retrying; preserve the original; do not interpret timeout as a design failure; do not silently downgrade the model or switch to SVG/API.
```

只有成功返回的候选图确实未通过内容精度门禁时，精确结构图才可继续判断 SVG 回退；不得用 Python、PPT/Word 文本框或 SVG 覆盖层补字，也不得以重生图冒充修改成功。
