# Run the project R scripts in order and save an automatic run record.
if (!dir.exists("02_code")) stop("请从项目根运行 run_pipeline.R")

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
scripts <- sort(list.files("02_code", pattern = "^[0-9]{2}_.*\\.R$", full.names = TRUE))
status <- 0L

run_script <- function(script, run_id) {
  previous_run_id <- Sys.getenv("EPI_RUN_ID", unset = NA_character_)
  Sys.setenv(EPI_RUN_ID = run_id)
  on.exit(
    if (is.na(previous_run_id)) Sys.unsetenv("EPI_RUN_ID") else Sys.setenv(EPI_RUN_ID = previous_run_id),
    add = TRUE
  )
  system2(
    file.path(R.home("bin"), "Rscript"),
    c("--vanilla", script),
    stdout = TRUE,
    stderr = TRUE
  )
}

for (script in scripts) {
  output <- run_script(script, run_id)
  script_status <- attr(output, "status")
  if (is.null(script_status)) script_status <- 0L
  cat("\n===== ", script, " =====\n", paste(output, collapse = "\n"), "\n",
      file = log_path, append = TRUE, sep = "")
  if (script_status != 0L) {
    status <- as.integer(script_status)
    break
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
