# EpiAgentKit 全局契约

适用于 R / Python 流行病学与生物统计工作的跨任务规则。本文件只保留每个会话都需要的分流、硬红线、单源指针和完成条件；领域流程、模板、参数与示例由对应 skill 及其 references 负责。

## 1. 先分流，再动手

- 开工先读取当前工作区适用的规则；正式项目再读 `BACKLOG.md`。保留来源不明的既有改动，只修改本请求范围；多个候选当前版无法判定时先问用户。
- Git 只在命令可用时使用。已有工作区只有当前目录为仓库时才检查状态或收尾，否则跳过；不安装 Git，也不隐式初始化仓库。只有用户在 `project-init` 中明确启用 Git 时，才可对新项目执行 `git init`。
- **轻量任务**：用户明确只要简单作业、单次处理、快速核验或一个小结果，且当前工作区不是既有标准研究项目时，只调用必要 skill、读写必要文件并做与风险相称的验证。不得自动初始化项目，不补建七层目录、registry、`results.yaml`、`BACKLOG.md`、`DECISIONS.md` 或 `SESSION_LOG.md`。
- **正式项目**：用户明确要求新建或初始化研究项目、投稿或咨询交付，或工作区已有项目级 `CLAUDE.md` 与 `01_data/`、`02_code/` 等标准骨架时，遵守完整项目契约。触发领域 skill 不等于自动升级为正式项目；边界不清且会显著改变文件布局时先问用户。

## 2. 最短路由

| 任务 | 主流程 skill | 伴随或边界 |
| --- | --- | --- |
| 新建、初始化项目或空工作区建骨架 | `project-init` | 咨询项目完成分析后再用 `consulting-delivery` |
| 文献依据、最新证据、方法或指标选择 | `evidence-research` | 核验后再进入分析或写作 |
| R 清洗、描述、回归、生存及其他统计分析 | `biostat-principles` → `r-biostats` | 实际出统计图时加 `publication-figures` |
| 统计图、数据图及含坐标或尺度映射的结果图 | `biostat-principles` → `publication-figures` | 不用于流程、机制或框架图 |
| 非统计视觉、流程、框架、机制、路线、架构或图形摘要 | `research-visuals` → `imagegen` | 统计图转 `publication-figures`；仅按该 skill 的回退条件转 `svg-diagrams` |
| 从零生成论文、论文部件、投稿材料或结构性重写 | `biostat-principles` → `academic-publishing` | `academic-humanizer` 终审；实际操作 Word 时加 `docx` |
| 编辑、润色或压缩已有学术文本 | `academic-humanizer` | 实际操作 Word 时加 `docx` |
| 报告正文或报告文件 | `report-writing` | 实际操作 Word 时加 `docx` |
| 中山大学学术汇报 | `sysu-ppt` | 实际操作演示文件时加 `pptx` |
| 咨询结果最终外发打包 | `biostat-principles` → `consulting-delivery` | 仅在分析已完成并验证后运行 |
| 项目质控、结果复核与一致性检查 | `biostat-principles` → `epi-project-audit` | 项目含咨询包时同时核对咨询交付规则 |
| Word、PowerPoint、Excel 或 PDF 的实际读写与验证 | `docx` / `pptx` / `xlsx` / `pdf` | 只负责实际文件操作，不取代内容主流程 |
| 维护 EpiAgentKit 的规则、skills、hooks、脚本或同步合同 | `epiagentkit-maintenance` | 修改 skill 时同时使用 `skill-creator` |
| 创建其他 skill；提交、push 或整理 git 历史 | `skill-creator`；`git-commit-helper` | Git 流程仅在命令可用且当前目录为仓库时执行 |

平台显式调用使用 Claude Code 的 `/skill-name` 或 Codex 的 `$skill-name`；自动触发以 skill description 为准。主流程 skill 定义步骤和验收标准，references 只在其适用条件满足时读取，不把条件细节复制回本文件。

## 3. 决策、安全与工作区

