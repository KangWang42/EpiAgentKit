---
name: r-biostats
description: |
  R 流行病学与生物统计的主要执行层，用于 R 数据清洗、描述统计、回归、生存、中介、Meta 分析、统计表图和代码调试；用户未指定且项目没有既定分析语言时也使用。开工先遵循 biostat-principles；统计图配合 publication-figures，客户外发再用 consulting-delivery。不用于已明确采用 Python 的分析、研究设计定稿或论文写作。
---

# R 生物统计执行

先按全局 `CLAUDE.md` 判定 Q/L/P/R，并遵循 `biostat-principles`。本 skill 把已经确认的研究问题转成最小、可运行、可核验的 R 分析，不因加载本 skill 自动创建正式项目目录或额外记录文件。

## 1. 输入与方法

1. 读取本轮必要输入；项目执行或正式发布时，再读取项目 `CLAUDE.md`、PROTOCOL、SAP、配置、方法决定与尚未解决且需要后续处理的事项。
2. 确认分析集、暴露或干预、终点、比较、时间零点、协变量和主要方法。多个合理口径会改变答案时先确认。
3. 从最早输入核对字段、类型、键、重复、缺失、范围和逐步样本量。
4. 方法必须匹配 estimand、研究设计、结局类型、时间结构和抽样设计，不按包的便利性替代研究问题。

只在需要时读取对应参考：

- 描述统计：[references/descriptive.md](references/descriptive.md)
- 回归与诊断：[references/regression.md](references/regression.md)
- 生存分析：[references/survival.md](references/survival.md)
- 中介分析：[references/mediation.md](references/mediation.md)
- Meta 分析：[references/meta.md](references/meta.md)
- 预测模型：[references/prognostic-models.md](references/prognostic-models.md)
- 代码风格：[references/code-style.md](references/code-style.md)

统计图转 `publication-figures`；其通用绘图实现说明见 [references/visualization.md](references/visualization.md)，但正式投稿格式以目标期刊当前官方要求为准。

## 2. 实现与运行

- 沿用现有包、对象命名和脚本结构；只抽取确有重复或高风险的逻辑，不为短任务过度封装。
- 原始数据只读，处理后数据写入项目规定的结果目录。
- 只有随机抽样、模拟、重采样、数据拆分或随机算法固定并记录种子。
- 普通 R 包缺失时按上游依赖政策在项目隔离环境补齐；失败不得静默换包、换方法或改用 Python。
- 多行代码写入 `.R` 文件。局部任务直接运行目标脚本；项目执行和正式发布通过 `run_pipeline.R` 从项目根启动新的 `Rscript --vanilla` 进程，并按已确认顺序运行全部相关脚本。
- 核对完整输出、样本量链、缺失、估计范围、区间、收敛、适用的模型假设和预期文件；warning、error、failed、nan 不得略过。

发现方向反转、无穷估计、异常缺失或样本量跳变时回到最早来源。可能改变口径或结论时停下报告，不通过删记录或改模型掩盖。

## 3. 结果及其使用文件

项目执行和正式发布的关键结果使用 [scripts/emit_summary.R](scripts/emit_summary.R) 写入 `results/results.yaml`。调用 `add_result()` 时必须填写实际生成结果的脚本、脚本中提取结果的对象、输入文件或其哈希值、分析集、运行编号，以及实际使用该结果的文件；禁止直接修改 YAML。文件结构和旧项目读取方式见 [结果数据文件](../biostat-principles/references/result-summary-schema.md)。

表格、图件、论文、报告和 PPT 按每项结果的固定名称从 `results/results.yaml` 取数。结果改变时应重新运行实际生成结果的脚本，并同步更新所有使用该结果的文件。方法选择或方案偏离写入 `DECISIONS.md`；总运行脚本自动记录实际命令、状态、输入输出文件哈希值和环境信息。只有需要后续补充材料、外部资源或由用户决定的事项才写入 `BACKLOG.md`。

试新方法按上游 E0/E1/E2 分级隔离；未达到预设条件或未经必要确认的方案不得覆盖主流程。

## 4. 完成条件

- 原始数据未改，声明脚本已实跑且状态成功。
- 输入行数、分析集分母、缺失与排除链可核对。
- 估计、区间、诊断和不确定性与研究目标匹配；异常已修复或明确解释。
- 项目执行和正式发布时，`results/results.yaml`、自动运行记录、方法决定和实际使用结果的文件保持一致。
- 局部任务只交付已经确认的产物和必要的复现说明，不补建范围外记录。
