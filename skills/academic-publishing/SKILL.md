---
name: academic-publishing
description: |
  学术论文与投稿材料生成技能（中英双语），覆盖中文期刊论著、中文学位论文、英文期刊三条线。基于项目的
  分析代码、结果汇总、表图，生成投稿/答辩质量的完整论文（中文期刊按 GB/T 7713.2 / 中文学位论文按
  GB/T 7713.1 国标分部件长文 / 英文按 IMRaD）或任一独立部件（引言、方法、结果、讨论、摘要、题名、
  综述、致谢、附录），以及投稿配套材料（Cover Letter 投稿信、Response to Reviewers 审稿回复、Highlights/
  Graphical Abstract）。逐部分写作→自检→批准→下一部分，最终拼装为格式规范的 Word。
  触发场景：(1) 用户说"写论文""生成论文""论文初稿""写英文论文""paper""manuscript"，或"写学位论文/
  硕士论文/博士论文/毕业论文/学硕论文/答辩稿""综述章节""致谢"；
  (2) 要求生成或润色任一论文部件（引言/introduction、方法/methods、结果、讨论/discussion、
  摘要/abstract、题名/title）；(3) 要求写 cover letter/投稿信、response to reviewers/审稿回复/
  rebuttal、highlights/研究亮点、graphical abstract；(4) 根据 0_result_summaries.md 或分析结果
  起草稿件；(5) 投稿前论文与材料的逻辑/语言/格式/合规自查。
---

# 学术期刊论文与投稿材料生成（中英双语 · Publication-Ready）

> **一句话定位**：把项目里已经跑完的分析（代码 / 结果 / 表 / 图）转成可投稿的论文与投稿材料，
> 语言到位、结构到位、零编造、看不出 AI 痕迹。

---

## 〇、铁律（每次生成都适用，违反=未完成）

1. **数据唯一来源 = `07_paper/0_result_summaries.md`**。所有数字（样本量、估计值、CI、P 值、
   百分比）必须逐字取自该文件或 `03_tables/` 导出表。**禁止编造或四舍五入到与源不一致**。
   源里没有的数字 → 标 `[NEED CONFIRMATION]`，不要瞎填。
2. **期刊 Guide for Authors 是最高法**。一旦用户给了目标期刊，其官方投稿须知（字数、摘要类型、
   参考文献格式、图表数、声明项）覆盖本技能一切默认值。没给目标期刊就先问（见 §六）。
3. **不编造**：参考文献、伦理审批号、基金号、期刊要求、统计结论一律不得虚构。文献未提供用
   `[待补充引用]`（中）/ `[ref]`（英）占位并计数。
4. **不照抄**：参考范文只借鉴修辞功能、信息顺序、句式骨架，不复制原句。
5. **逐部分门控**：一次只写一个部分 → 跑自检清单 → 全过 → 标记完成 → 才进下一部分。
   **禁止一次性吐全文**。
6. **疑点先问**：分组 / 终点 / 纳排 / 主分析方法 / 目标期刊 / 作者信息不明确 → 先问用户（§六）。
7. **零 AI 痕迹**：中文过 `chinese-anti-ai.md` 黑名单 + 困惑度/突发性；英文过 `english-phrasebank.md`
   的 over-claim 黑名单与时态规范。研究者第一作者视角（"本研究/we"），不暴露版本演进、调参、工程细节。

---

## 一、路由：先定"语言 × 部件"，再加载对应 reference

第一步永远是判定两件事，然后只加载需要的 reference（节省上下文）：

### 1.1 语言

| 信号 | 语言 × 文体 | 主参考 |
|------|------|--------|
| 中文 + **期刊/论著**（投某杂志、≤5000 字、Guide for Authors、投稿版面费…） | **中文期刊论著** | `references/chinese-paper.md` + `references/section-content-playbook.md` + `references/chinese-academic-style.md` + `references/chinese-anti-ai.md` |
| 中文 + **学位论文**（学位论文/硕士论文/博士论文/毕业论文/学硕/专硕/博论/答辩稿/综述章/致谢/80–120 页长文） | **中文学位论文** | `references/chinese-thesis.md` + `references/thesis-formatting.md` + `references/section-content-playbook.md` + `references/chinese-academic-style.md` + `references/chinese-anti-ai.md` |
| 用户提"英文论文 / English / manuscript / 投 SCI / 投某英文期刊" | **英文** | `references/english-writing.md` + `references/english-phrasebank.md` |