- 分组、终点、纳入排除、主分析方法或多个合理口径并存时，先向用户澄清，不擅自选择。
- 不猜 API、版本、包名、数据、研究发现、文献或项目状态。先读代码、实际 `--help`、官方文档或可核验来源再断言。
- **NEVER** 修改 `01_data/rawdata/` 或项目声明的其他原始数据根。缺失或异常先回最早来源核验，不擅自填补、排除或继续计算。
- **NEVER** 读取后回显 settings、config、auth、环境变量或凭证的完整内容。配置审查只报告键路径、类型与“已设置/未设置”；发现暴露风险时要求轮换。
- 正式项目内使用相对路径，不在项目根放临时、测试或零散结果。轻量任务保持输入只读、输出集中、命名清楚，不迁移用户既有目录。
- 安装或同步 EpiAgentKit 只负责复制规则、skills、hooks 并完成 `doctor`，不负责安装或升级 R、Python、Node、Java、LibreOffice、TeX、Git 或其他运行环境、包管理器与依赖。任务执行时先只读检查并复用已有兼容环境；缺失时只说明检测结果、影响与用户下一步可执行的准备方式，不代用户创建环境或执行安装、升级、降级命令，也不默认追求最新版。

## 4. 证据、结果与追溯

- **NEVER** 编造研究结果、引文、DOI / PMID、伦理号、基金号或期刊要求；无法核验时明确标记，不包装为正式依据。
- 数据缺陷先查原始与权威来源，再报告缺什么、能否补及影响。正式项目登记 `BACKLOG.md`；只有用户确认无法补全后才商定正文表述。
- 正式项目的结果变更先同步 `07_paper/results.yaml`，再派生 `0_result_summaries.md`；下游论文、报告与 PPT 通过 `val()` 取数，禁止手敲。方法变更写 `DECISIONS.md`，操作写 `SESSION_LOG.md`，缺口或想法写 `BACKLOG.md`。轻量任务不为满足此规则补建项目账本。
- 口径常量集中在 `02_code/config.R` 与 `conventions.R`。分享包是主流程派生物，不得只改分享包而不回写主流程源。
- 不把中间结果、调参痕迹、内部变量名、程序实现或探索性峰值写成最终结论。观察性证据不使用因果措辞，也不使用“证明”“最佳”等超出证据强度的表述。
- 清洗痕迹只进入 `DECISIONS.md`，方法正文写中性的最终口径。质性编码表述为研究者完成并已复核，真实过程只进入内部审计记录。

## 5. 执行与异常闭环

- 代码写完必须实跑。多行 R 写入 `.R` 文件后用 `Rscript 文件.R` 执行；本环境的 `Rscript -e` 只用于一行小命令。
- 不以 tail 或退出码代替核验；全量扫描 `error|warning|traceback|failed|nan`。代码 bug 修复后重跑，数据问题记 `DECISIONS.md`，经证实的库噪声记 `SESSION_LOG.md`。
- Agent 同时承担执行与监测职责。发现 NA、NR、空值、记录丢失、样本量意外变化、warning、错误或结果不一致时，回到最早数据与链路定位原因，并主动向用户报告现象、证据位置、影响范围、已采取动作及待决定事项；可能改变口径、结果或结论时停在安全点等待确认，不静默修补后继续，也不以比例小或“基本成功”带过。
- 试新方法或优化模型不得直接改主流程。按 `biostat-principles` 的隔离实验、公平对照和预设纳入条件执行。

## 6. 产物质量

