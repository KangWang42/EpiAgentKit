# 项目目录、命名与归档契约

本 reference 是正式研究项目结构细则的单源。初始化、项目化分析、写作、交付和审查 skill 均引用它，不在全局入口重复维护。简单作业、单次处理、快速核验或少量输出不适用本契约，也不得为满足本契约自动补建项目骨架。

## 1. 活跃工作区

- 项目根只保留规则、方案、日志、`.gitignore`、`.epiagentkit-raw-roots`、`.epiagentkit-layout.json`、可选 `.epiagentkit-check.json`、R 项目的 `.Rproj` 与标准编号目录；具体骨架以 `project-init` 模板为准。
- 临时、诊断、迁移和探索产物不得散落在根目录；Agent 创建前即进入 `09_backup/workbench/` 的独立批次，不先写到系统 Temp、活动目录或 `02_code/` 再搬移。
- 同一交付物只保留一组稳定语义名当前版。不得累积 `v2`、`new`、`final`、`最终版`、`完善版` 等并列文件。
- 移动产物时同步修改生成脚本的输出路径与正文引用；完成后全文搜索旧路径、旧编号与散落残留。

### 1.1 预声明布局合同

正式项目的每个活动目录、文件和位置必须先进入 `.epiagentkit-layout.json`，再创建或写入。初始化器登记标准骨架；后续分析、表图、论文、报告、PPT、咨询包和必要子目录在生成前追加精确条目。不得先把文件落在方便位置，再在收尾时猜测归属。

每个条目至少记录：

`path | kind(file/dir) | owner | purpose | producer | consumer | lifecycle(planned/active/current_deliverable)`

- `path` 使用项目相对路径并指向唯一位置；禁止绝对路径、`..`、宽泛 glob 和同一语义的多处镜像。
- `owner` 是负责该产物合同的 skill 或项目角色；`producer` 与 `consumer` 说明谁生成、谁读取；`lifecycle` 区分固定骨架、计划产物和当前交付物。
- 新增目录前先声明目录及其用途，再声明其中每个计划文件。表图的精确文件名还要进入 registry；结果数字仍进入 `results.yaml`，布局清单不复制结果内容。
- `09_backup/workbench/` 骨架及 `.gitkeep` 进入初始布局清单；其批次目录、临时解包、渲染、测试和诊断内容不进入活动布局，按 §1.2 隔离执行。`09_backup/` 内正式历史由 `INDEX.md` 与每批 `MANIFEST.md` 管理，不逐文件重复登记。
- 原始数据根保持只读，其内部来源文件不由布局合同重新命名；原始根本身和数据字典位置仍需声明。
- `check-project` 对已存在但未声明的活动路径报 ERROR，对已声明但尚未生成的 `planned` 条目不报错。旧项目没有布局清单时先报 WARN 并要求在下次正式变更前建立，不静默搬动现有文件。

### 1.2 Backup workbench

- Agent 创建的试验脚本、一次性脚本、诊断、迁移、临时渲染和阶段性测试统一放入 `09_backup/workbench/YYYY-MM-DD_HHMM_<主题>_<用途>/`。用途使用 `experiment`、`diagnostic`、`oneoff`、`render`、`migration` 或 `maintenance`；主题简短且可检索。
- 执行前写 `PLAN.md`，记录目标、只读输入或来源、主流程基线、唯一改动、运行命令、预期输出、晋级标准和状态；执行后写 `FINDINGS.md`，记录完整异常、结果、结论和采用、未采用或暂缓状态。
- 在该批次目录内创建并运行脚本。把当前进程的 `TEMP`、`TMP` 和 `TMPDIR` 指向批次内 `runtime/`；命令结束后只删除可重建的 runtime 缓存，不删除 `PLAN.md`、`FINDINGS.md`、脚本和需复核结果。既有第三方工具强制使用系统临时目录时，仅在它能可靠自动清理且没有 Agent 自建文件的情况下例外。
- 统计与方法实验还必须登记 `09_backup/EXPERIMENTS.md`。失败、持平和未采用结果同样保留；`EXPERIMENTS.md` 与 `FINDINGS.md` 不是正式结果数字单源。
- 晋级时先在 `.epiagentkit-layout.json` 和适用 registry 声明正式目标，再把经验证的必要逻辑按主流程命名重写或迁入活动目录并重跑正式验证。保留原 workbench 作为依据，不把整个试验目录直接改名为主流程，也不因试验成功静默改变方法、口径或结论。

## 2. 替换与归档

重生成报告、PPT、论文、表图或代码前，把被替代成品、对应旧代码、素材、渲染图与日志按原相对目录整组移入：

`09_backup/YYYY-MM-DD_HHMM_<主题>_<阶段>/`

每批归档必须：

1. 写 `MANIFEST.md`，记录归档时间、原路径、内容、替代版本与原因。
2. 在 `09_backup/INDEX.md` 顶部登记时间、主题、类型、目录、当前版路径与原因。
3. 从活跃工作区移走旧版，不以复制替代归档，不删除历史索引。
4. 多个候选版无法判断主次时先问用户。

归档先运行 dry-run，核对精确目标与目的地，再执行：

```bash
python <project-init技能目录>/scripts/archive_deliverables.py <项目根> \
  --target <被替代的精确相对路径> \
  --current <稳定语义名当前交付路径> \
  --topic <主题> --stage <阶段> --reason <原因> --json
python <project-init技能目录>/scripts/archive_deliverables.py <项目根> \
  --target <被替代的精确相对路径> \
  --current <稳定语义名当前交付路径> \
  --topic <主题> --stage <阶段> --reason <原因> --execute --json
```

