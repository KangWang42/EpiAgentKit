---
name: project-init
description: 按分析、论文、咨询、教学或单次任务的实际需要，初始化最小的卫生统计项目结构，并准备相应的 R 或 Python 代码、研究文件和可选 Git 配置。仅在用户明确要求创建项目或把空工作区建成正式项目时使用；简单作业、快速核验和已有项目分析不触发。开工先用 biostat-principles；咨询分析完成后再用 consulting-delivery 整理外发材料。
---

# 项目初始化

只有用户明确要求新建项目或把空工作区初始化时执行；Q/L、已有项目分析和一次快速核验不触发。开工先遵循 `biostat-principles`。

## 1. 选择项目类型

| `profile` 参数 | 适用场景 | 初始化内容 |
| --- | --- | --- |
| `analysis` | 正式研究设计与统计分析 | 数据、代码、结果、表图、PROTOCOL、SAP、方法决策、后续待解决事项、总运行脚本和环境说明 |
| `paper` | 分析与论文在同一项目 | `analysis` 核心加 `paper/`，不预建投稿版本 |
| `consulting` | 分析完成后需要客户交付 | `analysis` 核心加 `05_reports/`，不预建空交付包或论文目录 |
| `teaching` | 教学示例或课程材料 | `data/`、`code/`、`output/` 与 README，无正式研究记录文件 |
| `oneoff` | 用户明确要求建立可保存的单次任务目录 | `input/`、`code/`、`output/` 与 README，不创建正式项目的结果文件、表图编号表或管理文件 |

选择能够完成当前任务的最小类型。后续确有需要时再增加相应目录或正式产物，不预建空模块。

## 2. 初始化

从本 skill 的 `scripts/init_project.R` 加载函数：

```r
source("<project-init>/scripts/init_project.R", encoding = "UTF-8")
init_project(
  "cohort_example",
  profile = "analysis",
  type = 1,
  language = "r",
  root = ".",
  git = FALSE
)
```

- `type` 支持 cohort、case_control、cross_sectional、rct、meta、rwd、methodology 的序号或名称。
- 默认使用 R；只有用户明确选择或现有主流程为 Python 时使用 `language="python"`。
- `git=TRUE` 仅在用户明确启用且 Git 已存在时初始化；生成的 `.gitignore` 忽略整个 `09_backup/`，不安装 Git，不自动 push。旧项目中已经被 Git 跟踪的备份内容不自动移除，先由用户确认迁移范围。
- 旧调用的 `mode="research"|"consulting"` 仅用于兼容已有代码；新文档和新模板统一使用 `profile` 参数。

## 3. 正式研究项目结构

`analysis`、`paper` 和 `consulting` 共用以下最小核心：

```text
01_data/rawdata/       原始数据，只读
02_code/00_setup.R|py  配置、口径常量、项目自有稳定辅助函数与可选数据获取函数
02_code/               正式数据处理、统计分析、直接统计表图生成脚本及 vendored 辅助代码
03_tables/             实际生成的正式统计表
04_figures/            实际生成的正式统计图
results/derived/       可重建中间结果
results/runs/          程序自动生成的运行记录、完整日志和环境说明
09_backup/archive/     本地保存被当前版替代且需要恢复的正式文件
09_backup/workbench/   本地保存实验、诊断、复现和一次性工作
PROTOCOL.md            研究设计
SAP.md                 预设分析
DECISIONS.md           方法选择与方案偏离
BACKLOG.md             需要后续补充材料、外部资源或用户决定的事项
run_pipeline.R|py      从项目根运行全部已确认分析的总脚本
```

先按实际职责决定位置，再决定文件名和调用方式。新项目用一个 `02_code/00_setup.R|py` 集中原 `config`、`conventions`、`utils` 的内容；外部或跨项目稳定辅助实现仍放 `02_code/vendored/`。`02_code/` 其余主层文件只接收会形成正式分析数据、统计估计、`results/results.yaml` 或直接统计表图的顺序脚本。论文正文来源和确有长期需要的装配脚本属于 `paper/`，长期自动检查属于项目明确的 `tests/` 或 `checks/`，一次性验收、诊断、迁移和格式修补属于 `09_backup/workbench/`。文件有编号、职责已经拆分或会被总入口调用，均不能单独证明其属于正式分析代码。

