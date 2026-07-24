---
name: project-init
description: |
  初始化标准卫生统计研究或咨询项目，生成 R 或 Python 七层目录、PROTOCOL、SAP、结果单源、registry 与可选 Git 配置。仅在用户明确要求创建项目或把空工作区建成正式项目时使用；简单作业、快速核验和已有项目分析不触发。上游为 biostat-principles；咨询项目完成分析后再用 consulting-delivery。
---

# 项目初始化 skill

> **工作模式**：INQUIRE（问清信息）→ SCAFFOLD（建目录）→ POPULATE（填模板）→ VERIFY（自检）→ GUIDE（告诉用户下一步）。

---

## 一、开工前确认

先从用户请求与工作区读取已有信息，只追问无法发现且会改变骨架的字段：

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
4. 分析语言：R 或 Python
5. 存放根路径（默认当前工作目录）：
6. 是否显式启用 Git（默认 no；仅在用户选择 yes 且 Git 已可用时初始化）：
```

**项目名违反 snake_case** → 自动建议规范名并请用户确认（不要硬改）。
**同名目录已存在** → 停下来问用户覆盖、改名、还是追加。

---

## 二、目录结构

目录、编号、表图、registry、归档与 BACKLOG 的维护契约见 [references/project-hygiene.md](references/project-hygiene.md)。

### 研究模式（A）

```
{project}/
├── CLAUDE.md              # 继承 + 项目专属规则
├── AGENTS.md              # Codex 指向 CLAUDE.md 单源
├── README.md              # 项目说明
├── PROTOCOL.md            # 研究问题、设计、伦理与报告规范
├── SAP.md                 # 冻结的统计分析计划与偏离规则
├── SESSION_LOG.md         # 操作日志
├── DECISIONS.md           # 方法决策
├── BACKLOG.md             # 待补清单（缺文献/数据/方法/规划，全程只增不删）
├── .gitignore             # 忽略数据和临时
├── .epiagentkit-raw-roots # 可选额外原始数据根，每行一个项目相对路径
├── .Rproj                 # 仅 R 项目生成
├── 01_data/
│   ├── rawdata/           # 只读
│   └── README.md          # 数据字典
├── 02_code/
│   ├── config.R|py        # 表图 registry（空清单起步，实现见 references/registry.md）
│   ├── conventions.R|py   # 有序水平、配色、数字格式单源
│   ├── vendored/          # 项目自包含的结果/出图 helper
│   └── 01_data_cleaning.R|py # 清洗脚本模板
├── 03_tables/supplementary/
├── 04_figures/supplementary/
├── 05_reports/
├── 06_results/
├── 07_paper/
│   ├── results.yaml
│   └── 0_result_summaries.md
└── 09_backup/
    ├── INDEX.md            # 旧交付物 / 旧代码批次索引
    └── EXPERIMENTS.md      # 全部探索尝试索引，含失败/未采用结果
```

### 咨询模式（B）· 额外装配

咨询模式在研究模式基础上，额外：

- `05_reports/结果-{今日}-{主题占位}/` 按所选语言预建空交付包（`run_all.R` 或 `run_all.py`）
- `CLAUDE.md` 追加"交付前必过 consulting-delivery 终检"
- `DECISIONS.md` 追加首条"咨询任务，客户口径见 `DECISIONS.md` 顶部"

---

## 三、执行脚本

用 `scripts/init_project.R` 一键创建。R 里运行：

```r
skill_roots <- path.expand(c(
  Sys.getenv("EPIAGENTKIT_SKILLS"), Sys.getenv("EPICLAUDE_SKILLS"),
  "~/.claude/skills",  # Claude Code
  "~/.agents/skills",  # Codex 官方用户目录
  "~/.codex/skills"    # 既有 Codex 本地兼容目录
))
init_script <- file.path(skill_roots[nzchar(skill_roots)], "project-init/scripts/init_project.R")
init_script <- init_script[file.exists(init_script)][1]
if (is.na(init_script)) stop("找不到 project-init；请先安装 skills 或设置 EPIAGENTKIT_SKILLS")
source(init_script)
init_project(
  name = "cohort_smoking_chd",
  type = 1,           # 1=队列 2=病例对照 3=横断面 4=RCT 5=Meta 6=RWD 7=方法学
  mode = "research",  # "research" 或 "consulting"
  language = "r",     # "r" 或 "python"
  root = ".",
  git = FALSE          # 只有用户明确启用时改为 TRUE
)
```

`git = TRUE` 必须对应用户本轮的明确选择。脚本先用 `Sys.which("git")` 检测；未找到 Git 时继续创建项目并明确报告跳过，不执行安装。

---

## 四、模板文件内容

### 4.1 `CLAUDE.md` + `AGENTS.md`（项目级，单源继承）

```markdown
# {项目名} · 项目级规则

