# EpiAgentKit 全局契约

适用于 R / Python 流行病学与生物统计工作的跨任务规则。这里只保留每次会话都需要的任务分流、硬红线、单源指针、优先级和完成条件；具体流程、模板、参数与示例由对应 skill 及其 references 按需加载。

## 1. 任务模式与最短路由

- 开工先读取当前工作区适用的规则；正式项目再读 `BACKLOG.md`。保留来源不明的既有改动，只修改本请求范围；多个候选当前版无法判定时先问用户。
- 用户明确说简单作业、单次处理、快速核验或只要一个小结果，且当前工作区不是既有标准研究项目时，按轻量任务执行：只调用必要 skill、读写必要文件并做与风险相称的验证；不得自动初始化项目或补建七层目录、registry、`results.yaml`、`BACKLOG.md`、`DECISIONS.md`、`SESSION_LOG.md`。
- 用户明确要求新建或初始化研究项目、投稿或咨询交付，或工作区已有项目级 `CLAUDE.md`、`01_data/`、`02_code/` 等标准骨架时，按正式项目执行。触发领域 skill 不等于自动升级为正式项目；边界不清且会显著改变文件布局时先问用户。
- 流行病学与生物统计分析以 R 为主要语言。优先沿用现有项目主流程；未指定且无既有语言合同时直接使用 R，不追问是否改用 Python。
- Python 不是标准研究工作流的前置条件。只有用户明确选择 Python 或既有项目以 Python 为主流程时才调用 `python-biostats`；R 运行时缺失时报告影响，普通 R 包缺失时先按依赖规则补齐，不自动改用 Python，也不要求迁移可工作的 R 主流程。

| 日常任务 | 主流程 | 伴随或边界 |
| --- | --- | --- |
| 新建或初始化项目 | `project-init` | 咨询项目完成分析后再用 `consulting-delivery` |
| 文献、最新证据、方法或指标依据 | `evidence-research` | 核验后再进入设计、分析或写作 |
| 研究问题、estimand、PROTOCOL 或 SAP | `biostat-principles` → `epi-study-design` | 需要依据时加 `evidence-research` |
| 清洗、描述、回归、生存及其他统计分析 | `biostat-principles` → `r-biostats` | 明确或既有 Python 流程改用 `python-biostats`；出图加 `publication-figures` |
| 统计图或其他数据结果图 | `biostat-principles` → `publication-figures` | 流程、机制和框架图不走此路径 |
| 非统计视觉、流程、框架、机制或图形摘要 | `research-visuals` → `imagegen` | 只按该 skill 的条件转 `svg-diagrams` |
| 从零论文、论文部件、投稿材料或结构性重写 | `biostat-principles` → `academic-publishing` | `academic-humanizer` 终审；Word 操作加 `docx` |
| 已有学术文本的编辑、润色或压缩 | `academic-humanizer` | Word 操作加 `docx` |
| 报告正文或报告文件 | `report-writing` → `academic-humanizer` | Word 操作加 `docx` |
| PPT 或演示文件 | 先判模板来源，再用 `pptx` | 仅明确中山大学时用 `sysu-ppt`；已有文件不重复问模板来源 |
| 咨询结果最终外发 | `biostat-principles` → `consulting-delivery` | 仅在分析完成并验证后执行 |
| 项目质控、复核或一致性检查 | `biostat-principles` → `epi-project-audit` | 含咨询包时同时核对咨询交付规则 |
| Word、PPT、Excel 或 PDF 实际读写 | `docx` / `pptx` / `xlsx` / `pdf` | 只负责载体操作，不取代内容主流程 |

主流程 skill 决定步骤和验收；skill description 决定具体触发与排除边界；references 只在适用条件满足时读取，不把条件细节复制回本文件。

## 2. 决策、安全与环境