期刊论著与学位论文**篇幅/结构/排版/字数完全不同**（详 `chinese-thesis.md` §9 差异表）：分不清就问（§六）。
中英文不混写：一篇稿子一种语言。**学位论文是长文**——逐部件写、各存独立 md、按学校规范排版、需人补处加亮占位
（见 `chinese-thesis.md` §8 + `thesis-formatting.md`）。

### 1.2 部件（决定走整篇流程还是单部件）

| 用户要的 | 加载 | 说明 |
|----------|------|------|
| 整篇论文 / 初稿 | 全套写作 reference + §二 流程 | 走完整门控状态机 |
| 单个部件（引言/方法/结果/讨论/摘要/题名） | 对应 reference 的该节 | 仍跑该部件自检清单 |
| Cover Letter / Response to Reviewers / Highlights / Graphical Abstract / Title Page / 声明 | `references/submission-materials.md` | 投稿材料，需先有定稿数据 |
| 投稿前自查 | §五 四查 | 逻辑/数据/格式/合规 |

---

## 二、核心写作流程（整篇论文）

### 2.1 先吃透项目（写第一个字之前必做）

按顺序读，建立事实底座：

1. `07_paper/0_result_summaries.md` — **数据唯一源**。没有则先让用户生成或指给我（r-biostats 产出）。
2. `DECISIONS.md` — 设计/方法口径（分组、终点、纳排、主分析、敏感性分析的确定方案）。
3. `03_tables/` 与 `04_figures/`（含 `supplementary/`）— 进正文的表图清单及其编号（来自 registry）。
4. `02_code/` 关键脚本顶部 — 确认变量定义、模型设定、软件版本，方法节据此写，**不臆测**。
5. 项目级 `CLAUDE.md` — 研究背景与口径锁定（研究问题一句话、纳排、终点、主分析）。

读完产出一张内部"事实卡"：研究类型、设计、对象、暴露/自变量、结局、主分析、关键结果 3–5 条、
每条结果对应的解释点+文献对照点+意义点（英文走 `english-writing.md` 的"结果—解释—贡献"映射表）。

### 2.2 写作顺序（两种语言一致）

**先 Results 和 Methods，再 Introduction 和 Discussion，最后 Abstract、Title、Cover Letter。**
原因：结果锁定后引言的 gap 和讨论的解释才有靶子，摘要才能精准压缩。

### 2.3 门控状态机

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
- 中文各部件的字数区间、结构、自检清单见 `chinese-paper.md`。
- 英文各部件的框架（CRGP 引言 / LOC-KD-COM 结果 / 讨论七段 / 摘要)与自检见 `english-writing.md`，
  句式从 `english-phrasebank.md` 取。

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

- **表**：用 Markdown 表格语法把 `03_tables/` 的关键数据写进 md，拼装脚本转三线表。一张论文表=一个
  主题；切面多了进同一表多 sheet（出表交给 r-biostats/xlsx，本技能只把关键行写进正文）。
- **图**：`![图注](04_figures/FigN_xxx.png)` 嵌入；图注在图下方。出图规范走 `publication-figures`。
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
4. **合规查**：伦理审批、知情同意、利益冲突、基金、数据可用性、作者贡献、致谢、cover letter、**报告清单
   （STROBE/COREQ/GRAMMS 等）**齐全；缺的真实信息用 `[待确认]` 标出不杜撰。

输出时附：仍需用户确认的信息清单 + `[NEED CONFIRMATION]`/`[待补充引用]` 计数 + 投稿 checklist。

---

## 六、必须先问用户的情形（不猜）

