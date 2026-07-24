# ============================================================
# init_project.R
# 一键创建卫生统计研究项目骨架
#
# 用法：从 Claude Code 的 ~/.claude/skills、Codex 的 ~/.agents/skills，
#       或 EPIAGENTKIT_SKILLS 指定目录 source 本脚本后运行：
#   init_project("cohort_smoking_chd", type = 1, mode = "research", language = "r")
#   init_project("client_xxx_survival", type = 1, mode = "consulting", language = "python")
# ============================================================

init_project <- function(name,
                         type = 1,
                         mode = c("research", "consulting"),
                         language = c("r", "python"),
                         root = ".",
                         git = FALSE,
                         overwrite = FALSE) {
  mode <- match.arg(mode)
  language <- match.arg(language)
  type_names <- c("cohort", "case_control", "cross_sectional",
                  "rct", "meta", "rwd", "methodology")
  stopifnot(type %in% seq_along(type_names))

  # 项目需自包含关键 helper，避免运行时依赖仓库外相对路径。
  skill_roots <- unique(path.expand(c(
    Sys.getenv("EPIAGENTKIT_SKILLS"),
    Sys.getenv("EPICLAUDE_SKILLS"),
    "~/.claude/skills",
    "~/.agents/skills",
    "~/.codex/skills"
  )))
  skill_roots <- skill_roots[nzchar(skill_roots)]
  find_skill_file <- function(skill, relative_path) {
    candidates <- file.path(skill_roots, skill, relative_path)
    found <- candidates[file.exists(candidates)]
    if (!length(found)) {
      stop("缺少必需 skill 文件：", file.path(skill, relative_path),
           "；请安装完整 skills 或设置 EPIAGENTKIT_SKILLS")
    }
    found[[1]]
  }
  helper_sources <- if (language == "r") {
    c(
      emit_summary.R = find_skill_file("r-biostats", "scripts/emit_summary.R"),
      fig_setup.R = find_skill_file("publication-figures", "scripts/fig_setup.R")
    )
  } else {
    c(
      emit_summary.py = find_skill_file("python-biostats", "scripts/emit_summary.py")
    )
  }
  consulting_scaffold_source <- if (mode == "consulting") {
    find_skill_file("consulting-delivery", "scripts/consulting_scaffold.R")
  } else NULL

  # 名称检查 -----------------------------------------------
  if (!grepl("^[a-z][a-z0-9_]*$", name)) {
    warning("项目名建议 snake_case（小写 + 下划线），例如 'cohort_smoking_chd'")
  }

  proj <- file.path(root, name)
  if (dir.exists(proj) && !overwrite) {
    stop("目录已存在：", proj, "；如需覆盖请 overwrite = TRUE")
  }

  # 建目录 -------------------------------------------------
  dirs <- c(
    "01_data/rawdata",
    "02_code/vendored",
    "03_tables/supplementary",
    "04_figures/supplementary",
    "05_reports",
    "06_results",
    "07_paper",
    "09_backup"
  )
  invisible(lapply(file.path(proj, dirs),
                   dir.create, recursive = TRUE, showWarnings = FALSE))

  today <- format(Sys.Date(), "%Y-%m-%d")
  today_md <- sprintf("%d-%d",
                      as.integer(format(Sys.Date(), "%m")),
                      as.integer(format(Sys.Date(), "%d")))
  type_name <- type_names[type]

  # 项目规则：CLAUDE.md 为单源，AGENTS.md 指示 Codex 读取它 ----
  claude_md <- c(
    sprintf("# %s · 项目级规则", name),
    "",
    "本项目继承 EpiAgentKit 全局规则（Claude Code：`~/.claude/CLAUDE.md`；Codex：`~/.codex/AGENTS.md`）。",
    "`CLAUDE.md` 是项目规则单源；`AGENTS.md` 只负责指示 Codex 读取本文件，避免双份口径漂移。",
    "",
    "## 新会话必读（按序）",
    "",
    "1. 本文件的口径锁定与当前状态",
    "2. `PROTOCOL.md` 与 `SAP.md`（研究问题、预设分析及偏离）",
    "3. `07_paper/results.yaml`（结果机器单源）",
    "4. `DECISIONS.md` 末尾 2–3 条",
    "5. `BACKLOG.md` 主表未完成项",
    sprintf("6. `02_code/conventions.%s` 与 `02_code/config.%s`",
            if (language == "r") "R" else "py",
            if (language == "r") "R" else "py"),
    "7. `SESSION_LOG.md` 末 10 行",
    "",
    "## 当前状态（每次会话收尾更新，最多 10 行）",
    "",
    "- 当前阶段：方案待确认",
    "- 最新定稿版本 / 回退点：无",
    "- 进行中：填写 PROTOCOL.md 与 SAP.md",
    "- 已知坑 / 待办：见 BACKLOG.md",
    "- 下一步：确认研究方案后开始数据清洗",
    "",
    "## 项目基本信息",
    "",
    sprintf("- 研究类型：%s", type_name),
    sprintf("- 分析语言：%s", toupper(language)),
    "- 研究问题：[一句话 PICOS]",
    "- 数据来源：[数据集名 + 时间段]",
    "- 主要终点：[具体定义]",
    "- 分析计划：[主分析 + 敏感性]",
    "",
    "## 口径锁定（严禁擅自变动）",
    "",
    "- 纳入标准：",
    "- 排除标准：",
    "- 暴露变量：",
    "- 结局变量：",
    "- 随访时间：",
    "- 协变量：",
    "",
    "口径变动 → 先改本节 → 记录 `DECISIONS.md` → 重跑受影响的分析。",
    "",
    if (mode == "consulting")
      c("## 咨询模式专属",
        "",
        "- 交付前必过 `consulting-delivery` 的 FINAL 终检清单（§八）",
        "- `05_reports/` 内结果包必须自包含，`run_all.R` 能在空 session 跑通",
        "") else NULL
  )
  writeLines(claude_md, file.path(proj, "CLAUDE.md"), useBytes = TRUE)
  writeLines(
    c("# Codex 项目指引",
      "",
      "开始任何项目工作前，完整读取同目录 `CLAUDE.md`。",
      "`CLAUDE.md` 是项目口径、当前状态与工作流约束的单一真源；本文件不复制其内容，避免双份规则漂移。"),
    file.path(proj, "AGENTS.md"), useBytes = TRUE
  )

  # SESSION_LOG.md ----------------------------------------
  writeLines(
    c("# Session Log",
      "",
      "| 时间 | 操作 | 文件 | 结果 |",
      "|------|------|------|------|",
      sprintf("| %s | 项目初始化 | 全部目录和模板 | 骨架就绪 |", today)),
    file.path(proj, "SESSION_LOG.md"), useBytes = TRUE
  )

  # DECISIONS.md ------------------------------------------
  writeLines(
    c("# 方法决策记录",
      "",
      "所有会影响最终结果的方法选择都必须写到这里。",
      "格式：时间 + 选择 + 原因 + 放弃的替代方案。",
      "",
      "---",
      "",
      sprintf("## %s · 项目启动", today),
      "",
      sprintf("**决策**：项目类型 = %s，主分析计划 = [待用户确认]", type_name),
      "**证据ID**：[如适用，填写 evidence-research 的 EVID-…；无则写‘不适用’]",
      "**原因**：[待用户填写]",
      "**放弃方案**：[待用户填写]"),
    file.path(proj, "DECISIONS.md"), useBytes = TRUE
  )

  # PROTOCOL.md：研究问题与治理前置锁定 -------------------
  writeLines(
    c("# 研究方案（PROTOCOL）",
      "",
      "> 状态：草案。分析开始前由研究负责人确认；后续变更写入版本记录与 `DECISIONS.md`。",
      "",
      "## 研究问题与设计",
      "",
      sprintf("- 研究设计：%s", type_name),
      "- 研究问题（PICO/PECO）：",
      "- 研究目的与主要假设：",
      "- 数据来源与研究时间窗：",
      "",
      "## 研究对象与变量",
      "",
      "- 目标人群与研究场景：",
      "- 纳入标准：",
      "- 排除标准：",
      "- 暴露 / 干预与对照：",
      "- 主要结局及测量时点：",
      "- 次要结局：",
      "- 预设协变量与混杂因素：",
      "",
      "## 治理与报告",
      "",
      "- 伦理审批 / 知情同意：",
      "- 注册或预注册平台与编号（如适用）：",
      "- 数据安全与访问权限：",
      "- 适用报告规范（如 STROBE / CONSORT / PRISMA）：",
      "",
      "## 版本记录",
      "",
      "| 日期 | 版本 | 变更 | 确认人 |",
      "|------|------|------|--------|",
      sprintf("| %s | 0.1 | 初始化草案 | 待确认 |", today)),
    file.path(proj, "PROTOCOL.md"), useBytes = TRUE
  )

  # SAP.md：统计分析计划前置锁定 --------------------------
  writeLines(
    c("# 统计分析计划（SAP）",
      "",
      "> 状态：草案。查看结果前冻结主要分析；任何偏离必须在 `DECISIONS.md` 记录原因并标明预设或探索性。",
      "",
      "## 分析目标",
      "",
      "- 主要估计目标（estimand）：",
      "- 主要 / 次要假设：",
      "- 分析人群：",
      "- 主要与次要终点：",
      "",
      "## 数据处理",
      "",
      sprintf("- 变量定义与有序水平：见 `02_code/conventions.%s`",
              if (language == "r") "R" else "py"),
      "- 缺失数据处理：",
      "- 异常值与数据质量规则：",
      "- 样本量 / 精度 / 功效依据：",
      "",
      "## 统计方法",
      "",
      "- 描述性分析：",
      "- 主要模型与效应量：",
      "- 协变量调整策略：",
      "- 模型假设与诊断：",
      "- 多重比较控制：",
      "- 验证 / 交叉验证切分与防信息泄漏规则：",
      "- 主评价指标与最小有意义差异：",
      "- 亚组与交互作用（预设）：",
      "- 敏感性分析（预设）：",
      "- 探索性分析边界：每次先登记于 `09_backup/EXPERIMENTS.md`，再隔离运行",
      "",
      "## 可复现性与偏离",
      "",
      "- 随机过程、种子与拆分标识（如适用）：",
      if (language == "r")
        "- 软件与包版本记录：`sessionInfo()` 或项目既有锁文件"
      else
        "- 软件与包版本记录：Python 版本与项目既有锁文件",
      "- SAP 冻结日期 / 确认人：",
      "- 偏离记录：见 `DECISIONS.md`",
      "",
      "## 版本记录",
      "",
      "| 日期 | 版本 | 变更 | 确认人 |",
      "|------|------|------|--------|",
      sprintf("| %s | 0.1 | 初始化草案 | 待确认 |", today)),
    file.path(proj, "SAP.md"), useBytes = TRUE
  )

  # 探索实验总索引：记录全部尝试，主线只接收满足预设条件的结果 ----
  writeLines(
    c("# 探索实验索引",
      "",
      "每次尝试在看结果前登记一行，并在对应目录建立 `PLAN.md`；完成后更新状态和 `FINDINGS.md`。",
      "失败、持平与未采用的尝试同样保留，避免重复试验和选择性报告。未合并结果不得写入主 `results.yaml`。",
      "",
      "| 实验ID | 日期 | 问题 / 假设 | 主线基线 | 唯一改动 | 数据切分与主指标 | 预设晋级标准 | 状态 | 目录 |",
      "|--------|------|-------------|----------|----------|------------------|--------------|------|------|"),
    file.path(proj, "09_backup/EXPERIMENTS.md"), useBytes = TRUE
  )

  # 版本归档总索引：工作区只留当前版，旧版按批次可检索 ----
  writeLines(
    c("# 版本归档索引",
      "",
      "工作区只保留稳定命名的当前版；被替代的报告、PPT、论文、代码、素材与核验输出按同一批次归档。",
      "每个批次目录使用 `YYYY-MM-DD_HHMM_<主题>_<阶段>`，保留原相对目录并写 `MANIFEST.md`。新记录加在表格顶部。",
      "",
      "| 归档时间 | 主题 | 类型 | 归档目录 | 当前版路径 | 原因 |",
      "|----------|------|------|----------|------------|------|"),
    file.path(proj, "09_backup/INDEX.md"), useBytes = TRUE
  )

  # BACKLOG.md --------------------------------------------
  writeLines(
    c("# BACKLOG · 待补清单",
      "",
      "全项目周期随时冒出来的缺口与待办都进这里：缺文献、缺数据、缺方法/分析、",
      "写作待补、下一步规划。规划研究方案时先扫本文件，决定下一步让 AI 做",
      "什么、自己去找哪些数据 / 做哪些决策。",
      "",
      "维护规则：",
      "",
      "- 任何时候（清洗 / 分析 / 出图 / 写作 / 审查）发现缺口或想法 → 立即追加一行到主表顶部，不留到\"以后\"。",
      "- 本表只装\"主流程要用的事\"——做完的、没做的同在一张表，靠「状态」列区分，不另设已完成表。",
      "- **待完善内容**：开头加【文献/数据/方法/分析/写作/规划】类别标签，便于规划时筛。",
      "- **完善方式**：AI（agent 可直接做：编程 / 分析 / 检索 / 下载）| 人工（需我提供数据 / 外部资源 / 做决策）。",
      "- **重要性**三档：",
      "  - 必补 —— 不补研究做不了 / 结论不成立 / 无法投稿（阻断项，最高优先）。",
      "  - 建议 —— 补了完善论文（敏感性、稳健性、对照、双标化等），不补也能成稿。",
      "  - 可选 —— 探索 / 锦上添花 / 不确定有无用。",
      "- **状态**：完成填 `✅ YYYY-MM-DD`，未完成留空；做完只打勾不删行（删了查不到\"补过没\"）。",
      "- **做了发现不该进主流程**（效果不好 / 实属探索）→ 不留主表，整条挪到 `09_backup/<日期>_<主题>/` 并在 FINDINGS.md 记结论；本表「已移出」区只留一行指针。",
      "",
      "## 待办与已完成（同一张表，新发现加到顶部）",
      "",
      "| 待完善内容 | 完善方式 | 重要性 | 状态 |",
      "|------------|----------|--------|------|",
      "",
      "## 已移出主流程（挪至 09_backup，留指针不留正文）",
      "",
      "| 原待完善内容 | 去向（09_backup/…） | 原因 | 日期 |",
      "|--------------|----------------------|------|------|"),
    file.path(proj, "BACKLOG.md"), useBytes = TRUE
  )

  # README.md ---------------------------------------------
  writeLines(
    c(sprintf("# %s", name),
      "",
      sprintf("**研究类型**：%s", type_name),
      sprintf("**启动日期**：%s", today),
      sprintf("**模式**：%s", if (mode == "research") "研究" else "咨询"),
      sprintf("**分析语言**：%s", toupper(language)),
      "",
      "## 目录结构",
      "",
      "```",
      "01_data/       # 原始数据（只读）",
      sprintf("02_code/       # %s 脚本", if (language == "r") "R" else "Python"),
      "03_tables/     # 最终表",
      "04_figures/    # 最终图",
      "05_reports/    # 结果分享包",
      "06_results/    # 中间产物",
      "07_paper/      # 论文稿 + 结果汇总",
      "09_backup/     # INDEX.md + 分批归档",
      "```",
      "",
      "研究方案见 `PROTOCOL.md`，预设统计分析见 `SAP.md`；缺口统一记入 `BACKLOG.md`，旧版批次登记于 `09_backup/INDEX.md`，全部探索尝试登记于 `09_backup/EXPERIMENTS.md`。",
      "",
      "## 快速开始",
      "",
      "1. 填写并确认 `PROTOCOL.md` 与 `SAP.md`，冻结主要口径和预设分析",
      "2. 把原始数据放入 `01_data/rawdata/`，填写 `01_data/README.md` 数据字典",
      "3. 同步 `CLAUDE.md` 的口径锁定节（Codex 由 `AGENTS.md` 指向该单源）",
      sprintf("4. 开始清洗：打开 `02_code/01_data_cleaning.%s`",
              if (language == "r") "R" else "py")),
    file.path(proj, "README.md"), useBytes = TRUE
  )

  # 07_paper/results.yaml（机器可读单源）------------------
  writeLines(
    c("# 结果单一真源（machine-readable）。数字只在此处改；",
      "# 下游论文/报告/PPT 一律 val(\"07_paper/results.yaml\", \"key\") 取数，禁手敲。",
      "# 改下游须先回写此处再向其余下游传播（双向一致性）。",
      sprintf("# 写入与渲染用 02_code/vendored/emit_summary.%s 的 add_result()；",
              if (language == "r") "R" else "py"),
      "# 0_result_summaries.md 由 render_summary_md() 从本文件生成，勿手改 md。",
      "meta:",
      "  project: \"[项目名]\"",
      "results: {}",
      "# 示例（由 add_result 自动写成，勿手敲）：",
      "#  S2_vs_S1_diff:",
      "#    label: S2 vs S1 组间差异",
      "#    section: 主要结果",
      "#    source: 02_code/03_main.R",
      "#    table: [由 table_path(\"main_effect\") 生成]",
      "#    raw: {est: -1.82, ci_low: -3.29, ci_high: -0.36, p: 0.015, unit: kg}",
      "#    rendered: {full: \"...\", est_ci: \"...\", p: \"...\"}",
      "#    interp: \"结论/效应解读（人写）；数字变了会自动标 interp_review 待复核\"",
      "# conclusion: \"跨结果总结论（人写，set_conclusion 写）\""),
    file.path(proj, "07_paper/results.yaml"), useBytes = TRUE
  )

  # 07_paper/0_result_summaries.md（由 results.yaml 自动生成）----
  writeLines(
    c("# 结果汇总（论文数据源 · 由 results.yaml 自动生成）",
      "",
      sprintf("本文件由 `emit_summary.%s` 的 `render_summary_md()` 从 `results.yaml` 渲染，**勿手改**。",
              if (language == "r") "R" else "py"),
      "改数字 → 改 `results.yaml`（或重跑产出脚本的 add_result）→ 重跑 render_summary_md。",
      "所有图表 / docx / 论文正文的数字一律 val() 从 results.yaml 取，与本文件同源。",
      "",
      "（首次分析后此处自动填入分节结果。）"),
    file.path(proj, "07_paper/0_result_summaries.md"), useBytes = TRUE
  )

  # 01_data/README.md -------------------------------------
  writeLines(
    c("# 数据字典",
      "",
      "## 数据来源",
      "",
      "- 数据集名称：",
      "- 提供方：",
      "- 数据时间范围：",
      "- 样本量（原始）：",
      "- 获取日期：",
      "- 伦理批件号：",
      "",
      "## 变量清单",
      "",
      "| 变量名 | 类型 | 单位 | 编码 | 说明 | 缺失率 |",
      "|--------|------|------|------|------|--------|",
      "| id | chr | — | 匿名编码 | 唯一标识 | 0% |",
      "| age | num | 年 | — | 基线年龄 | — |",
      "| sex | int | — | 1=男 2=女 | — | — |"),
    file.path(proj, "01_data/README.md"), useBytes = TRUE
  )

  # 02_code 口径与 registry 单一真源 --------------------
  if (language == "r") {
    writeLines(
      c("# 全项目口径常量单一真源 ----------------------------------",
        "ORDERED_LEVELS <- list()",
        "",
        "lv <- function(name) {",
        "  if (!name %in% names(ORDERED_LEVELS)) stop(\"未在 ORDERED_LEVELS 注册：\", name)",
        "  ORDERED_LEVELS[[name]]",
        "}",
        "",
        "PALETTE <- c(\"#0072B2\", \"#D55E00\", \"#009E73\", \"#CC79A7\",",
        "             \"#E69F00\", \"#56B4E9\", \"#F0E442\", \"#000000\")",
        "DIGITS_EST <- 2L",
        "DIGITS_P <- 3L",
        "P_FLOOR <- 0.001"),
      file.path(proj, "02_code/conventions.R"), useBytes = TRUE
    )
    writeLines(
      c("source(\"02_code/conventions.R\", encoding = \"UTF-8\")",
        "",
        "# 顺序 = 论文行文顺序 = 自动编号；新增 / 退役 / 调序只改下列清单。",
        "TABLE_REGISTRY <- character()",
        "TABLE_S_REGISTRY <- character()",
        "FIG_REGISTRY <- character()",
        "FIG_S_REGISTRY <- character()",
        "",
        "table_path <- function(stem) {",
        "  i <- match(stem, TABLE_REGISTRY)",
        "  if (!is.na(i)) return(sprintf(\"03_tables/Table%d_%s.xlsx\", i, stem))",
        "  i <- match(stem, TABLE_S_REGISTRY)",
        "  if (!is.na(i)) return(sprintf(\"03_tables/supplementary/TableS%d_%s.xlsx\", i, stem))",
        "  stop(\"stem 不在 table registry：\", stem)",
        "}",
        "",
        "fig_path <- function(stem, ext = \"png\") {",
        "  ext <- tolower(ext)",
        "  if (!ext %in% c(\"png\", \"pdf\")) stop(\"图件扩展名只允许 png 或 pdf\")",
        "  i <- match(stem, FIG_REGISTRY)",
        "  if (!is.na(i)) return(sprintf(\"04_figures/Fig%d_%s.%s\", i, stem, ext))",
        "  i <- match(stem, FIG_S_REGISTRY)",
        "  if (!is.na(i)) return(sprintf(\"04_figures/supplementary/FigS%d_%s.%s\", i, stem, ext))",
        "  stop(\"stem 不在 figure registry：\", stem)",
        "}"),
      file.path(proj, "02_code/config.R"), useBytes = TRUE
    )
  } else {
    writeLines(
      c("# 全项目口径常量单一真源",
        "ORDERED_LEVELS: dict[str, list[object]] = {}",
        "PALETTE = [\"#0072B2\", \"#D55E00\", \"#009E73\", \"#CC79A7\",",
        "           \"#E69F00\", \"#56B4E9\", \"#F0E442\", \"#000000\"]",
        "DIGITS_EST = 2",
        "DIGITS_P = 3",
        "P_FLOOR = 0.001",
        "",
        "def levels(name: str) -> list[object]:",
        "    if name not in ORDERED_LEVELS:",
        "        raise KeyError(f\"未在 ORDERED_LEVELS 注册：{name}\")",
        "    return ORDERED_LEVELS[name]"),
      file.path(proj, "02_code/conventions.py"), useBytes = TRUE
    )
    writeLines(
      c("# 顺序 = 论文行文顺序 = 自动编号；新增、退役或调序只改下列清单。",
        "TABLE_REGISTRY: list[str] = []",
        "TABLE_S_REGISTRY: list[str] = []",
        "FIG_REGISTRY: list[str] = []",
        "FIG_S_REGISTRY: list[str] = []",
        "",
        "def _registered(stem: str, main: list[str], supplementary: list[str], kind: str, ext: str) -> str:",
        "    if stem in main:",
        "        number = main.index(stem) + 1",
        "        return f\"{'03_tables/Table' if kind == 'table' else '04_figures/Fig'}{number}_{stem}.{ext}\"",
        "    if stem in supplementary:",
        "        number = supplementary.index(stem) + 1",
        "        root = '03_tables/supplementary/TableS' if kind == 'table' else '04_figures/supplementary/FigS'",
        "        return f\"{root}{number}_{stem}.{ext}\"",
        "    raise KeyError(f\"stem 不在 {kind} registry：{stem}\")",
        "",
        "def table_path(stem: str) -> str:",
        "    return _registered(stem, TABLE_REGISTRY, TABLE_S_REGISTRY, 'table', 'xlsx')",
        "",
        "def fig_path(stem: str, ext: str = 'png') -> str:",
        "    ext = ext.lower()",
        "    if ext not in {'png', 'pdf'}:",
        "        raise ValueError('图件扩展名只允许 png 或 pdf')",
        "    return _registered(stem, FIG_REGISTRY, FIG_S_REGISTRY, 'figure', ext)"),
      file.path(proj, "02_code/config.py"), useBytes = TRUE
    )
  }

  copied <- file.copy(
    unname(helper_sources),
    file.path(proj, "02_code/vendored", names(helper_sources)),
    overwrite = TRUE
  )
  if (!all(copied)) stop("项目 helper 复制失败；初始化未通过可复现性检查")

  # 02_code/01_data_cleaning.* ----------------------------
  if (language == "r") {
    cleaning <- c(
      "# 脚本：02_code/01_data_cleaning.R",
      "# 目的：从 01_data/rawdata/ 只读导入原始数据并生成分析数据",
      "# 输入：01_data/rawdata/xxx.csv",
      "# 输出：06_results/cohort_clean.xlsx；06_results/sample_flow.xlsx",
      "",
      "library(tidyverse)",
      "library(here)",
      "library(writexl)",
      "",
      'here::i_am("02_code/01_data_cleaning.R")',
      'source("02_code/config.R", encoding = "UTF-8")',
      "",
      '# raw <- readr::read_csv("01_data/rawdata/xxx.csv", show_col_types = FALSE)',
      "# 核对类型、键、重复、缺失、范围和每一步样本损失后再写出派生数据。",
      '# writexl::write_xlsx(cohort, "06_results/cohort_clean.xlsx")',
      '# writexl::write_xlsx(flowchart, "06_results/sample_flow.xlsx")',
      "",
      'message("清洗模板已加载；请填充项目已确认的实际逻辑")'
    )
    cleaning_path <- file.path(proj, "02_code/01_data_cleaning.R")
  } else {
    cleaning <- c(
      '"""从 01_data/rawdata/ 只读导入原始数据并生成分析数据。"""',
      "",
      "from pathlib import Path",
      "import pandas as pd",
      "",
      'PROJECT_ROOT = Path(__file__).resolve().parents[1]',
      '# raw = pd.read_csv(PROJECT_ROOT / "01_data/rawdata/xxx.csv")',
      "# 核对类型、键、重复、缺失、范围和每一步样本损失后再写出派生数据。",
      '# cohort.to_excel(PROJECT_ROOT / "06_results/cohort_clean.xlsx", index=False)',
      '# flowchart.to_excel(PROJECT_ROOT / "06_results/sample_flow.xlsx", index=False)',
      "",
      'print("清洗模板已加载；请填充项目已确认的实际逻辑")'
    )
    cleaning_path <- file.path(proj, "02_code/01_data_cleaning.py")
  }
  writeLines(cleaning, cleaning_path, useBytes = TRUE)

  # .gitignore --------------------------------------------
  writeLines(
    c("# 数据（敏感）",
      "01_data/rawdata/*",
      "!01_data/rawdata/.gitkeep",
      "!01_data/README.md",
      "",
      "# 中间产物",
      "06_results/*",
      "!06_results/.gitkeep",
      "",
      "# 系统与语言缓存",
      if (language == "r") ".Rproj.user/" else "__pycache__/",
      if (language == "r") ".Rhistory" else "*.py[cod]",
      if (language == "r") ".RData" else ".pytest_cache/",
      ".DS_Store",
      "Thumbs.db",
      "~$*",
      "",
      "# 编辑器",
      ".vscode/",
      ".idea/",
      "",
      "# 临时",
      "*.tmp",
      "*.bak"),
    file.path(proj, ".gitignore"), useBytes = TRUE
  )
  writeLines(
    c("# 每行一个项目相对原始数据根；01_data/rawdata 已默认保护，无需重复。",
      "# 例如：01_data/external_raw",
      "# 例如：source_exports"),
    file.path(proj, ".epiagentkit-raw-roots"), useBytes = TRUE
  )
  keep_dirs <- c("01_data/rawdata", "03_tables", "03_tables/supplementary",
                 "04_figures", "04_figures/supplementary", "05_reports",
                 "06_results", "09_backup")
  invisible(file.create(file.path(proj, keep_dirs, ".gitkeep")))

  # .Rproj 仅用于 R 项目 ---------------------------------
  if (language == "r") {
    writeLines(
      c("Version: 1.0",
        "",
        "RestoreWorkspace: No",
        "SaveWorkspace: No",
        "AlwaysSaveHistory: Default",
        "",
        "EnableCodeIndexing: Yes",
        "UseSpacesForTab: Yes",
        "NumSpacesForTab: 2",
        "Encoding: UTF-8",
        "",
        "AutoAppendNewline: Yes",
        "StripTrailingWhitespace: Yes",
        "LineEndingConversion: Posix"),
      file.path(proj, paste0(name, ".Rproj")), useBytes = TRUE
    )
  }

  # 咨询模式：预建一个结果包骨架 --------------------------
  if (mode == "consulting") {
    pack_name <- sprintf("结果-%s-主题占位", today_md)
    scaffold_env <- new.env(parent = globalenv())
    sys.source(consulting_scaffold_source, envir = scaffold_env)
    scaffold_env$create_delivery_pack(
      pack_name,
      root = file.path(proj, "05_reports"),
      language = if (language == "r") "R" else "python"
    )
  }

  # Git（可选；不可用时不安装，也不阻止项目创建）----------
  git_state <- "disabled"
  git_bin <- unname(Sys.which("git"))
  if (isTRUE(git) && !nzchar(git_bin)) {
    git_state <- "unavailable"
  } else if (isTRUE(git)) {
    old_wd <- getwd()
    git_result <- tryCatch(
      {
        setwd(proj)
        system2(git_bin, c("init", "--quiet"), stdout = TRUE, stderr = TRUE)
      },
      error = function(error) error,
      finally = setwd(old_wd)
    )
    git_status <- if (inherits(git_result, "error")) {
      1L
    } else {
      status <- attr(git_result, "status")
      if (is.null(status)) 0L else as.integer(status)
    }
    git_state <- if (identical(git_status, 0L)) "initialized" else "failed"
  }

  # 完成报告 ----------------------------------------------
  message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
  message("项目 [", name, "] 创建成功")
  message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
  message("路径：", normalizePath(proj))
  message("类型：", type_name, "  |  模式：", mode, "  |  语言：", language)
  message("")
  message("下一步：")
  message("  1. 填写并确认 ", file.path(name, "PROTOCOL.md"), " 与 SAP.md")
  message("  2. 把原始数据放入 ", file.path(name, "01_data/rawdata/"), " 并填写数据字典")
  message("  3. 同步口径：打开 ", file.path(name, "CLAUDE.md"))
  message("  4. 开始清洗：", file.path(name, "02_code", basename(cleaning_path)))
  if (identical(git_state, "initialized")) {
    message("Git 已初始化；完成初始化与验证后按全局偏好自动 commit，用户明确要求时才 push。")
  } else if (identical(git_state, "unavailable")) {
    message("Git 不可用，已跳过版本管理；未安装 Git，项目骨架不受影响。")
  } else if (identical(git_state, "failed")) {
    message("Git 可用但初始化失败，已保留项目骨架；请手动运行 git init 查看具体错误，不执行安装。")
  } else {
    message("Git 未启用，已跳过版本管理。")
  }

  invisible(proj)
}