数据下载、数据接口同步或其它外部获取代码按是否需要持续复现判断：只用一次且不承担正式来源复现时放入 workbench；仍用于更新数据、重建原始输入或证明数据来源时，可在 `00_setup.R|py` 中定义为明确命名的函数，但读取设置文件时不得自动下载，也不默认在每次统计分析中执行。函数体较长但属于同一稳定获取流程时可以保留；不要为了合并文件把执行条件写成多层分支。

首次生成清洗数据前，把权威分析输入的相对路径、格式、工作表或对象、用途和其它镜像角色写入项目设置与数据说明，不把 `data_neat` 等简称自行解释为目录。正式数据准备按 `biostat-principles` 的分析就绪数据合同生成 `results/derived/data-readiness.json`；项目模板提供 `02_code/vendored/data_readiness.R|py`，但不预设所有项目都使用 Excel、RDS 或同一文件名。

总运行脚本使用明确的脚本清单和研究顺序，不按编号通配符自动发现文件。数据准备脚本与正式分析脚本分别列出；只有存在正式分析步骤时，才在第一项统计分析前验证数据状态、权威输入、哈希、未决项和本次运行编号。新增正式分析步骤时同时审查其职责、把路径加入正确清单并验证；论文装配、发布验收和一次性检查使用各自命令，不混入总分析入口。`paper/`、`tests/` 或 `checks/` 只在项目实际需要时创建，不为目录完整性预建空文件。

初始化时不创建空的 `results/results.yaml`。第一次正式分析由实际生成结果的脚本调用随项目保存的 `emit_summary` 函数创建该文件。文件内容和旧项目读取方式见 `biostat-principles/references/result-summary-schema.md`。

`.epiagentkit-layout.json` 只说明当前使用的目录及正式产物类型，不逐文件登记。分析脚本负责生成结果文件，表图编号表负责表图顺序，咨询包的内容说明负责外发文件。详细规则见 [项目目录与归档](references/project-hygiene.md)，表图编号规则见 [表图编号表](references/registry.md)。

## 4. 记录职责

- 项目 `CLAUDE.md`：当前阶段和已经确认的分析口径。
- 项目 `README.md`：只说明运行方法、输入输出位置和阅读顺序，不重复维护项目整体阶段、各项工作完成状态或已经确认的研究口径。
- PROTOCOL/SAP：设计与预设分析。
- `DECISIONS.md`：会影响方法、结果解释或方案偏离的决定。
- `BACKLOG.md`：跨任务仍阻塞并需要数据、外部资源或用户决定的事项；当轮可解决问题不登记。
- `results/runs/<run_id>.json`：由总运行脚本自动记录命令、时间、状态、脚本、文件哈希值和运行环境；不创建 `SESSION_LOG.md`。
- `09_backup/INDEX.md`：仅在首个正式归档批次出现时创建，只索引 `archive/`。
- `EXPERIMENTS.md`：仅在第一次 E2 正式比较时创建，只列出 `workbench/` 中的 E2 批次；E0 通常不另建文件，E1 只保留该批次的 `PLAN.md` 和 `FINDINGS.md`，并按实际需要保存运行记录。

不得为了补齐历史而事后编造运行记录、方法决定或实验记录。

## 5. 验证与完成

初始化后核对：

1. 所选项目类型之外的目录和占位文件未创建；
2. 原始数据保护文件存在，且未写入原始数据内容；
3. `.epiagentkit-layout.json` 只说明目录和正式产物类型，不逐文件列举；
4. 正式研究项目的总运行脚本、配置和所选语言的结果写入函数可以解析；
5. 总运行脚本分别显式列出数据准备与正式分析步骤，未自动发现编号脚本；存在正式分析步骤时，分析就绪检查不能被绕过；论文、验收和一次性代码未混入 `02_code/`；
6. `results/results.yaml`、`SESSION_LOG.md` 和 `EXPERIMENTS.md` 未被提前创建；
7. 权威分析输入合同保留为空待确认，不擅自创建 `data_neat` 目录或选择 Excel/RDS；
8. Git 状态与用户选择一致；正式项目的 `.gitignore` 忽略整个 `09_backup/`，该目录下没有用于纳入 Git 的 `.gitkeep`。

初始化只建立项目的基本结构，不代表 PROTOCOL、SAP、分析或交付已经完成。咨询结果包在分析完成并验证后由 `consulting-delivery` 创建。