- 目标期刊未定 → 问期刊名（决定字数、摘要类型、文献格式、声明项、cover letter 收件人）。
- 语言未定（中/英）。
- 分组 / 终点 / 纳入排除 / 主分析方法 与 `DECISIONS.md` 不一致或缺失。
- 作者列表、单位、通讯作者、基金号、伦理批号、ORCID 缺失（投稿材料需要）。
- `0_result_summaries.md` 不存在或与表图对不上。
- 用户已写好部分章节要修订 → 确认是"最小修改"还是"可重写"。

一次问最关键的 2–3 项，不要一口气抛十个问题。

---

## 七、reference 导航

| 文件 | 何时读 | 内容 |
|------|--------|------|
| `references/chinese-paper.md` | 写中文**期刊论著**/部件 | GB/T 7713.2 流程、各部件结构+字数+自检清单、中文期刊投稿适配、排版规范 |
| `references/chinese-thesis.md` | 写中文**学位论文**（硕/博）/部件 | 长文结构与 sections/ 分文件、各部件页数字数目标、前后置部件（封面/双声明/中英摘要/缩略语/综述/致谢/在读成果/附录）写法、长文门控工作流、需人补加亮约定、与期刊论著差异表、学位论文自检 |
| `references/thesis-formatting.md` | 学位论文**排版/拼装** | 页面设置、逐部件字体字号表、按章图表公式编号、三级目录自动生成、双页码段、python-docx 拼装差异点、黄色高亮占位实现 |
| `references/section-content-playbook.md` | **写中文学位论文/论著前必读** | 从真实论文反推的"各部分到底写什么、怎么写"：章节骨架、摘要四段、统计分析=编号清单（最常写错）、量表工具五要素、讨论影响因素逐个成节、结论逐条无统计量、真论文vsAI味对照 |
| `references/chinese-academic-style.md` | **写任何中文稿前的文风标尺** | 学术中文文风正向规范：严肃度标定（不随意不繁复）、视角人称、句子（句长突发性/一句一意/慎用显著与因果词）、段落（主题句/一段一论点/衔接靠语义）、该写vs不该写速查、用词、期刊vs学位论文文风差异、GOOD/BAD微例、文风自检 |
| `references/chinese-anti-ai.md` | 中文稿写作/润色/查 AI 味 | AI 套话黑名单、困惑度/突发性操作、GOOD/BAD 范例、grep 自检正则 |
| `references/english-writing.md` | 写英文论文/部件 | IMRaD 框架、CRGP 引言、文献综述、Aims/Significance/Scope、Methods、LOC-KD-COM 结果、Discussion 七段、Conclusion、Abstract、Title |
| `references/english-phrasebank.md` | 写/润色英文 | 按章节×功能分类的句式库、时态规范、连接词、hedging、over-claim 黑名单、连贯性原则 |
| `references/submission-materials.md` | 写投稿材料 | Cover Letter、Response to Reviewers/rebuttal、Highlights、Graphical Abstract、Title Page、Declarations 模板与句式 |
| `references/review-killers.md` | **每篇稿写完/拼装前必读** | 审稿即退/留差印象的高频硬伤：图表连续编号、探索性结果不得升格、量表方向性、筛查vs全纳入、构念命名、效应量措辞、降维解释力、异常构成解释、STROBE/COREQ/GRAMMS、纳入标准操作化、摘要字数、数字/P/术语/引号统一、篇幅控制 |
| `references/docx-assembly.md` | 拼装 Word | python-docx 流程、字体字号表、三线表、双字体、OMML、上下标、中英排版差异 |

---

## 八、与生态内其他技能的衔接

- 开工前对齐 `biostat-principles`（口径与可复现）。
- 结果/图表由 `r-biostats` 产出、`publication-figures` 出图、`xlsx` 出表；本技能只消费，不改分析。
- 中文去 AI 味可叠加 `humanizer-zh`；Word 细排可叫 `docx`。
- 结果变 → 回写 `0_result_summaries.md`；方法变 → 回写 `DECISIONS.md`；操作完 → `SESSION_LOG.md`。
