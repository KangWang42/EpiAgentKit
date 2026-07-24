---
name: academic-publishing
description: |
  基于已验证的代码、结果单源和表图生成或结构性重写中英文期刊论文、学位论文部件、摘要、题名、cover letter、审稿回复、highlights 和投稿正式往来，并做投稿前一致性自查。开工先用 biostat-principles，终审用 academic-humanizer；实际 Word 操作再配合 docx。已有文本的局部润色或压缩只用 academic-humanizer。
---

# 学术期刊论文与投稿材料生成（中英双语 · Publication-Ready）

> **一句话定位**：把项目里已经跑完的分析（代码 / 结果 / 表 / 图）转成可投稿的论文与投稿材料，
> 语言到位、结构到位、零编造、无模板化写作痕迹。

---

## 〇、强制要求（每次生成都适用，违反=未完成）

1. **数据唯一来源 = `07_paper/results.yaml`（机器单源）/ 其派生 `0_result_summaries.md`**。所有数字
   （样本量、估计值、CI、P 值、百分比）必须取自该源；脚本化拼装时用 `val("07_paper/results.yaml", "key")`
   取已渲染成品串，**禁止手敲数字、禁止四舍五入到与源不一致**（"禁手敲"指经 `val()` 取数以保持同步，**不是禁止阿拉伯数字**——统计值一律用阿拉伯数字、按各自精度呈现，NEVER 为规避而虚化成中文数字如"零点四四"）。源里没有 → 标 `[NEED CONFIRMATION]`，不瞎填。
   **双向一致性**：若需改某数字，回到 results.yaml（或其产出脚本）改、再传播下游；**NEVER** 只在正文就地改。
2. **期刊 Guide for Authors 是最高法**。一旦用户给了目标期刊，其官方投稿须知（字数、摘要类型、
   参考文献格式、图表数、声明项）覆盖本技能一切默认值。没给目标期刊就先问（见 §六）。
3. **不编造**：参考文献、伦理审批号、基金号、期刊要求、统计结论一律不得虚构。文献未提供用
   `[待补充引用]`（中）/ `[ref]`（英）占位并计数。
4. **不照抄**：参考范文只借鉴修辞功能、信息顺序、句式骨架，不复制原句。
5. **逐部分完成检查**：一次只写一个部分 → 跑自检清单 → 全过 → 标记完成 → 才进下一部分。
   **禁止一次性吐全文**。
6. **疑点先问**：分组 / 终点 / 纳排 / 主分析方法 / 目标期刊 / 作者信息不明确 → 先问用户（§六）。
7. **证据约束的自然学术文风**：所有语言先过 `academic-humanizer` 的不可变事实清单与论断—证据一致性审查；中文再过
   `chinese-style-audit.md`，英文再过 `english-phrasebank.md`。研究者第一作者视角（"本研究/we"），
   不暴露版本演进、调参或工程细节，不用固定句长配额制造表面变化。
8. **局部修改也走完整标准**（CRITICAL，最易出错）：哪怕只改一句 / 一段 / 一节，动前先按 §一加载该部件对应的
   全部 reference，动后立即对被改部分跑该部件自检 + §九 一致性检查，并复扫确认与其它部件口径一致——
   "改了方法不同步摘要 / 改了一节主语风格与全文不一致"是最常见错误。执行项见 §九。
9. **编辑前建立不可变事实清单**：提取数字、统计方向、引文、公式、表图指向、终点定义和主要论断；改后逐项比对。
   原文内部冲突先报告，不自行选值、改引文或改变结论方向。

---

## 一、路由：先定"语言 × 部件"，再加载对应 reference

第一步永远是判定两件事，然后只加载需要的 reference（节省上下文）：

### 1.1 语言

| 信号 | 语言 × 文体 | 主参考 |
|------|------|--------|
| 中文 + **期刊/论著**（投某杂志、≤5000 字、Guide for Authors、投稿版面费…） | **中文期刊论著** | `references/chinese-paper.md` + `references/section-content-playbook.md` + `references/chinese-academic-style.md` + `references/chinese-style-audit.md` |
| 中文 + **学位论文**（学位论文/硕士论文/博士论文/毕业论文/学硕/专硕/博论/答辩稿/综述章/致谢/80–120 页长文） | **中文学位论文** | `references/chinese-thesis.md` + `references/thesis-formatting.md` + `references/section-content-playbook.md` + `references/chinese-academic-style.md` + `references/chinese-style-audit.md` |
| 用户提"英文论文 / English / manuscript / 投 SCI / 投某英文期刊" | **英文** | `references/english-writing.md` + `references/english-phrasebank.md` |

