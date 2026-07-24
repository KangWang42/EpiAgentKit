---
name: r-biostats
description: |
  R 流行病学与生物统计执行层，用于 R 数据清洗、描述统计、回归、生存、中介、Meta 分析、统计表图和代码调试。开工先对齐 biostat-principles；统计图配合 publication-figures，客户外发再用 consulting-delivery。不用于 Python 分析、研究设计定稿或论文写作。
---

# R 流行病学与生物统计执行 skill

> **上游原则**：本 skill 是执行层，开工先对齐 `biostat-principles` 六原则；规则冲突按全局 `CLAUDE.md` 的唯一优先级处理。
> **核心工作模式**：`PLAN → CODE → RUN → VERIFY → DOC`。阶段可以在简单任务中合并，但运行和验证不能省略。
> **任务形态**：简单作业、单次处理或少量输出走 `biostat-principles` §8 轻量任务通道；不得自动创建正式项目骨架或账本。已在正式项目内时，目录、连续编号、表图、registry、归档与 BACKLOG 细则读取 `../project-init/references/project-hygiene.md`。

---

## 一、五阶状态机（强制）

### 状态图

```
[用户请求]
    ↓
[PLAN]   锁定口径、输入输出、分析方法、验证标准     ←─┐ 不通过回到此处
    ↓ 关键歧义确认或口径明确                          │
[CODE]   单一职责、最小实现；正式项目再编号             │
    ↓                                                  │
[RUN]    Rscript 实际执行，不跳过                      │
    ↓ 报错 → 修 → 重跑（最多 2 次）──────────────────┘
    ↓ 仍失败 → 停下来汇报
[VERIFY] 检查输出文件、数字范围、与预期一致
    ↓ 不通过回到 CODE                                  
    ↓                                                  
[DOC]    正式项目更新账本；轻量任务简述输入、输出与验证
    ↓
[完成]
```

### 每一阶的退出条件

| 阶段 | 不允许进入下一阶的情况 |
|------|---------------------|
| PLAN | 口径有歧义、输入路径不明、没写验证标准 |
| CODE | 实现与任务无关、用了绝对路径或留下临时调试；正式项目脚本未按项目规则编号 |
| RUN | 没真跑过、有 warning 没处理、报错被 `tryCatch` 吞掉 |
| VERIFY | 样本量与预期不符、数字明显异常（NA 爆表、HR=Inf）、图表留白/乱码/空白页 |
| DOC | 正式项目的 session_log 未更新，或结果变了但 results.yaml（→派生 md）没改；轻量任务未说明输入、输出与验证 |

### 失败回退规则

- 同一根因连续两轮没有新增证据 → 停止重复尝试并汇报；出现新的可验证假设时可继续定位
- VERIFY 不过 → 必须回到 CODE，不能"大致对就行"
- 用户打断说"不对" → 立即回到 PLAN，不要在原路径上继续改

---

## 二、PLAN 阶段模板

复杂分析或需要用户确认时展示此合同；简单且口径明确的任务可在工作计划中内部维护，不强制固定回复样板。

正式项目开工前先读项目 `PROTOCOL.md`、`SAP.md`、`CLAUDE.md` 与 `DECISIONS.md`。方案或 SAP 仍为草案、主要终点/分析人群/主模型未确认，或实际做法偏离 SAP 时，先向用户确认并记录偏离；不得先看结果再把主要分析写成“预设”。轻量任务只读取实际存在且与请求有关的说明文件，不补建缺失的项目文档。

```
【口径】
  - 研究对象：XX 人群 (N=?)
  - 暴露/干预：XX
  - 结局/终点：XX
  - 协变量：X1, X2, ...
  - 主分析方法：XX 模型
  - 敏感性分析：XX

【输入】
  - 数据：01_data/rawdata/xxx.csv（或上游脚本产物 06_results/xxx.xlsx）
  - 依赖：02_code/NN_前置脚本.R

【输出】
  - 脚本：02_code/NN_本次任务.R
  - 表：03_tables/TableN_xxx.xlsx（sheet: ...；路径经 config.R 的 table_path() 取）
  - 图：04_figures/FigN_xxx.pdf + .png（路径经 fig_path() 取）
  - 中间：06_results/xxx.<既有合同格式>（按消费者选择 csv/tsv/parquet/xlsx；模型等对象可用 .rds）

【验证】
  - 样本量 = 基线表 N
  - 主效应值在 [合理范围]
  - PH 假设 / 线性假设 / 收敛性如何判定
```

