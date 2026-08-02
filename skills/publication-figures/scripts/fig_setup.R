# ============================================================
# 中性统计图工作稿默认：主题、字体、配色和按需导出。
# 正式投稿的尺寸、格式、分辨率、背景和字体仍服从目标期刊当前官方要求。
# ============================================================
suppressWarnings(suppressMessages({
  library(ggplot2)
  has <- function(p) requireNamespace(p, quietly = TRUE)
}))

# ---- 中文字体注册（一次）----
.register_cn_font <- function() {
  if (!has("sysfonts") || !has("showtext")) return("sans")
  paths <- Sys.glob(c("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
                      "/System/Library/Fonts/PingFang.ttc",
                      "/usr/share/fonts/**/SourceHanSans*.otf"))
  if (length(paths) == 0) return("sans")
  try(sysfonts::font_add("zh_sans", regular = paths[[1]]), silent = TRUE)
  showtext::showtext_auto(); showtext::showtext_opts(dpi = 300)
  "zh_sans"
}
PLOT_FAMILY <- .register_cn_font()   # 含中文用它；纯英文图也安全

# ---- 配色：优先 conventions.R 的 PALETTE，否则 Okabe-Ito ----
pub_palette <- function(n = NULL) {
  if (exists("PALETTE", inherits = TRUE)) return(get("PALETTE", inherits = TRUE))
  cols <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7",
            "#E69F00", "#56B4E9", "#F0E442", "#000000")
  if (is.null(n)) return(cols)
  if (n <= length(cols)) cols[seq_len(n)] else grDevices::hcl.colors(n, "Dark 3")
}
scale_color_pub <- function(...) ggplot2::scale_color_manual(values = pub_palette(), ...)
scale_fill_pub  <- function(...) ggplot2::scale_fill_manual(values = pub_palette(), ...)

# ---- 中性主题（theme_classic 打底）----
theme_pub <- function(base_size = 8, family = PLOT_FAMILY, legend = "right") {
  theme_classic(base_size = base_size, base_family = family) +
    theme(
      plot.title   = element_text(face = "bold", hjust = 0.5, size = base_size + 1),
      axis.line    = element_line(linewidth = 0.4),
      axis.ticks   = element_line(linewidth = 0.4),
      axis.text    = element_text(colour = "black"),
      legend.position = legend,
      legend.key.size = unit(3.5, "mm"),
      legend.background = element_blank(),
      legend.title = element_text(size = base_size),
      strip.background = element_blank(),
      strip.text   = element_text(face = "bold", size = base_size)
    )
}

# ---- 各图型推荐尺寸（mm，宽×高）——比例合适，不统一 88×85 ----
FIG_SIZES <- list(
  default = c(88, 70), square = c(88, 85), roc = c(88, 85), calib = c(88, 85),
  wide = c(180, 85), rcs = c(120, 85), heatmap = c(130, 130), km = c(120, 120),
  forest = c(160, 120), nomogram = c(180, 120), corr = c(130, 130)
)
fig_dim <- function(type = "default") FIG_SIZES[[type]] %||% FIG_SIZES$default
`%||%` <- function(a, b) if (is.null(a)) b else a

# ---- 按实际用途导出；默认只生成 PNG 工作预览 ----
save_fig <- function(p, stem, w_mm = 88, h_mm = 70, type = NULL,
                     formats = "png", dpi = 300, bg = "white") {
  if (!is.null(type)) { d <- fig_dim(type); w_mm <- d[1]; h_mm <- d[2] }
  formats <- unique(tolower(formats))
  if (!length(formats) || any(!formats %in% c("png", "pdf"))) {
    stop("formats 仅支持当前已验证的 png 或 pdf；其它投稿格式按期刊要求另行验证")
  }
  pdf_dev <- if (capabilities("cairo")) grDevices::cairo_pdf else grDevices::pdf
  png_dev <- if (has("ragg")) ragg::agg_png else "png"
  paths <- vapply(formats, function(format) {
    path <- if (exists("fig_path", inherits = TRUE)) get("fig_path")(stem, format) else paste0(stem, ".", format)
    if (format == "pdf") {
      ggsave(path, p, width = w_mm, height = h_mm, units = "mm", device = pdf_dev, bg = bg)
    } else {
      ggsave(path, p, width = w_mm, height = h_mm, units = "mm", dpi = dpi,
             device = png_dev, bg = bg)
    }
    path
  }, character(1))
  invisible(stats::setNames(paths, formats))
}