期刊论著与学位论文**篇幅/结构/排版/字数完全不同**（详 `chinese-thesis.md` §9 差异表）：分不清就问（§六）。
中英文不混写：一篇稿子一种语言。**学位论文是长文**——逐部件写、各存独立 md、按学校规范排版、需人补处加亮占位
（见 `chinese-thesis.md` §8 + `thesis-formatting.md`）。

**图表内文字必须与论文语言一致（CRITICAL，最易漏）**：正文换语言时，图表里的文字也要换——
轴标签 / 图例 / 注释 / 表头 / **因子水平标签** / 单位都随论文语言。**英文稿 NEVER 沿用中文图表**：
图须用英文标签**重出**（改 `publication-figures` 的标签映射后，用项目原分析语言重跑出图脚本），表头与分类标签译英。
治本做法：标签映射在所选语言的 `conventions.R|py` 维护**中英对照**（`label_zh` / `label_en`），出图/制表按当前论文语言取，换语言只切语言键、不手改每张图。开工时先确认现有图表语言与目标稿语言是否一致，不一致先列出需重出的图表。

### 1.2 部件（决定走整篇流程还是单部件）

| 用户要的 | 加载 | 说明 |
|----------|------|------|
| 整篇论文 / 初稿 | 全套写作 reference + §二 流程 | 走完整的分部件完成顺序 |
| 单个部件（引言/方法/结果/讨论/摘要/题名） | 对应 reference 的该节 | 仍跑该部件自检清单 |
| Cover Letter / Response to Reviewers / Highlights / Graphical Abstract / Title Page / 声明 | `references/submission-materials.md` | 投稿材料，需先有定稿数据 |
| 编辑部往来 / 延期 / 撤稿 / 更正 / 科研邮件 | `references/submission-materials.md` + `../academic-humanizer/references/writing-modes.md` | 正式回复，事实与动作必须可核 |
| 基金申请书润色 / Specific Aims / Project Summary | `academic-humanizer` | 保留愿景，按“承诺—可行性”审校；不套论文收缩规则 |
| 投稿前自查 | §五 四查 | 逻辑/数据/格式/合规 |

---

## 二、核心写作流程（整篇论文）

### 2.1 先吃透项目（写第一个字之前必做）

按顺序读，建立事实底座：

1. `PROTOCOL.md` 与 `SAP.md` — 研究问题、预设终点/分析和注册口径；先区分预设、偏离与探索性。
2. `07_paper/results.yaml`（结果机器单源）/ 其派生 `0_result_summaries.md` — **数据唯一源**，脚本拼装用 `val()` 取数。没有则先让用户生成或指定来源（由 `r-biostats` 或 `python-biostats` 产出）。
3. `DECISIONS.md` — 设计/方法口径及相对 SAP 的偏离、原因和确认记录。
4. `03_tables/` 与 `04_figures/`（含 `supplementary/`）— 进正文的表图清单及其编号（来自 registry）。
5. `02_code/` 关键脚本顶部 — 确认变量定义、模型设定、软件版本，方法节据此写，**不臆测**。
6. 项目级 `CLAUDE.md` — 研究背景与当前口径锁定。

读完产出一张内部"事实卡"：研究类型、设计、对象、暴露/自变量、结局、主分析、关键结果 3–5 条、
每条结果对应的解释点+文献对照点+意义点（英文走 `english-writing.md` 的"结果—解释—贡献"映射表）。如有作者
既往论文或已认可段落，同时建立声纹卡：术语、主语、hedging、连接方式、句式节奏和段落密度。

### 2.2 写作顺序（两种语言一致）

**先 Results 和 Methods，再 Introduction 和 Discussion，最后 Abstract、Title、Cover Letter。**
原因：结果锁定后引言的 gap 和讨论的解释才有靶子，摘要才能精准压缩。

### 2.3 分部件完成顺序

```
吃透项目 → [Methods] → 自检 → 过 →
          [Results] → 自检 → 过 →
          [Introduction] → 自检 → 过 →
          [Discussion(+Conclusion)] → 自检 → 过 →
          [Abstract] → 自检 → 过 →
          [Title + Keywords] → 自检 → 过 →
          [References 整理 / 占位计数] →
          [投稿材料(按需)] →
          [拼装 Word] → 验证 → END
```

