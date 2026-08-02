# Initialize the smallest project structure needed for the selected task type.

init_project <- function(name,
                         type = 1,
                         profile = c("analysis", "paper", "consulting", "teaching", "oneoff"),
                         language = c("r", "python"),
                         root = ".",
                         git = FALSE,
                         overwrite = FALSE,
                         mode = NULL) {
  if (!is.null(mode)) {
    mode <- match.arg(mode, c("research", "consulting"))
    profile <- if (mode == "consulting") "consulting" else "analysis"
    warning("mode 参数只用于兼容旧调用；新调用请使用 profile 指定项目类型")
  }
  profile <- match.arg(profile)
  language <- match.arg(language)
  type_names <- c("cohort", "case_control", "cross_sectional", "rct", "meta", "rwd", "methodology")
  if (is.numeric(type)) {
    if (length(type) != 1L || !type %in% seq_along(type_names)) stop("type 序号无效")
    type_name <- type_names[[type]]
  } else {
    type_name <- match.arg(as.character(type), type_names)
  }
  if (!grepl("^[a-z][a-z0-9_]*$", name)) {
    warning("项目名建议使用小写 snake_case")
  }

  project <- file.path(root, name)
  if (dir.exists(project) && !overwrite) stop("目录已存在：", project, "；如需覆盖已知模板请 overwrite = TRUE")
  dir.create(project, recursive = TRUE, showWarnings = FALSE)
  formal <- profile %in% c("analysis", "paper", "consulting")
  today <- format(Sys.Date(), "%Y-%m-%d")

  skill_roots <- unique(path.expand(c(
    Sys.getenv("EPIAGENTKIT_SKILLS"), Sys.getenv("EPICLAUDE_SKILLS"),
    "~/.claude/skills", "~/.agents/skills", "~/.codex/skills"
  )))
  skill_roots <- skill_roots[nzchar(skill_roots)]
  find_skill_file <- function(skill, relative_path) {
    candidates <- file.path(skill_roots, skill, relative_path)
    found <- candidates[file.exists(candidates)]
    if (!length(found)) stop("缺少必需 skill 文件：", file.path(skill, relative_path))
    found[[1]]
  }
  write_utf8 <- function(lines, relative_path) {
    target <- file.path(project, relative_path)
    dir.create(dirname(target), recursive = TRUE, showWarnings = FALSE)
    writeLines(lines, target, useBytes = TRUE)
  }

  if (formal) {
    dirs <- c(
      "01_data/rawdata", "02_code/vendored", "03_tables", "04_figures",
      "results/derived", "results/runs", "09_backup/archive", "09_backup/workbench"
    )
    if (profile == "paper") dirs <- c(dirs, "paper")
    if (profile == "consulting") dirs <- c(dirs, "05_reports")
  } else if (profile == "teaching") {
    dirs <- c("data", "code", "output")
  } else {
    dirs <- c("input", "code", "output")
  }
  invisible(lapply(file.path(project, dirs), dir.create, recursive = TRUE, showWarnings = FALSE))
  invisible(file.create(file.path(project, dirs, ".gitkeep")))

  if (!formal) {
    write_utf8(
      c(
        paste0("# ", name), "",
        paste0("- 项目类型：", profile),
        paste0("- 使用语言：", language),
        "",
        "只保留本任务需要的输入、代码和输出。输入保持只读；代码实际运行；输出集中保存。"
      ),
      "README.md"
    )
    script_name <- if (language == "r") "code/main.R" else "code/main.py"
    write_utf8(
      if (language == "r") {
        c("# 读取输入、完成本任务并把输出写入 output/。", "message(\"请填入本任务逻辑\")")
      } else {
        c('"""Read the declared input and write the requested output."""', 'print("请填入本任务逻辑")')
      },
      script_name
    )
  } else {
    write_utf8(
      c(
        paste0("# ", name, " 项目规则"), "",
        "本项目继承 EpiAgentKit 全局规则。每轮先判 Q 问答、L 局部产物、P 项目执行或 R 正式发布。", "",
        "## 当前状态", "",
        "- 阶段：方案待确认",
        "- 当前总运行脚本：run_pipeline.R 或 run_pipeline.py",
        "- 当前结果数据文件：尚未由正式分析脚本生成",
        "- 后续待解决事项：见 BACKLOG.md", "",
        "## 已经确认的研究口径", "",
        paste0("- 研究类型：", type_name),
        paste0("- 分析语言：", toupper(language)),
        "- 研究问题或 estimand：",
        "- 数据来源与时间窗：",
        "- 分析集与纳排：",
        "- 暴露或干预、比较和终点：",
        "- 主要方法：", "",
        "改变上述口径前先确认，并把决定或方案偏离写入 DECISIONS.md。运行事实由 results/runs/ 自动记录。"
      ),
      "CLAUDE.md"
    )
    write_utf8(
      c("# Codex 项目指引", "", "开始项目工作前完整读取同目录 CLAUDE.md；本文件不复制项目口径。"),
      "AGENTS.md"
    )
    write_utf8(
      c(
        "# 研究方案", "", "> 状态：草案。确认后再开始正式分析。", "",
        "## 研究问题与设计", "",
        paste0("- 研究设计：", type_name),
        "- 研究问题（PICO/PECO）：",
        "- 主要估计目标：",
        "- 数据来源与研究时间窗：", "",
        "## 研究对象与变量", "",
        "- 目标人群：", "- 纳入标准：", "- 排除标准：",
        "- 暴露或干预与比较：", "- 主要结局与测量时点：", "- 次要结局：", "",
        "## 伦理、注册、数据权限与报告", "",
        "- 伦理审批与知情同意：", "- 注册或预注册：",
        "- 数据访问与共享权限：", "- 适用报告规范：", "",
        "## 版本记录", "", "| 日期 | 版本 | 变更 | 确认责任 |", "| --- | --- | --- | --- |",
        paste0("| ", today, " | 0.1 | 初始化草案 | 待确认 |")
      ),
      "PROTOCOL.md"
    )
    write_utf8(
      c(
        "# 统计分析计划", "", "> 状态：草案。查看主要结果前确认主要分析方法。", "",
        "## 分析目标与分析集", "", "- estimand：", "- 主要与次要假设：", "- 分析集：", "- 主要与次要终点：", "",
        "## 数据处理", "", "- 变量定义与有序水平：见 02_code/conventions", "- 缺失数据：", "- 异常值：", "- 样本量或精度依据：", "",
        "## 统计方法", "", "- 描述统计：", "- 主要模型与效应量：", "- 调整策略：", "- 模型诊断：",
        "- 多重性：", "- 亚组、敏感性与探索边界：", "- 随机种子或切分标识：", "",
        "## 计划确认与方案偏离", "", "- 主要分析确认日期与责任人：", "- 方案偏离：见 DECISIONS.md"
      ),
      "SAP.md"
    )
    write_utf8(
      c(
        "# 方法决策与方案偏离", "",
        "只记录会影响方法、结果解释或方案偏离的决定，不记录普通命令或文件操作。", "",
        "| 日期 | 决定或偏离 | 理由与证据 | 影响范围 | 确认责任 |",
        "| --- | --- | --- | --- | --- |"
      ),
      "DECISIONS.md"
    )
    write_utf8(
      c(
        "# 后续待解决事项", "",
        "只记录无法在当轮解决且需要补充数据、外部资源或用户决定的事项；完成后更新状态，不复制运行历史。", "",
        "| ID | 未决事项 | 需要的材料或决定 | 影响 | 状态 |",
        "| --- | --- | --- | --- | --- |"
      ),
      "BACKLOG.md"
    )
    write_utf8(
      c(
        paste0("# ", name), "",
        paste0("- 项目类型：", profile), paste0("- 研究设计：", type_name), paste0("- 分析语言：", language), "",
        "先确认 PROTOCOL.md 与 SAP.md，再从项目根运行总运行脚本。`results/results.yaml` 由第一次正式分析创建，每次运行的命令、状态、日志和环境信息自动写入 `results/runs/`。",
        "",
        if (language == "r") "```text\nRscript --vanilla run_pipeline.R\n```" else "```text\npython run_pipeline.py\n```"
      ),
      "README.md"
    )
    write_utf8(
      c(
        "# 数据字典", "", "## 来源与权限", "",
        "- 数据集：", "- 权威来源：", "- 时间范围：", "- 获取日期：", "- 访问与共享权限：", "",
        "## 变量", "", "| 变量 | 类型 | 单位或编码 | 定义 | 缺失 |", "| --- | --- | --- | --- | --- |"
      ),
      "01_data/README.md"
    )
    write_utf8(
      c("# 每行一个额外原始数据根。01_data/rawdata 已默认保护。"),
      ".epiagentkit-raw-roots"
    )

    if (language == "r") {
      write_utf8(
        c(
          "ORDERED_LEVELS <- list()", "", "PALETTE <- c(\"#0072B2\", \"#D55E00\", \"#009E73\", \"#CC79A7\")",
          "DIGITS_EST <- 2L", "DIGITS_P <- 3L", "P_FLOOR <- 0.001"
        ),
        "02_code/conventions.R"
      )
      write_utf8(
        c(
          'source("02_code/conventions.R", encoding = "UTF-8")', "",
          "TABLE_REGISTRY <- character()", "FIG_REGISTRY <- character()", "",
          "table_path <- function(stem, ext = \"xlsx\") {",
          "  i <- match(stem, TABLE_REGISTRY)", "  if (is.na(i)) stop(\"未登记 table stem：\", stem)",
          "  path <- sprintf(\"03_tables/Table%d_%s.%s\", i, stem, ext)", "  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)", "  path", "}", "",
          "fig_path <- function(stem, ext = \"png\") {",
          "  i <- match(stem, FIG_REGISTRY)", "  if (is.na(i)) stop(\"未登记 figure stem：\", stem)",
          "  path <- sprintf(\"04_figures/Fig%d_%s.%s\", i, stem, ext)", "  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)", "  path", "}"
        ),
        "02_code/config.R"
      )
      write_utf8(
        c(
          "# 从 01_data/rawdata/ 只读导入，核对键、类型、重复、缺失、范围和样本损失。",
          'source("02_code/config.R", encoding = "UTF-8")',
          'message("数据读取与核对脚本已准备；请填入已经确认的项目处理规则")'
        ),
        "02_code/01_data_cleaning.R"
      )
      helper_sources <- c(
        emit_summary.R = find_skill_file("r-biostats", "scripts/emit_summary.R"),
        fig_setup.R = find_skill_file("publication-figures", "scripts/fig_setup.R")
      )
      pipeline_source <- find_skill_file("project-init", "assets/run_pipeline.R")
      pipeline_target <- file.path(project, "run_pipeline.R")
    } else {
      write_utf8(
        c(
          "ORDERED_LEVELS = {}", "PALETTE = [\"#0072B2\", \"#D55E00\", \"#009E73\", \"#CC79A7\"]",
          "DIGITS_EST = 2", "DIGITS_P = 3", "P_FLOOR = 0.001"
        ),
        "02_code/conventions.py"
      )
      write_utf8(
        c(
          "from pathlib import Path", "", "ROOT = Path(__file__).resolve().parents[1]",
          "TABLE_REGISTRY = []", "FIG_REGISTRY = []", "",
          "def table_path(stem, ext=\"xlsx\"):",
          "    if stem not in TABLE_REGISTRY:", "        raise KeyError(f\"未登记 table stem：{stem}\")",
          "    path = ROOT / \"03_tables\" / f\"Table{TABLE_REGISTRY.index(stem) + 1}_{stem}.{ext}\"",
          "    path.parent.mkdir(parents=True, exist_ok=True)", "    return path", "",
          "def fig_path(stem, ext=\"png\"):",
          "    if stem not in FIG_REGISTRY:", "        raise KeyError(f\"未登记 figure stem：{stem}\")",
          "    path = ROOT / \"04_figures\" / f\"Fig{FIG_REGISTRY.index(stem) + 1}_{stem}.{ext}\"",
          "    path.parent.mkdir(parents=True, exist_ok=True)", "    return path"
        ),
        "02_code/config.py"
      )
      write_utf8(
        c(
          '"""Read raw inputs without modifying them and create declared derived data."""',
          'print("数据读取与核对脚本已准备；请填入已经确认的项目处理规则")'
        ),
        "02_code/01_data_cleaning.py"
      )
      helper_sources <- c(emit_summary.py = find_skill_file("python-biostats", "scripts/emit_summary.py"))
      pipeline_source <- find_skill_file("project-init", "assets/run_pipeline.py")
      pipeline_target <- file.path(project, "run_pipeline.py")
    }
    copied <- file.copy(unname(helper_sources), file.path(project, "02_code/vendored", names(helper_sources)), overwrite = TRUE)
    if (!all(copied)) stop("项目所需的共用函数复制失败")
    if (!file.copy(pipeline_source, pipeline_target, overwrite = TRUE)) stop("总运行脚本模板复制失败")

    json_escape <- function(value) {
      value <- gsub("\\\\", "\\\\\\\\", value)
      gsub('"', '\\\\"', value, fixed = TRUE)
    }
    category_roots <- unique(vapply(strsplit(dirs, "/", fixed = TRUE), `[[`, character(1), 1L))
    roles <- list(
      `01_data` = c("biostat-principles", "raw data boundary", "verified source", "analysis scripts"),
      `02_code` = c(if (language == "r") "r-biostats" else "python-biostats", "analysis source", "analysis workflow", "run_pipeline"),
      `03_tables` = c("r-biostats", "statistical tables", "analysis scripts", "paper report delivery"),
      `04_figures` = c("publication-figures", "statistical figures", "figure scripts", "paper report delivery"),
      results = c(if (language == "r") "r-biostats" else "python-biostats", "derived results and run records", "run_pipeline", "files that use project results"),
      `09_backup` = c("project-init", "formal archive and isolated workbench", "scoped workflows", "recovery and validation"),
      paper = c("academic-publishing", "manuscript materials", "publishing workflow", "submission"),
      `05_reports` = c("consulting-delivery", "delivery packages", "delivery workflow", "external reader")
    )
    category_lines <- vapply(category_roots, function(path) {
      role <- roles[[path]]
      sprintf(
        '    {"path": "%s", "owner": "%s", "purpose": "%s", "producer": "%s", "consumers": ["%s"], "lifecycle": "active"}',
        json_escape(path), json_escape(role[[1]]), json_escape(role[[2]]), json_escape(role[[3]]), json_escape(role[[4]])
      )
    }, character(1))
    if (length(category_lines) > 1L) category_lines[-length(category_lines)] <- paste0(category_lines[-length(category_lines)], ",")
    artifact_lines <- c(
      '    {"class": "result_data_file", "pattern": "results/results.yaml", "producer": "analysis or confirmed-result import script", "consumers": ["tables", "figures", "paper", "reports"]},',
      '    {"class": "run_record", "pattern": "results/runs/*.json", "producer": "run_pipeline", "consumers": ["validation", "formal release review"]},',
      '    {"class": "statistical_table", "pattern": "03_tables/*", "producer": "registered analysis script", "consumers": ["paper", "reports", "delivery"]},',
      '    {"class": "statistical_figure", "pattern": "04_figures/*", "producer": "registered figure script", "consumers": ["paper", "reports", "delivery"]}'
    )
    if (profile == "paper") artifact_lines <- c(artifact_lines, ',    {"class": "manuscript", "pattern": "paper/*", "producer": "academic-publishing", "consumers": ["submission"]}')
    if (profile == "consulting") artifact_lines <- c(artifact_lines, ',    {"class": "delivery_package", "pattern": "05_reports/*", "producer": "consulting-delivery", "consumers": ["authorized recipient"]}')
    write_utf8(
      c(
        "{", '  "schema_version": 2,', '  "policy": "directory-and-artifact-types",',
        sprintf('  "profile": "%s",', profile), '  "categories": [', category_lines, "  ],",
        '  "artifact_classes": [', artifact_lines, "  ]", "}"
      ),
      ".epiagentkit-layout.json"
    )
  }

  write_utf8(
    if (formal) {
      c(
        "01_data/rawdata/*", "!01_data/rawdata/.gitkeep", "!01_data/README.md", "",
        "results/derived/*", "!results/derived/.gitkeep", "results/runs/*.log", "results/runs/*-environment.txt", "",
        if (language == "r") c(".Rproj.user/", ".Rhistory", ".RData") else c("__pycache__/", "*.py[cod]", ".pytest_cache/"),
        ".DS_Store", "Thumbs.db", "~$*", "*.tmp", "*.bak"
      )
    } else {
      c(if (profile == "teaching") "data/private/*" else "input/private/*", "__pycache__/", ".Rhistory", ".DS_Store", "Thumbs.db", "~$*")
    },
    ".gitignore"
  )

  if (formal && language == "r") {
    write_utf8(
      c(
        "Version: 1.0", "", "RestoreWorkspace: No", "SaveWorkspace: No", "AlwaysSaveHistory: No", "",
        "EnableCodeIndexing: Yes", "UseSpacesForTab: Yes", "NumSpacesForTab: 2", "Encoding: UTF-8",
        "AutoAppendNewline: Yes", "StripTrailingWhitespace: Yes", "LineEndingConversion: Posix"
      ),
      paste0(name, ".Rproj")
    )
  }

  git_state <- "disabled"
  git_bin <- unname(Sys.which("git"))
  if (isTRUE(git) && !nzchar(git_bin)) {
    git_state <- "unavailable"
  } else if (isTRUE(git)) {
    result <- system2(git_bin, c("-C", project, "init", "--quiet"), stdout = TRUE, stderr = TRUE)
    status <- attr(result, "status")
    git_state <- if (is.null(status) || identical(as.integer(status), 0L)) "initialized" else "failed"
  }

  message("项目已创建：", normalizePath(project, winslash = "/", mustWork = TRUE))
  message("项目类型：", profile, "；语言：", language, "；Git：", git_state)
  if (formal) {
    message("下一步：确认 PROTOCOL.md 与 SAP.md；从项目根运行 ", basename(pipeline_target))
    message("results/results.yaml 将由第一次正式分析创建，请勿直接编辑。")
  } else {
    message("下一步：填入 ", script_name, " 并只验证本任务需要的输出。")
  }
  invisible(project)
}