会改变研究答案的口径项填不出时先问用户；不影响答案的路径或展示细节可从工作区核验后继续。

---

## 三、硬禁止 / 必须（CRITICAL）

### 禁止

| 违禁 | 替代 |
|------|------|
| 在最终脚本残留临时 `print()` / `cat()` 调试 | 删除调试输出；长期运行信息使用有语义的 `message()` 或日志 |
| `for (i in 1:n)` 导致空序列或索引错误 | 用 `seq_along()`；按可读性和返回类型选择循环、`apply` 或 `purrr`，不为风格强制改写 |
| 绝对路径 `"C:/Users/..."` | 相对路径 `"01_data/rawdata/xx.csv"` |
| `setwd()` | 以项目根为工作目录（Rproj 或 here） |
| 修改 `01_data/rawdata/` | 只读，派生写到 `06_results/` |
| `library(plyr)` + `dplyr` 混用 | 只用 `dplyr` |
| 同一段代码无理由混用多套索引语义 | 跟随项目既有风格并保持对象类型清楚 |
| 随意改变既有交换格式 | 跟随项目合同；面向人工阅读的正式表优先 xlsx，机器交换可使用 csv/tsv/parquet，模型等对象用 rds |
| 脚本里写死 `Table6` / `Fig3` 路径 | 经 `config.R` 的 `table_path()` / `fig_path()` 取（registry，见 project-init `references/registry.md`） |
| 未核验可读性和含义的装饰性配色 | 按 `publication-figures`、目标期刊、色觉可达性和项目语义选择调色板 |
| 代码写完不跑就交 | **必须 `Rscript` 实际执行** |
| `Rscript -e "多行脚本"` 跑分析 | 本环境多行 `-e` 会 **segfault**；多行一律写成 `.R` 文件再 `Rscript 文件.R` 跑（`-e` 只用于一行小命令） |
| 结果变了不更新 `results.yaml`（→派生 md） | 强制同步：`add_result` + `render_summary_md` |

### 必须

- **语言边界**：用户、现有主流程或项目规则指定 R 时使用 `.R`；指定 Python 时转 `python-biostats`。不为统一风格跨语言重写。
- **代码风格遵 [references/code-style.md](references/code-style.md)**（软约束，服从工作流/红线）：依赖直接逐行 `library()`；顺序式 R 分析不按 Python 习惯把每一步封成函数；管道尽量连续，中间对象少且语义清楚；批处理先定义控制向量，再按返回值或副作用选择 `map*()` / `walk*()`；RUN / VERIFY 必做，但不把硬编码核验块和调试展示默认塞进交付脚本。
- R 脚本顶部：声明实际依赖并说明目的、输入和输出；仅在随机抽样、模拟、重采样、拆分或随机算法中设置并记录 seed
- 命名：文件 `NN_描述.R`、变量 `snake_case`；函数只在复用、参数化批处理、稳定工具或复杂算法边界确有必要时抽取，并使用 `snake_case`
- 中文注释关键步骤（为什么这样切分、为什么选这个模型）
- 双格式导出：`ggsave()` 同时存 PDF (`cairo_pdf`) + PNG (`ragg::agg_png`, 300dpi)
- 编码 UTF-8，不要 GBK
- **结果数字写入单源**：算完每个指标即 `add_result()` 写入 `07_paper/results.yaml`（`scripts/emit_summary.R`，口径单源、自动渲染），再 `render_summary_md()` 生成 `0_result_summaries.md`。**NEVER** 手敲 rendered、**NEVER** 手改派生的 md。详见 [结果单源 schema](../biostat-principles/references/result-summary-schema.md)。

---

## 四、技术栈

按任务实际使用选择依赖，每个包直接写一行 `library()`；不要把下列清单全部复制进脚本，也不要用 `suppressPackageStartupMessages()` 包裹。

```r
# 核心数据处理与 I/O
library(tidyverse)
library(here)
library(readxl)
library(writexl)

# 按任务选择表格、模型或绘图包
library(gtsummary)
library(broom)
library(survival)
# 按图形合同选择调色板包
```

**导入顺序**：先 `tidyverse`，再领域包。避免混用 `plyr` / `reshape` 与 `dplyr`。

