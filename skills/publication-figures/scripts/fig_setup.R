# ============================================================
# 中性统计图工作稿默认：主题、字体、配色和按需导出。
# 正式投稿的尺寸、格式、分辨率、背景和字体仍服从目标期刊当前官方要求。
# ============================================================
suppressWarnings(suppressMessages({
  library(ggplot2)
  has <- function(p) requireNamespace(p, quietly = TRUE)
}))

# ---- 中英文字体注册（一次）----
.first_font <- function(paths) {
  hits <- unique(Sys.glob(paths))
  if (length(hits)) hits[[1]] else NULL
}

.register_en_font <- function() {
  fallback <- "Times New Roman"
  if (!has("sysfonts") || !has("showtext")) return(fallback)
  regular <- .first_font(c(
    "C:/Windows/Fonts/times.ttf",
    "~/Library/Fonts/Times New Roman.ttf",
    "/Library/Fonts/Times New Roman.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/times.ttf"
  ))
  if (is.null(regular)) return(fallback)
  args <- list(family = "pub_times", regular = regular)
  variants <- list(
    bold = c(
      "C:/Windows/Fonts/timesbd.ttf",
      "~/Library/Fonts/Times New Roman Bold.ttf",
      "/Library/Fonts/Times New Roman Bold.ttf",
      "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold.ttf"
    ),
    italic = c(
      "C:/Windows/Fonts/timesi.ttf",
      "~/Library/Fonts/Times New Roman Italic.ttf",
      "/Library/Fonts/Times New Roman Italic.ttf",
      "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Italic.ttf"
    ),
    bolditalic = c(
      "C:/Windows/Fonts/timesbi.ttf",
      "~/Library/Fonts/Times New Roman Bold Italic.ttf",
      "/Library/Fonts/Times New Roman Bold Italic.ttf",
      "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman_Bold_Italic.ttf"
    )
  )
  for (style in names(variants)) {
    path <- .first_font(variants[[style]])
    if (!is.null(path)) args[[style]] <- path
  }
  registered <- tryCatch(
    {
      do.call(sysfonts::font_add, args)
      TRUE
    },
    error = function(e) FALSE
  )
  if (!registered) return(fallback)
  showtext::showtext_auto(); showtext::showtext_opts(dpi = 300)
  "pub_times"
}

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
PLOT_FAMILY_EN <- .register_en_font()
PLOT_FAMILY <- .register_cn_font()

pub_family <- function(language = c("mixed", "english", "chinese")) {
  language <- match.arg(language)
  if (identical(language, "english")) PLOT_FAMILY_EN else PLOT_FAMILY
}

# ---- 配色：优先项目设置中的 PALETTE，否则 Okabe-Ito ----
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
theme_pub <- function(base_size = 8, family = NULL, legend = "right",
                      language = c("mixed", "english", "chinese")) {
  if (is.null(family)) family <- pub_family(match.arg(language))
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
