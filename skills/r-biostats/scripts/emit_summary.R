# Read and write the second-version EpiAgentKit result data file.
suppressWarnings(suppressMessages(library(yaml)))

`%||%` <- function(a, b) if (is.null(a)) b else a
.cfg <- function(name, default) if (exists(name, inherits = TRUE)) get(name, inherits = TRUE) else default
.digits_est <- function() .cfg("DIGITS_EST", 2L)
.digits_p <- function() .cfg("DIGITS_P", 3L)
.p_floor <- function() .cfg("P_FLOOR", 0.001)
.minus <- function(value) gsub("-", "−", value, fixed = TRUE)

fmt_num <- function(value, digits = .digits_est()) {
  if (is.null(value) || is.na(value)) return(NA_character_)
  .minus(formatC(round(value, digits), format = "f", digits = digits))
}

fmt_p <- function(value, digits = .digits_p(), floor = .p_floor()) {
  if (is.null(value) || is.na(value)) return(NA_character_)
  if (value < floor) {
    paste0("P < ", formatC(floor, format = "f", digits = digits))
  } else {
    paste0("P = ", formatC(round(value, digits), format = "f", digits = digits))
  }
}

.render_one <- function(est, ci_low, ci_high, p, unit, digits, style) {
  has_est <- !is.null(est) && !is.na(est)
  has_ci <- !is.null(ci_low) && !is.na(ci_low) && !is.null(ci_high) && !is.na(ci_high)
  has_p <- !is.null(p) && !is.na(p)
  estimate <- if (has_est) fmt_num(est, digits) else NA_character_
  if (has_est && nzchar(unit)) estimate <- paste0(estimate, if (unit == "%") "" else " ", unit)
  interval <- if (has_ci) {
    if (style == "zh") {
      sprintf("（95%% CI：%s，%s）", fmt_num(ci_low, digits), fmt_num(ci_high, digits))
    } else {
      sprintf(" (95%% CI: %s, %s)", fmt_num(ci_low, digits), fmt_num(ci_high, digits))
    }
  } else NA_character_
  p_value <- if (has_p) fmt_p(p) else NA_character_
  full <- paste0(if (has_est) estimate else "", if (has_ci) interval else "")
  if (has_p) full <- paste0(full, if (nzchar(full)) if (style == "zh") "，" else "; " else "", p_value)
  Filter(Negate(is.na), list(estimate = estimate, interval = interval, p_value = p_value, full = full))
}

.load_manifest <- function(path) {
  if (!file.exists(path)) return(list(meta = list(schema_version = 2L), results = list()))
  value <- yaml::read_yaml(path)
  if (!is.list(value)) stop("results.yaml 顶层内容必须由带名称的字段组成：", path)
  value$meta <- value$meta %||% list()
  value$results <- value$results %||% list()
  if (!is.list(value$meta) || !is.list(value$results)) stop("results.yaml 的 meta 与 results 必须由带名称的字段组成")
  value
}

.atomic_write_yaml <- function(document, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  temporary <- tempfile(pattern = ".results-", tmpdir = dirname(path), fileext = ".yaml")
  backup <- tempfile(pattern = ".results-backup-", tmpdir = dirname(path), fileext = ".yaml")
  on.exit(unlink(c(temporary, backup), force = TRUE), add = TRUE)
  yaml::write_yaml(document, temporary)
  if (!file.exists(path)) {
    if (!file.rename(temporary, path)) stop("无法写入完整的结果数据文件：", path)
    return(invisible(path))
  }
  if (file.rename(temporary, path)) return(invisible(path))
  if (!file.rename(path, backup)) stop("无法暂存原有结果数据文件：", path)
  if (!file.rename(temporary, path)) {
    file.rename(backup, path)
    stop("结果数据文件替换失败，已恢复原文件：", path)
  }
  unlink(backup, force = TRUE)
  invisible(path)
}

.as_paths <- function(value) {
  if (is.null(value)) return(character())
  value <- as.character(value)
  value <- value[nzchar(trimws(value))]
  gsub("\\\\", "/", value)
}

.display_text <- function(value) {
  if (is.null(value) || length(value) != 1L || is.na(value)) return("")
  trimws(as.character(value))
}