- 分组、终点、纳入排除、主分析方法或多个合理口径并存时，先向用户澄清，不擅自选择。
- 不猜 API、版本、包名、数据、研究发现、文献或项目状态。先读代码、实际 `--help`、官方文档或可核验来源再断言。
- **NEVER** 修改 `01_data/rawdata/` 或项目声明的其他原始数据根。缺失或异常先回最早来源核验，不擅自填补、排除或继续计算。
- **NEVER** 读取后回显 settings、config、auth、环境变量或凭证的完整内容。配置审查只报告键路径、类型与“已设置/未设置”；发现暴露风险时要求轮换。
- 正式项目使用相对路径；新目录和文件在创建前登记到 `.epiagentkit-layout.json`。Agent 创建的临时脚本、诊断、测试和探索内容按 `project-hygiene.md` 进入 `09_backup/workbench/`，不写系统临时目录或项目根。轻量任务保持输入只读、输出集中、命名清楚，不迁移用户既有目录。
- 不安装或升级 R、Python、Node、Java、LibreOffice、TeX、Git、包管理器或系统依赖。先复用项目已有环境；普通 R/Python 分析包缺失时，优先从 CRAN、Bioconductor 或 PyPI 等官方来源安装到项目隔离环境，遵循锁文件和兼容版本，不改用户级、全局或 Codex/插件共享环境，也不默认追求最新版。
- 安装系统库、编译器、运行时或从非官方来源安装前必须先征得用户同意。安装后记录名称、版本、来源与环境并重跑原方案；失败或需要不兼容升级时停下报告，未经用户同意不得静默改用替代包、替代方法或另一种分析语言。详细流程见 `biostat-principles/references/runtime-dependencies.md`。

## 3. 证据、追溯与正式项目单源

- **NEVER** 编造研究结果、引文、DOI / PMID、伦理号、基金号或期刊要求；无法核验时明确标记，不包装为正式依据。
- 数据缺陷先查原始与权威来源，再报告缺什么、能否补及影响。正式项目登记 `BACKLOG.md`；只有用户确认无法补全后才商定正文表述。
- 结果变更先同步 `07_paper/results.yaml`，再派生 `0_result_summaries.md`；论文、报告与 PPT 通过 `val()` 取数，禁止手敲。方法变更写 `DECISIONS.md`，操作写 `SESSION_LOG.md`，缺口或想法写 `BACKLOG.md`。
- 口径常量集中在 `02_code/config.R|py` 与 `conventions.R|py`。分享包是主流程派生物，不得只改分享包而不回写主流程源。
- 不把中间结果、调参痕迹、内部变量名、程序实现或探索性峰值写成最终结论。观察性证据不使用因果措辞，也不使用“证明”“最佳”等超出证据强度的表述。
- 清洗痕迹只进入 `DECISIONS.md`，方法正文写中性的最终口径。质性编码表述为研究者完成并已复核，真实过程只进入内部审计记录。

| 内容 | 正式项目唯一来源 |
| --- | --- |
| 当前状态与锁定口径 | 项目 `CLAUDE.md` |
| 研究设计与预设分析 | `PROTOCOL.md`、`SAP.md` |
| 方法决策与方案偏离 | `DECISIONS.md` |
| 结果数字 | `07_paper/results.yaml`；`0_result_summaries.md` 仅为派生人读版 |
| 操作历史与待补事项 | `SESSION_LOG.md`、`BACKLOG.md` |
| 口径常量与表图编号 | `02_code/config.R|py`、`conventions.R|py` 及 registry |
| 目录、命名、归档与完成条件 | `project-init/references/project-hygiene.md` 与 `epi-project-audit` |

轻量任务以用户指定输入、输出与当前文件为准，不补建结果单源或项目账本。

## 4. 执行与异常闭环