- 所有代码、正文、表格、图件、文档和演示文件同时遵循用户要求、既有模板、项目规则、对应学科或载体规范及主流程 skill；冲突按第 8 节处理。
- “恰当、优雅”落实为可检查标准：功能与读者匹配，事实和数字准确，层级清楚，结构紧凑，术语一致，版式克制，最终尺寸可读。正确性与证据强度优先于视觉修饰；未指定风格时采用对应 skill 的中性默认，不自行添加装饰。
- 论文、报告与汇报采用研究者视角和相应学术书面语；标题使用名词短语，英文缩写首次出现给出全称。正式文字与图内标签只使用来源材料、研究方案或可核验方法文献中的规范术语；不使用内部管理或软件工程隐喻、口语化动作、生硬直译、自造缩略语或自造四字短语。术语无法确认时保留原词并先问用户。
- 非统计视觉先走 `research-visuals` → `imagegen`，按载体、读者、证据属性、信息功能和实际显示尺寸设计。真实界面、终端、文档与分析产物用实际渲染截图；真实统计图走 `publication-figures`；科研原始图像不得生成式重绘；SVG 只按 `research-visuals` 与 `svg-diagrams` 的明确条件使用。
- 任何正式产物不得出现 emoji、网络词、em dash 或生成过程痕迹。交付前按主流程 skill 自检；发现一类问题后全文扫描同类并一次清理，交付时先报告已自检项。

## 7. 正式项目单源

| 内容 | 唯一来源 |
| --- | --- |
| 当前状态与锁定口径 | 项目 `CLAUDE.md` |
| 研究设计与预设分析 | `PROTOCOL.md`、`SAP.md` |
| 方法决策与方案偏离 | `DECISIONS.md` |
| 结果数字 | `07_paper/results.yaml`；`0_result_summaries.md` 仅为派生人读版 |
| 操作历史与待补事项 | `SESSION_LOG.md`、`BACKLOG.md` |
| 口径常量与表图编号 | `02_code/config.R`、`conventions.R` 及 registry |
| 目录、命名、归档与完成条件 | `project-init/references/project-hygiene.md` 与 `epi-project-audit` |

轻量任务以用户指定输入、输出与当前文件为准，不套用本节项目账本。

## 8. 唯一优先级

1. 用户当轮明确指示
2. 本文件 CRITICAL 硬红线
3. 项目级 `CLAUDE.md` 的项目特定规则
4. 已加载 skill 的执行流程
5. skill 内默认值、偏好与示例

任何层级涉及分组、终点、纳入排除或主分析方法歧义时均先问用户。其他 skill 只引用此顺序，不另设冲突排序。

## 9. 维护与完成

- Skill 优化不是只增不减。修改任何 EpiAgentKit skill 前，先定义观察到的缺口、必须保留的旧行为、最小变更集和新旧代表性验证用例，再判断现有内容应保留、重写、合并、下沉、脚本化或删除。每个概念保持一个单源：全局约束放本文件，核心路由放 `SKILL.md`，条件细节与示例放 `references/`，重复且需确定性的操作放 `scripts/`。变更后同时验证触发边界、旧能力、新场景、引用可达性和上下文成本；除非用户明确改变行为，不以“简化”为由丢失原功能。
- 轻量任务完成时确认请求本身已满足、输出可打开或可复现，并报告最小验证；不运行正式项目签发，也不补项目账本。
- 正式项目完成时确认原始数据未改，结果、方法、日志、BACKLOG、当前状态与 registry 已同步，当前交付物使用稳定语义名且只留一组，旧版已按 `project-hygiene.md` 归档。
- 正式项目审查或交付签发前，运行 `python <epi-project-audit技能目录>/scripts/run_check_project.py <项目根> --json`。该入口从用户安装清单的 `source` 键解析中央 `epiagentkit.py`；不得只在当前项目或 `PATH` 中查找后宣称未安装。ERROR 阻止签发，WARN 逐项解释；该命令不注册 Stop，也不自动续跑。
- 修改 EpiAgentKit 规则、skills 或 hooks 后，以仓库为单源运行 `sync --target all` 与 `doctor --target all`。
- Git 收尾遵循第 1 节边界：已有仓库的明确修改请求完成并验证后，默认按 Conventional Commits 自动提交；不满足使用条件时跳过。只有用户当轮明确要求 push 时才推送，不询问、不提醒或自行累积推送；绝不 force push 或改写远端历史。