脚本拒绝 glob、项目根、原始数据根、备份根、项目外路径、父子重叠目标和覆盖已有批次；保留原相对路径、文件哈希、`MANIFEST.md` 与 `INDEX.md`，执行失败时回滚已移动目标。

## 3. `02_code/` 契约

- 分析语言优先沿用既有主流程或用户明确选择，并在项目 `CLAUDE.md` 记录；新项目未指定时直接使用 R，标准 R 项目不要求 Python 环境。Python 仅作为用户明确选择或既有 Python 主流程的补充；R 环境或依赖缺失时不自动换用 Python，也不为统一风格跨 R/Python 重写。
- 编号脚本使用 `01..` 到 `0N..` 连续序列，不留 `test.R|py`、`temp.R|py`、`final.R|py` 等无编号文件。
- `02_code/` 只保留从原始数据复现到最终结果的主流程阶段。编号脚本不超过 10 个；阶段内子分析用参数切分。
- `config.R|py`、`conventions.R|py`、`lib/`、`vendored/` 与已有的 `run_pipeline` 不计入编号脚本数。
- 正式研究主流程不另建 `run_all.R|py`、`main.R|py` 或无项目依据的一键入口；`consulting-delivery` 结果包规定的 `run_all.R|py` 除外。
- 退役、被替代、临时诊断和探索脚本立即归档，不留在主流程目录。
- R 风格与执行规范见 `r-biostats/references/code-style.md`；Python 执行规范见 `python-biostats`。两者共用 `biostat-principles` 的复现与随机过程合同。

## 4. 表图与 registry

- 主表命名 `Table{N}_{描述}.xlsx`，附表 `TableS{N}_...`；主图命名 `Fig{N}_{描述}.{png,pdf,svg}`，附图 `FigS{N}_...`。
- N 按论文首次引用顺序连续。附表、附图放 `supplementary/`；敏感性、消融、探索和审计产物进入相应二级目录或归档。
- registry 有序清单是编号唯一来源。脚本通过 `table_path(stem)` 与 `fig_path(stem, ext)` 取路径，不写死 `Table6`、`Fig3`。实现见 `registry.md`。
- PPT、论文、标书、报告和网页的非统计视觉资产默认由 `research-visuals` 调用 imagegen 生成 PNG；用户或格式要求矢量、工具不可用，或 Image 1、适用 Image 2 与允许的整图重生成均不能保证内容精度时，才由 `svg-diagrams` 最终回退生成 SVG + PNG。统计图以 PDF 与 PNG 为主，科研原始图像保留未经生成式改写的来源文件。
- 不长期保留无编号表图，不保留同主题多版本；最终人工阅读表使用 xlsx，内部机器交换可按消费者使用 csv、tsv 或 parquet。
- 一张论文表对应一个 xlsx 主题；多个 outcome、模型或亚组放同一工作簿的多个 sheet。交付工作簿不放 cover、说明或数据字典 sheet。

## 5. 数据与中间对象

- 中间格式服从项目合同和消费者：人工复核可用 xlsx，机器交换可用 csv、tsv 或 parquet，模型、MCA、ggplot 等对象可用 `.rds` 或等价语言对象格式。
- `05_reports/` 对外交付物不含 rds/RData；`06_results/` 按内容命名，不编号。
- 脚本间通过落盘对象传值，不依赖交互环境中的临时变量。

## 6. BACKLOG 单源

`BACKLOG.md` 主表固定四列：

| 待完善内容 | 完善方式 | 重要性 | 状态 |
| --- | --- | --- | --- |

- 待完善内容以【文献/数据/方法/分析/写作/规划】标签开头。
- 完善方式为“AI”或“人工”；重要性为“必补”“建议”或“可选”。
- 新发现立即加到主表顶部。完成后只填 `✅ YYYY-MM-DD`，不删行、不另建已完成表。
- 不应进入主流程的探索项整条移到对应 `09_backup/` 的 `FINDINGS.md`；BACKLOG 的“已移出”区仅留去向、原因与日期。
- 新会话先扫未完成项：优先推进 AI 可完成的必补项，提示用户处理需要数据或决策的人工项。
- BACKLOG 不保存结果数字；结果仍以 `07_paper/results.yaml` 为准。

## 7. 收尾核对

- 签发前运行 `python <epi-project-audit技能目录>/scripts/run_check_project.py <项目根> --json`；入口会从平台安装清单解析中央 EpiAgentKit 源，不在项目内复制 `epiagentkit.py`。ERROR 必须修复，基于 mtime 或缺 provenance 的 WARN 需解释但不冒充确定性失败。
- 所有代码、表、图编号连续，生成脚本与正文引用同步。
- 有序分类水平来自所选语言的 `conventions.R|py`，脚本不散写 level、配色、P 值格式或 registry。
- 当前工作区每类交付物只有一组稳定名当前版，旧版批次有 MANIFEST 与 INDEX 记录。
- `.epiagentkit-layout.json` 覆盖全部活动目录与文件；新产物在创建前已登记，未声明路径为零。
- 一次性脚本、退役文件和探索结果已归档；根目录无零散产物。
- 统计图、非统计图解、论文、报告与咨询包分别通过对应 skill 的终检。

项目可在根目录用可选 `.epiagentkit-check.json` 扩展合法 helper、剪枝目录或指定 provenance receipt；默认契约集中在 `hooks/final_project_check.py::DEFAULT_CONTRACT`，阶段脚本不得另写一套允许清单。
