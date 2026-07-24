# ============================================================
# 发表级出图默认（publication-figures / T1 简单图零调参达标）
# source 即得：theme_pub() 主题 + save_fig() 双存 + 中文字体注册 + 配色。
# 目标：简单图不必每次手调尺寸/字体/图例/比例——默认就「比例合适、图例不压数据、字体嵌入」。
# 进阶/顶刊图（T2/T3）在此基础上叠配方技法。
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

# ---- 发表级主题（theme_classic 打底，图例默认外置不压数据）----
theme_pub <- function(base_size = 8, family = PLOT_FAMILY, legend = "right") {
  theme_classic(base_size = base_size, base_family = family) +
    theme(
      plot.title   = element_text(face = "bold", hjust = 0.5, size = base_size + 1),
      axis.line    = element_line(linewidth = 0.4),
      axis.ticks   = element_line(linewidth = 0.4),
      axis.text    = element_text(colour = "black"),
      legend.position = legend,                       # 默认右侧外置，绝不内嵌压数据
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

# ---- 双存：PDF(cairo) + PNG(300dpi)；优先 registry 的 fig_path() ----
save_fig <- function(p, stem, w_mm = 88, h_mm = 70, type = NULL) {
  if (!is.null(type)) { d <- fig_dim(type); w_mm <- d[1]; h_mm <- d[2] }
  pdf_dev <- if (capabilities("cairo")) grDevices::cairo_pdf else grDevices::pdf
  png_dev <- if (has("ragg")) ragg::agg_png else "png"
  pdf_path <- if (exists("fig_path", inherits = TRUE)) get("fig_path")(stem, "pdf") else paste0(stem, ".pdf")
  png_path <- if (exists("fig_path", inherits = TRUE)) get("fig_path")(stem, "png") else paste0(stem, ".png")
  ggsave(pdf_path, p, width = w_mm, height = h_mm, units = "mm", device = pdf_dev)
  ggsave(png_path, p, width = w_mm, height = h_mm, units = "mm", dpi = 300,
         device = png_dev, bg = "white")
  invisible(c(pdf = pdf_path, png = png_path))
}