每个部件：**WRITE 写入独立 md → SELF-CHECK 跑该部件自检清单 → 字数核对 → APPROVE 标记完成 → NEXT**。
- 中文各部件的字数区间、结构、自检清单见 `chinese-paper.md`（期刊）/ `chinese-thesis.md`（学位论文）。
- 英文各部件的框架（CRGP 引言 / LOC-KD-COM 结果 / 讨论七段 / 摘要)与自检见 `english-writing.md`，
  句式从 `english-phrasebank.md` 取。

**粒度与字数（学位论文长文）**：详细度高的章节细到三级小节逐个写，**一节过薄（三五行带过）= 未完成**；内容多
的章拆成小点、一个小点写足再写下一个。字数达标靠补"该写而没写"的实质内容，绝不空话/重复/形容词凑字。
小节密度硬要求与逐部件字数表见 `chinese-thesis.md` §3.1 / §3，交付前逐部件核对。

### 2.4 文件落位

```
07_paper/
  sections/           中文稿各部件 .md（01_metadata … 07_references）
  sections_en/        英文稿各部件 .md（01_title_page … 09_abstract）
  submission/         cover_letter.md / response_to_reviewers.md / highlights.md / graphical_abstract.md
  0_result_summaries.md   数据源（只读）
  论文终稿.docx / manuscript.docx   最终输出
```

每个部件写入独立文件，不改其他部件文件。修订已认可的章节用**最小修改原则**：只改用户标注点，
其余不动，改完 grep 验证禁用词归零。

---

## 三、图、表、公式嵌入（中英通用）

正文必须真正含图表，不能只写"见表1/see Table 1"而正文无内容：

- **随文排版（默认，从一开始就这样拼）**：每个表/图紧随其**首次被引用的段落**之后插入（结果节为主），**NEVER**
  默认把图表集中堆在参考文献后；仅附表附图（S 系列）集中文末。拼装脚本按"扫正文首次引用顺序→就地插入"实现，
  未显式引用的主表图兜底补在结论后。
- **表**：用 Markdown 表格语法把 `03_tables/` 的关键数据写进 md，拼装脚本转三线表。一张论文表=一个
  主题；切面多了进同一表多 sheet（出表交给所选语言的分析 skill 与 `xlsx`，本技能只把关键行写进正文）。
- **图**：统计结果图走 `publication-figures`，以 PDF+PNG 为主；流程图、研究框架、技术路线、机制图、包含关系、科学教育插图和图形摘要等非统计视觉走 `research-visuals`，按论文最终版面、目标期刊和读者选择视觉语言并优先调用 imagegen，最终以 `FigN_xxx.png` 随文嵌入。真实显微、病理、影像或其它科研原始图像不得生成式重绘。只有用户或期刊要求矢量、工具不可用，或 Image 1、适用 Image 2 与允许的整图重生成均不能保证内容精度时，才由 `svg-diagrams` 生成 SVG + 同名 PNG，SVG 源不得丢失。`![图注](04_figures/FigN_xxx.png)` 随文嵌入，图注在图下方。
- **公式**：`$$LaTeX$$` 标记，拼装时转 OMML；**禁止**输出 `RPF_(i)`、`²⁹` 这类 fallback 字符串。
- **上下标**：用 `~i~` / `^2^`，拼装转真上下标，不要直接塞 Unicode 下标字符。

详见 `references/docx-assembly.md`。

---

## 四、拼装为 Word

终稿 docx **必须**由 `python-docx` 直接生成，**禁用** `pandoc -o`（中文字体字号、三线表、首行缩进、
真上下标控制不到位）。脚本放项目 `02_code/`（属一次性文档脚本→写完归 `09_backup/<日期>_scripts_oneoff/`，
不进编号流水线）。字体字号表、三线表规格、双字体、OMML 公式映射、英文稿排版差异，全部见
`references/docx-assembly.md`。英文稿若期刊接受可直接交 `docx` 技能产出干净 Word。

---

## 五、投稿前四查（交付前必过）

**先逐条过 `references/review-killers.md`（13 条审稿硬伤），再做四查**：

1. **逻辑查**：题名↔全文、摘要↔结果、引言 Gap↔结果是否回答、讨论是否回扣 Gap、结论无新内容、
   **探索性结果未在讨论/结论升格、未据此提具体建议**（review-killers §2）。
2. **数据查**：样本量全文一致；摘要=结果=讨论=表图=`0_result_summaries.md` 同一数字；数字精度/CI/P
   写法全文统一；效应量措辞与强度匹配（弱相关加"弱"、横断面不写因果）；模型名与变量名一致。