---

## 五、按分析类型加载参考

根据任务类型，读取对应 reference 文件获得具体模板：

| 任务 | 参考文件 | 关键包 |
|------|---------|-------|
| 数据清洗 / 缺失处理 | 用本文件 §八.2 模板 | tidyverse, naniar, mice |
| 基线表 / 描述统计 | [references/descriptive.md](references/descriptive.md) | gtsummary, compareGroups |
| 回归（线性/逻辑/Poisson/负二项） | [references/regression.md](references/regression.md) | stats, MASS, broom |
| 生存分析（KM/Cox/时变/竞争风险） | [references/survival.md](references/survival.md) | survival, survminer, cmprsk |
| 预后/预测模型 · 分期系统（建模/切点/训练验证/判别/校准/DCA/列线图/与现有系统比较） | [references/prognostic-models.md](references/prognostic-models.md) | rms, survival, riskRegression, timeROC |
| 中介/调节效应 | [references/mediation.md](references/mediation.md) | mediation, lavaan |
| Meta 分析 / 森林图 | [references/meta.md](references/meta.md) | meta, metafor |
| 可视化规范 | [references/visualization.md](references/visualization.md) | ggplot2, ggsci, patchwork |
| 结果汇总单源（results.yaml + 派生 md） | [结果单源 schema](../biostat-principles/references/result-summary-schema.md) | yaml（`scripts/emit_summary.R`） |

> references/ 目录下文件按需补充；如果某类文件暂缺，使用本文件下方通用模板。

---

## 六、项目结构约定

```
project/
├── CLAUDE.md / PROTOCOL.md / SAP.md / SESSION_LOG.md / DECISIONS.md / BACKLOG.md
├── 01_data/rawdata/      # 只读
├── 02_code/              # config.R / conventions.R / vendored/ + 编号脚本
├── 03_tables/TableN.xlsx # 最终表
├── 04_figures/FigN.pdf/png
├── 05_reports/结果-M-D-主题/ # 咨询/汇报结果包
├── 06_results/           # 中间对象：表格 xlsx；非表格对象 rds；按内容命名不编号
├── 07_paper/             # 论文 + results.yaml(数字单源) + 0_result_summaries.md(由其派生)
└── 09_backup/            # 旧版 / 探索实验；EXPERIMENTS.md 索引全部尝试
```

脚本之间传值 → **必须落盘到 `06_results/`**，不要靠 R 环境变量（复现会断）。

---

## 七、脚本头部模板（每个 R 脚本顶部必写）

```r
# ============================================================
# 脚本：02_code/03_cox_main.R
# 目的：主分析—Cox 比例风险模型（暴露 X 对 OS 的影响）
# 输入：06_results/cohort_clean.xlsx
# 输出：03_tables/Table3_cox.xlsx（路径经 table_path("cox") 取）
#       04_figures/Fig2_forest.pdf/.png（路径经 fig_path("forest", ext) 取）
#       06_results/cox_fit.rds（模型对象，非表格才可 rds）
# 依赖脚本：02_code/02_data_clean.R
# 日期：2026-MM-DD
# ============================================================

library(tidyverse)
library(survival)
library(survminer)
library(broom)
library(writexl)

# 仅当本脚本含随机过程时设置并记录 seed
here::i_am("02_code/03_cox_main.R")  # 锚定工作目录
source("02_code/config.R", encoding = "UTF-8")
```

---

## 八、标准工作流（PLAN → DOC 对应实现）

### 1. 探查（PLAN 阶段的前置）

```r
dat <- readr::read_csv("01_data/rawdata/cohort.csv")

dat |> glimpse()
dat |> summarise(across(everything(), ~ sum(is.na(.))))  # 缺失
dat |> select(where(is.numeric)) |> summary()
```

**输出到控制台检查即可，不落盘**。这一步看完再填 PLAN 模板。

### 2. 清洗（CODE）

```r
cohort <- dat |>
  filter(!is.na(exposure), age >= 18) |>
  mutate(
    sex = factor(sex, levels = c(1, 2), labels = c("Male", "Female")),
    bmi_cat = cut(bmi, c(0, 18.5, 24, 28, Inf),
                  labels = c("Underweight", "Normal", "Overweight", "Obese"))
  )

writexl::write_xlsx(cohort, "06_results/cohort_clean.xlsx")  # 人工复核示例；机器交换格式按项目合同选择
```