本项目继承 EpiAgentKit 全局规则（Claude Code：`~/.claude/CLAUDE.md`；Codex：`~/.codex/AGENTS.md`）。
`CLAUDE.md` 是项目规则单源；`AGENTS.md` 指示 Codex 开工前完整读取它，避免双份项目口径漂移。

## 新会话必读（新 agent 开局第一步，按序读完再动手）

> 本文件每 session 必然注入；下面这份清单 = 不依赖记忆、不重读全项目即可进入状态的最短路径。

1. 本文件「口径锁定」节 —— **当前口径以此为准**（下游全部服从）
2. `PROTOCOL.md` + `SAP.md` —— 研究问题、预设分析及偏离边界
3. `07_paper/results.yaml` —— 结果机器单源（→ 派生 `0_result_summaries.md`；下游 `val()` 取数）
4. `DECISIONS.md` 末尾 2~3 条 —— 最近的方法变更与原因
5. `BACKLOG.md` 主表未完成项 —— 全程累积的待补项（缺文献 / 数据 / 方法 / 下一步规划），挑「完善方式=AI」的必补项作为下一步候选
6. 所选语言的 `02_code/conventions.R|py` + `config.R|py` —— 口径常量真源（有序水平 / 配色 / registry）
7. `SESSION_LOG.md` 末 10 行 —— 上次做到哪、卡在哪

**信任但验证**：涉及数字的任务，先快速核 `0_result_summaries` 关键数字 vs 最新输出文件 mtime / registry 是否对得上；对不上立即触发 `epi-project-audit`，不盲信本文件可能已陈旧的内容。

## 当前状态（快照，非历史；每次会话收尾必更新，≤10 行）

> append-only 的 SESSION_LOG 读不出"现在在哪"，本节专门回答这点。改方法/出新结果/定稿版本后立即更新。

- 当前阶段：[如 主分析已定稿，正在写讨论]
- 最新定稿版本 / 回退点：[如 数据 v3 / commit abc1234 / 手工备份批次]
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
- `05_reports/` 内结果包必须自包含，对应语言的 `run_all.R|py` 能在空 session 或用户已准备的兼容 Python 环境中跑通
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
**证据ID**：[如适用，填写 evidence-research 的 EVID-…；无则写“不适用”]
**原因**：[待用户填写]
**放弃方案**：[待用户填写]
```

### 4.3b `BACKLOG.md`（待补清单）

全项目周期累积的"待补/想法/下一步"单一入口。**只增不删**——发现即记，做完勾掉留痕。
关键不在建文件，而在 agent 任何阶段（清洗 / 分析 / 出图 / 写作 / 审查）一发现缺口就立即追加，
不靠记忆、不留到"以后"（全局 CLAUDE.md §3 已设硬红线）。

```markdown
# BACKLOG · 待补清单

全项目周期随时冒出来的缺口与待办都进这里：缺文献、缺数据、缺方法/分析、
写作待补、下一步规划。规划研究方案时先扫本文件，决定下一步让 AI 做
什么、自己去找哪些数据 / 做哪些决策。

维护规则：

- 任何时候（清洗 / 分析 / 出图 / 写作 / 审查）发现缺口或想法 → 立即追加一行到主表顶部，不留到"以后"。
- 本表只装"主流程要用的事"——做完的、没做的同在一张表，靠「状态」列区分，不另设已完成表。
- **待完善内容**：开头加【文献/数据/方法/分析/写作/规划】类别标签，便于规划时筛。
- **完善方式**：AI（agent 可直接做：编程 / 分析 / 检索 / 下载）| 人工（需我提供数据 / 外部资源 / 做决策）。
- **重要性**三档：
  - 必补 —— 不补研究做不了 / 结论不成立 / 无法投稿（阻断项，最高优先）。
  - 建议 —— 补了完善论文（敏感性、稳健性、对照、双标化等），不补也能成稿。
  - 可选 —— 探索 / 锦上添花 / 不确定有无用。
- **状态**：完成填 `✅ YYYY-MM-DD`，未完成留空；做完只打勾不删行（删了查不到"补过没"）。
- **做了发现不该进主流程**（效果不好 / 实属探索）→ 不留主表，整条挪到 `09_backup/<日期>_<主题>/` 并在 FINDINGS.md 记结论；本表「已移出」区只留一行指针，正文留痕在 backup。

## 待办与已完成（同一张表，新发现加到顶部）

| 待完善内容 | 完善方式 | 重要性 | 状态 |
|------------|----------|--------|------|

