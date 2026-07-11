# ============================================================
# 结果单一真源助手（r-biostats / P0-A1）
# 定位：数字在此**渲染一次**写入 results.yaml（raw 原始分量 + rendered 成品串）；
#       下游论文/报告/PPT 一律 val() 读 rendered，禁止再次格式化或手敲。
# 真源 = results.yaml；0_result_summaries.md 由 render_summary_md() 从它派生。
# 双向规则：数字只在此改；若需在下游改，先回到产出脚本/此处回写，再向其余下游传播。
#
# 用法：
#   source("02_code/vendored/emit_summary.R", encoding = "UTF-8")
#   source("02_code/config.R", encoding = "UTF-8")
#   add_result("07_paper/results.yaml", "S2_vs_S1_diff",
#              label="S2 vs S1 组间反弹差异", est=-1.82, ci_low=-3.29, ci_high=-0.36,
#              p=0.015, unit="kg", section="主要结果",
#              source="02_code/03_rebound.R", table=table_path("main_effect"))
#   render_summary_md("07_paper/results.yaml", "07_paper/0_result_summaries.md")
#   val("07_paper/results.yaml", "S2_vs_S1_diff")          # 取 full 成品串
#   val("07_paper/results.yaml", "S2_vs_S1_diff", "p")     # 取 P 部分
#
# 数字口径（唯一真源，改这里全项目同步）：见下 fmt_* —— 优先读 conventions.R 的同名常量（若已 source）。
# ============================================================
suppressWarnings(suppressMessages(library(yaml)))

# ---- 口径常量（可被 conventions.R 覆盖：若已定义同名变量则用之）----
.cfg <- function(name, default) if (exists(name, inherits = TRUE)) get(name, inherits = TRUE) else default
.DIGITS_EST <- function() .cfg("DIGITS_EST", 2L)   # 估计值小数位
.DIGITS_P   <- function() .cfg("DIGITS_P", 3L)     # P 值小数位
.P_FLOOR    <- function() .cfg("P_FLOOR", 0.001)   # P 下限阈值

# ---- 格式化（单一真源）----
.minus <- function(s) gsub("-", "−", s, fixed = TRUE)   # 正经减号 U+2212
fmt_num <- function(x, d = .DIGITS_EST()) {
  if (is.null(x) || is.na(x)) return(NA_character_)
  .minus(formatC(round(x, d), format = "f", digits = d))
}
fmt_p <- function(p, d = .DIGITS_P(), floor = .P_FLOOR()) {
  if (is.null(p) || is.na(p)) return(NA_character_)
  if (p < floor) paste0("P < ", formatC(floor, format = "f", digits = d))
  else paste0("P = ", formatC(round(p, d), format = "f", digits = d))
}
fmt_ci <- function(lo, hi, d = .DIGITS_EST(), style = "zh") {
  if (is.null(lo) || is.na(lo) || is.null(hi) || is.na(hi)) return(NA_character_)
  lo <- fmt_num(lo, d); hi <- fmt_num(hi, d)
  if (style == "zh") sprintf("（95%%CI：%s，%s）", lo, hi)   # （95%CI：lo，hi）
  else sprintf(" (95%% CI: %s, %s)", lo, hi)
}

# ---- 组装某条结果的 rendered 成品串 ----
.render_one <- function(est = NA, ci_low = NA, ci_high = NA, p = NA, unit = "",
                        d = .DIGITS_EST(), style = "zh") {
  out <- list()
  has_est <- !is.null(est) && !is.na(est)
  has_ci  <- !is.null(ci_low) && !is.na(ci_low) && !is.null(ci_high) && !is.na(ci_high)
  has_p   <- !is.null(p) && !is.na(p)
  est_s <- if (has_est) fmt_num(est, d) else NA_character_
  .sep  <- if (identical(unit, "%")) "" else " "   # 百分号紧贴，其余单位空格
  est_u <- if (has_est && nzchar(unit)) paste0(est_s, .sep, unit) else est_s
  ci_s  <- if (has_ci) fmt_ci(ci_low, ci_high, d, style) else NA_character_
  p_s   <- if (has_p) fmt_p(p) else NA_character_
  if (has_est) out$est <- est_u
  if (has_ci)  out$ci  <- ci_s
  if (has_p)   out$p   <- p_s
  if (has_est && has_ci) out$est_ci <- paste0(est_u, ci_s)
  # full：尽量信息全（est+ci+p）
  full <- est_u
  if (has_ci) full <- paste0(full, ci_s)
  if (has_p)  full <- if (is.na(full)) p_s else paste0(full, "，", p_s)  # 中文逗号
  out$full <- full
  out
}

.load_yaml <- function(path) {
  if (file.exists(path)) yaml::read_yaml(path) else list(meta = list(), results = list())
}
`%||%` <- function(a, b) if (is.null(a)) b else a
.raw_sig <- function(est, ci_low, ci_high, p, unit)   # 原始数值指纹：判断数字是否变了
  paste(est, ci_low, ci_high, p, unit, sep = "|")