### 3. 基线表（CODE）

```r
# gtsummary 风格
table1 <- cohort |>
  gtsummary::tbl_summary(
    by = exposure,
    missing = "no",
    statistic = list(all_continuous() ~ "{mean} ({sd})",
                     all_categorical() ~ "{n} ({p}%)")
  ) |>
  gtsummary::add_p() |>
  gtsummary::add_overall()

# 主表一律 xlsx（路径经 table_path() 取）；docx 排版交给论文拼装阶段
table1 |>
  gtsummary::as_tibble() |>
  writexl::write_xlsx(table_path("baseline"))
```

### 4. 主分析（CODE + RUN）

按 `references/[对应分析].md` 里的模板落地。跑完后必须执行 VERIFY：核对分析样本量、系数缺失、P 值范围、模型假设与收敛状态，并扫描完整运行输出。当前批次的固定样本量等核验放在 RUN / VERIFY 过程或审计记录中，不默认把一组硬编码 `stopifnot()` 插进交付脚本；只有需要长期保护的研究设计不变量才保留为代码约束。

### 5. 可视化（CODE）

**任何出图先过 `publication-figures` skill**（mm 物理尺寸、字体嵌入、选型、自检清单都在那边）；本节只给落盘骨架：

```r
p <- ggplot(cohort, aes(x, y, color = group)) +
  geom_point() +
  scale_color_viridis_d(end = 0.85) +
  theme_minimal(base_size = 12)

ggsave(fig_path("xxx", "pdf"), p, width = 180, height = 120, units = "mm", device = cairo_pdf)
ggsave(fig_path("xxx", "png"), p, width = 180, height = 120, units = "mm",
       dpi = 300, device = ragg::agg_png)
```

### 6. DOC 阶段（必做）

**A. 写入结果单源 `07_paper/results.yaml`**（结果变了就写；**NEVER 手写 0_result_summaries.md**）：

```r
source("02_code/vendored/emit_summary.R", encoding = "UTF-8")
yp <- "07_paper/results.yaml"
add_result(yp, "exposure_HR", label = "暴露 X 对 OS 的 HR",
           est = 1.45, ci_low = 1.12, ci_high = 1.87, p = 0.004,
           section = "主分析", source = "02_code/03_cox_main.R",
           table = table_path("cox_main"),
           interp = "暴露 X 与 OS 风险升高相关，调整年龄/性别/BMI/吸烟后仍稳健。")
render_summary_md(yp, "07_paper/0_result_summaries.md")  # 派生人读版
```

数字渲染、`val()` 取数、解读待复核机制详见 [结果单源 schema](../biostat-principles/references/result-summary-schema.md)。下游论文/报告/PPT 一律 `val()` 取，禁手敲。

**B. 追加 `SESSION_LOG.md`**：

```markdown
| 2026-MM-DD HH:MM | 主分析 Cox | 02_code/03_cox_main.R | HR=1.45 (1.12-1.87) |
```

**C. 如果方法变动了，更新 `DECISIONS.md`**：

```markdown
## 2026-MM-DD · 主分析改用 Cox 而非逻辑回归

**选择**: Cox 比例风险模型
**原因**: 随访时间差异大（中位 3.2 年，IQR 1.5–5.8），逻辑回归会忽略时间维度
**放弃方案**: 逻辑回归（作为敏感性分析保留）
```

**D. 分析中冒出"还能补"的想法 → 追加 `BACKLOG.md`**：
还能加哪个敏感性/亚组分析、缺哪项协变量数据、某方法能强化但本轮没做、下一步设想——
当轮就写进项目根 `BACKLOG.md` 主表（格式见 project-init `references/project-hygiene.md` §6），
不靠记忆、不只在回复里口头提。

---

## 九、R 代码风格（PREFERENCE）

风格细则与好/差对照见 [references/code-style.md](references/code-style.md)（软约束，服从工作流/红线）。一句话：
直接逐行 `library()`；按 R 的顺序式分析习惯分节，不把每一步封成函数；一条变换尽量用管道连到底；中间对象少而语义清楚；先定义控制向量，再用 `map2()` / `walk()` / `walk2()` 等完成批处理；核验过程与最终脚本分离；注释只解释口径与理由，不翻译代码。

