---
name: project-init
description: |
  标准化卫生统计研究项目初始化 skill。一键创建七层目录结构、模板文件、Git 配置；支持"研究模式"和"咨询模式"双预设。
  触发场景：(1) 用户说"创建项目"、"初始化"、"新建项目"；(2) 需要标准研究项目结构；(3) 开始新的数据分析任务；(4) 接了咨询任务需要快速起项目。
  上游依赖：biostat-principles（目录规约）；若研究类型=咨询，下游接 consulting-delivery。
---

# 项目初始化 skill

> **工作模式**：INQUIRE（问清信息）→ SCAFFOLD（建目录）→ POPULATE（填模板）→ VERIFY（自检）→ GUIDE（告诉用户下一步）。

---

## 一、开工前必问

**信息不全不开工**。逐项问清以下：

```
1. 项目名称（英文 snake_case，例如 cohort_smoking_chd）：
2. 研究类型：
   [1] 队列研究（cohort）
   [2] 病例对照（case-control）
   [3] 横断面（cross-sectional）
   [4] 临床试验 / 干预（RCT）
   [5] Meta 分析 / 系统综述
   [6] 真实世界研究（RWD）
   [7] 方法学研究
3. 模式：
   [A] 研究模式（自己做研究 / 投稿用）
   [B] 咨询模式（给客户做交付用，自动装配 consulting-delivery 骨架）
4. 存放根路径（默认当前工作目录）：
5. 是否启用 Git（默认 yes）：
```

**项目名违反 snake_case** → 自动建议规范名并请用户确认（不要硬改）。
**同名目录已存在** → 停下来问用户覆盖、改名、还是追加。

---

## 二、目录结构

### 研究模式（A）

```
{project}/
├── CLAUDE.md              # 继承 + 项目专属规则
├── README.md              # 项目说明
├── SESSION_LOG.md         # 操作日志
├── DECISIONS.md           # 方法决策
├── BACKLOG.md             # 待补清单（缺文献/数据/方法/规划，全程只增不删）
├── .gitignore             # 忽略数据和临时
├── .Rproj                 # RStudio 项目文件
├── 01_data/
│   ├── rawdata/           # 只读
│   └── README.md          # 数据字典
├── 02_code/
│   ├── config.R           # 口径常量 + 表图 registry（空清单起步，实现见 references/registry.md）
│   └── 01_data_cleaning.R # 清洗脚本模板
├── 03_tables/
├── 04_figures/
├── 05_reports/
├── 06_results/
├── 07_paper/
│   └── 0_result_summaries.md
└── 09_backup/
```

### 咨询模式（B）· 额外装配

咨询模式在研究模式基础上，额外：

- `05_reports/结果-{今日}-{主题占位}/` 预建一个空交付包（含 `run_all.R`、`00_客户说明.md`、`data/` `code/` `tables/` `figures/`）
- `CLAUDE.md` 追加"交付前必过 consulting-delivery 终检"
- `DECISIONS.md` 追加首条"咨询任务，客户口径见 `DECISIONS.md` 顶部"

---

## 三、执行脚本

用 `scripts/init_project.R` 一键创建。R 里运行：

```r
source("~/.claude/skills/project-init/scripts/init_project.R")
init_project(
  name = "cohort_smoking_chd",
  type = 1,           # 1=队列 2=病例对照 3=横断面 4=RCT 5=Meta 6=RWD 7=方法学
  mode = "research",  # "research" 或 "consulting"
  root = ".",
  git = TRUE
)
```

---

## 四、模板文件内容

### 4.1 `CLAUDE.md`（项目级，继承全局）

