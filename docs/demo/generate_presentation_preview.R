#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(grid)
  library(png)
  library(showtext)
  library(sysfonts)
})

file_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- normalizePath(
  sub("^--file=", "", file_arg[[1]]),
  winslash = "/",
  mustWork = TRUE
)
demo_dir <- dirname(script_path)
output_dir <- file.path(demo_dir, "output")
figure_path <- file.path(output_dir, "adjusted-survival-paper.png")
slide_path <- file.path(output_dir, "presentation-preview.png")

font_candidates <- Sys.glob(c(
  "C:/Windows/Fonts/msyh.ttc",
  "C:/Windows/Fonts/simhei.ttf",
  "/System/Library/Fonts/PingFang.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
  "/usr/share/fonts/opentype/adobe-source-han-sans/SourceHanSansCN-Regular.otf"
))
bold_candidates <- Sys.glob(c(
  "C:/Windows/Fonts/msyhbd.ttc",
  "C:/Windows/Fonts/simhei.ttf",
  "/System/Library/Fonts/PingFang.ttc",
  "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
  "/usr/share/fonts/opentype/adobe-source-han-sans/SourceHanSansCN-Bold.otf"
))
font_path <- font_candidates[[1]]
bold_path <- if (length(bold_candidates) > 0) bold_candidates[[1]] else font_path
font_add("presentation_sans", regular = font_path, bold = bold_path)
showtext_auto()
showtext_opts(dpi = 144)

ink <- "#172033"
muted <- "#64748B"
accent <- "#0F766E"
figure <- readPNG(figure_path)

draw_text <- function(
    label,
    x,
    y,
    size,
    face = "plain",
    colour = ink,
    just = "left") {
  grid.text(
    label,
    x = unit(x, "npc"),
    y = unit(y, "npc"),
    just = just,
    gp = gpar(
      fontfamily = "presentation_sans",
      fontface = face,
      fontsize = size,
      col = colour,
      lineheight = 1.25
    )
  )
}

ragg::agg_png(
  slide_path,
  width = 1600,
  height = 900,
  units = "px",
  res = 144,
  background = "#F7F8FA"
)
grid.newpage()
grid.rect(gp = gpar(fill = "#F7F8FA", col = NA))
grid.rect(
  x = 0.025,
  y = 0.5,
  width = 0.012,
  height = 1,
  gp = gpar(fill = accent, col = NA)
)
draw_text("模拟数据", 0.06, 0.93, 8, face = "bold", colour = accent)
draw_text(
  "调整后无事件生存率：强化方案组持续较高",
  0.06,
  0.865,
  24,
  face = "bold"
)
grid.lines(
  x = unit(c(0.06, 0.94), "npc"),
  y = unit(c(0.805, 0.805), "npc"),
  gp = gpar(col = "#D5DCE4", lwd = 1)
)

draw_text("研究设计", 0.06, 0.74, 10, face = "bold", colour = muted)
draw_text(
  "固定模拟队列\n36 个月行政随访\n多变量 Cox 回归",
  0.06,
  0.695,
  13,
  just = c("left", "top")
)
grid.roundrect(
  x = 0.235,
  y = 0.39,
  width = 0.35,
  height = 0.27,
  r = unit(5, "mm"),
  gp = gpar(fill = "#E8F3F1", col = NA)
)
draw_text("主要结果", 0.085, 0.485, 9, face = "bold", colour = accent)
draw_text(
  "强化方案的调整后曲线在\n整个随访期内保持较高；\n风险集与置信区间同步呈现。",
  0.085,
  0.445,
  14,
  face = "bold",
  just = c("left", "top")
)
draw_text(
  "模拟结果不代表真实医学结论。",
  0.06,
  0.105,
  8.5,
  colour = muted
)

grid.roundrect(
  x = 0.72,
  y = 0.44,
  width = 0.50,
  height = 0.61,
  r = unit(4, "mm"),
  gp = gpar(fill = "white", col = "#D9E0E7", lwd = 0.8)
)
grid.raster(
  figure,
  x = 0.72,
  y = 0.44,
  width = 0.46,
  height = 0.54,
  interpolate = TRUE
)
draw_text("12", 0.94, 0.055, 7.5, colour = muted, just = "right")
invisible(dev.off())
