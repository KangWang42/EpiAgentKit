# Write and validate the machine-readable data-readiness state for a formal project.

DATA_READINESS_PATH <- "results/derived/data-readiness.json"

.readiness_json_escape <- function(value) {
  value <- gsub("\\\\", "\\\\\\\\", as.character(value))
  value <- gsub('"', '\\\\"', value, fixed = TRUE)
  value <- gsub("\r", "\\\\r", value, fixed = TRUE)
  gsub("\n", "\\\\n", value, fixed = TRUE)
}

.readiness_json_string <- function(value) {
  paste0('"', .readiness_json_escape(value), '"')
}

.readiness_relative_path <- function(value, field, must_exist = FALSE) {
  if (length(value) != 1L || is.na(value) || !nzchar(trimws(value))) {
    stop(field, " 必须是非空项目相对路径", call. = FALSE)
  }
  normalized <- gsub("\\\\", "/", trimws(value))
  parts <- strsplit(normalized, "/", fixed = TRUE)[[1]]
  if (grepl("^(?:[A-Za-z]:/|/)", normalized) || any(parts == "..")) {
    stop(field, " 必须位于项目内且不能包含 ..", call. = FALSE)
  }
  normalized <- sub("^\\./", "", normalized)
  if (grepl('["\r\n]', normalized)) {
    stop(field, " 包含不支持的控制字符", call. = FALSE)
  }
  if (must_exist && !file.exists(normalized)) {
    stop(field, " 不存在：", normalized, call. = FALSE)
  }
  normalized
}

