---
name: r-biostats
description: |
  R 语言流行病学与生物统计分析执行层。专为医学研究生、临床数据分析、真实世界数据(RWD)研究、统计咨询设计。
  触发场景：(1) 用户进行任何 R 统计分析；(2) 需要描述统计、回归、生存分析、中介效应、Meta 分析；(3) 需要数据清洗或可视化；(4) R 代码错误调试；(5) 生成出版级或咨询级图表表格。
  上游依赖：开工前先对齐 biostat-principles；交付给客户前先过 consulting-delivery。
---

# R 流行病学与生物统计执行 skill

> **上游原则**：本 skill 是执行层，开工先对齐 `biostat-principles` 六原则；规则冲突按全局 `CLAUDE.md` 的唯一优先级处理。
> **核心工作模式**：`PLAN → CODE → RUN → VERIFY → DOC` 五阶状态机，每阶必须有显式验证后才能进入下一阶。
> **任务形态**：简单作业、单次处理或少量输出走 `biostat-principles` §8 轻量任务通道；不得自动创建正式项目骨架或账本。已在正式项目内时，目录、连续编号、表图、registry、归档与 BACKLOG 细则读取 `../project-init/references/project-hygiene.md`。

---

## 一、五阶状态机（强制）

### 状态图

```
[用户请求]
    ↓
[PLAN]   列出口径、输入输出、分析方法、验证标准     ←─┐ 不通过回到此处
    ↓ 用户确认或 trivial 豁免                          │
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
| CODE | 线性分析被不必要地函数化、连续管道被无意义中间对象切碎，或用了绝对路径/print 调试；正式项目脚本未按项目规则编号 |
| RUN | 没真跑过、有 warning 没处理、报错被 `tryCatch` 吞掉 |
| VERIFY | 样本量与预期不符、数字明显异常（NA 爆表、HR=Inf）、图表留白/乱码/空白页 |
| DOC | 正式项目的 session_log 未更新，或结果变了但 results.yaml（→派生 md）没改；轻量任务未说明输入、输出与验证 |

### 失败回退规则

- RUN 报错连续 2 次修不好 → 停下来汇报用户，不要瞎试第 3 次
- VERIFY 不过 → 必须回到 CODE，不能"大致对就行"
- 用户打断说"不对" → 立即回到 PLAN，不要在原路径上继续改

---

## 二、PLAN 阶段模板

**每次分析开头必须输出此块**（trivial 任务可压缩为一行）：

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
  - 中间：06_results/xxx.xlsx（表格化；仅模型等非表格对象用 .rds）

【验证】
  - 样本量 = 基线表 N
  - 主效应值在 [合理范围]
  - PH 假设 / 线性假设 / 收敛性如何判定
```

**口径有 ≥1 项填不出 → 先问用户，不要开工。**

---

## 三、硬禁止 / 必须（CRITICAL）

### 禁止

| 违禁 | 替代 |
|------|------|
| `print()`, `cat()` 调试 | 直接返回对象，RStudio 里跑分块 |
| `for (i in 1:n)` 循环 | 先定义控制向量，再用 `map()` / `map2()` / `pmap()`（或对应的 `walk()` / `walk2()`）；确需 `for` 时用 `seq_along()` |
| 绝对路径 `"C:/Users/..."` | 相对路径 `"01_data/rawdata/xx.csv"` |
| `setwd()` | 以项目根为工作目录（Rproj 或 here） |
| 修改 `01_data/rawdata/` | 只读，派生写到 `06_results/` |
| `library(plyr)` + `dplyr` 混用 | 只用 `dplyr` |
| `df$col` + `df[,'col']` 混用 | 统一 tidyverse 管道 |
| 散落 `.tsv` 输出 | 表格化数据统一 `.xlsx` |
| 表格化中间数据存 `.rds` | 存 xlsx；`.rds`/`.RData` 仅限非表格对象（模型 / MCA / ggplot） |
| 脚本里写死 `Table6` / `Fig3` 路径 | 经 `config.R` 的 `table_path()` / `fig_path()` 取（registry，见 project-init `references/registry.md`） |
| `scale_fill_manual(values = ...)` 自选配色 | `ggsci::scale_fill_lancet()` / `pal_jama()` |
| 代码写完不跑就交 | **必须 `Rscript` 实际执行** |
| `Rscript -e "多行脚本"` 跑分析 | 本环境多行 `-e` 会 **segfault**；多行一律写成 `.R` 文件再 `Rscript 文件.R` 跑（`-e` 只用于一行小命令） |
| 结果变了不更新 `results.yaml`（→派生 md） | 强制同步：`add_result` + `render_summary_md` |