add_result <- function(path, key, producer, source, analysis_set, run_id,
                       input = NULL, input_hash = "", consumers = NULL,
                       label = "", est = NA, ci_low = NA, ci_high = NA,
                       p = NA, unit = "", section = "结果",
                       digits = .digits_est(), style = "zh",
                       term_label = "", short_label = "",
                       scale_label = "", change_definition = "") {
  if (!style %in% c("zh", "en")) stop("style 必须为 zh 或 en")
  required <- c(key = key, producer = producer, source = source,
                analysis_set = analysis_set, run_id = run_id)
  missing <- names(required)[!nzchar(trimws(required))]
  inputs <- .as_paths(input)
  if (!length(inputs) && !nzchar(trimws(input_hash))) missing <- c(missing, "input_or_input_hash")
  if (length(missing)) stop("缺少必要的结果来源信息：", paste(missing, collapse = ", "))

  document <- .load_manifest(path)
  schema <- document$meta$schema_version
  if (length(document$results) && !is.null(schema) && !identical(as.integer(schema), 2L)) {
    stop("旧版 results.yaml 只能读取；新结果请按第 2 版结构写入 results/results.yaml")
  }
  display <- .render_one(est, ci_low, ci_high, p, unit, digits, style)
  presentation <- list(
    term_label = term_label,
    short_label = short_label,
    scale_label = scale_label,
    change_definition = change_definition
  )
  for (name in names(presentation)) {
    value <- .display_text(presentation[[name]])
    if (nzchar(value)) display[[name]] <- value
  }
  provenance <- list(
    producer = gsub("\\\\", "/", producer), source = source,
    input = inputs, analysis_set = analysis_set, run_id = run_id
  )
  if (nzchar(trimws(input_hash))) provenance$input_hash <- trimws(input_hash)
  document$results[[key]] <- list(
    label = label, section = section,
    estimate = list(value = est, ci_low = ci_low, ci_high = ci_high, p_value = p, unit = unit),
    display = display, provenance = provenance, consumers = .as_paths(consumers)
  )
  document$meta$schema_version <- 2L
  document$meta$updated_at <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z")
  .atomic_write_yaml(document, path)
  invisible(display$full)
}

.display <- function(item) {
  if (!is.null(item$display)) return(item$display)
  rendered <- item$rendered
  if (is.null(rendered)) stop("结果缺少 display/rendered")
  list(estimate = rendered$est, interval = rendered$ci,
       p_value = rendered$p, full = rendered$full)
}

val <- function(path, key, which = "full") {
  document <- .load_manifest(path)
  if (is.null(document$results[[key]])) stop("results.yaml 中没有名为 ", key, " 的结果")
  value <- .display(document$results[[key]])[[which]]
  if (is.null(value)) stop("键 ", key, " 无 display.", which)
  value
}

render_summary_md <- function(path, output) {
  document <- .load_manifest(path)
  lines <- c("# 结果汇总", "", "> 本文件根据 results/results.yaml 自动生成，仅用于核对；如需修改数字，请回到实际生成结果的分析脚本。", "")
  if (!length(document$results)) lines <- c(lines, "暂无结果。")
  sections <- unique(vapply(document$results, function(item) item$section %||% "结果", character(1)))
  for (section in sections) {
    lines <- c(lines, paste0("## ", section), "")
    for (key in names(document$results)) {
      item <- document$results[[key]]
      if (!identical(item$section %||% "结果", section)) next
      provenance <- item$provenance %||% list()
      producer <- provenance$producer %||% item$source %||% "未记录"
      run_id <- provenance$run_id %||% "legacy"
      lines <- c(lines, sprintf("- **%s**（`%s`）：%s（生成脚本：`%s`；运行编号：`%s`）",
                                item$label %||% key, key, .display(item)$full, producer, run_id))
    }
    lines <- c(lines, "")
  }
  dir.create(dirname(output), recursive = TRUE, showWarnings = FALSE)
  temporary <- tempfile(pattern = paste0(".", basename(output), "-"), tmpdir = dirname(output))
  on.exit(unlink(temporary, force = TRUE), add = TRUE)
  writeLines(lines, temporary, useBytes = TRUE)
  if (file.exists(output)) unlink(output)
  if (!file.rename(temporary, output)) stop("无法写入自动生成的结果摘要：", output)
  invisible(output)
}