.readiness_text <- function(state_path) {
  if (!file.exists(state_path)) {
    stop("缺少数据就绪状态：", state_path, call. = FALSE)
  }
  paste(readLines(state_path, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
}

.readiness_string_field <- function(text, field, nullable = FALSE) {
  pattern <- paste0('"', field, '"[[:space:]]*:[[:space:]]*"([^"\\r\\n]*)"')
  matched <- regexec(pattern, text, perl = TRUE)
  values <- regmatches(text, matched)[[1]]
  if (length(values) >= 2L) return(values[[2]])
  if (nullable && grepl(paste0('"', field, '"[[:space:]]*:[[:space:]]*null'), text, perl = TRUE)) {
    return(NA_character_)
  }
  stop("数据就绪状态缺少有效字段：", field, call. = FALSE)
}

.readiness_integer_field <- function(text, field) {
  pattern <- paste0('"', field, '"[[:space:]]*:[[:space:]]*([0-9]+)')
  matched <- regexec(pattern, text, perl = TRUE)
  values <- regmatches(text, matched)[[1]]
  if (length(values) < 2L) stop("数据就绪状态缺少有效字段：", field, call. = FALSE)
  as.integer(values[[2]])
}

write_data_readiness <- function(status = c("pending_review", "analysis_ready"),
                                 authoritative_input,
                                 input_format,
                                 input_locator,
                                 unresolved_issues,
                                 producer,
                                 decision_source = NULL,
                                 run_id = Sys.getenv("EPI_RUN_ID", unset = ""),
                                 state_path = DATA_READINESS_PATH) {
  status <- match.arg(status)
  unresolved_issues <- suppressWarnings(as.integer(unresolved_issues))
  if (length(unresolved_issues) != 1L || is.na(unresolved_issues) || unresolved_issues < 0L) {
    stop("unresolved_issues 必须是非负整数", call. = FALSE)
  }
  if (status == "analysis_ready" && unresolved_issues != 0L) {
    stop("analysis_ready 要求阻断性未决项为 0", call. = FALSE)
  }
  authoritative_input <- .readiness_relative_path(
    authoritative_input, "authoritative_input", must_exist = TRUE
  )
  producer <- .readiness_relative_path(producer, "producer", must_exist = TRUE)
  state_path <- .readiness_relative_path(state_path, "state_path", must_exist = FALSE)
  if (length(input_format) != 1L || is.na(input_format) || !nzchar(trimws(input_format))) {
    stop("input_format 必须明确", call. = FALSE)
  }
  if (length(input_locator) != 1L || is.na(input_locator) || !nzchar(trimws(input_locator))) {
    stop("input_locator 必须明确；单表文件使用 file", call. = FALSE)
  }
  if (grepl('["\r\n]', input_format) || grepl('["\r\n]', input_locator)) {
    stop("input_format 或 input_locator 包含不支持的字符", call. = FALSE)
  }
  if (status == "analysis_ready" && !nzchar(trimws(run_id))) {
    stop("analysis_ready 必须由带运行编号的正式数据准备脚本生成", call. = FALSE)
  }
  decision_value <- "null"
  if (!is.null(decision_source) && length(decision_source) && !is.na(decision_source) && nzchar(trimws(decision_source))) {
    decision_source <- .readiness_relative_path(
      decision_source, "decision_source", must_exist = status == "analysis_ready"
    )
    decision_value <- .readiness_json_string(decision_source)
  }
  input_hash <- unname(tools::md5sum(authoritative_input))
  if (is.na(input_hash) || !nzchar(input_hash)) stop("无法计算权威分析输入哈希", call. = FALSE)
  generated_at <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z")
  lines <- c(
    "{",
    '  "schema_version": 1,',
    paste0('  "status": ', .readiness_json_string(status), ","),
    paste0('  "authoritative_input": ', .readiness_json_string(authoritative_input), ","),
    paste0('  "input_format": ', .readiness_json_string(trimws(input_format)), ","),
    paste0('  "input_locator": ', .readiness_json_string(trimws(input_locator)), ","),
    paste0('  "unresolved_issues": ', unresolved_issues, ","),
    paste0('  "producer": ', .readiness_json_string(producer), ","),
    paste0('  "decision_source": ', decision_value, ","),
    paste0('  "run_id": ', .readiness_json_string(trimws(run_id)), ","),
    '  "hash_algorithm": "md5",',
    paste0('  "input_hash": ', .readiness_json_string(input_hash), ","),
    paste0('  "generated_at": ', .readiness_json_string(generated_at)),
    "}"
  )
  dir.create(dirname(state_path), recursive = TRUE, showWarnings = FALSE)
  temporary <- paste0(state_path, ".", Sys.getpid(), ".tmp")
  writeLines(lines, temporary, useBytes = TRUE)
  if (!file.copy(temporary, state_path, overwrite = TRUE)) {
    unlink(temporary)
    stop("无法更新数据就绪状态：", state_path, call. = FALSE)
  }
  unlink(temporary)
  invisible(state_path)
}

read_data_readiness <- function(state_path = DATA_READINESS_PATH) {
  state_path <- .readiness_relative_path(state_path, "state_path", must_exist = TRUE)
  text <- .readiness_text(state_path)
  schema_version <- .readiness_integer_field(text, "schema_version")
  if (!identical(schema_version, 1L)) stop("不支持的数据就绪状态版本", call. = FALSE)
  list(
    status = .readiness_string_field(text, "status"),
    authoritative_input = .readiness_string_field(text, "authoritative_input"),
    input_format = .readiness_string_field(text, "input_format"),
    input_locator = .readiness_string_field(text, "input_locator"),
    unresolved_issues = .readiness_integer_field(text, "unresolved_issues"),
    producer = .readiness_string_field(text, "producer"),
    decision_source = .readiness_string_field(text, "decision_source", nullable = TRUE),
    run_id = .readiness_string_field(text, "run_id"),
    hash_algorithm = .readiness_string_field(text, "hash_algorithm"),
    input_hash = .readiness_string_field(text, "input_hash"),
    generated_at = .readiness_string_field(text, "generated_at")
  )
}

assert_data_readiness <- function(state_path = DATA_READINESS_PATH) {
  state <- read_data_readiness(state_path)
  if (!identical(state$status, "analysis_ready")) {
    stop("数据尚未达到 analysis_ready：", state$status, call. = FALSE)
  }
  if (!identical(state$unresolved_issues, 0L)) {
    stop("仍有阻断性未决项：", state$unresolved_issues, call. = FALSE)
  }
  input_path <- .readiness_relative_path(
    state$authoritative_input, "authoritative_input", must_exist = TRUE
  )
  .readiness_relative_path(state$producer, "producer", must_exist = TRUE)
  if (!is.na(state$decision_source)) {
    .readiness_relative_path(state$decision_source, "decision_source", must_exist = TRUE)
  }
  if (!identical(state$hash_algorithm, "md5")) {
    stop("R 数据就绪检查只接受 md5 状态记录", call. = FALSE)
  }
  actual_hash <- unname(tools::md5sum(input_path))
  if (!identical(actual_hash, state$input_hash)) {
    stop("权威分析输入已在状态生成后改变：", input_path, call. = FALSE)
  }
  if (!nzchar(trimws(state$run_id))) stop("数据就绪状态缺少运行编号", call. = FALSE)
  current_run_id <- Sys.getenv("EPI_RUN_ID", unset = "")
  if (nzchar(current_run_id) && !identical(current_run_id, state$run_id)) {
    stop("数据就绪状态不是本次数据准备生成", call. = FALSE)
  }
  state
}

analysis_source <- function(state_path = DATA_READINESS_PATH) {
  state <- assert_data_readiness(state_path)
  list(
    path = state$authoritative_input,
    format = state$input_format,
    locator = state$input_locator
  )
}

analysis_input <- function(state_path = DATA_READINESS_PATH) {
  analysis_source(state_path)$path
}

if (sys.nframe() == 0L) {
  args <- commandArgs(trailingOnly = TRUE)
  if (!identical(args, "--check")) stop("用法：Rscript --vanilla data_readiness.R --check", call. = FALSE)
  state <- assert_data_readiness()
  message("数据就绪检查通过：", state$authoritative_input)
}
