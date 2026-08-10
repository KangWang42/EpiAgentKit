# Run the project R scripts in order and save an automatic run record.
if (!dir.exists("02_code")) stop("请从项目根运行 run_pipeline.R")

# 数据准备和正式统计分析分别列出；第一项分析前会检查数据就绪状态。
preparation_scripts <- c(
  "02_code/01_data_cleaning.R"
)
analysis_scripts <- character()
scripts <- c(preparation_scripts, analysis_scripts)
readiness_helper <- "02_code/vendored/data_readiness.R"
missing_scripts <- scripts[!file.exists(scripts)]
if (length(analysis_scripts) && !file.exists(readiness_helper)) {
  missing_scripts <- c(missing_scripts, readiness_helper)
}
if (length(missing_scripts)) {
  stop("正式分析脚本缺失：", paste(missing_scripts, collapse = "，"))
}

json_escape <- function(value) {
  value <- gsub("\\\\", "\\\\\\\\", as.character(value))
  value <- gsub('"', '\\\\"', value, fixed = TRUE)
  value <- gsub("\r", "\\\\r", value, fixed = TRUE)
  gsub("\n", "\\\\n", value, fixed = TRUE)
}
json_string <- function(value) paste0('"', json_escape(value), '"')
json_array <- function(values) paste0("[", paste(vapply(values, json_string, character(1)), collapse = ", "), "]")

started <- Sys.time()
run_id <- paste0(format(started, "%Y%m%dT%H%M%S%z"), "_", Sys.getpid())
dir.create("results/runs", recursive = TRUE, showWarnings = FALSE)
log_path <- file.path("results/runs", paste0(run_id, ".log"))
environment_path <- file.path("results/runs", paste0(run_id, "-environment.txt"))
status <- 0L

run_script <- function(script, run_id, args = character()) {
  previous_run_id <- Sys.getenv("EPI_RUN_ID", unset = NA_character_)
  Sys.setenv(EPI_RUN_ID = run_id)
  on.exit(
    if (is.na(previous_run_id)) Sys.unsetenv("EPI_RUN_ID") else Sys.setenv(EPI_RUN_ID = previous_run_id),
    add = TRUE
  )
  system2(
    file.path(R.home("bin"), "Rscript"),
    c("--vanilla", script, args),
    stdout = TRUE,
    stderr = TRUE
  )
}

run_logged_step <- function(script, run_id, args = character(), label = script) {
  output <- run_script(script, run_id, args)
  script_status <- attr(output, "status")
  if (is.null(script_status)) script_status <- 0L
  cat("\n===== ", label, " =====\n", paste(output, collapse = "\n"), "\n",
      file = log_path, append = TRUE, sep = "")
  as.integer(script_status)
}

for (script in preparation_scripts) {
  step_status <- run_logged_step(script, run_id)
  if (step_status != 0L) {
    status <- step_status
    break
  }
}

if (status == 0L && length(analysis_scripts)) {
  step_status <- run_logged_step(
    readiness_helper,
    run_id,
    args = "--check",
    label = "data readiness gate"
  )
  if (step_status != 0L) status <- step_status
}

if (status == 0L) {
  for (script in analysis_scripts) {
    step_status <- run_logged_step(script, run_id)
    if (step_status != 0L) {
      status <- step_status
      break
    }
  }
}

writeLines(capture.output(sessionInfo()), environment_path, useBytes = TRUE)
output_roots <- c("results", "03_tables", "04_figures", "paper", "05_reports")
files <- unlist(lapply(output_roots[dir.exists(output_roots)], function(root) {
  list.files(root, recursive = TRUE, full.names = TRUE, all.files = FALSE)
}), use.names = FALSE)
files <- files[file.exists(files) & !dir.exists(files)]
files <- files[!grepl("^results/runs/", gsub("\\\\", "/", files))]
hashes <- if (length(files)) tools::md5sum(files) else character()
file_lines <- if (length(files)) vapply(seq_along(files), function(index) {
  sprintf("    %s: %s", json_string(gsub("\\\\", "/", files[index])), json_string(unname(hashes[index])))
}, character(1)) else character()
if (length(file_lines) > 1L) file_lines[-length(file_lines)] <- paste0(file_lines[-length(file_lines)], ",")

run_record <- c(
  "{",
  sprintf("  \"run_id\": %s,", json_string(run_id)),
  sprintf("  \"started_at\": %s,", json_string(format(started, "%Y-%m-%dT%H:%M:%S%z"))),
  sprintf("  \"finished_at\": %s,", json_string(format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"))),
  sprintf("  \"status\": %s,", json_string(if (status == 0L) "success" else "failed")),
  sprintf("  \"exit_code\": %d,", status),
  "  \"command\": \"Rscript --vanilla run_pipeline.R\",",
  sprintf("  \"scripts\": %s,", json_array(gsub("\\\\", "/", scripts))),
  sprintf("  \"log\": %s,", json_string(gsub("\\\\", "/", log_path))),
  sprintf("  \"environment\": %s,", json_string(gsub("\\\\", "/", environment_path))),
  "  \"hash_algorithm\": \"md5\",",
  "  \"files\": {",
  file_lines,
  "  }",
  "}"
)
record_path <- file.path("results/runs", paste0(run_id, ".json"))
writeLines(run_record, record_path, useBytes = TRUE)
latest_tmp <- file.path("results/runs", ".latest.json.tmp")
writeLines(run_record, latest_tmp, useBytes = TRUE)
if (file.exists("results/runs/latest.json")) unlink("results/runs/latest.json")
if (!file.rename(latest_tmp, "results/runs/latest.json")) stop("无法更新最近一次运行记录")

if (status != 0L) stop("项目脚本运行失败；请检查 ", log_path, call. = FALSE)
message("项目脚本运行完成；运行编号：", run_id)