---

## 十、导出规范（CRITICAL）

### 表格

```r
# 单 sheet 简表（路径一律经 registry helper 取，不写死编号）
writexl::write_xlsx(tbl, table_path("xxx"))

# 多 sheet（同一主题）
writexl::write_xlsx(
  list(Overall = tbl_all, BySex = tbl_sex, Sensitivity = tbl_sens),
  table_path("regression")
)
```

**一个 xlsx = 一个分析主题**，不要把基线 + 回归 + 生存全塞一本。

### 图件

```r
# 出图用 publication-figures 的 fig_setup.R（theme_pub + save_fig 双存，勿在此重定义）
source("02_code/vendored/fig_setup.R", encoding = "UTF-8")
save_fig(p_forest, "forest", type = "forest")   # type 自带各图型推荐尺寸；详见 publication-figures
```

---

## 十一、常见错误排查（FAQ）

| 症状 | 最可能原因 | 处置 |
|------|----------|------|
| 中文乱码 PDF | 字体未嵌入 | 用 `cairo_pdf` 而不是默认 `pdf()` |
| 中文乱码 PNG | 用了默认 png 设备 | 用 `ragg::agg_png` |
| `coxph` 收敛警告 | 分类变量某层样本为 0 / 完全分离 | 合并稀有类或用 Firth 校正 |
| `gtsummary` 输出慢 | 变量类型没声明 | 预先 `factor()` / `as.numeric()` |
| 含随机过程的结果跨电脑不一致 | seed、拆分或依赖版本未锁定 | 固定随机过程并记录 seed、拆分标识与 `sessionInfo()` |
| `readr::read_csv` 列类型错 | 自动猜测失败 | 显式 `col_types = cols(...)` |
| Meta 分析异质性高 | 亚组混杂或量纲不一 | 亚组分析 + 检查效应指标 |
| `Rscript -e` 跑多行脚本 segfault / 直接崩 | 本环境对 `-e` 传多行 R 不稳（非脚本本身问题） | 写成 `.R` 文件用 `Rscript 文件.R` 跑；`-e` 只留一行小命令 |

**遇到新问题**：先读 `?函数名`、warning 全文和最小复现，再检查数据与包文档；代码问题自行定位并修复。依赖或运行环境缺失时说明检测结果、影响和用户下一步准备方式，但不代为安装。只有问题涉及分组、终点、纳排、主方法口径或缺失外部输入时才问用户，不用询问代替排错。

---

## 十二、咨询任务特别加成

如果本任务是给客户的咨询交付（不是自己的研究），**额外执行 `consulting-delivery` skill**，它会要求：

- 整包放入 `05_reports/结果-M-D-主题/`
- 生成 `run_all.R` 一键复现
- 写 `00_客户说明.md`（非技术视角）
- 写 `01_方法与结果.docx`（可直接发给客户）
- 发给客户前跑 `academic-humanizer`，核对不可变事实清单、论断强度与学术语体

---

## 十三、完成前终检清单

宣告完成前，逐项对照：

- [ ] PLAN 阶段的 4 块（口径/输入/输出/验证）都明确写出
- [ ] R 脚本编号命名且放在 `02_code/`（或结果包 `code/`）
- [ ] 脚本实际跑过（`Rscript 文件.R` 输出无 error，warning 已理解；**未用 `Rscript -e` 传多行**）
- [ ] 输出表格在 `03_tables/`，图在 `04_figures/`，中间在 `06_results/`
- [ ] 中间格式符合项目合同和消费者需求；正式人工表可打开，机器交换格式保留类型与精度，模型对象有明确来源
- [ ] 表格同主题合并到一个 xlsx 的多 sheet
- [ ] 图件格式、字体、尺寸和配色通过 `publication-figures` 验收
- [ ] `SESSION_LOG.md` 已追加本次操作
- [ ] 若结果变化 → `add_result()` 写 `07_paper/results.yaml` + `render_summary_md()` 派生 md（未手写 md、未手敲数字）
- [ ] 若方法变化 → `DECISIONS.md` 已同步
- [ ] 若冒出"还能补"的想法（待做分析/缺数据/下一步）→ `BACKLOG.md` 已追加
- [ ] 根目录无临时文件残留，旧版已入 `09_backup/`
- [ ] 若是咨询任务 → `consulting-delivery` 终检也通过