### 必须

- **默认语言 R**：`02_code/` 分析脚本默认 `.R`，仅特殊要求项目用 Python（见 project-init `references/project-hygiene.md`）。
- **代码风格遵 [references/code-style.md](references/code-style.md)**（软约束，服从工作流/红线）：依赖直接逐行 `library()`；顺序式 R 分析不按 Python 习惯把每一步封成函数；管道尽量连续，中间对象少且语义清楚；批处理先定义控制向量，再按返回值或副作用选择 `map*()` / `walk*()`；RUN / VERIFY 必做，但不把硬编码核验块和调试展示默认塞进交付脚本。
- R 脚本顶部：`library()` 全部依赖 + `set.seed(123)` + 注释说明本脚本目的/输入/输出
- 命名：文件 `NN_描述.R`、变量 `snake_case`；函数只在复用、参数化批处理、稳定工具或复杂算法边界确有必要时抽取，并使用 `snake_case`
- 中文注释关键步骤（为什么这样切分、为什么选这个模型）
- 双格式导出：`ggsave()` 同时存 PDF (`cairo_pdf`) + PNG (`ragg::agg_png`, 300dpi)
- 编码 UTF-8，不要 GBK
- **结果数字写入单源**：算完每个指标即 `add_result()` 写入 `07_paper/results.yaml`（`scripts/emit_summary.R`，口径单源、自动渲染），再 `render_summary_md()` 生成 `0_result_summaries.md`。**NEVER** 手敲 rendered、**NEVER** 手改派生的 md。详见 [references/result-summary-schema.md](references/result-summary-schema.md)。

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
library(ggsci)
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
| 结果汇总单源（results.yaml + 派生 md） | [references/result-summary-schema.md](references/result-summary-schema.md) | yaml（`scripts/emit_summary.R`） |

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
library(ggsci)

set.seed(123)
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

writexl::write_xlsx(cohort, "06_results/cohort_clean.xlsx")  # 表格化数据存 xlsx，不存 rds
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
  ggsci::scale_color_lancet() +
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

数字渲染、`val()` 取数、解读待复核机制详见 [references/result-summary-schema.md](references/result-summary-schema.md)。下游论文/报告/PPT 一律 `val()` 取，禁手敲。

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
| 跨电脑结果不一致 | 没 `set.seed()` | 加 seed + 记录 `sessionInfo()` |
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
- [ ] **`06_results/` 中表格化数据是 `.xlsx`**；`.rds`/`.RData` 仅限非表格对象（模型 / ggplot / MCA），逐个能说出为何不能表格化
- [ ] 表格同主题合并到一个 xlsx 的多 sheet
- [ ] 图件 PDF + PNG 双格式、中文不乱码、ggsci 配色
- [ ] `SESSION_LOG.md` 已追加本次操作
- [ ] 若结果变化 → `add_result()` 写 `07_paper/results.yaml` + `render_summary_md()` 派生 md（未手写 md、未手敲数字）
- [ ] 若方法变化 → `DECISIONS.md` 已同步
- [ ] 若冒出"还能补"的想法（待做分析/缺数据/下一步）→ `BACKLOG.md` 已追加
- [ ] 根目录无临时文件残留，旧版已入 `09_backup/`
- [ ] 若是咨询任务 → `consulting-delivery` 终检也通过
