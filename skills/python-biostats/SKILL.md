---
name: python-biostats
description: Python 流行病学与生物统计分析执行层，用于 Python 数据清洗、描述统计、回归、生存分析、预测验证、统计表图、代码调试和结果复现。开工先对齐 biostat-principles；统计图配合 publication-figures，客户外发再用 consulting-delivery。不用于 R 分析、研究设计定稿、论文写作或仅操作 xlsx 文件。
---

# Python 流行病学与生物统计执行

把已确认的研究问题和分析计划转成可运行、可核验、可追溯的 Python 分析。服从现有项目风格，不为使用 Python 而重写可工作的 R 主流程。

## 1. 建立执行合同

1. 先对齐 `biostat-principles`，判定轻量任务或正式项目。
2. 正式项目读取项目 `CLAUDE.md`、`PROTOCOL.md`、`SAP.md`、`DECISIONS.md`、配置与待办；轻量任务只读必要输入。
3. 明确研究对象、暴露或干预、结局、分析人群、主方法、输入、输出和验证标准。关键口径并存时先问用户。
4. 只读检查 Python 与所需包；复用已有兼容环境。依赖缺失时报告包名、影响和用户准备方式，不安装、升级、降级或创建环境。

## 2. 实现与运行

1. 先检查最早输入的字段、类型、重复、缺失、范围和样本损失，再写清洗或模型代码。
2. 选择与 estimand、结局类型、时间结构和抽样设计匹配的方法，不按库的便利性替代研究设计。
3. 保留现有项目编码风格；用清晰的函数边界封装重复或易错逻辑，不强制面向对象或链式写法。
4. 只有随机抽样、模拟、重采样、拆分或随机算法需要固定并记录随机种子。
5. 多行分析写入 `.py` 文件，用 `python path/to/script.py` 实际运行。不得只检查语法或退出码。
6. 扫描完整输出中的 error、warning、traceback、failed、nan；核对样本量、缺失、估计范围、置信区间、收敛、模型假设和输出文件。
7. 发现样本量跳变、方向反转、无穷估计、异常缺失或口径冲突时回到最早链路定位；可能改变结果或结论时停在安全点报告。

## 3. 项目输出与结果单源

- 正式项目使用相对路径和项目已有 registry；表格、图件和中间对象遵守项目规则。轻量任务输出集中、命名清楚，不补建正式账本。
- 统计图调用 `publication-figures`，根据实际期刊、估计目标和可读性选择图型与格式。
- 正式项目把每项已验证结果写入 `07_paper/results.yaml`，再派生 `0_result_summaries.md`；下游按稳定键取数，不手敲。
- 使用 [scripts/emit_summary.py](scripts/emit_summary.py) 写入、渲染和读取结果。语言中性 schema 见 `../biostat-principles/references/result-summary-schema.md`。
- 方法变化写 `DECISIONS.md`，操作写 `SESSION_LOG.md`，新缺口写 `BACKLOG.md`。

## 4. 方法与工具选择

按现有环境与任务选择库，不把以下示例视为强制依赖：

| 任务 | 常见实现 | 最低核验 |
| --- | --- | --- |
| 数据与表格 | pandas、polars、pyarrow | 类型、键、重复、缺失、行数链 |
| 描述与检验 | scipy、statsmodels | 分母、分布、效应量、区间与多重性 |
| 回归 | statsmodels、scikit-learn | 编码、参照组、收敛、诊断与区间 |
| 生存与竞争风险 | lifelines、scikit-survival 或项目既有库 | 时间零点、删失、风险集、假设与事件数 |
| 预测验证 | scikit-learn、项目既有库 | 数据泄漏、切分单位、校准、判别与不确定性 |
| 表图 | pandas/openpyxl、matplotlib/seaborn | 数字单源、最终尺寸、字体与输出可打开 |

## 5. 完成条件

- 脚本在已有环境中从声明输入实际运行到声明输出。
- 原始输入未改，样本损失链和分析样本量已核对。
- warning、nan、收敛、模型假设和异常估计已逐项解释或修复。
- 结果、表图、解释和方法方向一致；观察性研究未使用超出证据强度的因果措辞。
- 正式项目的结果单源、方法决策、日志和待办已同步；轻量任务报告最小复现方式。
