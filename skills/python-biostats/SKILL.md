---
name: python-biostats
description: Python 流行病学与生物统计分析的可选执行层，仅用于用户明确要求 Python，或既有项目已经以 Python 为主流程时的数据清洗、描述统计、回归、生存分析、预测验证、统计表图、代码调试和结果复现。开工先遵循 biostat-principles；统计图配合 publication-figures，客户外发再用 consulting-delivery。未指定语言的普通统计分析、R 环境或依赖缺失、研究设计定稿、论文写作或仅操作 xlsx 文件不触发。
---

# Python 生物统计执行

先按全局 `CLAUDE.md` 判定 Q/L/P/R，并遵循 `biostat-principles`。仅在用户明确选择 Python 或既有项目以 Python 为主流程时执行；Python 运行时缺失时先询问是否安装，用户不安装则评估现有 R 环境中的经核验等价实现。不存在等价实现时说明差异并等待选择，不静默切换，也不重写可工作的 R 主流程。

## 1. 输入与方法

1. 读取本轮必要输入；项目执行或正式发布时，再读取项目规则、PROTOCOL、SAP、配置、方法决定与尚未解决且需要后续处理的事项。
2. 确认分析集、暴露或干预、终点、比较、时间零点、协变量和主要方法。多个合理口径会改变答案时先确认。
3. 从最早输入核对字段、类型、键、重复、缺失、范围和逐步样本量。
4. 方法匹配 estimand、研究设计、结局类型、时间结构和抽样设计，不按库的便利性替代研究问题。

可沿用项目已有的 pandas、polars、scipy、statsmodels、scikit-learn、lifelines 或 scikit-survival；这些是可能实现，不是强制依赖。统计图转 `publication-figures`。

## 2. 实现与运行

- 沿用项目风格，只封装重复或高风险逻辑；原始数据只读。
- 只有随机抽样、模拟、重采样、数据拆分或随机算法固定并记录种子。
- 普通 Python 包缺失时按 `biostat-principles` 的依赖政策在项目隔离环境补齐；失败不得静默换包、换方法或换语言。
- 多行分析写入 `.py`。局部任务运行目标脚本；项目执行和正式发布通过 `run_pipeline.py` 调用项目现有且版本兼容的 Python，启动独立进程并按已确认顺序运行全部相关脚本。
- 非机械修改 `.py` 后，先用项目现有 Python 执行 `python -m py_compile <受影响脚本>`，通过后再运行受影响的最小入口或总运行脚本。编译通过只是一道即时门禁，不能替代实跑和科学结果检查。
- 核对完整 stdout/stderr、样本量链、缺失、估计范围、区间、收敛、适用的模型假设和预期文件；warning、traceback、failed、nan 不得略过。

异常可能改变口径或结论时回到最早来源并停下报告，不通过删记录、改模型或捕获异常掩盖。

## 3. 结果与完成

项目执行和正式发布的关键结果使用 [scripts/emit_summary.py](scripts/emit_summary.py) 写入 `results/results.yaml`。每项必须填写实际生成结果的脚本、脚本中提取结果的对象、输入文件或其哈希值、分析集、运行编号，以及实际使用该结果的文件；禁止直接修改 YAML。文件结构和旧项目读取方式见 [结果数据文件](../biostat-principles/references/result-summary-schema.md)。

方法选择或方案偏离写入 `DECISIONS.md`；总运行脚本自动记录实际命令、状态、输入输出文件哈希值和环境信息。只有需要后续补充材料、外部资源或由用户决定的事项才写入 `BACKLOG.md`。试新方法按 `biostat-principles` 的 E0/E1/E2 规则隔离。

完成时确认原始数据未改、相关脚本实际运行、样本与诊断已核对、异常已处理，并且项目执行和正式发布涉及的 `results/results.yaml`、自动运行记录和实际使用结果的文件一致。局部任务只交付用户指定的产物和必要的复现说明。
