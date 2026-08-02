# Create a minimal R or Python consulting delivery package.

create_delivery_pack <- function(name, root = "05_reports", overwrite = FALSE,
                                 language = c("R", "python"),
                                 data_policy = c("reference", "include"),
                                 data_authority = "") {
  language <- match.arg(language)
  data_policy <- match.arg(data_policy)
  if (!nzchar(trimws(name))) stop("交付包名称不能为空")
  if (data_policy == "include" && !nzchar(trimws(data_authority))) {
    stop("data_policy='include' 必须提供 data_authority；未授权时使用 reference")
  }
  if (grepl("(^|[_. -])(v[0-9]+|new|final|latest|最终版|最新版|修改版)([_. -]|$)", name, ignore.case = TRUE)) {
    warning("交付包应使用含义明确且长期不变的名称；日期和轮次写入归档记录")
  }

  pack <- file.path(root, name)
  if (dir.exists(pack) && !overwrite) stop("目录已存在：", pack, "；如需覆盖已知模板请 overwrite = TRUE")
  subdirs <- c("code", "outputs", "run_records", if (data_policy == "include") "data")
  invisible(lapply(file.path(pack, subdirs), dir.create, recursive = TRUE, showWarnings = FALSE))
  invisible(file.create(file.path(pack, subdirs, ".gitkeep")))

  if (language == "R") {
    writeLines(
      c(
        "# 按实际依赖顺序列出需要运行的脚本；不要根据文件名猜测顺序。",
        "RUN_ORDER <- character()"
      ),
      file.path(pack, "code/run_order.R"), useBytes = TRUE
    )
    pipeline <- c(
      '# 请先在 code/run_order.R 中列出实际脚本，再从交付包根目录运行本文件。',
      'if (!file.exists("code/run_order.R")) stop("缺少 code/run_order.R")',
      'source("code/run_order.R", encoding = "UTF-8")',
      'if (!length(RUN_ORDER)) stop("请在 code/run_order.R 中按实际顺序列出需要运行的脚本")',
      'run_id <- paste0(format(Sys.time(), "%Y%m%dT%H%M%S%z"), "_", Sys.getpid())',
      'dir.create("run_records", showWarnings = FALSE)',
      'log_path <- file.path("run_records", paste0(run_id, ".log"))',
      'status <- 0L',
      'for (script in RUN_ORDER) {',
      '  if (!file.exists(script)) stop("缺少声明脚本：", script)',
      '  previous_run_id <- Sys.getenv("EPI_RUN_ID", unset = NA_character_)',
      '  Sys.setenv(EPI_RUN_ID = run_id)',
      '  output <- tryCatch(system2(file.path(R.home("bin"), "Rscript"), c("--vanilla", script), stdout = TRUE, stderr = TRUE), finally = if (is.na(previous_run_id)) Sys.unsetenv("EPI_RUN_ID") else Sys.setenv(EPI_RUN_ID = previous_run_id))',
      '  code <- attr(output, "status"); if (is.null(code)) code <- 0L',
      '  cat("\\n===== ", script, " =====\\n", paste(output, collapse = "\\n"), "\\n", file = log_path, append = TRUE, sep = "")',
      '  if (code != 0L) { status <- as.integer(code); break }',
      '}',
      'writeLines(capture.output(sessionInfo()), file.path("run_records", paste0(run_id, "-environment.txt")), useBytes = TRUE)',
      'run_record <- c("{", paste0("  \\"run_id\\": \\"", run_id, "\\","), paste0("  \\"status\\": \\"", if (status == 0L) "success" else "failed", "\\","), paste0("  \\"exit_code\\": ", status), "}")',
      'writeLines(run_record, file.path("run_records", paste0(run_id, ".json")), useBytes = TRUE)',
      'if (status != 0L) stop("交付包复现失败；见 ", log_path, call. = FALSE)',
      'message("交付包复现完成；运行编号：", run_id)'
    )
    writeLines(pipeline, file.path(pack, "run_pipeline.R"), useBytes = TRUE)
    entry <- "run_pipeline.R"
    command <- "Rscript --vanilla run_pipeline.R"
  } else {
    writeLines(
      c("# List the scripts in the order required to reproduce the package.", "RUN_ORDER = []"),
      file.path(pack, "code/run_order.py"), useBytes = TRUE
    )
    pipeline <- c(
      "from __future__ import annotations", "",
      "from datetime import datetime", "from pathlib import Path", "import importlib.util", "import json", "import os", "import subprocess", "import sys", "",
      "ROOT = Path(__file__).resolve().parent", "spec = importlib.util.spec_from_file_location('run_order', ROOT / 'code/run_order.py')",
      "if spec is None or spec.loader is None: raise SystemExit('cannot load code/run_order.py')",
      "module = importlib.util.module_from_spec(spec)", "spec.loader.exec_module(module)",
      "if not module.RUN_ORDER: raise SystemExit('list the required scripts in code/run_order.py')", "",
      "run_id = f\"{datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')}_{os.getpid()}\"",
      "run_records = ROOT / 'run_records'", "run_records.mkdir(exist_ok=True)", "log_path = run_records / f'{run_id}.log'", "exit_code = 0",
      "environment = dict(os.environ)", "environment['EPI_RUN_ID'] = run_id",
      "with log_path.open('w', encoding='utf-8') as log:",
      "    for relative in module.RUN_ORDER:",
      "        script = ROOT / relative", "        if not script.is_file(): raise SystemExit(f'missing declared script: {relative}')",
      "        completed = subprocess.run([sys.executable, str(script)], cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')",
      "        log.write(f'\\n===== {relative} =====\\n' + completed.stdout)",
      "        if completed.returncode:", "            exit_code = completed.returncode", "            break",
      "(run_records / f'{run_id}-environment.txt').write_text(sys.version + '\\n', encoding='utf-8')",
      "run_record = {'run_id': run_id, 'status': 'success' if exit_code == 0 else 'failed', 'exit_code': exit_code, 'scripts': module.RUN_ORDER}",
      "(run_records / f'{run_id}.json').write_text(json.dumps(run_record, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8')",
      "if exit_code: raise SystemExit(f'package reproduction failed; inspect {log_path.relative_to(ROOT)}')",
      "print(f'package reproduction completed; run ID: {run_id}')"
    )
    writeLines(pipeline, file.path(pack, "run_pipeline.py"), useBytes = TRUE)
    entry <- "run_pipeline.py"
    command <- "python run_pipeline.py"
  }

  writeLines(
    c(
      paste0("# ", name), "",
      "## 交付目的", "",
      "请在正式交付前填写本包用于回答的问题、经授权的收件人和允许用途。", "",
      "## 包内文件", "",
      "- `code/`：完成本次分析所需的脚本及运行顺序。",
      "- `outputs/`：报告、表格、图件或其他交付结果。",
      if (data_policy == "include") "- `data/`：经明确授权且完成本次复现所需的最小数据。" else "- 数据未随包提供；所需文件、获取方式和放置位置必须写入 `DELIVERY_CONTENTS.md`。",
      "- `run_records/`：每次运行的完整日志、环境说明和运行状态。", "",
      "## 运行条件", "",
      "使用 `DELIVERY_CONTENTS.md` 中注明的 R 或 Python 版本及依赖。准备好所需输入后，从本目录运行：", "",
      paste0("```text\n", command, "\n```"), "",
      "运行成功后，结果写入 `outputs/`，相应日志和运行状态写入 `run_records/`。", "",
      "## 输入、授权与限制", "",
      "实际输入文件、SHA-256、分享授权、输出用途和已知限制均记录在 `DELIVERY_CONTENTS.md`。缺少所需输入或兼容运行环境时，不应声称已经完成复现。"
    ),
    file.path(pack, "README.md"), useBytes = TRUE
  )
  writeLines(
    c(
      "# 交付内容与复现说明", "", "## 交付目的与收件人", "",
      "- 交付目的：", "- 经授权的收件人：", "- 本次交付文件夹名称及日期：", "",
      "## 输入数据与授权", "",
      paste0("- 数据提供方式：", if (data_policy == "include") "经授权随包提供" else "不随包提供"),
      paste0("- 授权依据：", if (data_policy == "include") data_authority else "请填写输入文件的获取方式、放置位置及可使用范围"), "",
      "| 输入文件 | 随包提供或放置位置 | SHA-256 | 授权依据 | 使用限制 |",
      "| --- | --- | --- | --- | --- |", "",
      "## 运行方法", "", paste0("- 总运行脚本：`", entry, "`"), "- 已验证的 R 或 Python 版本：", "- 依赖说明文件：", "- 最近一次成功运行的记录：", "",
      "## 交付文件", "", "| 文件 | 生成该文件的脚本 | 使用的结果名称 | 用途 |", "| --- | --- | --- | --- |", "",
      "## 已知限制", "", "-"
    ),
    file.path(pack, "DELIVERY_CONTENTS.md"), useBytes = TRUE
  )
  message("交付包基本结构已创建：", pack, "；数据提供方式：", data_policy)
  invisible(pack)
}

verify_reproducibility <- function(pack_path) {
  stopifnot(dir.exists(pack_path))
  if (file.exists(file.path(pack_path, "run_pipeline.R"))) {
    command <- file.path(R.home("bin"), "Rscript")
    args <- c("--vanilla", "run_pipeline.R")
  } else if (file.exists(file.path(pack_path, "run_pipeline.py"))) {
    command <- Sys.which("python")
    if (!nzchar(command)) stop("缺少 Python 运行时；先询问安装或评估现有 R 环境中的等价实现")
    args <- "run_pipeline.py"
  } else {
    stop("缺少 run_pipeline.R 或 run_pipeline.py")
  }
  old <- setwd(pack_path)
  on.exit(setwd(old), add = TRUE)
  status <- system2(command, args)
  if (status != 0L) stop("复现失败；状态码 ", status)
  invisible(TRUE)
}