## 已移出主流程（挪至 09_backup，留指针不留正文）

| 原待完善内容 | 去向（09_backup/…） | 原因 | 日期 |
|--------------|----------------------|------|------|
```

### 4.3c `PROTOCOL.md`、`SAP.md` 与探索实验索引

- `PROTOCOL.md` 在分析前锁定研究问题、设计、人群、暴露/干预、终点、伦理/注册和适用报告规范。
- `SAP.md` 在查看主要结果前锁定 estimand、分析人群、缺失处理、主要模型、诊断、多重性、验证切分、敏感性和亚组分析。
- 任何方案偏离写入 `DECISIONS.md`，并区分预设与探索性。
- 每次试新方法先登记 `09_backup/EXPERIMENTS.md`，再在独立目录写 `PLAN.md`、运行并以 `FINDINGS.md` 记录全部结果。不满足预设主流程纳入条件的结果不进入主 `results.yaml`；需展示时只进入消融/探索性附录。

### 4.4 结果单源 `07_paper/results.yaml`（+ 派生 `0_result_summaries.md`）

`init_project.R` 生成**机器可读单源** `results.yaml` 与其派生 `0_result_summaries.md`（标注勿手改）。
数字由所选语言的 `emit_summary.R` 或 `emit_summary.py` 渲染一次写入 results.yaml（raw 分量 + rendered 成品串 + interp 解读），
`render_summary_md()` 派生 md；下游论文/报告/PPT 一律 `val("07_paper/results.yaml","key")` 取数禁手敲。
schema 与用法详见 `biostat-principles/references/result-summary-schema.md`。改数字只改 results.yaml 再重派生（双向一致性）。

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

### 4.6 `02_code/01_data_cleaning.R|py`（清洗模板）

按 `language` 生成 R 或 Python 模板。模板只包含只读输入、项目根定位、配置入口、样本损失核验和派生输出占位；不预填研究专属纳排、变量编码或随机种子。实际逻辑必须来自已确认的 PROTOCOL 与 SAP。

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

### 4.8 `.Rproj`（仅 R 项目）

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
  - CLAUDE.md / AGENTS.md / PROTOCOL.md / SAP.md / 日志与待补清单就绪
  - config.R|py / conventions.R|py / 对应语言 vendored helper 与空 registry 就绪
  - 探索实验索引 09_backup/EXPERIMENTS.md 就绪
  - 版本归档索引 09_backup/INDEX.md 就绪
  - 数据字典模板已生成
  - 清洗脚本模板已生成 (02_code/01_data_cleaning.R|py)
  - .gitignore 已配置（原始数据不入 git）
  - Git：已初始化并按全局偏好收尾，或因未启用 / 不可用而跳过；缺少 Git 不阻止签发
  - [咨询模式] 交付包骨架已预建：05_reports/结果-{今日}/
  
下一步：
  1. 填写并确认 PROTOCOL.md 与 SAP.md
  2. 把原始数据放入 01_data/rawdata/，填写数据字典
  3. 同步 CLAUDE.md 的口径锁定节
  4. 开始清洗：打开对应语言的 02_code/01_data_cleaning.R|py
```

---

## 六、与其他 skill 的协作

| 上游 | project-init 做什么 | 下游 |
|------|-------------------|------|
| `biostat-principles` | 目录规约落地 | `r-biostats` 或 `python-biostats` 接着做分析 |
| 用户说"新建项目" | 建骨架 + 模板 | 研究设计走 `epi-study-design`；执行走所选语言 skill |
| 咨询模式 | 额外预建结果包骨架 | `consulting-delivery` 做填充 |

---

## 七、常见坑

| 场景 | 处理 |
|------|------|
| 用户给了中文项目名 | 建议改 snake_case，但尊重用户决定；中文名要警示 shell 转义问题 |
| 目录已存在 | 停下来问是继续现有项目、改名还是另选目录；不得默认追加 `_v2` 制造并列版本 |
| 用户要启用 Git 且 Git 已可用 | 执行 `git init`；完成初始化与验证后按全局偏好自动首次 commit；仅在用户当轮明确要求时 push |
| Git 不可用 | 继续创建项目并报告“Git 已跳过”；不执行 `git init`，不安装 Git，不把缺少 Git 判为失败 |
| 想试多个模型或参数 | 先登记 `09_backup/EXPERIMENTS.md` 并隔离运行；不得直接改主流程或只保留最好结果 |
| 咨询模式没指定主题 | 用 `主题占位`，在 `00_客户说明.md` 里提示用户改 |
| 用户说"要不要用 renv" | 默认 **否**；除非用户明确要求，renv 对小咨询任务反而拖累速度 |