# ---- 写入/更新一条结果（upsert）----
# interp = 该结果的结论/效应解读（人写散文）。数字变了而解读未同步 → 自动标 interp_review=TRUE（待复核），
# 因为"改数字解决不了解读"：估计值/方向/显著性一变，结论措辞往往要改。
add_result <- function(path, key, label = "", est = NA, ci_low = NA, ci_high = NA,
                       p = NA, unit = "", section = "结果", source = "", table = "",
                       interp = NULL, digits = .DIGITS_EST(), style = "zh") {
  doc <- .load_yaml(path)
  if (is.null(doc$results)) doc$results <- list()
  old <- doc$results[[key]]
  new_sig <- .raw_sig(est, ci_low, ci_high, p, unit)
  if (!is.null(interp)) {                       # 本次显式给了解读 → 采用，视为已复核
    interp_val <- interp; review <- FALSE
  } else if (!is.null(old)) {                   # 沿用旧解读
    interp_val <- old$interp %||% ""
    changed <- !is.null(old$raw_sig) && !identical(old$raw_sig, new_sig)
    review <- if (changed && nzchar(interp_val)) TRUE else (old$interp_review %||% FALSE)
    if (changed && nzchar(interp_val))
      warning(sprintf("[解读待复核] %s 的数字已变，请核对其结论/效应解读后 confirm_interp()。", key))
  } else { interp_val <- ""; review <- FALSE }
  doc$results[[key]] <- list(
    label = label, section = section, source = source, table = table,
    raw = list(est = est, ci_low = ci_low, ci_high = ci_high, p = p, unit = unit),
    rendered = .render_one(est, ci_low, ci_high, p, unit, digits, style),
    interp = interp_val, interp_review = review, raw_sig = new_sig
  )
  doc$meta$updated <- as.character(Sys.Date())
  yaml::write_yaml(doc, path)
  invisible(doc$results[[key]]$rendered$full)
}

# ---- 设/改解读并清除待复核标记（数字变更后复核完调用）----
confirm_interp <- function(path, key, interp = NULL) {
  doc <- .load_yaml(path)
  if (is.null(doc$results[[key]])) stop(sprintf("results.yaml 无键：%s", key))
  if (!is.null(interp)) doc$results[[key]]$interp <- interp
  doc$results[[key]]$interp_review <- FALSE
  yaml::write_yaml(doc, path); invisible(TRUE)
}

# ---- 总结论（跨多个结果的整体判断，人写）----
set_conclusion <- function(path, text) {
  doc <- .load_yaml(path); doc$conclusion <- text
  yaml::write_yaml(doc, path); invisible(TRUE)
}

# ---- 列出所有"解读待复核"的键（数字动过、解读未跟上）----
stale_interps <- function(path) {
  doc <- .load_yaml(path)
  Filter(Negate(is.null), lapply(names(doc$results), function(k)
    if (isTRUE(doc$results[[k]]$interp_review)) k else NULL)) |> unlist()
}

# ---- 下游取数（R 侧）：返回 rendered 成品串 ----
val <- function(path, key, which = "full") {
  doc <- .load_yaml(path)
  if (is.null(doc$results[[key]]))
    stop(sprintf("results.yaml 无键：%s", key))
  v <- doc$results[[key]]$rendered[[which]]
  if (is.null(v)) stop(sprintf("键 %s 无 rendered.%s", key, which))
  v
}

# ---- 由 results.yaml 派生 0_result_summaries.md（人读数据源：数字 + 解读 + 结论）----
# 数字与解读都来自 results.yaml（解读 = 人写的 interp/conclusion）。md 是派生物，勿手改：
# 改数字 → 改 results.yaml；改解读 → confirm_interp()/set_conclusion()，再重跑本函数。
render_summary_md <- function(path, md_path) {
  doc <- .load_yaml(path)
  res <- doc$results
  if (length(res) == 0) { writeLines("# 结果汇总（暂无）", md_path); return(invisible()) }
  secs <- vapply(res, function(x) if (is.null(x$section)) "结果" else x$section, "")
  stale <- stale_interps(path)
  lines <- c("# 结果汇总（由 results.yaml 自动生成，勿手改；改数字改 yaml、改解读用 confirm_interp/set_conclusion 后重跑）", "")
  if (length(stale))
    lines <- c(lines, sprintf("> [解读待复核] 以下结果数字已变、解读尚未跟上，请逐条核对后 confirm_interp()：%s",
                              paste(stale, collapse = "、")), "")
  for (s in unique(secs)) {
    lines <- c(lines, paste0("## ", s), "")
    for (key in names(res)[secs == s]) {
      x <- res[[key]]
      src <- paste0(c(if (nzchar(x$source %||% "")) x$source, if (nzchar(x$table %||% "")) x$table), collapse = "；")
      tail <- if (nzchar(src)) sprintf("（来源：%s）", src) else ""
      lines <- c(lines, sprintf("- **%s**（`%s`）：%s%s",
                                if (nzchar(x$label %||% "")) x$label else key, key, x$rendered$full, tail))
      if (nzchar(x$interp %||% "")) {                      # 结论/效应解读
        flag <- if (isTRUE(x$interp_review)) " [解读待复核]" else ""
        lines <- c(lines, sprintf("  - 解读%s：%s", flag, x$interp))
      }
    }
    lines <- c(lines, "")
  }
  if (nzchar(doc$conclusion %||% ""))
    lines <- c(lines, "## 结论", "", doc$conclusion, "")
  writeLines(lines, md_path, useBytes = TRUE)
  invisible(md_path)
}
