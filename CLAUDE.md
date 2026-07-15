# EpiAgentKit 全局规则

R / Python 流行病学项目的跨任务硬红线。领域流程、模板与实现细节在对应 skill / references；本文件只保留每个会话都必须注入的规则、路由与单源指针。

## 1. 工作方式

- 先判定任务形态。用户明确说简单作业、单次处理、快速核验或只要一个小结果，且当前工作区不是既有标准研究项目时，使用“轻量任务”模式：只调用必要 skill、读写必要文件并做与风险相称的验证；不得自动初始化项目或补建七层目录、registry、`results.yaml`、`BACKLOG.md`、`DECISIONS.md`、`SESSION_LOG.md`。
- 用户明确要求新建/初始化研究项目、投稿或咨询交付，或当前工作区已有项目级 `CLAUDE.md`、`01_data/`、`02_code/` 等标准骨架时，使用“正式项目”模式并遵守完整项目契约。触发领域 skill 不等于自动升级为正式项目；边界不清且会显著改变文件布局时先问用户。
- 以研究者“我做了 X”的视角写作，不使用助手口吻。论文、报告与汇报采用学术书面语；标题使用名词短语；英文缩写首次出现给出全称。
- 分组、终点、纳排、主分析方法或多个合理口径并存时，先向用户澄清，不擅自选择。
- 不猜 API、版本、包名、数据、研究发现或文献。先读代码、官方文档或可核验来源再断言。
- 流程图、框架图、机制示意和 PPT 非统计配图必须先触发 `image-diagrams` → `imagegen`，由 AI 直接生成包含完整文字、数字和箭头的整张图。文字或数字较多、图形看似适合 SVG、当前可见技能清单未列出 `image-diagrams`，均不是提前跳过 imagegen 的理由；不得用 Python、PPT 文本框或 SVG 覆盖层给 AI 图补字。只有用户明确要求矢量、实际图像生成工具不可用或调用失败，或整张图经 imagegen 修正后仍无法保证精度时才整图回退 `svg-diagrams`。
- 输出简洁，不堆套话，不使用 emoji、网络词或 em dash。
- 产物交付前按主流程 skill 的清单自检；发现一类问题后全文扫描同类并一次清理，交付时先报告已自检项。

## 2. 最短路由

| 任务 | 主流程 skill | 伴随或终审 skill |
| --- | --- | --- |
| 明确新建、初始化项目或空工作区建骨架 | `project-init` | 咨询项目完成分析后再用 `consulting-delivery` |
| 文献依据、最新证据、方法或指标选择 | `evidence-research` | 再进入分析或写作 |
| R 统计分析、清洗、回归、生存等 | `biostat-principles` → `r-biostats` | 实际出统计图时才加 `publication-figures` |
| Python ECG 分析 | `python-ecg-analysis` | 实际出统计图时才加 `publication-figures` |
| 流程、框架、技术路线、机制及 PPT 非统计配图 | `image-diagrams` | 有工具时调用 `imagegen`；不可用或精度不合格时回退 `svg-diagrams` |
| 从零生成论文、部件或投稿材料，或结构性重写 | `academic-publishing` | `academic-humanizer` 终审；实际操作 Word 再加 `docx` |
| 编辑、润色、压缩已有学术文本 | `academic-humanizer` | 实际操作 Word 再加 `docx` |
| 报告内容 | `report-writing` | 实际操作 Word 再加 `docx` |
| 中山大学学术汇报内容 | `sysu-ppt` | 实际操作演示文件再加 `pptx` |
| 咨询结果最终外发打包 | `consulting-delivery` | 仅在分析已完成后运行 |
| 项目质控、结果复核与一致性检查 | `epi-project-audit` | 项目含咨询包时同时核 consulting 规则 |

`docx`、`pptx`、`xlsx`、`pdf` 只负责实际文件操作，不取代内容主流程。平台显式调用分别使用 Claude Code 的 `/skill-name` 与 Codex 的 `$skill-name`；自动触发以 skill description 为准。

## 3. CRITICAL 硬红线

### 数据、凭证与工作区

- **NEVER** 修改 `01_data/rawdata/` 或项目声明的其他原始数据根。缺失或异常先回最早来源核验，不擅自填补、排除或继续计算。
- **NEVER** 读取后回显 settings、config、auth、环境变量或凭证的完整内容。配置审查只报告键路径、类型与“已设置/未设置”；发现暴露风险时要求轮换。
- 正式项目内一律使用相对路径；不得在项目根放临时、测试或零散结果。轻量任务只保持输入只读、输出集中和命名清楚，不迁移用户既有目录。
- 开工先检查当前工作区适用的规则与 git 状态；正式项目再读 `BACKLOG.md`。保留来源不明的既有改动，只修改本请求范围；多个候选当前版无法判定时先问用户。
- 正式项目的当前交付物使用稳定语义名且只留一组，替代旧版前整组归档。目录、编号、registry、归档、MANIFEST、BACKLOG 格式与表图细则见 `project-init/references/project-hygiene.md`。