```markdown
# {项目名} · 项目级规则

本文件继承 `~/.claude/CLAUDE.md` 的全局 EpiClaude 规则。以下是本项目专属约束。

## 新会话必读（新 agent 开局第一步，按序读完再动手）

> 本文件每 session 必然注入；下面这份清单 = 不依赖记忆、不重读全项目即可进入状态的最短路径。

1. 本文件「口径锁定」节 —— **当前口径以此为准**（下游全部服从）
2. `07_paper/0_result_summaries.md` —— 最新结果数字（论文唯一数据源）
3. `DECISIONS.md` 末尾 2~3 条 —— 最近的方法变更与原因
4. `BACKLOG.md` 待办表 —— 全程累积的待补项（缺文献 / 数据 / 方法 / 下一步规划），挑「执行方=agent」的高优先级项作为下一步候选
5. `02_code/conventions.R` + `config.R` —— 口径常量真源（有序因子序 / 配色 / registry）
6. `SESSION_LOG.md` 末 10 行 —— 上次做到哪、卡在哪

**信任但验证**：涉及数字的任务，先快速核 `0_result_summaries` 关键数字 vs 最新输出文件 mtime / registry 是否对得上；对不上立即触发 `/epi-project-audit`，不盲信本文件可能已陈旧的内容。

## 当前状态（快照，非历史；每次会话收尾必更新，≤10 行）

> append-only 的 SESSION_LOG 读不出"现在在哪"，本节专门回答这点。改方法/出新结果/定稿版本后立即更新。

- 当前阶段：[如 主分析已定稿，正在写讨论]
- 最新定稿版本 / 回退点：[如 数据 v3 / commit abc1234]
- 进行中（半成品，勿当成品）：[如 敏感性分析 02_code/06 待跑]
- 已知坑 / 待办：[只放当下最紧要 1~2 条；完整累积清单在 `BACKLOG.md`]
- 下一步：[一句话]

## 项目基本信息

- 研究类型：{type_name}
- 研究问题：[一句话 PICOS]
- 数据来源：[数据集名 + 时间段]
- 主要终点：[具体定义]
- 分析计划：[主分析 + 敏感性]

## 口径锁定（严禁擅自变动）

- 纳入标准：
- 排除标准：
- 暴露变量：
- 结局变量：
- 随访时间：
- 协变量：

口径变动 → 先改本节 → 记录 `DECISIONS.md` → 重跑受影响的分析。

## 项目级覆盖规则

（若无，保留此节为空）

## 咨询模式专属（仅咨询模式保留）

- 交付前必过 `consulting-delivery` 的 FINAL 终检清单（§八）
- `05_reports/` 内结果包必须自包含，`run_all.R` 能在空 session 跑通
```

### 4.2 `SESSION_LOG.md`

```markdown
# Session Log

| 时间 | 操作 | 文件 | 结果 |
|------|------|------|------|
| {init_time} | 项目初始化 | 全部目录和模板 | 骨架就绪 |
```

### 4.3 `DECISIONS.md`

```markdown
# 方法决策记录

所有会影响最终结果的方法选择都必须写到这里。
格式：时间 + 选择 + 原因 + 放弃的替代方案。

---

## {init_date} · 项目启动

**决策**：项目类型 = {type_name}，主分析计划 = [待用户确认]
**原因**：[待用户填写]
**放弃方案**：[待用户填写]
```

### 4.3b `BACKLOG.md`（待补清单）

全项目周期累积的"待补/想法/下一步"单一入口。**只增不删**——发现即记，做完勾掉留痕。
关键不在建文件，而在 agent 任何阶段（清洗 / 分析 / 出图 / 写作 / 审查）一发现缺口就立即追加，
不靠记忆、不留到"以后"（全局 CLAUDE.md §2 已设硬红线）。

```markdown
# BACKLOG · 待补清单

全项目周期随时冒出来的缺口与待办都进这里：缺文献、缺数据、缺方法/分析、
写作待补、下一步规划。规划研究方案时先扫本文件，决定下一步让 agent 做
什么、自己去找哪些数据 / 做哪些决策。

维护规则：

- 任何时候（清洗 / 分析 / 出图 / 写作 / 审查）发现缺口或想法 → 立即追加一行到「待办」表顶部，不留到"以后"。
- 类别：文献 | 数据 | 方法 | 分析 | 写作 | 规划
- 执行方：agent（可直接做）| 我（需找数据 / 外部资源 / 做决策）
- 优先级：高 | 中 | 低
- 做完不删：勾掉移到「已完成」并注完成日期；彻底作废移「已放弃」并注原因。

## 待办（新发现加到本表顶部）

| 类别 | 待补内容 | 执行方 | 优先级 | 记录日期 |
|------|----------|--------|--------|----------|

## 已完成（留痕不删）

| 类别 | 待补内容 | 完成日期 |
|------|----------|----------|

## 已放弃

| 类别 | 待补内容 | 放弃原因 | 日期 |
|------|----------|----------|------|
```

### 4.4 `07_paper/0_result_summaries.md`

```markdown
# 结果汇总（论文唯一数据源）

本文件是项目的**最终结果**。所有图表、docx、论文正文的数字，都应从这里取。
一旦结果变化 → 第一时间同步更新这里 → 再更新下游图表和正文。

---

## 样本特征

N = [待填]

（基线表在 03_tables/Table1_baseline.xlsx）

## 主分析

[分析名称]
- 模型：
- 样本：
- 结果：
- 来源：`02_code/NN_xxx.R` → `03_tables/TableN_xxx.xlsx`

## 敏感性分析

## 亚组分析

## 结论（一句话）
```

### 4.5 `01_data/README.md`（数据字典模板）

```markdown
# 数据字典

## 数据来源

- 数据集名称：
- 提供方：
- 数据时间范围：
- 样本量（原始）：
- 获取日期：
- 伦理批件号（如适用）：

## 变量清单

| 变量名 | 类型 | 单位 | 编码 | 说明 | 缺失率 |
|--------|------|------|------|------|--------|
| id | chr | — | 匿名编码 | 唯一标识 | 0% |
| age | num | 年 | — | 基线年龄 | — |
| sex | int | — | 1=男 2=女 | — | — |
| ... | | | | | |

## 变更记录

（原始数据不修改。衍生变量在派生数据里记。）

| 时间 | 变更 | 原因 |
|------|------|------|
```

