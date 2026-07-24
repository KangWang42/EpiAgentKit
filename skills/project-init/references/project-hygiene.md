# 项目目录、命名与归档契约

本 reference 是正式研究项目结构细则的单源。初始化、项目化分析、写作、交付和审查 skill 均引用它，不在全局入口重复维护。简单作业、单次处理、快速核验或少量输出不适用本契约，也不得为满足本契约自动补建项目骨架。

## 1. 活跃工作区

- 项目根只保留规则、方案、日志、`.gitignore`、`.epiagentkit-raw-roots`、可选 `.epiagentkit-check.json`、R 项目的 `.Rproj` 与标准编号目录；具体骨架以 `project-init` 模板为准。
- 临时、诊断、迁移和探索产物不得散落在根目录；一次性脚本完成后移入 `09_backup/<日期>_scripts_oneoff/`。
- 同一交付物只保留一组稳定语义名当前版。不得累积 `v2`、`new`、`final`、`最终版`、`完善版` 等并列文件。
- 移动产物时同步修改生成脚本的输出路径与正文引用；完成后全文搜索旧路径、旧编号与散落残留。

## 2. 替换与归档

重生成报告、PPT、论文、表图或代码前，把被替代成品、对应旧代码、素材、渲染图与日志按原相对目录整组移入：

`09_backup/YYYY-MM-DD_HHMM_<主题>_<阶段>/`

每批归档必须：

1. 写 `MANIFEST.md`，记录归档时间、原路径、内容、替代版本与原因。
2. 在 `09_backup/INDEX.md` 顶部登记时间、主题、类型、目录、当前版路径与原因。
3. 从活跃工作区移走旧版，不以复制替代归档，不删除历史索引。
4. 多个候选版无法判断主次时先问用户。

## 3. `02_code/` 契约

- 分析语言由用户、既有主流程或项目初始化时的 `language` 明确选择，并在项目 `CLAUDE.md` 记录；不为统一风格跨 R/Python 重写。
- 编号脚本使用 `01..` 到 `0N..` 连续序列，不留 `test.R`、`temp.R`、`final.R` 等无编号文件。
- `02_code/` 只保留从原始数据复现到最终结果的主流程阶段。编号脚本不超过 10 个；阶段内子分析用参数切分。
- `config.R|py`、`conventions.R|py`、`lib/`、`vendored/` 与已有的 `run_pipeline` 不计入编号脚本数。
- 正式研究主流程不另建 `run_all.R|py`、`main.R|py` 或无项目依据的一键入口；`consulting-delivery` 结果包规定的 `run_all.R|py` 除外。
- 退役、被替代、临时诊断和探索脚本立即归档，不留在主流程目录。
- R 风格、依赖声明、随机种子与执行规范见 `r-biostats/references/code-style.md`。

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
- 一次性脚本、退役文件和探索结果已归档；根目录无零散产物。
- 统计图、非统计图解、论文、报告与咨询包分别通过对应 skill 的终检。

项目可在根目录用可选 `.epiagentkit-check.json` 扩展合法 helper、剪枝目录或指定 provenance receipt；默认契约集中在 `hooks/final_project_check.py::DEFAULT_CONTRACT`，阶段脚本不得另写一套允许清单。