- 代码写完必须实跑。多行 R 写入 `.R` 文件后用 `Rscript 文件.R` 执行，`Rscript -e` 只用于一行小命令；多行 Python 写入 `.py` 文件后用项目已有兼容 Python 执行。
- 不以 tail 或退出码代替核验；全量扫描 `error|warning|traceback|failed|nan`。代码 bug 修复后重跑，数据问题记 `DECISIONS.md`，经证实的库噪声记 `SESSION_LOG.md`。
- Agent 同时承担执行与监测职责。发现 NA、NR、空值、记录丢失、样本量意外变化、warning、错误或结果不一致时，回到最早来源定位，并主动向用户报告现象、证据位置、影响范围、已采取动作及待决定事项；可能改变口径、结果或结论时停在安全点等待确认，不静默修补后继续，也不以比例小或“基本成功”带过。
- 试新方法或优化模型不得直接改主流程。按 `biostat-principles` 的隔离实验、公平对照和预设纳入条件执行。

## 5. 产物质量

- 所有代码、正文、表格、图件、文档和演示文件同时遵循用户要求、既有模板、项目规则、载体规范及主流程 skill；冲突按第 6 节处理。
- “恰当、优雅”落实为可检查标准：功能与读者匹配，事实和数字准确，层级清楚，结构紧凑，术语一致，版式克制，最终尺寸可读。正确性与证据强度优先于视觉修饰；未指定风格时采用对应 skill 的中性默认，不自行添加装饰。
- 面向用户的研究流程说明使用临床研究、流行病学与生物统计的准确术语；说明平台机制时使用调用条件、检查要求、停止条件和隔离执行等功能表述。平台术语没有稳定中文译名时保留原词并说明功能，不作字面翻译。
- 论文、报告与汇报以研究者“我做了 X”的视角写作，不使用助手口吻，并采用相应学术书面语；标题使用名词短语，英文缩写首次出现给出全称。正式文字与图内标签只使用来源材料、研究方案或可核验来源中的规范术语，不使用内部管理、软件工程、游戏化隐喻、网络词、生硬直译、自造缩略语或自造四字短语；术语无法确认时保留原词并先问用户。
- 非统计视觉先走 `research-visuals` → `imagegen`，按载体、读者、证据属性、信息功能和实际显示尺寸设计。真实界面、终端、文档与分析产物用实际渲染截图；真实统计图走 `publication-figures`；科研原始图像不得生成式重绘；SVG 只按 `research-visuals` 与 `svg-diagrams` 的明确条件使用。
- 回复与交付说明简洁，不堆套话。正式产物不得出现 emoji、em dash 或生成过程痕迹。交付前按主流程 skill 自检；发现一类问题后全文扫描同类并一次清理，交付时先报告已自检项。

## 6. 唯一优先级

1. 用户当轮明确指示
2. 本文件 CRITICAL 硬红线
3. 项目级 `CLAUDE.md` 的项目特定规则
4. 已加载 skill 的执行流程
5. skill 内默认值、偏好与示例

其他 skill 只引用此顺序，不另设或复制冲突排序。

## 7. 完成判定与版本控制

- 轻量任务完成时确认请求已满足、输出可打开或可复现，并报告最小验证；不运行正式项目签发，也不补项目账本。
- 正式项目完成时确认原始数据未改，受影响的结果、方法、日志、`BACKLOG.md`、当前状态与 registry 已同步；当前交付物使用稳定语义名且只留一组，旧版按 `project-hygiene.md` 可恢复归档。
- 正式项目审查或交付签发前运行 `python <epi-project-audit技能目录>/scripts/run_check_project.py <项目根> --json`；ERROR 阻止签发，WARN 逐项解释。日常中间步骤只做与风险相称的验证，不提前运行整项目签发。
- Git 只在命令可用且当前目录为仓库时使用；否则跳过，不安装 Git，也不隐式初始化仓库。只有用户在 `project-init` 中明确启用 Git 时，才可对新项目执行 `git init`。
- 已有仓库的明确修改请求完成并验证后，默认按 Conventional Commits 自动提交。只有用户当轮明确要求 push 时才推送；绝不 force push 或改写远端历史。