3. **格式查**：字数（摘要 200–500 字、正文对齐期刊上限）/摘要结构/关键词/参考文献格式/**图表按引用顺序
   连续编号且引用与存在一一对应**/术语统一/质性引语加引号。
4. **合规查**：方案/注册与 SAP 偏离已如实标识，伦理审批、知情同意、利益冲突、基金、数据可用性、作者贡献、致谢、cover letter、**报告清单（STROBE/COREQ/GRAMMS 等）**齐全；缺的真实信息用 `[待确认]` 标出不杜撰。

输出时附：仍需用户确认的信息清单 + `[NEED CONFIRMATION]`/`[待补充引用]` 计数 + 投稿 checklist。

写作中发现但当轮补不了的缺口（某段需补一篇文献、缺某项数据无法下结论、某分析能强化论证但还没做、讨论里冒出的下一步设想），**立即追加一行到项目根 `BACKLOG.md` 主表**（格式见 project-init `references/project-hygiene.md` §6）；占位符 `[待补充引用]` 只标"此处缺引用"，BACKLOG 才记"要去补什么、谁去补"——两者并用，不互相替代。

---

## 六、必须先问用户的情形（不猜）

- 目标期刊未定 → 问期刊名（决定字数、摘要类型、文献格式、声明项、cover letter 收件人）。
- 语言未定（中/英）。
- 分组 / 终点 / 纳入排除 / 主分析方法 与 `DECISIONS.md` 不一致或缺失。
- 作者列表、单位、通讯作者、基金号、伦理批号、ORCID 缺失（投稿材料需要）。
- `0_result_summaries.md` 不存在或与表图对不上。
- 用户已写好部分章节要修订 → 确认是"最小修改"还是"可重写"。
- **数据有缺陷（缺失 / 需反推分母 / 口径不全 / 需近似）→ 先问能否补真实数据（年鉴 / 普查 / 标准人口库）、用户能提供什么；
  同时写进 BACKLOG。补全前论文按现有口径照常推进，补不全再问期望表述。NEVER 把缺陷自行写成"局限"或把清洗痕迹写进正文**（见全局 `CLAUDE.md` §4）。

一次问最关键的 2–3 项，不要一口气抛十个问题。

---

## 七、reference 导航

| 文件 | 何时读 | 内容 |
|------|--------|------|
| `references/chinese-paper.md` | 写中文**期刊论著**/部件 | GB/T 7713.2 流程、各部件结构+字数+自检清单、中文期刊投稿适配、排版规范 |
| `references/chinese-thesis.md` | 写中文**学位论文**（硕/博）/部件 | 长文结构与 sections/ 分文件、各部件页数字数目标、前后置部件（封面/双声明/中英摘要/缩略语/综述/致谢/在读成果/附录）写法、长文分部件工作流、需人补加亮约定、与期刊论著差异表、学位论文自检 |
| `references/thesis-formatting.md` | 学位论文**排版/拼装** | 页面设置、逐部件字体字号表、按章图表公式编号、三级目录自动生成、双页码段、python-docx 拼装差异点、黄色高亮占位实现 |
| `references/section-content-playbook.md` | **写中文学位论文/论著前必读** | 从真实论文反推的"各部分到底写什么、怎么写"：章节骨架、摘要四段、统计分析编号清单、量表工具五要素、讨论逐因素成节、结论逐条无统计量、合格稿与模板化稿对照 |
| `references/chinese-academic-style.md` | **写任何中文稿前的文风标尺** | 学术中文文风正向规范：严肃度标定、视角人称、句子与段落、因果措辞、术语一致和文风自检 |
| `references/chinese-style-audit.md` | 中文稿写作/润色审校 | 模板化表达、证据强度、语体与 grep 审计线索；命中需结合语境判断 |
| `references/english-writing.md` | 写英文论文/部件 | IMRaD 框架、CRGP 引言、文献综述、Aims/Significance/Scope、Methods、LOC-KD-COM 结果、Discussion 七段、Conclusion、Abstract、Title |
| `references/english-phrasebank.md` | 写/润色英文 | 按章节×功能分类的句式库、时态规范、连接词、hedging、over-claim 黑名单、连贯性原则 |
| `references/submission-materials.md` | 写投稿材料与正式往来 | Cover Letter、Response to Reviewers/rebuttal、Highlights、Graphical Abstract、Title Page、Declarations、编辑部与科研邮件 |
| `references/review-killers.md` | **每篇稿写完/拼装前必读** | 审稿即退/留差印象的高频硬伤：图表连续编号、探索性结果不得升格、量表方向性、筛查vs全纳入、构念命名、效应量措辞、降维解释力、异常构成解释、STROBE/COREQ/GRAMMS、纳入标准操作化、摘要字数、数字/P/术语/引号统一、篇幅控制 |
| `references/docx-assembly.md` | 拼装 Word | python-docx 流程、字体字号表、三线表、双字体、OMML、上下标、中英排版差异 |

