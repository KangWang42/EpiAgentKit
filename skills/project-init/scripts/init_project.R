# ============================================================
# init_project.R
# 一键创建卫生统计研究项目骨架
#
# 用法：
#   source("~/.claude/skills/project-init/scripts/init_project.R")
#   init_project("cohort_smoking_chd", type = 1, mode = "research")
#   init_project("client_xxx_survival", type = 1, mode = "consulting")
# ============================================================

init_project <- function(name,
                         type = 1,
                         mode = c("research", "consulting"),
                         root = ".",
                         git = TRUE,
                         overwrite = FALSE) {
  mode <- match.arg(mode)
  type_names <- c("cohort", "case_control", "cross_sectional",
                  "rct", "meta", "rwd", "methodology")
  stopifnot(type %in% seq_along(type_names))

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
    "02_code",
    "03_tables",
    "04_figures",
    "05_reports",
    "06_results",
    "07_paper",
    "09_backup"
  )
  invisible(lapply(file.path(proj, dirs),
                   dir.create, recursive = TRUE, showWarnings = FALSE))

  today <- format(Sys.Date(), "%Y-%m-%d")
  today_md <- format(Sys.Date(), "%-m-%-d")
  type_name <- type_names[type]

  # CLAUDE.md ---------------------------------------------
  claude_md <- c(
    sprintf("# %s · 项目级规则", name),
    "",
    "本文件继承 `~/.claude/CLAUDE.md` 的全局 EpiClaude 规则。",
    "以下是本项目专属约束。",
    "",
    "## 项目基本信息",
    "",
    sprintf("- 研究类型：%s", type_name),
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
      "**原因**：[待用户填写]",
      "**放弃方案**：[待用户填写]"),
    file.path(proj, "DECISIONS.md"), useBytes = TRUE
  )

  # BACKLOG.md --------------------------------------------
  writeLines(
    c("# BACKLOG · 待补清单",
      "",
      "全项目周期随时冒出来的缺口与待办都进这里：缺文献、缺数据、缺方法/分析、",
      "写作待补、下一步规划。规划研究方案时先扫本文件，决定下一步让 agent 做",
      "什么、自己去找哪些数据 / 做哪些决策。",
      "",
      "维护规则：",
      "",
      "- 任何时候（清洗 / 分析 / 出图 / 写作 / 审查）发现缺口或想法 → 立即追加一行到「待办」表顶部，不留到\"以后\"。",
      "- 类别：文献 | 数据 | 方法 | 分析 | 写作 | 规划",
      "- 执行方：agent（可直接做）| 我（需找数据 / 外部资源 / 做决策）",
      "- 优先级：高 | 中 | 低",
      "- 做完不删：勾掉移到「已完成」并注完成日期；彻底作废移「已放弃」并注原因。",
      "",
      "## 待办（新发现加到本表顶部）",
      "",
      "| 类别 | 待补内容 | 执行方 | 优先级 | 记录日期 |",
      "|------|----------|--------|--------|----------|",
      sprintf("| 示例-方法 | 主分析可加竞争风险模型作敏感性分析 | agent | 中 | %s |", today),
      sprintf("| 示例-数据 | 缺基线用药史，需回原始库提取或问数据方 | 我 | 高 | %s |", today),
      "",
      "（首次使用删除上面两行示例）",
      "",
      "## 已完成（留痕不删）",
      "",
      "| 类别 | 待补内容 | 完成日期 |",
      "|------|----------|----------|",
      "",
      "## 已放弃",
      "",
      "| 类别 | 待补内容 | 放弃原因 | 日期 |",
      "|------|----------|----------|------|"),
    file.path(proj, "BACKLOG.md"), useBytes = TRUE
  )

  # README.md ---------------------------------------------
  writeLines(
    c(sprintf("# %s", name),
      "",
      sprintf("**研究类型**：%s", type_name),
      sprintf("**启动日期**：%s", today),
      sprintf("**模式**：%s", if (mode == "research") "研究" else "咨询"),
      "",
      "## 目录结构",
      "",
      "```",
      "01_data/       # 原始数据（只读）",
      "02_code/       # R 脚本",
      "03_tables/     # 最终表",
      "04_figures/    # 最终图",
      "05_reports/    # 结果分享包",
      "06_results/    # 中间产物",
      "07_paper/      # 论文稿 + 结果汇总",
      "09_backup/     # 归档",
      "```",
      "",
      "另有 `BACKLOG.md`（待补清单）：缺文献 / 缺数据 / 缺方法 / 下一步规划随时记录，规划时先看它。",
      "",
      "## 快速开始",
      "",
      "1. 把原始数据放入 `01_data/rawdata/`",
      "2. 填写 `01_data/README.md` 数据字典",
      "3. 锁口径：打开 `CLAUDE.md`，填\"口径锁定\"节",
      "4. 开始清洗：打开 `02_code/01_data_cleaning.R`"),
    file.path(proj, "README.md"), useBytes = TRUE
  )

  # 07_paper/0_result_summaries.md ------------------------
  writeLines(
    c("# 结果汇总（论文唯一数据源）",
      "",
      "本文件是项目的**最终结果**。所有图表、docx、论文正文的数字，",
      "都应从这里取。一旦结果变化 → 第一时间同步更新这里。",
      "",
      "---",
      "",
      "## 样本特征",
      "",
      "N = [待填]",
      "",
      "## 主分析",
      "",
      "[分析名称]",
      "- 模型：",
      "- 样本：",
      "- 结果：",
      "- 来源：`02_code/NN_xxx.R` → `03_tables/TableN_xxx.xlsx`",
      "",
      "## 敏感性分析",
      "",
      "## 亚组分析",
      "",
      "## 结论（一句话）"),
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

  # 02_code/01_data_cleaning.R ----------------------------
  cleaning_r <- c(
    "# ============================================================",
    "# 脚本：02_code/01_data_cleaning.R",
    "# 目的：从 01_data/rawdata/ 读取原始数据，清洗为分析用数据集",
    "# 输入：01_data/rawdata/xxx.csv",
    "# 输出：06_results/cohort_clean.xlsx（表格化数据一律 xlsx；06_results 按内容命名不编号）",
    "#       03_tables/Table0_flowchart.xlsx",
    "# ============================================================",
    "",
    "library(tidyverse)",
    "library(here)",
    "library(writexl)",
    "",
    'here::i_am("02_code/01_data_cleaning.R")',
    "set.seed(123)",
    "",
    "# 1. 读取 ----------------------------------------------------",
    '# raw <- readr::read_csv("01_data/rawdata/xxx.csv", show_col_types = FALSE)',
    "",
    "# 2. 样本量损失链 --------------------------------------------",
    "# n_raw <- nrow(raw)",
    "# step1 <- raw |> filter(!is.na(exposure))",
    "# step2 <- step1 |> filter(age >= 18)",
    "",
    "# 3. 编码分类变量 --------------------------------------------",
    "# cohort <- step2 |>",
    "#   mutate(sex = factor(sex, levels = c(1, 2), labels = c('Male', 'Female')))",
    "",
    "# 4. 保存 ----------------------------------------------------",
    '# writexl::write_xlsx(cohort, "06_results/cohort_clean.xlsx")',
    "",
    '# flowchart <- tibble(step = ..., n = ..., loss = ...)',
    '# writexl::write_xlsx(flowchart, "03_tables/Table0_flowchart.xlsx")',
    "",
    'message("清洗完成（模板，待填充实际逻辑）")'
  )
  writeLines(cleaning_r, file.path(proj, "02_code/01_data_cleaning.R"), useBytes = TRUE)

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
      "# 系统",
      ".Rproj.user/",
      ".Rhistory",
      ".RData",
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
  file.create(file.path(proj, "01_data/rawdata/.gitkeep"))

  # .Rproj ------------------------------------------------
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

  # 咨询模式：预建一个结果包骨架 --------------------------
  if (mode == "consulting") {
    pack_name <- sprintf("结果-%s-主题占位", today_md)
    pack <- file.path(proj, "05_reports", pack_name)
    invisible(lapply(
      file.path(pack, c("data", "code", "06_results", "tables", "figures")),
      dir.create, recursive = TRUE, showWarnings = FALSE
    ))

    writeLines(
      c(sprintf("# %s", pack_name),
        "",
        "（首次使用请把\"主题占位\"改成实际主题，例如\"训练测试集\"）",
        "",
        "## 这份文件夹是什么",
        "",
        "[一句话说明]",
        "",
        "## 怎么看结果",
        "",
        "- 方法与结论 → `01_方法与结果.docx`",
        "- 表格 → `tables/`",
        "- 图件 → `figures/`",
        "",
        "## 怎么重现",
        "",
        "1. 在 RStudio 打开 `run_all.R`",
        "2. Session → Set Working Directory → To Source File Location",
        "3. Ctrl+Shift+Enter 运行全文"),
      file.path(pack, "00_客户说明.md"), useBytes = TRUE
    )

    writeLines(
      c("# ============================================================",
        sprintf("# %s · 一键复现脚本", pack_name),
        "# ============================================================",
        "",
        'if (!file.exists("run_all.R")) stop("工作目录错了")',
        "",
        'required_pkgs <- c("tidyverse", "readxl", "writexl", "ggsci", "ragg")',
        "missing_pkgs <- setdiff(required_pkgs, rownames(installed.packages()))",
        'if (length(missing_pkgs) > 0) install.packages(missing_pkgs)',
        "",
        'scripts <- list.files("code", pattern = "^[0-9]{2}_.*\\\\.R$", full.names = TRUE) |> sort()',
        "set.seed(123)",
        'for (s in scripts) { cat("执行：", s, "\\n"); source(s, encoding = "UTF-8") }',
        'writeLines(capture.output(sessionInfo()), "sessionInfo.txt")',
        'cat("\\n全部分析已复现；表格见 tables/，图件见 figures/\\n")'),
      file.path(pack, "run_all.R"), useBytes = TRUE
    )

    writeLines(
      c(sprintf("# %s", pack_name),
        "",
        "交付包骨架已就绪。文件清单见 `00_客户说明.md`。"),
      file.path(pack, "README.md"), useBytes = TRUE
    )
  }

  # Git ---------------------------------------------------
  if (git) {
    old <- setwd(proj)
    on.exit(setwd(old))
    try(system2("git", c("init", "--quiet")), silent = TRUE)
    try(system2("git", c("add", ".")), silent = TRUE)
    try(system2("git",
                c("commit", "-m", "chore: init project skeleton", "--quiet")),
        silent = TRUE)
  }

  # 完成报告 ----------------------------------------------
  message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
  message("项目 [", name, "] 创建成功")
  message("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
  message("路径：", normalizePath(proj))
  message("类型：", type_name, "  |  模式：", mode)
  message("")
  message("下一步：")
  message("  1. 把原始数据放入 ", file.path(name, "01_data/rawdata/"))
  message("  2. 填写 ", file.path(name, "01_data/README.md"), "（数据字典）")
  message("  3. 锁口径：打开 ", file.path(name, "CLAUDE.md"))
  message("  4. 开始清洗：", file.path(name, "02_code/01_data_cleaning.R"))

  invisible(proj)
}
