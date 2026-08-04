#!/usr/bin/env Rscript

options(encoding = "UTF-8")

file_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- normalizePath(
  sub("^--file=", "", file_arg[[1]]),
  winslash = "/",
  mustWork = TRUE
)
demo_dir <- dirname(script_path)
repo_root <- normalizePath(file.path(demo_dir, "..", ".."), winslash = "/")
output_dir <- file.path(demo_dir, "output", "pptx")
publication_dir <- file.path(demo_dir, "output", "publication-figures")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

toolkit_path <- file.path(repo_root, "skills", "sysu-ppt", "scripts", "sysu_toolkit.R")
template_path <- file.path(
  repo_root,
  "skills",
  "sysu-ppt",
  "assets",
  "template-公卫学院.pptx"
)
survival_figure <- file.path(publication_dir, "adjusted-survival-paper.png")
model_results_path <- file.path(publication_dir, "cox-forest-results.csv")
output_path <- file.path(output_dir, "presentation-preview.pptx")

required <- c(toolkit_path, template_path, survival_figure, model_results_path)
missing <- required[!file.exists(required)]
if (length(missing)) {
  stop("缺少 PPT 生成输入：", paste(missing, collapse = "；"))
}

source(toolkit_path)

format_p_value <- function(value) {
  ifelse(value < 0.001, "<0.001", sprintf("%.3f", value))
}

model_results <- read.csv(
  model_results_path,
  stringsAsFactors = FALSE,
  check.names = FALSE,
  fileEncoding = "UTF-8"
)
model_table <- data.frame(
  `模型项` = model_results$label,
  `风险比（95% 置信区间）` = model_results$estimate_label,
  `P 值` = format_p_value(model_results$p_value),
  check.names = FALSE
)

ft <- sysu_flextable(
  model_table,
  widths = c(4.8, 3.3, 1.2),
  fsize = 15,
  align = "center"
)
ft <- flextable::align(ft, j = 1, align = "left", part = "all")

ppt <- sysu_init(template_path)
ppt <- sysu_add_cover(
  ppt,
  "固定模拟队列的生存分析",
  "多变量 Cox 回归与调整后生存曲线",
  "演示材料",
  "模拟数据，不构成医学证据"
)
ppt <- sysu_add_image(
  ppt,
  "强化方案组的调整后无事件生存率持续较高",
  survival_figure,
  img_w = 7.9,
  img_h = 4.9,
  caption = "图 1　固定模拟队列中两种治疗方案的调整后无事件生存曲线及 95% 置信区间"
)
ppt <- sysu_add_table(
  ppt,
  "强化方案与较低的无事件风险相关",
  ft,
  note = "数据来源：固定模拟队列的实际 Cox 回归输出；模拟结果仅用于展示可复核的分析与汇报流程。"
)

sysu_save(ppt, output_path, genre = "meeting")
message("已生成 ", normalizePath(output_path, winslash = "/"))