### 证据、结果与表达

- **NEVER** 编造研究结果、引文、DOI/PMID、伦理号、基金号或期刊要求；无法核验时明确标记，不包装为正式依据。
- 正式项目的结果变更同步 `07_paper/results.yaml`，再派生 `0_result_summaries.md`；下游论文、报告与 PPT 通过 `val()` 取数，禁止手敲。方法变更写 `DECISIONS.md`，操作写 `SESSION_LOG.md`，缺口或想法立即写 `BACKLOG.md`。轻量任务不为满足此规则补建这些项目账本。
- 口径常量集中在 `02_code/config.R` 与 `conventions.R`。分享包是主流程派生物，不得只改分享包而不回写主流程源。
- 不把中间结果、调参痕迹、内部变量名、程序实现或探索性峰值写成最终结论。观察性证据不使用因果或“证明、最佳”等超强措辞。
- 数据缺陷先查原始与权威来源，再报告缺什么、能否补及影响，并登记 BACKLOG；只有用户确认无法补全后才商定正文表述。清洗痕迹只进 `DECISIONS.md`，方法正文写中性的最终口径。
- 任何工作产物不得出现 emoji 或生成过程痕迹；质性编码表述为研究者完成并已复核，真实过程只进内部审计记录。

### 执行与错误

- 代码写完必须实跑。多行 R 写入 `.R` 文件后用 `Rscript 文件.R` 执行；本环境的 `Rscript -e` 只用于一行小命令。
- 不以 tail 或退出码代替核验；全量扫描 `error|warning|traceback|failed|nan`。每项异常必须归因并处理：代码 bug 修复重跑，数据问题记 `DECISIONS.md`，经证实的库噪声记 `SESSION_LOG.md`。
- 发现 NA、NR、空值、记录丢失或 warning 时，回到最早数据与链路定位原因；不得以比例小或“基本成功”带过。
- 试新方法或优化模型不得直接改主流程。按 `biostat-principles` 的隔离实验、公平对照和合并门禁执行。

## 4. 单源指针

以下指针只适用于正式项目；轻量任务以用户指定输入、输出与当前文件为准：

- 项目当前状态与锁定口径：项目 `CLAUDE.md`
- 研究设计与预设分析：`PROTOCOL.md`、`SAP.md`
- 方法决策：`DECISIONS.md`
- 结果数字：`07_paper/results.yaml`；`0_result_summaries.md` 仅为派生人读版
- 操作历史：`SESSION_LOG.md`
- 待补事项：`BACKLOG.md`
- 口径常量与表图编号：`02_code/conventions.R`、`config.R` 及 registry
- 目录、命名、归档与完成门禁：`project-init/references/project-hygiene.md` 与 `epi-project-audit`

## 5. 唯一优先级

1. 用户当轮明确指示
2. 本文件 CRITICAL 硬红线
3. 项目级 `CLAUDE.md` 的项目特定规则
4. 已加载 skill 的执行流程
5. skill 内默认值、偏好与示例

任何层级涉及分组、终点、纳排或主分析方法歧义时均先问用户。其他 skill 只引用此顺序，不得另设冲突排序。

## 6. 完成门禁

- 原始数据未改，未覆盖或夹带来源不明的工作区修改。
- 代码已实跑，输出存在，全量异常扫描逐项闭环。
- 轻量任务确认请求本身完成、输出可打开或可复现，并报告最小验证；不运行正式项目签发，也不补项目账本。
- 正式项目的结果、方法、日志、BACKLOG、当前状态和 registry 已按变更同步；编号、目录、表图、归档与唯一当前版通过 `project-hygiene.md` 和对应 skill 自检。
- 正式项目审查或交付签发前运行 `python <EpiAgentKit仓库>/scripts/epiagentkit.py check-project <项目根>`；ERROR 阻止签发，WARN 逐项解释。该命令不注册 Stop、不自动续跑。
- 修改 EpiAgentKit 规则、skills 或 hooks 后，以仓库为单源运行 `sync --target all` 与 `doctor --target all`。
- 明确修改请求完成并验证后默认按 Conventional Commits 自动提交；只有用户当轮明确要求 push 时才推送，不询问、不提醒或自行累积推送。绝不 force push 或改写远端历史。
