# Imagegen 科研视觉提示词配方

先完成视觉简报和内容契约，再选择配方。提示词不是风格词堆砌；每个字段只写会改变结果的信息。提示词不设固定字数，以消除结构歧义且不重复为准。

## 目录

1. 通用视觉简报
2. 通用主提示词
3. PPT 主视觉或章节配图
4. 论文概念或科学教育插图
5. 精确流程、技术路线或图形摘要
6. 标书立项、创新或影响配图
7. 网页 hero 或登录侧栏
8. 网页卡片、内容插图或空状态
9. 报告封面或章节插图
10. 携图定向编辑与重生成回退

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
Constraints: <准确性、真实性和载体限制>
Must not infer: <来源不支持且不得生成的结论、数字、公式、关系或细节>
Avoid: <针对本任务的生成痕迹与无关元素>
```

完整论文、项目或多图任务先按 `figure-planning.md` 建立来源到图件矩阵。每个采用候选分别保存 `Source anchors / Primary message / Rationale / Evidence class / Suggested aspect ratio`；不把整篇论文压成一段脱离来源的超长提示词，也不按章节数量机械生成图片。

计算模型、网络架构、模块详解、并行分支、跳连、反馈或张量流图需要更多表达词汇时，先读 `external/SOURCE.md`，再按关键词检索归档的上游提示词原文。只抽取与真实方法一致的布局和模块描述，并重新组装进本配方；不继承上游固定确认、字数、配色、平台或 API 要求。

## 2. 通用主提示词

```text
Act as a scientific visual editor and academic art director.
Create one complete image for the carrier and function below. Choose the visual treatment from the research content and surrounding layout; do not apply a generic “scientific” style.

<插入视觉简报>

Build one clear focal point, a stable visual hierarchy, and purposeful negative space. Match detail density to the final display size. Derive scientific credibility from the actual subject, evidence workflow, field setting, instrument, document, or mechanism, not from decorative science symbols.

Do not invent data, findings, paper titles, journal marks, medical claims, instrument readings, organizations, labels, or relationships. No watermark, logo, pseudo-text, random interface copy, decorative formulas, plastic 3D icons, clay style, children’s cartoon style, stock-photo staging, neon gradient, holographic display, cinematic volumetric lighting, meaningless floating objects, or unrelated microscopes/DNA/test tubes.
```

## 3. PPT 主视觉或章节配图

```text
Use case: scientific-educational or photorealistic-natural
Carrier: academic PPT, <全页 16:9 / 实际图片区比例>
Function: establish context for <主题> without repeating the slide title
Composition: one dominant subject on <left/right>; reserve clean negative space on <opposite side> for native slide title and body; subject faces or moves toward the slide interior
Text (verbatim): none; no title, caption, labels, page number, or interface text inside the image
Constraints: remain legible when projected; moderate contrast; integrate with <模板背景与配色>
Avoid: poster advertising, dark atmospheric crop, generic laboratory scene, decorative bokeh, excessive depth of field
```

## 4. 论文概念或科学教育插图

```text
Use case: scientific-educational
Carrier: paper figure, <single-column / double-column / graphical abstract>
Function: explain <核心命题>
Subject: <真实对象和支持元素>
Composition: white or publication-compatible background; one focal mechanism; limited supporting elements; clear reading order; safe margin against cropping
Text (verbatim): <逐字短标签> or none
Constraints: no figure number, title, long caption, invented data, journal branding, or unsupported biological detail; suitable for final print size
Avoid: sci-fi glow, decorative molecular structures, cartoon anatomy, colorful card wall, fake plots
```

## 5. 精确流程、技术路线或图形摘要

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
Constraints: node and edge counts must match the contract; no added, merged, inferred, or omitted steps; approved icons use one coherent family and remain secondary to labels and arrows; no title, watermark, legend, pseudo-text, or decorative icon
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

## 6. 标书立项、创新或影响配图

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

## 7. 网页 hero 或登录侧栏

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

## 8. 网页卡片、内容插图或空状态

```text
Use case: scientific-educational or editorial illustration
Carrier: website <feature card / article illustration / empty state>, <1:1 / 4:3>
Function: communicate <单一功能或状态>
Composition: one strong silhouette and at most one supporting object; generous padding; recognizable at <目标像素>
Text (verbatim): none
Constraints: harmonize with adjacent cards without repeating an identical template; no control icon replacement when the interface already uses an icon library
Avoid: complex scene, small texture, pseudo-text, plastic 3D badge, random background shapes
```

## 9. 报告封面或章节插图

```text
Use case: editorial illustration, paper collage, or photorealistic-natural
Carrier: report <cover / section image>, <portrait / 3:2 / 4:3>
Function: establish an editorial frame for <主题>
Composition: one focal subject; reserve native title area; controlled texture; clear edge against the page background
Text (verbatim): none; report title, date, version, and organization remain native document text
Constraints: professional, evidence-oriented, printable, and compatible with <页面配色>
Avoid: campaign poster, saturated marketing palette, dramatic spotlight, fake paper text, decorative clutter
```

## 10. 携图定向编辑与重生成回退

需要修改既有图片、根据既有图重绘或修正上一版时，携带当前编辑目标。全部目标都有本地路径时用 `referenced_image_paths`；否则用能覆盖全部目标的最小 `num_last_images_to_include`；不得同时设置两者，也不附加无关风格参考。

每轮只锁定一个主要问题，并把初始原图与当前目标共同约束为以下编辑合同：

```text
Edit the attached target image.
Change only: <单一、可观察的修改目标>.
Preserve exactly: <主体身份、载体比例、构图、对象数量、阅读顺序、全部节点与边、逐字标签、配色、光线、材质和安全区>.
Allowed to change: <完成目标所必需的局部区域或属性>.
Protected regions: <不得变化的区域>.
Do not add, delete, move, restyle, relabel, or infer unrelated elements. Return one complete edited image, not a patch or explanation.
```

修正后必须把结果与初始原图做全幅比较，而不是只看修改区域。最多连续两次携图定向编辑；第二轮以第一轮结果为当前目标，但重复全部不变量。可替代的生成稿仍失败时，才把完整内容合同写进纯文本提示词整图重生一次。精确结构图仍不准确时整图回退 `svg-diagrams`；不可替代的用户原图保留原件，不得用 Python、PPT/Word 文本框或 SVG 覆盖层补字或以重生图冒充修改成功。