---

## 八、与生态内其他技能的衔接

- 开工前对齐 `biostat-principles`（口径与可复现）。
- 结果由 `r-biostats` 或 `python-biostats` 按项目主语言产出；统计图由 `publication-figures` 生成，流程/结构/机制、科学插图和图形摘要等非统计视觉由 `research-visuals` 按载体建立视觉简报、调用 imagegen，并仅在全部适用生成路径耗尽后最终回退 `svg-diagrams`，`xlsx` 出表；本技能只消费，不改分析。
- 所有学术文本润色统一走 `academic-humanizer` 的不可变事实清单、中文或英文语体与论断强度审查；Word 细排可叫 `docx`。
- 结果变 → 回写 `07_paper/results.yaml` 并重新派生 `0_result_summaries.md`；方法变 → 回写 `DECISIONS.md`；操作完 → `SESSION_LOG.md`。

---

## 九、改动后语言 / 逻辑一致性自检（强制要求 8 配套，每次生成或修改后必跑）

任何生成或修改完一个部件/一段后，立即对该部分逐条过下表，再对全文复扫确认一致；中文稿 grep 命中即改归零。

| 检查项 | 规则出处 | grep 自查（命中=改） |
|---|---|---|
| 方法/结果每个操作句有明确主语（变换不堆砌） | `chinese-academic-style.md` §2、`section-content-playbook.md` §10.1 | `grep -nE "(^\|。\|；\|后，\|时，)(采用\|计算\|提取\|纳入\|检索\|参照\|评估\|拟合\|绘制\|反推\|重新计算\|以报告)" 04_methods.md 05_results.md`；命中句逐一确认主语（排除"纳入标准/纳入的"等名词性假阳性），缺则补"本研究/研究者/结果/该队列"等并变换，**不每句机械"本研究"** |
| 不以教科书式定义介绍本研究的研究类型/方法 | `section-content-playbook.md` §10.1、§10.4 | `grep -nE "本(研究\|文\|综述)(为\|是)[^，。]{0,25}[，,]即"`；命中即删定义、直接写"本研究按…框架对…进行…/做了什么" |
| 研究目的段不用轻连接词开头 | `chinese-academic-style.md` §6ter | `grep -nE "^(基于此\|综上\|由此\|据此\|因此)[，,]本(研究\|文)"`；命中改为承接前文空白的实义过渡（"针对…现状，本研究…"） |
| 结论/摘要结论禁局限禁验证展望句 | playbook §8.2、`review-killers.md` §13b | `grep -nE "尚需.{0,20}验证|有待.{0,10}证实|受小样本.{0,10}约束|乐观偏差|泛化能力.{0,6}不足"` 命中若在结论/摘要结论=改 |
| 禁随意/不负责任表达 | `chinese-academic-style.md` §6bis、`review-killers.md` §13c | `grep -nE "值得指出的是\|最关键现象出现在\|乍看.{0,8}实际上\|不难发现\|我们可以看到"` 归零 |
| 段首禁套路化评价式开头 | `chinese-academic-style.md` §6ter | 人工读：是否"对…不仅关系到…还直接影响…/众所周知…"开头 |
| 关键术语首次中英全称+缩写，全文贯穿 | `chinese-academic-style.md` §6、`review-killers.md` §12 | 人工核每个新概念首次出现 |
| 结果分条要点式（结论先行），非数字流水账 | playbook §6.2 | 人工读主结果段 |
| 数字/术语/主语风格全文一致 | `review-killers.md` §12 | 跑审计脚本（见下）看数字集合 / 未用引用 / 模板化套话 |
| 模板化套话清理 | `chinese-style-audit.md` | 审计脚本的套话命中或 reference 搜索线索；合法术语与引文不机械删除 |

**每次改动后跑一遍审计**：若项目有审计脚本（如 `09_paper.py --step audit`）则运行，它自动扫占位符 / 未用引用 /
章节完整性 / Table-Fig 对应 / 模板化套话 / 随意表达，覆盖上表多数机检项；无此脚本则按上表 grep 逐项人工自查。