### 4.6 `02_code/01_data_cleaning.R`（清洗模板）

```r
# ============================================================
# 脚本：02_code/01_data_cleaning.R
# 目的：从 01_data/rawdata/ 读取原始数据，清洗为分析用数据集
# 输入：01_data/rawdata/xxx.csv
# 输出：06_results/cohort_clean.xlsx（表格化数据一律 xlsx；06_results 按内容命名不编号）
#       03_tables/Table0_flowchart.xlsx（样本量损失链）
# 依赖脚本：（无，本脚本是上游）
# ============================================================

library(tidyverse)
library(here)
library(writexl)

here::i_am("02_code/01_data_cleaning.R")
set.seed(123)

# 1. 读取 ----------------------------------------------------
raw <- readr::read_csv("01_data/rawdata/xxx.csv", show_col_types = FALSE)

# 2. 样本量损失链 --------------------------------------------
n_raw <- nrow(raw)

step1 <- raw |> filter(!is.na(exposure))
n_step1 <- nrow(step1)

step2 <- step1 |> filter(age >= 18)
n_step2 <- nrow(step2)

# ... 每一步记录样本量

# 3. 编码分类变量 --------------------------------------------
cohort <- step2 |>
  mutate(
    sex = factor(sex, levels = c(1, 2), labels = c("Male", "Female")),
    # bmi_cat = cut(bmi, c(0, 18.5, 24, 28, Inf),
    #               labels = c("Underweight", "Normal", "Overweight", "Obese"))
  )

# 4. 保存 ----------------------------------------------------
writexl::write_xlsx(cohort, "06_results/cohort_clean.xlsx")

flowchart <- tibble(
  step = c("原始", "排除暴露缺失", "排除 <18 岁"),
  n = c(n_raw, n_step1, n_step2),
  loss = c(0, n_raw - n_step1, n_step1 - n_step2)
)
writexl::write_xlsx(flowchart, "03_tables/Table0_flowchart.xlsx")

message("清洗完成。最终样本量: ", nrow(cohort))
```

### 4.7 `.gitignore`

```
# 数据（敏感）
01_data/rawdata/*
!01_data/rawdata/.gitkeep
!01_data/README.md

# 中间产物
06_results/*
!06_results/.gitkeep

# 系统
.Rproj.user/
.Rhistory
.RData
.DS_Store
Thumbs.db
~$*

# 编辑器
.vscode/
.idea/

# 临时
*.tmp
*.bak
```

### 4.8 `.Rproj`（最小模板）

```
Version: 1.0

RestoreWorkspace: No
SaveWorkspace: No
AlwaysSaveHistory: Default

EnableCodeIndexing: Yes
UseSpacesForTab: Yes
NumSpacesForTab: 2
Encoding: UTF-8

AutoAppendNewline: Yes
StripTrailingWhitespace: Yes
LineEndingConversion: Posix
```

---

## 五、VERIFY 自检

初始化完成后，输出自检报告：

```
【项目初始化自检】
  - 7 层目录已建
  - CLAUDE.md / SESSION_LOG.md / DECISIONS.md / BACKLOG.md 就绪
  - 数据字典模板已生成
  - 清洗脚本模板已生成 (02_code/01_data_cleaning.R)
  - .gitignore 已配置（原始数据不入 git）
  - Git 仓库已初始化 + 首次提交
  - [咨询模式] 交付包骨架已预建：05_reports/结果-{今日}/
  
下一步：
  1. 把原始数据放入 01_data/rawdata/
  2. 填写 01_data/README.md 数据字典
  3. 锁口径：打开 CLAUDE.md，填"口径锁定"节
  4. 开始清洗：打开 02_code/01_data_cleaning.R
```

---

## 六、与其他 skill 的协作

| 上游 | project-init 做什么 | 下游 |
|------|-------------------|------|
| `biostat-principles` | 目录规约落地 | `r-biostats` 接着做分析 |
| 用户说"新建项目" | 建骨架 + 模板 | 口径讨论 → `r-biostats` PLAN 阶段 |
| 咨询模式 | 额外预建结果包骨架 | `consulting-delivery` 做填充 |

---

## 七、常见坑

| 场景 | 处理 |
|------|------|
| 用户给了中文项目名 | 建议改 snake_case，但尊重用户决定；中文名要警示 shell 转义问题 |
| 目录已存在 | 停下来问，不覆盖；默认建议加 `_v2` 后缀 |
| 不在 git 仓库但用户要启 git | 先 `git init`，.gitignore 必须在第一次 commit 之前存在 |
| 咨询模式没指定主题 | 用 `主题占位`，在 `00_客户说明.md` 里提示用户改 |
| 用户说"要不要用 renv" | 默认 **否**；除非用户明确要求，renv 对小咨询任务反而拖累速度 |
