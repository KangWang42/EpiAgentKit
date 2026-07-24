# ============================================================
# 数据型配图函数库（适配 PPT 嵌入）
# 非统计流程图、结构图、技术路线、包含关系、机制示意和场景配图统一使用
# research-visuals 优先调用 imagegen；只有明确矢量需求或全部适用 imagegen 路径耗尽时才最终回退 svg-diagrams。
# 不在本文件继续维护 ggplot 矩形/箭头流程图基元。
# ============================================================
suppressPackageStartupMessages({
  library(ggplot2)
  library(showtext)
  library(sysfonts)
})
font_candidates <- Sys.glob(c(
  "C:/Windows/Fonts/msyh.ttc",
  "C:/Windows/Fonts/simhei.ttf",
  "/System/Library/Fonts/PingFang.ttc",
  "/usr/share/fonts/**/SourceHanSans*.otf"
))
plot_family <- "sans"
if (length(font_candidates)) {
  font_add("zh_sans", regular = font_candidates[[1]])
  plot_family <- "zh_sans"
}
showtext_auto()

BLUE <- "#0072B2"
RED <- "#B22222"

# 二维谱系散点（信息×灵活性等带坐标尺度的数据图）
# items: data.frame(name, x, y, grp)
# 图内不放标题；标题和解释写入 PPT 正文或 caption。
make_spectrum <- function(items, xlab = "X →", ylab = "Y →", pal = c(BLUE, RED)) {
  suppressPackageStartupMessages(library(ggrepel))
  ggplot(items, aes(x, y, color = grp)) +
    geom_point(size = 6) +
    geom_text_repel(aes(label = name), family = plot_family, size = 7,
                    box.padding = 0.7, seed = 1, segment.color = "grey70") +
    scale_color_manual(values = pal, name = NULL) +
    labs(x = xlab, y = ylab) +
    theme_minimal(base_family = plot_family, base_size = 20) +
    theme(legend.position = "top", legend.text = element_text(size = 20),
          panel.grid.minor = element_blank())
}

# 渲染提示：右栏图按约 5.5–6.2 英寸输出，整图按约 8.6–9.8 英寸输出。
# 统计图遵循 publication-figures；非统计视觉遵循 research-visuals 并优先嵌入 PNG。
