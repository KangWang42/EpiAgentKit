<div align="center">

# EpiAgentKit

**把流行病学与卫生统计任务，变成快慢自适应、可执行、可复核、可发表或交付的工作流。**

Shared research workflow kit for Claude Code and Codex, built for epidemiology and biostatistics.

[![Claude Code](https://img.shields.io/badge/Claude_Code-supported-5B4B8A?style=flat-square)](https://code.claude.com/docs)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI_Codex-supported-111827?style=flat-square)](https://openai.com/codex/)
![R workflows](https://img.shields.io/badge/R-statistical_workflows-276DC3?style=flat-square)
![Python workflows](https://img.shields.io/badge/Python-statistical_workflows-3776AB?style=flat-square)
![Agent Skills](https://img.shields.io/badge/Agent_Skills-progressive_disclosure-0F766E?style=flat-square)

[30 秒安装](#30-秒安装) · [项目能做什么](#项目能做到什么) · [实际示例](#从命令到输出) · [任务范围](#工作流怎样随任务变化) · [双平台架构](#它如何工作) · [安全边界](#安全边界) · [维护指南](#维护与贡献)

</div>

[![真实 R 分析代码、Word 论文页和通用学术汇报页共同展示从统计分析到科研成品的工作结果](docs/assets/epiagentkit-hero.webp)](docs/showcase/composites/academic-ppt.png)

> EpiAgentKit 不是新的统计软件，也不是一组万能提示词。它是一套面向科研 Agent 的规则、技能、工具和确定性检查，让研究者能够在同一套约束下组织项目、运行分析、制作成果并完成审查。

| 按任务增加必要步骤                                                   | 结果可追溯                                                                       | 双平台一致                                              |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 问答、局部修改和快速尝试立即执行，只在进入主分析或发布时增加必要检查 | 关键结果由生成脚本写入结果清单，并关联输入、分析集、运行编号和实际使用结果的文件 | Claude Code 与 Codex 从同一仓库安装、同步并接受相同检查 |

## 项目能做到什么

只需要描述当前任务，EpiAgentKit 会按任务类型加载必要 skill，并形成可检查的文件、代码或交付物。

统计分析以 R 为主要和默认路径，标准研究工作流不要求用户具备 Python 环境。任务所需运行时缺失时先做只读检查，说明用途、安装范围和风险并询问是否安装；用户不安装时优先使用现有语言中的经核验等价实现，以相同输入、方法口径和验收标准核对。不存在等价实现时明确差异，不把近似替代说成相同效果。

| 研究任务                       | 它会做什么                                                                                                                    | 典型产物                                                     |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 新建研究项目                   | 在 `analysis`、`paper`、`consulting`、`teaching` 和 `oneoff` 五种项目类型中选择当前任务所需的最小结构               | 可直接开始工作且没有多余空目录的项目基本结构                 |
| 核验文献与方法依据             | 核对题名、作者、DOI/PMID、来源身份和撤稿状态，必要时组织正式证据检索                                                          | 核验记录、证据核对表、方法选择依据                           |
| 完善研究设计与 SAP             | 把研究想法转成 PICO/PECO、estimand、终点、时间零点、偏倚控制、样本量或精度依据及预设分析                                      | 可审查的 PROTOCOL、SAP、未决事项与设计备忘录                 |
| 生成研究生开题报告             | 把研究方案、真实证据和学院模板组织成可评审的学位论文开题报告，并检查表单、方法、引文、版式和归档状态                          | 开题报告正文、DOCX、技术路线与归档前核查结果                 |
| 完成 R 统计分析                | 执行数据清洗、描述统计、回归、生存分析、中介分析与 Meta 分析；从项目根运行总脚本，并自动保存命令、状态、日志和环境信息        | 可复现 R 脚本、结果对象、必要表图与自动运行记录              |
| 完成明确选择的 Python 统计分析 | 在用户指定 Python 或既有 Python 项目中执行数据清洗、描述统计、回归、生存分析、预测验证与异常核查，并与 R 共用结果数字唯一来源 | 可复现 Python 脚本、结果对象、表图与方法记录                 |
| 制作发表级统计图               | 按真实数据和最终物理尺寸生成森林图、生存曲线、ROC、热图、回归诊断等结果图                                                     | PDF、PNG 或 SVG 图件及对应出图代码                           |
| 生成科研非统计视觉             | 为论文、PPT、标书、报告、README 和技术文档生成流程、路线、框架、机制与图形摘要，并区分内容图、真实截图和氛围图                | 经来源、结构、文字和嵌入后显示复核的完整图件                 |
| 写论文与投稿材料               | 基于项目已有结果起草中英文论文部件、学位论文、Cover Letter、Highlights 和审稿回复，并执行证据约束审校                         | Markdown 或 Word 稿件、投稿材料与自检记录                    |
| 评审论文与生成审稿报告         | 以同行评审人身份核对稿件中的数据与论断是否对应，并审查设计、偏倚、统计、解释、报告规范、语言和伦理，区分报告缺项与方法错误    | 可定位、分 major/minor、说明未核验内容的完整 reviewer report |
| 写报告与制作学术汇报           | 把分析结果转成面向读者的报告，或按用户模板、机构/会议模板或中性设计生成组会、开题、中期与答辩汇报                  | 报告正文、DOCX、可直接汇报的 PPTX                            |
| 打包统计咨询结果               | 按数据授权、交付目的和收件人可用软件整理最小外发包，中间格式、编号和报告长度由实际用途决定                                    | 交付内容清单、必要代码与结果、总运行脚本                     |
| 全项目质量审查                 | 区分日常受影响部分检查与正式发布检查，核对数据、代码、结果、表图、正文，以及伦理、合规、隐私和结果追溯记录                    | 通过、有明确限制地通过或不通过，并列出证据位置和处理建议     |
| 处理常见科研文件               | 在内容主流程之外读取、编辑、验证和转换 Word、PowerPoint、Excel 与 PDF                                                         | `.docx`、`.pptx`、`.xlsx`、`.pdf` 等实际文件         |

### 你可以直接这样提需求

```text
在这个现有队列项目中完成 Cox 回归和森林图，并核对全部 warning。

快速核验这条 DOI 的题名、作者与撤稿状态，不做系统综述。

根据 results/results.yaml 起草结果与讨论，生成 Word 稿，并检查数字一致性。

以期刊审稿人身份审查这篇论文的数据、方法、统计、论断和语言，生成完整审稿报告。

全面审查这个项目的命名、代码、结果、论文和交付包是否一致。
```

## 从命令到输出

以下 showcase 均引用仓库中的真实成果，可展开预览，也可下载对应的 PDF、Word、PPTX、图片、脚本和机器可读结果。各 skill 独立折叠，后续增加示例不会持续拉长 README。模拟结果只用于演示可复核工作流，不构成真实医学证据。

<details>
<summary><strong>academic-ppt · 通用学术汇报与实际 PPTX</strong></summary>

<a href="docs/showcase/composites/academic-ppt.png"><img src="docs/showcase/composites/academic-ppt.png" alt="并排展示中性组会汇报的生存曲线结果页和开题答辩的失访机制研究问题页" width="100%"></a>

| 中性组会汇报 | 开题答辩汇报 |
| --- | --- |
| [PPTX](docs/showcase/academic-ppt/survival-analysis-meeting.pptx) · [代表页](docs/showcase/academic-ppt/survival-analysis-meeting.png) | [PPTX](docs/showcase/academic-ppt/missing-data-proposal-defense.pptx) · [代表页](docs/showcase/academic-ppt/missing-data-proposal-defense.png) |

组会稿使用固定模拟队列的实际 Cox 模型结果和生存曲线，封面后直接进入研究设计、结果、解释边界和下一步；开题稿使用另一套中性视觉体系，围绕失访机制、方法比较、评价指标、质量控制和研究计划展开，不预设实证结果。两份 PPTX 均由 Microsoft PowerPoint 实际导出全部页面并检查文字、箭头、图表比例、页面边界和投影可读性。[查看生成脚本](docs/demo/generate_academic_ppt_showcase.py)

</details>

<details>
<summary><strong>publication-figures · 统计分析与发表级统计图</strong></summary>

```text
使用固定模拟队列完成多变量 Cox 回归。分别制作带 95% 置信区间和风险集的调整后生存曲线，
以及呈现全部模型项、参照和效应区间的森林图；两张图分别核对时间到事件和多变量效应表达。
```

<a href="docs/showcase/composites/publication-figures.png"><img src="docs/showcase/composites/publication-figures.png" alt="并排展示调整后无事件生存曲线和多变量 Cox 回归森林图" width="100%"></a>

[生存曲线 PDF](docs/demo/output/publication-figures/adjusted-survival.pdf) · [森林图 PDF](docs/demo/output/publication-figures/cox-forest.pdf)

`biostat-principles → r-biostats → publication-figures` 负责模型口径、估计方向、参照水平、最终物理尺寸和数值一致性。[查看分析与出图脚本](docs/demo/generate_survival_demo.R) · [查看固定模拟数据](docs/demo/survival-demo-data.csv) · [查看主要结果](docs/demo/output/publication-figures/survival-demo-results.csv) · [查看森林图结果](docs/demo/output/publication-figures/cox-forest-results.csv)

</details>

<details>
<summary><strong>research-visuals · 科研非统计视觉</strong></summary>

<a href="docs/showcase/composites/research-visuals.png"><img src="docs/showcase/composites/research-visuals.png" alt="并排展示跨尺度空间卷积注意力模块和跨领域科研执行流程" width="100%"></a>

[查看跨尺度注意力模块原图](docs/showcase/research-visuals/multiscale-attention.png) · [查看科研执行流程原图](docs/assets/research-workflow.webp)

`research-visuals → imagegen` 先按图中实际对象分流。计算机、人工智能和机器学习图读取专门的计算机视觉规范，保留数据表示、模块、分支、汇合与输出；流行病学和公共卫生图继续使用研究对象、时间、变量与证据状态语法。统计数据图仍转 `publication-figures`，真实界面和论文页使用实际渲染，科研原始图像不生成式重绘。

</details>

<details>
<summary><strong>evidence-research / consulting-delivery / epiagentkit-maintenance / academic-humanizer · 具体任务内容图</strong></summary>

<a href="docs/showcase/composites/content-skill-illustrations.png"><img src="docs/showcase/composites/content-skill-illustrations.png" alt="四格展示方法依据核验、咨询交付包、Skill 维护回归和学术文本局部修订的具体工作内容" width="100%"></a>

| 方法依据核验 | 咨询交付包 | Skill 维护回归 | 学术文本局部修订 |
| --- | --- | --- | --- |
| [PNG](docs/showcase/illustrations/evidence-research.png) | [PNG](docs/showcase/illustrations/consulting-delivery.png) | [PNG](docs/showcase/illustrations/epiagentkit-maintenance.png) | [PNG](docs/showcase/illustrations/academic-humanizer.png) |

四张图分别呈现：从研究问题、来源核验到证据决策；从已验证分析到外发文件；从代表性问题到双平台检查；从不可变结果到局部净稿。咨询交付和文本修订中的数值来自仓库固定模拟队列；证据核验图只展示工作结构，不把图中的来源卡当作已经完成的真实检索结果。

</details>

<details>
<summary><strong>academic-publishing · 论文与 Word 实际渲染</strong></summary>

<a href="docs/showcase/composites/manuscripts.png"><img src="docs/showcase/composites/manuscripts.png" alt="中文观察性分析完整作者稿和英文外部模型评价方法学完整作者稿的第一页" width="100%"></a>

| 中文观察性分析完整稿                                                                                                                           | 英文方法学完整稿                                                                                                                               |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [Word](docs/demo/output/academic-publishing/manuscript-preview-zh.docx) · [PDF](docs/demo/output/academic-publishing/manuscript-preview-zh.pdf) | [Word](docs/demo/output/academic-publishing/manuscript-preview-en.docx) · [PDF](docs/demo/output/academic-publishing/manuscript-preview-en.pdf) |

README 仅并排展示两份文档的第一页，Word 与 PDF 包含连续单栏排列的完整章节。中文稿使用固定模拟队列的实际模型结果、基线汇总、模型诊断和统计图；英文稿讨论外部模型评价中的校准斜率，不虚构实证发现、作者、机构、伦理号或基金信息。[查看 Word 生成与渲染脚本](docs/demo/generate_manuscript_preview.py)

</details>

<details>
<summary><strong>epi-study-design / report-writing / manuscript-peer-review / workflow-retrospective · 实际文档</strong></summary>

<a href="docs/showcase/composites/document-skills.png"><img src="docs/showcase/composites/document-skills.png" alt="四格展示研究方案与 SAP、固定模拟队列分析报告、观察性队列稿件同行评审报告和工作流问题交接报告的真实文档页" width="100%"></a>

| Skill | 可打开文件 |
| --- | --- |
| `epi-study-design` | [DOCX](docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.docx) · [PDF](docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.pdf) · [代表页](docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.png) |
| `report-writing` | [分析报告 DOCX](docs/demo/output/document-skills/report-writing/fixed-cohort-survival-report.docx) · [复现核查备忘录 DOCX](docs/demo/output/document-skills/report-writing/fixed-cohort-reproducibility-memo.docx) · [代表页](docs/demo/output/document-skills/report-writing/fixed-cohort-survival-report.png) |
| `manuscript-peer-review` | [DOCX](docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.docx) · [PDF](docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.pdf) · [代表页](docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.png) |
| `workflow-retrospective` | [workflow.txt](docs/demo/output/document-skills/workflow-retrospective/workflow.txt) · [展示 DOCX](docs/demo/output/document-skills/workflow-retrospective/workflow-retrospective-display.docx) · [PDF](docs/demo/output/document-skills/workflow-retrospective/workflow-retrospective-display.pdf) · [代表页](docs/demo/output/document-skills/workflow-retrospective/workflow-retrospective-display.png) |

研究设计稿把未知的精度假设保留为待确认；分析报告只读取固定模拟结果；同行评审报告区分报告缺项、稿内不一致与解释越界，并明确未取得原始数据；工作流复盘仍以 `workflow.txt` 为正式交接内容，DOCX 是便于 README 展示和下载的排版副本。四份文件的英文和拉丁统计符号使用 Times New Roman，统计符号按规范区分斜体与正体，数据表为白底三线表。[查看生成与渲染脚本](docs/demo/generate_document_skill_showcase.py)

</details>

<details>
<summary><strong>project-init · 项目初始化</strong></summary>

| 分析项目                                                                           | 咨询项目                                                                                  |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 队列研究的 `analysis` 结构，包含设计、SAP、分析代码、表图、结果和自动运行记录位置 | 横断面研究的 `consulting` 结构，在分析核心之外增加 `05_reports/`，但不提前创建空交付包 |
| [查看实际初始化成果](docs/showcase/project-init/analysis.md)                        | [查看实际初始化成果](docs/showcase/project-init/consulting.md)                             |

两套结构均由 [`init_project.R`](skills/project-init/scripts/init_project.R) 实际运行产生。原始数据目录只含保护占位文件；`09_backup/` 保留在本地并由项目 `.gitignore` 整体排除；`results/results.yaml`、`SESSION_LOG.md`、`EXPERIMENTS.md` 和正式咨询包不会在没有实际结果时提前创建。

</details>

<details>
<summary><strong>svg-diagrams · 可编辑 SVG 图解</strong></summary>

<a href="skills/svg-diagrams/assets/journal-flow-screening.svg"><img src="skills/svg-diagrams/assets/journal-flow-screening.svg" alt="可编辑的文献筛选流程 SVG" width="48%"></a>
<a href="skills/svg-diagrams/assets/journal-flow-branching.svg"><img src="skills/svg-diagrams/assets/journal-flow-branching.svg" alt="可编辑的分支流程 SVG" width="48%"></a>

[筛选流程 SVG](skills/svg-diagrams/assets/journal-flow-screening.svg) · [分支流程 SVG](skills/svg-diagrams/assets/journal-flow-branching.svg) · [SVG 验证脚本](skills/svg-diagrams/scripts/validate_svg.py)

</details>

<details>
<summary><strong>build-web-ui · 科研数据工作台</strong></summary>

<a href="docs/showcase/build-web-ui/desktop.png"><img src="docs/showcase/build-web-ui/desktop.png" alt="科研数据工作台桌面端示例，显示研究对象、数据冻结准备度、随访趋势、复核队列和质控规则" width="72%"></a>
<a href="docs/showcase/build-web-ui/mobile.png"><img src="docs/showcase/build-web-ui/mobile.png" alt="科研数据工作台 390 像素手机端响应式示例" width="22%"></a>

[打开实际 HTML 页面](docs/showcase/build-web-ui/index.html) · [桌面端截图](docs/showcase/build-web-ui/desktop.png) · [手机端截图](docs/showcase/build-web-ui/mobile.png) · [浏览器渲染脚本](docs/demo/render_build_web_ui_showcase.py)

示例属于管理台与科研工具界面，使用模拟名称和数字展示对象、状态、异常、动作与复核路径；未引入前端组件库，桌面与手机截图均来自已有 Chromium 的真实页面渲染。当前浅色蓝灰只服务这个管理台示例，不是 `build-web-ui` 的默认主题；实际网页必须按目的、读者、内容、使用环境、品牌与用户偏好重新建立配色合同。

</details>

<details>
<summary><strong>其它内容、审查与文件 skills · 命令—输出索引</strong></summary>

下面把其余可执行入口、当前仓库成果和适用格式规范集中在一个索引中，便于直接打开、下载或继续生成：

[单独打开或下载完整的命令—输出索引](docs/showcase/command-to-output.md)

| Skill | 命令或请求示例 | 当前可查看输出 |
| --- | --- | --- |
| `biostat-principles` → `r-biostats` | `Rscript docs/demo/generate_survival_demo.R` | [模拟数据](docs/demo/survival-demo-data.csv)、[结果清单](docs/demo/output/publication-figures/survival-demo-results.csv) |
| `evidence-research` | 核验一条 DOI、方法依据或最新指南 | [具体任务图](docs/showcase/illustrations/evidence-research.png) · [证据矩阵规范](skills/evidence-research/references/evidence-matrix.md) |
| `epi-study-design` | 把研究想法转成 PROTOCOL / SAP | [方案与 SAP DOCX](docs/demo/output/document-skills/epi-study-design/home-bp-monitoring-protocol-sap.docx) |
| `graduate-opening-report` | 按完整内容蓝图、研究方案和学院模板生成研究生学位论文开题报告 | [观察性队列结构测试 DOCX](docs/showcase/graduate-opening-report/observational-cohort.docx) · [随机对照结构测试 DOCX](docs/showcase/graduate-opening-report/randomized-intervention.docx) · [测试边界说明](docs/showcase/graduate-opening-report/INDEX.md) · [完整内容蓝图](skills/graduate-opening-report/references/full-report-blueprint.md) · [归档前核查清单](skills/graduate-opening-report/references/archive-checklist.md) |
| `python-biostats` | 明确指定 Python 后执行同一研究口径 | [Python 执行边界](skills/python-biostats/SKILL.md)；仓库不把 R 结果冒充 Python 示例 |
| `academic-humanizer` | 修订已有论文、报告或投稿文本 | [局部修订实例图](docs/showcase/illustrations/academic-humanizer.png) · [中文稿 Word](docs/demo/output/academic-publishing/manuscript-preview-zh.docx) |
| `report-writing` | 把已核验结果整理成报告正文 | [分析报告 DOCX](docs/demo/output/document-skills/report-writing/fixed-cohort-survival-report.docx) · [复现核查备忘录 DOCX](docs/demo/output/document-skills/report-writing/fixed-cohort-reproducibility-memo.docx) |
| `consulting-delivery` | 把已完成分析整理为外发交付包 | [具体交付图](docs/showcase/illustrations/consulting-delivery.png) · [咨询项目结构示例](docs/showcase/project-init/consulting.md) |
| `manuscript-peer-review` | 以同行评审人身份生成可定位审稿报告 | [同行评审 DOCX](docs/demo/output/document-skills/manuscript-peer-review/cohort-manuscript-review-report.docx) · [审稿标准](skills/manuscript-peer-review/references/review-criteria.md) |
| `epi-project-audit` | `python <skill>/scripts/run_check_project.py <项目根> --json` | [审查清单](skills/epi-project-audit/references/audit-checklist.md) · [论断校准](skills/epi-project-audit/references/claim-calibration.md) |
| `build-web-ui` | 按网页类型、主题配色与组件行为创建、美化或验收真实网页与 Web UI | [桌面示例](docs/showcase/build-web-ui/desktop.png) · [手机示例](docs/showcase/build-web-ui/mobile.png) · [实际 HTML](docs/showcase/build-web-ui/index.html) · [视觉设计手册](skills/build-web-ui/references/design-playbook.md) · [配色系统](skills/build-web-ui/references/color-systems.md) · [开源组件采用](skills/build-web-ui/references/external-design-research.md) · [浏览器验收规范](skills/build-web-ui/references/quality-gates.md) |
| `docx` / `pdf` | 打开、渲染、验证或转换实际文件 | [Word](docs/demo/output/academic-publishing/manuscript-preview-zh.docx) · [PDF](docs/demo/output/academic-publishing/manuscript-preview-zh.pdf) |
| `xlsx` | 读取、清洗、创建或核验工作簿 | [工作簿操作规范](skills/xlsx/SKILL.md)；需绑定用户数据后生成，不放虚构表格 |
| `workflow-retrospective` | 根据会话纠正生成 `workflow.txt` | [交接报告 TXT](docs/demo/output/document-skills/workflow-retrospective/workflow.txt) · [展示 DOCX](docs/demo/output/document-skills/workflow-retrospective/workflow-retrospective-display.docx) |
| `epiagentkit-maintenance` / `skill-creator` | 修改 skill、规则或同步规范 | [具体维护图](docs/showcase/illustrations/epiagentkit-maintenance.png) · [维护约定](AGENTS.md#skill-maintenance) |
| `git-commit-helper` | 审查完整差异并创建 Conventional Commit | [当前提交历史](https://github.com/KangWang42/EpiAgentKit/commits/main) |

</details>

<details>
<summary><strong>文件命名与当前版</strong></summary>

| 文件类型                         | 命名规则                                            | 示例                                                             |
| -------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------- |
| 可重复生成的脚本                 | 使用动作与对象，名称长期稳定                        | `generate_survival_demo.R`、`generate_manuscript_preview.py` |
| 当前成果                         | 使用内容语义，不用 `final`、`latest`、`new`     | `adjusted-survival.png`、`cox-forest.png`                    |
| 同类语言版本                     | 在语义名称后加语言标识                              | `manuscript-preview-zh.docx`、`manuscript-preview-en.docx`   |
| 审阅候选                         | 只留在当次 `workbench/review/`，明确候选或修改轮次 | `<topic>-edit1.png`                                           |
| 被当前版替代且需要恢复的正式文件 | 整批移入 `09_backup/archive/<时间>_<主题>_<阶段>/` | 由归档清单记录原路径与哈希值                                  |

README 和正式交付位置只引用一组当前版。预览 PNG、可编辑 Word、PDF 和机器可读结果可以并存，因为它们承担不同用途；同一内容的模糊版本后缀不会并排留在当前目录。

</details>

## 工作流怎样随任务变化

Claude Code 与 Codex 共用同一套全局规则。系统先根据用户要求和现有工作区确定本轮范围，领域技能只完成这个范围内的工作；自动检查用于保护原始数据、结果来源、敏感信息和正式发布要求。简单问题不会因为调用某个技能而变成完整项目，正式投稿或外发也不会省略必要核验。

| 范围       | 何时使用                           | 记录与验证                                                                             |
| ---------- | ---------------------------------- | -------------------------------------------------------------------------------------- |
| Q 问答     | 解释、判断、只读核验               | 直接回答，不创建项目文件                                                               |
| L 局部产物 | 单文件、单部件、单项格式或快速结果 | 只验证本次修改及其直接影响，不补建记录文件                                             |
| P 项目执行 | 改变数据、代码、方法或正式结果     | 同步实际生成结果的分析脚本、`results/results.yaml`、使用这些结果的文件和自动运行记录 |
| R 正式发布 | 投稿、外发、归档或全面质控         | 运行正式发布检查，ERROR 阻止发布，可接受限制须明确说明                                 |

| 阶段       | EpiAgentKit 的检查要求                                                                  |
| ---------- | --------------------------------------------------------------------------------------- |
| 问题定义   | 先确认 PICO/PECO、estimand、时间零点、分组、终点、纳排标准、分析集与主要分析口径        |
| 证据核验   | 核验来源身份，区分已核验事实、合理推断和待补证据                                        |
| 统计分析   | 代码必须实跑，输出必须存在，异常必须全量扫描并逐项归因                                  |
| 图表制作   | 统计数据图、非统计视觉和原始科研证据按属性分流，图件放入实际论文、PPT、报告或网页后复核 |
| 论文与汇报 | 统计数字来自机器可读的唯一来源，论文、报告、PPT 和图表不手敲关键结果                    |
| 结果交付   | 交付包服从数据授权和接收方环境；包含或引用输入均可，但必须可追溯                        |
| 项目审查   | 科学、合规、隐私、追溯或复现 ERROR 阻止发布；结构偏好通常为 WARN/INFO                   |

## 它如何工作

EpiAgentKit 把 Agent 的行为分成四层，仓库是 Claude Code 与 Codex 的共同配置源。

![EpiAgentKit 仓库中的 CLAUDE.md、skills、hooks 和 scripts 通过 install、sync 与 doctor 同步到 Claude Code 和 Codex 的真实配置目录](docs/assets/platform-architecture.webp)

| 层           | 组件                                                | 作用                                                                     |
| ------------ | --------------------------------------------------- | ------------------------------------------------------------------------ |
| 全局规则     | [`CLAUDE.md`](CLAUDE.md)                           | 每个会话必须遵守的安全要求、任务分流、唯一来源说明与完成条件             |
| 领域技能     | [`skills/`](skills/)                               | 按需加载分析、证据、写作、视觉、交付与审查流程，避免把所有规范塞进上下文 |
| 确定性 hooks | [`hooks/`](hooks/)                                 | 保护原始数据，检查 R 语法、文本痕迹、图件与结果文件                      |
| 配置管理器   | [`scripts/epiagentkit.py`](scripts/epiagentkit.py) | 安装、同步、冲突清理、双端一致性验收与项目终检                           |

### 四类任务范围

| 范围       | 什么时候使用                 | 系统行为                                                                 |
| ---------- | ---------------------------- | ------------------------------------------------------------------------ |
| Q 问答     | 解释、判断、只读核验         | 只回复，不创建文件                                                       |
| L 局部产物 | 单个已经确认的产物或快速尝试 | 直接执行，只检查实际受影响的内容                                         |
| P 项目执行 | 改变正式分析过程             | 通过总运行脚本执行，更新 `results/results.yaml`、方法决定和自动运行记录 |
| R 正式发布 | 投稿、外发、归档或全面质控   | 增加期刊要求、授权、隐私、交付和正式发布检查                             |

触发某个领域 skill 不会自动扩大范围。E0 快速核验通常不建实验目录；E1 在一个独立工作目录中写清比较前提、实际运行和结论，记录可以合并也可以分开；只有 E2 正式比较才建立全项目的比较记录，并保留所有方案的结果。

正式项目把可恢复旧版与临时工作彻底分开：

```text
09_backup/
├── archive/     被当前版替代且需要恢复的正式文件
└── workbench/   实验、诊断、复现和一次性脚本
```

`09_backup/INDEX.md` 只索引 `archive/`；项目 `EXPERIMENTS.md` 只在 E2 出现时索引 `workbench/` 中的正式比较。新项目不再把批次直接写到 `09_backup/` 根，旧项目的根级历史批次仍可读取。

整个 `09_backup/` 只在本地用于恢复、实验与核验，项目 `.gitignore` 会整体排除该目录；其中不放用于 Git 跟踪空目录的 `.gitkeep`，公开文档也不依赖其中的文件。

## 30 秒安装

最简单的方法是把仓库地址交给当前使用的 Agent，让它完成检查、安装、备份和验收；不需要先手动克隆仓库、复制规则或逐个放置 skills。

### 在 Claude Code 中

```text
请把 EpiAgentKit 安装到当前 Claude Code：https://github.com/KangWang42/EpiAgentKit。保留我现有的个人配置，安装完成后检查是否可用。
```

### 在 Codex 中

```text
请把 EpiAgentKit 安装到当前 Codex：https://github.com/KangWang42/EpiAgentKit。保留我现有的个人配置，安装完成后检查是否可用。
```

需要同时配置两端时，把“当前 Claude Code / Codex”改为“Claude Code 与 Codex”。获取仓库、选择安装目标、备份、同步和检查由 Agent 按仓库说明完成。用户不需要先处理 Git、Python、目录或复制命令。

### release 1.1

只需要规则和 18 个可分发 skills 时，可以把 [EpiAgentKit 1.1 release](https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.1) 直接交给当前 Agent：

```text
请把这个 EpiAgentKit release 安装到我当前使用的 Agent：https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.1。保留我现有的个人配置，安装完成后检查 skills 是否可用。
```

release 使用普通版本目录解压，不直接作为 `~/.claude`、`~/.codex` 或 `~/.agents`。完整的 Agent 安装要求、人工备用命令、更新和回退方法见 [release 1.1 使用说明](docs/release-1.1-usage.md)，排除范围与外部依赖见 [许可说明](docs/release-notice.md)。轻量 release 不分发 `docx`、`pdf`、`pptx`、`xlsx`、机构模板和 imagegen 系统能力。

<details>
<summary><strong>只在明确需要自己操作时查看命令行方式</strong></summary>

配置管理器会保留已有个人配置，只更新同名 EpiAgentKit 文件与受管 hook，并在安装结束后自动运行 `doctor`。向 Codex 安装规则时，还会通过独立的 `runtime` 组件在 `~/.codex/config.toml` 顶层安全合并 [`allow_login_shell = false`](https://learn.chatgpt.com/docs/config-file/config-reference#configtoml)：该设置合并步骤仅修改这一项，保留其它设置、注释、换行和 UTF-8 BOM，先校验 TOML 再原子写入；dry-run 不落盘，重复同步不产生差异，`doctor` 只报告该键是否为 `false`，不回显配置内容。这个设置减少登录 shell 与 profile 带来的不确定性，不负责选择或安装 PowerShell 7；Windows 调用仍会先识别 `powershell.exe` 5.1 与 `pwsh` 7，并避免把只兼容 7 的复杂脚本交给 5.1。

```bash
git clone https://github.com/KangWang42/EpiAgentKit.git
cd EpiAgentKit
python scripts/epiagentkit.py install
```

```bash
# Claude Code 与 Codex 完整安装
python scripts/epiagentkit.py install --target all --preset full --yes

# 只安装统计分析技能包
python scripts/epiagentkit.py install --target all --preset analysis --yes

# 只安装论文与报告技能包
python scripts/epiagentkit.py install --target all --preset writing --yes

# 只安装网页设计、实现与浏览器验收技能
python scripts/epiagentkit.py install --target all --preset web --yes

# 只为 Codex 安装通用学术 PPT 与科研视觉技能包
python scripts/epiagentkit.py install --target codex --preset ppt --yes

# 先演练，不修改用户目录
python scripts/epiagentkit.py install --target all --preset full --yes --dry-run
```

```bash
# 从仓库同步已安装内容，并复核 Claude Code 与 Codex 一致性
python scripts/epiagentkit.py sync --target all
python scripts/epiagentkit.py doctor --target all

# 查看预设与可分发技能
python scripts/epiagentkit.py list

# 自选技能，依赖项自动补齐
python scripts/epiagentkit.py install --target all --preset custom --skills academic-ppt,report-writing --with-rules --yes

# 对正式研究项目运行项目最终检查
python scripts/epiagentkit.py check-project <项目根>
```

Codex 默认把自定义 skills 安装到官方目录 `~/.agents/skills/`。`--codex-layout codex` 与 `both` 仅用于兼容旧布局，并会提示重复技能风险。

源仓库也支持两个不进入 Git 的本机选项：在根目录的 `.epiagentkit-local-skills` 中逐行写入只供本机保留、不同步的 skill 名；创建空文件 `.epiagentkit-preserve-global-rules` 后，安装器和同步器保留现有全局 `CLAUDE.md`/`AGENTS.md`，并将规则文件从 doctor 的受管组件中移除。Codex 的 `runtime` 组件独立保留：只要本次请求同步规则，仍会管理和检查 `allow_login_shell`；只同步 skills 时不修改该设置。这两个本机策略文件不进入 release。

</details>

## 功能与技能

| 类型             | Skills                                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 原则、证据与设计 | `biostat-principles` · `evidence-research` · `epi-study-design`                                                                                |
| 项目与分析       | `project-init` · `r-biostats` · `python-biostats` · `publication-figures`                                                                   |
| 科研视觉         | `research-visuals` · `svg-diagrams`                                                                                                               |
| 网页与 Web UI     | `build-web-ui`                                                                                                                                     |
| 论文与报告       | `academic-publishing` · `graduate-opening-report` · `academic-humanizer` · `report-writing`                                                     |
| 汇报与交付       | `academic-ppt` · `consulting-delivery`                                                                                                            |
| 项目审查         | `epi-project-audit`                                                                                                                                  |
| 文件与维护       | `docx` · `pdf` · `pptx` · `xlsx` · `workflow-retrospective` · `epiagentkit-maintenance` · `skill-creator` · `git-commit-helper` |

先选择完成任务所需的内容工作流，再添加必要的图件或文件操作，最后进行相应检查。研究设计使用 `biostat-principles → epi-study-design`；统计分析默认转 `r-biostats`，仅在用户明确选择或既有 Python 项目中转 `python-biostats`，实际出统计图时再加 `publication-figures`；网页创建、改版、美化与真实浏览器验收使用 `build-web-ui`，独立图片再按需调用 imagegen；研究生学位论文开题报告使用 `biostat-principles → graduate-opening-report`，研究设计、证据核验、终审和 Word 文件分别加 `epi-study-design`、`evidence-research`、`academic-humanizer` 和 `docx`；论文从零生成使用 `academic-publishing → academic-humanizer`，需要 Word 时再加 `docx`；组会、开题和答辩使用 `academic-ppt → pptx`；非统计视觉统一使用 `research-visuals → imagegen`。最多定向修改两轮，第二次修改后披露当前图的内容硬伤和审美问题，由用户决定是否继续；只有 imagegen 实际不可用、用户明确要求 SVG/矢量源、编辑现有 SVG 或目标格式强制矢量时才使用 `svg-diagrams`。

## 为什么不只是一个提示词仓库

- **原始数据只读**：`01_data/rawdata/` 与项目声明的其它原始根不得被 Agent 修改。
- **口径先于模型**：分组、终点、纳排和主分析存在多个合理定义时，必须先澄清。
- **生成脚本写结果清单**：新正式项目以 `results/results.yaml` 保存数值、显示格式和来源；解释与结论不混入结果清单，旧路径只读兼容。
- **代码必须实跑**：不以退出码或日志尾部代替核验，必须全量扫描 `error|warning|traceback|failed|nan`。
- **按本轮范围控制工作量**：Q/L 立即执行且不补写历史记录；P 只同步受影响部分；明确投稿、外发或全面审查才运行正式发布检查。
- **探索按影响分级**：E0 不创建记录文件，E1 保存单批次证据，E2 才维护正式比较索引；满足预设条件并经必要确认后才进入主流程。
- **目录按类别管理**：`.epiagentkit-layout.json` 只声明活动目录与产物类别；类别内文件由生成脚本、表图登记表或交付内容清单管理，不逐文件登记。
- **运行情况自动记录**：`run_pipeline.R|py` 把命令、时间、运行状态、脚本、输入输出文件哈希值和环境信息写入 `results/runs/<run_id>.json`，同时保留完整日志，不要求人工填写 `SESSION_LOG.md`。
- **中文以读者能直接理解为准**：逐句写清科研动作、证据、条件和确认责任；词面扫描只发现线索，不用软件内部简写替代科研表达。
- **当前版保持唯一**：含义明确且长期不变的文件名只保留一组当前交付物；被替代的正式文件进入 `09_backup/archive/`，试验与一次性工作进入 `09_backup/workbench/`，两类索引不混用。
- **修订范围可以逐项核对**：已有论文和 Word 稿先确认唯一输入、用户纠正、允许修改和不得改动的内容；只有正式的多轮修订或需要多个交付文件时，才建立 `revision-state.json`，并由同一组修改记录生成净稿、标注稿和审稿回复。
- **双平台共用正文**：Claude Code 和 Codex 读取同一份规则与技能，不维护两套容易漂移的内容。

## 安全边界

| EpiAgentKit 会做                                     | EpiAgentKit 不会做                                                                 |
| ---------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 依据项目文件、真实分析结果和可核验来源推进任务       | 编造研究发现、文献、DOI/PMID、伦理号、基金号或期刊要求                             |
| 在授权范围内整理非原始文件、运行代码、生成成果并审查 | 修改原始数据，或在数据异常未解决时擅自填补、排除和继续计算                         |
| 把观察性结果校准为合适的论断强度                     | 把关联写成已证实因果，或把探索性峰值包装成最终结论                                 |
| 自动完成可确定的执行、核验、同步和常规判断           | 在证据不足时编造研究问题、终点、分析集、异常处置、署名或必须由责任人确认的科学决定 |

正式归档只处理已经确认的非原始文件：先用 dry-run 列出将要移动的文件，再移动到 `09_backup/archive/` 中不会覆盖旧批次的位置，同时生成 `MANIFEST.json`（文件及其哈希值清单）和 `INDEX.md`（正式归档索引）。来源、当前版本或引用关系不清时停止并请用户决定。Git 可用时可额外保留恢复历史；没有 Git 时工作流会跳过 Git，不会代为安装。项目约定来自作者的研究与咨询实践，不是领域唯一标准，可按团队规范删改。

## 维护与贡献

### 从其它项目交接工作流问题

在普通研究项目中发现 Agent 没有遵循规范时，可以先让 `workflow-retrospective` 根据当前会话、用户纠正和可定位产物生成 `workflow.txt`。该文件会区分事实、推断、候选调整和未知信息，重点说明现有流程为什么没有在制作或验收阶段阻止问题；它不会在信息不完整的项目中直接改写 EpiAgentKit。可直接发送：

```text
$workflow-retrospective
根据当前会话中我已经指出的问题和能够定位的项目产物，在当前工作目录生成或更新 workflow.txt。逐项说明正确结果、实际表现、最早失效环节、现有流程没有阻止的原因、影响和证据限制。把事实、推断和候选调整分开，并写清适用工作项、触发条件、执行动作、完成证据、不适用范围和合法例外，保证脱离当前会话仍能理解。不修改正式研究产物，也不要假定你已经看到 EpiAgentKit 的完整工作流。
```

之后在 EpiAgentKit 根目录引用该文件。维护流程会重新核对完整规则和合法例外，并根据最早失效环节决定是否修改根规则、skill、reference、脚本、hook、同步器、测试或文档，而不是照抄报告建议：

```text
只修改当前 EpiAgentKit 仓库。读取 <workflow.txt 的路径>，使用 epiagentkit-maintenance 和 skill-creator 核对完整工作流。把报告作为现场证据而不是最终方案，合并同源问题，保留旧行为和合法例外，并完成能够实现要求的最小有效调整。
```

### 用 Codex 快速完善 skills

如果你有新的研究场景、补充方法或希望加入的 skill，欢迎一起参与共建。请尽量同时提供实际输入、期望结果、需要保留的旧行为和可靠参考。新建 skill 在提交前应附至少两份内容与验收重点不同的真实成果；修改既有 skill 默认以代表性实跑和回归测试验收，只有你明确要求时才另外生成审阅成果。

从本仓库根目录启动 Codex，把实际失败、正确示例、必须保留的旧行为和希望改变的结果一起给出。Codex 官方支持用 `$skill-creator` 显式选择 skill 创建与更新流程；长期仓库规范放在 `AGENTS.md`，任务流程放在各 skill 的 `SKILL.md`、`references/` 和 `scripts/` 中。可直接发送：

```text
$skill-creator
只修改当前 EpiAgentKit 仓库。先完整读取 AGENTS.md、CLAUDE.md，并使用 epiagentkit-maintenance 与 skill-creator。

实际问题：<粘贴失败现象、文件位置或错误输出>
正确结果：<说明希望得到什么，最好附一个可靠示例>
必须保留：<列出不能被这次修改破坏的旧行为>

请先复现并找到最早失效的工作流步骤，再确定保留、重写、合并、移动、脚本化或删除哪些内容。修改适用的规则、skill、reference、模板、调用者和回归测试，不要只追加同义提醒或只替换点名词语。先运行目标组件验证和直接相关的测试；只有变更根规则、任务分流、共享依赖、hooks、安装/同步器或跨 skill 共同合同时，才运行完整单元测试和 audit_workflow_contracts.py。新建 skill 时生成至少两份可独立打开、要求不同且分别合格的验收成果，连同 review/INDEX.md 交给我检查，并在我明确确认当前成果前不要 commit、sync 或 doctor；修改既有 skill 时不要自动生成这些成果，除非我本轮明确要求。不要 push，除非我本轮明确要求。
```

启用成果审阅时，成果可以是图片、渲染截图、文档、表格、报告、代码产物或其它能直接检查的真实文件；同一结果的换色、格式转换、修订前后版或日志拆分不能替代两个代表性任务。确认提交后再运行 `python scripts/epiagentkit.py sync --target all` 与 `python scripts/epiagentkit.py doctor --target all`，并新开 Codex 会话验证已安装的新 skill。Codex 关于 [`AGENTS.md`](https://learn.chatgpt.com/docs/agent-configuration/agents-md) 与 [skills](https://learn.chatgpt.com/docs/build-skills) 的当前说明以官方文档为准。

维护本仓库时先使用 `epiagentkit-maintenance`。优化不是只增不减：先确认要保留的旧行为，再决定哪些内容重写、合并、移到专门的 reference 或脚本、删除或新增，并用新旧代表性场景共同验证。每次先运行目标 validator、语法检查、代表性实跑和直接相关测试：

```bash
python scripts/audit_skill_contracts.py
python -m unittest scripts.tests.test_workflow_routing -v  # 示例：替换为受影响的测试模块
```

根规则、任务分流、共享依赖、hooks、安装/同步器或跨 skill 共同合同发生变化时，再运行完整单元测试和 `python scripts/audit_workflow_contracts.py`。提交成功后才运行 `python scripts/epiagentkit.py sync --target all` 与 `python scripts/epiagentkit.py doctor --target all`。

维护者需要重新生成轻量包时运行 `python scripts/build_release.py`。构建器只接受固定白名单，遇到未提交修改或既有目标时停止；完成许可核对后才分别使用 `--allow-dirty` 或 `--force`。默认输出 `releases/1.1/EpiAgentKit-release-1.1.zip` 及外部 SHA-256 文件。

行为发生变化时，还需要对受影响的 R、Python 或 Bash 脚本做语法检查和代表性实跑。详细 contributor 约定见 [`AGENTS.md`](AGENTS.md)，全局规则迁移说明见 [`docs/global-rule-migration.md`](docs/global-rule-migration.md)。

<details>
<summary><strong>参考来源与许可证说明</strong></summary>

Skill 分流与维护规范参考了 GitHub [awesome-copilot skills 固定提交 `dae77f2`](https://github.com/github/awesome-copilot/tree/dae77f24132c1d686c30fd5b29aee0d63668d1d2/skills) 中的最小兼容 skill 栈、输入—操作—输出匹配、可观察成功条件、基线验证和渐进披露模式。EpiAgentKit 只吸收这些通用设计原则，不复制其长篇通用 playbook、破坏性 Git 操作或与流行病学证据链冲突的固定流程。

`research-visuals` 借鉴并重新实现了 [TingxiYu/academic-figure-skill](https://github.com/TingxiYu/academic-figure-skill) 与 [LigphiDonk/academic-figure-generator](https://github.com/LigphiDonk/academic-figure-generator) 中围绕研究问题进行图前说明、逐项核对资料来源和多轮检查图件质量的方法。仓库只归档选定的开源参考文档与提示词，没有引入其正式运行脚本、示例图片或第三方 API 配置。完整来源、固定快照、许可证与 SHA-256 见 [`external/SOURCE.md`](skills/research-visuals/references/external/SOURCE.md)。

`docx`、`pdf`、`pptx`、`xlsx` 与 `skill-creator` 来自 [anthropics/skills](https://github.com/anthropics/skills)，各目录保留原始 LICENSE。

</details>
