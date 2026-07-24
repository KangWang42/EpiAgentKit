# ============================================================
# consulting_scaffold.R
# 创建 R / Python 统计咨询交付包骨架
# ============================================================

create_delivery_pack <- function(name, root = "05_reports", overwrite = FALSE,
                                 language = c("R", "python")) {
  language <- match.arg(language)
  if (!grepl("^结果-\\d+-\\d+", name)) {
    warning("建议命名为 '结果-M-D[-主题]' 格式，例如 '结果-4-20-训练测试集'")
  }

  pack <- file.path(root, name)
  if (dir.exists(pack) && !overwrite) {
    stop("目录已存在：", pack, "；如需覆盖请 overwrite = TRUE")
  }

  subdirs <- c("data", "code", "results", "tables", "figures")
  invisible(lapply(
    file.path(pack, subdirs),
    dir.create, recursive = TRUE, showWarnings = FALSE
  ))
  invisible(file.create(file.path(pack, subdirs, ".gitkeep")))

  if (language == "R") {
    writeLines(
      c("# 交付包口径常量；从主流程 conventions.R 派生后再交付",
        "ORDERED_LEVELS <- list()",
        "PALETTE <- c(\"#00468B\", \"#ED0000\", \"#42B540\", \"#0099B4\")",
        "DIGITS_EST <- 2L",
        "DIGITS_P <- 3L",
        "P_FLOOR <- 0.001"),
      file.path(pack, "code/conventions.R"), useBytes = TRUE
    )
    writeLines(
      c('source("code/conventions.R", encoding = "UTF-8")',
        "TABLE_REGISTRY <- character()",
        "FIG_REGISTRY <- character()",
        "table_path <- function(stem) {",
        "  i <- match(stem, TABLE_REGISTRY)",
        "  if (is.na(i)) stop(\"stem 不在交付包 table registry：\", stem)",
        "  sprintf(\"tables/Table%d_%s.xlsx\", i, stem)",
        "}",
        "fig_path <- function(stem, ext = \"png\") {",
        "  i <- match(stem, FIG_REGISTRY)",
        "  if (is.na(i)) stop(\"stem 不在交付包 figure registry：\", stem)",
        "  sprintf(\"figures/Fig%d_%s.%s\", i, stem, ext)",
        "}"),
      file.path(pack, "code/config.R"), useBytes = TRUE
    )
    run_all <- c(
      "# ============================================================",
      paste0("# ", name, " · 一键复现脚本"),
      "# 使用方法：在 RStudio 将工作目录设为本文件目录后运行全文",
      "# ============================================================",
      "",
      'if (!file.exists("run_all.R")) {',
      '  stop("工作目录不对。请把工作目录设为 run_all.R 所在目录")',
      "}",
      "",
      'if (getRversion() < "4.2.0") warning("建议使用 R >= 4.2.0")',
      "",
      "required_pkgs <- character()  # 按实际脚本填写，不猜依赖",
      "missing_pkgs <- setdiff(required_pkgs, rownames(installed.packages()))",
      "if (length(missing_pkgs) > 0) {",
      '  stop("缺少依赖：", paste(missing_pkgs, collapse = ", "))',
      "}",
      "",
      'source("code/config.R", encoding = "UTF-8")',
      'scripts <- list.files("code", pattern = "^[0-9]{2}_.*\\\\.R$", full.names = TRUE) |> sort()',
      "# 如脚本含随机过程，由对应脚本按 SAP 固定并记录 seed；入口不无条件重置。",
      "for (script in scripts) {",
      '  message("执行：", script)',
      '  source(script, encoding = "UTF-8", echo = FALSE)',
      "}",
      'writeLines(capture.output(sessionInfo()), "environment.txt")',
      'message("全部分析已复现完成；表格见 tables/，图件见 figures/")'
    )
    writeLines(run_all, file.path(pack, "run_all.R"), useBytes = TRUE)
    entry <- "run_all.R"
    reproduce <- "在 RStudio 打开 `run_all.R`，把工作目录设为本文件所在目录后运行全文。"
  } else {
    writeLines(
      c("# 交付包口径常量；从主流程 conventions.py 派生后再交付",
        "ORDERED_LEVELS = {}",
        "PALETTE = [\"#00468B\", \"#ED0000\", \"#42B540\", \"#0099B4\"]",
        "DIGITS_EST = 2",
        "DIGITS_P = 3",
        "P_FLOOR = 0.001"),
      file.path(pack, "code/conventions.py"), useBytes = TRUE
    )
    writeLines(
      c("from pathlib import Path",
        "",
        "ROOT = Path(__file__).resolve().parents[1]",
        "TABLE_REGISTRY = []",
        "FIG_REGISTRY = []",
        "",
        "def table_path(stem):",
        "    if stem not in TABLE_REGISTRY:",
        "        raise ValueError(f\"stem 不在交付包 table registry：{stem}\")",
        "    return ROOT / \"tables\" / f\"Table{TABLE_REGISTRY.index(stem) + 1}_{stem}.xlsx\"",
        "",
        "def fig_path(stem, ext=\"png\"):",
        "    if stem not in FIG_REGISTRY:",
        "        raise ValueError(f\"stem 不在交付包 figure registry：{stem}\")",
        "    return ROOT / \"figures\" / f\"Fig{FIG_REGISTRY.index(stem) + 1}_{stem}.{ext}\""),
      file.path(pack, "code/config.py"), useBytes = TRUE
    )
    run_all <- c(
      "from __future__ import annotations",
      "",
      "import os",
      "import runpy",
      "import subprocess",
      "import sys",
      "from pathlib import Path",
      "",
      "ROOT = Path(__file__).resolve().parent",
      "os.chdir(ROOT)",
      "scripts = sorted((ROOT / \"code\").glob(\"[0-9][0-9]_*.py\"))",
      "for script in scripts:",
      "    print(f\"执行：{script.relative_to(ROOT)}\")",
      "    runpy.run_path(str(script), run_name=\"__main__\")",
      "",
      "environment = [sys.version, \"\", \"pip freeze:\"]",
      "freeze = subprocess.run(",
      "    [sys.executable, \"-m\", \"pip\", \"freeze\"],",
      "    check=True, capture_output=True, text=True",
      ").stdout",
      "(ROOT / \"environment.txt\").write_text(\"\\n\".join(environment) + freeze, encoding=\"utf-8\")",
      "print(\"全部分析已复现完成；表格见 tables/，图件见 figures/\")"
    )
    writeLines(run_all, file.path(pack, "run_all.py"), useBytes = TRUE)
    writeLines(
      c("# 按主流程实际锁定依赖；不得凭模板猜包或版本。"),
      file.path(pack, "requirements.txt"), useBytes = TRUE
    )
    entry <- "run_all.py"
    reproduce <- paste0(
      "使用已准备且兼容的 Python 隔离环境运行 `python run_all.py`。",
      "若环境或依赖缺失，请根据 `requirements.txt` 自行准备；",
      "本交付包不会创建环境，也不会安装或升级运行时与依赖。"
    )
  }

  writeLines(
    c("# 文件清单",
      "",
      "| 文件 | 内容 |",
      "|------|------|",
      "| `01_方法与结果.docx` | 方法、结果与结论（图表嵌入正文） |",
      sprintf("| `%s` | 一键复现全部分析 |", entry),
      "| `data/` | 分析用数据；填充后逐文件列出 |",
      "| `code/` | 分析脚本与口径/registry；填充后逐文件列出 |",
      "| `results/` | 自动生成的中间数据 |",
      "| `tables/` | 最终表；填充后逐文件列出 |",
      "| `figures/` | 最终图；填充后逐文件列出 |",
      "",
      paste0("复现：", reproduce)),
    con = file.path(pack, "00_客户说明.md"),
    useBytes = TRUE
  )
  writeLines(
    c(paste0("# ", name),
      "",
      "本交付包的文件清单见 `00_客户说明.md`。",
      "",
      paste0("复现方法：", reproduce)),
    file.path(pack, "README.md"),
    useBytes = TRUE
  )

  message("交付包骨架已建：", pack)
  message("  语言：", language, "；复现入口：", entry)
  message("  下一步：把数据放入 data/、脚本放入 code/、填 00_客户说明.md")
  invisible(pack)
}

verify_reproducibility <- function(pack_path) {
  stopifnot(dir.exists(pack_path))
  old <- setwd(pack_path)
  on.exit(setwd(old), add = TRUE)

  if (file.exists("run_all.R")) {
    command <- file.path(R.home("bin"), "Rscript")
    args <- c("--vanilla", "-e", 'source("run_all.R")')
  } else if (file.exists("run_all.py")) {
    command <- Sys.which("python")
    if (!nzchar(command)) stop("找不到 python；请在目标虚拟环境中运行复现检查")
    args <- "run_all.py"
  } else {
    stop("缺少 run_all.R 或 run_all.py")
  }

  message("在隔离进程中测试复现...")
  status <- system2(command, args)
  if (status != 0) {
    stop("复现失败；状态码 ", status, "；请检查路径、依赖与脚本顺序")
  }
  if (!file.exists("environment.txt")) {
    warning("复现入口未生成 environment.txt")
  }
  message("复现通过")
  invisible(TRUE)
}
