# example_ppt.R — 覆盖全部版式的可运行演示（Rscript example_ppt.R）
Sys.setlocale("LC_ALL", "Chinese (Simplified)_China.utf8")
suppressPackageStartupMessages(library(ggplot2))

# 稳健定位脚本目录（兼容 Rscript path 与 source()）
.this <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
here <- if (length(.this)) dirname(normalizePath(.this)) else
        tryCatch(dirname(sys.frame(1)$ofile), error = function(e) getwd())
source(file.path(here, "sysu_toolkit.R"))

dir.create(file.path(here, "_tmp"), showWarnings = FALSE)
img <- file.path(here, "_tmp", "demo.png")
# 图内不放标题——标题/解释靠 PPT 正文与 caption="图N …"
ggsave(img, ggplot(mtcars, aes(wt, mpg, color = factor(cyl))) +
         geom_point(size = 3) + theme_minimal(base_size = 16) +
         labs(x = "车重", y = "油耗", color = "缸数"),
       width = 6, height = 4.2, dpi = 150, bg = "white")

ppt <- sysu_init("default")          # 默认中大医学；改 "模板2" 可演示原公卫模板

ppt <- sysu_add_cover(ppt, "汇报 PPT 工具箱演示", "Toolkit Demonstration", "汇报人：张三", "2026 组会")

ppt <- sysu_add_text(ppt, "1 纯文字页", block_list(
  prose(bd("字体　"), tx("中文宋体、英文 Times New Roman 自动分流，例如 RCS spline 与 p-value。")),
  num_item("①", "成段优先", "用 prose 写流畅文字，避免满屏列表。"),
  num_item("②", "强调", "关键术语用 bd() 加粗主色。")))

ppt <- sysu_add_two_text(ppt, "2 双栏文字",
  block_list(bullet("左栏"), sub_bullet("要点 A"), sub_bullet("要点 B")),
  block_list(bullet("右栏"), sub_bullet("要点 C"), sub_bullet("要点 D")))

ppt <- sysu_add_text_image(ppt, "3 左右图文",
  block_list(prose(tx("左文右图，图按真实比例等比缩放、自动居中。"))),
  img, img_w = 5.6, img_h = 3.9, side = "right", caption = "图 1 示例配图")

ppt <- sysu_add_image_caption(ppt, "4 上图下文", img, img_w = 6.4, img_h = 4.0,
  block_list(prose(bd("结论　"), tx("上方为图，下方为结论文字。"))), img_pos = "top",
  caption = "图 2 上图下文示意")

ppt <- sysu_add_image(ppt, "5 整图页", img, img_w = 8.4, img_h = 5.0, caption = "图 3 居中大图")

df <- data.frame(方法 = c("二分","四分位","RCS"), 信息损失 = c("大","中","小"), 推荐度 = c("低","中","高"))
ppt <- sysu_add_table(ppt, "6 表格页", sysu_flextable(df, widths = c(2.2,2.6,2.2), fsize = 16),
                      note = "注：示例数据。")

ppt <- sysu_add_text_table(ppt, "7 左文右表",
  block_list(bullet("解读"), sub_bullet("看右表对比")), sysu_flextable(df, widths = c(1.6,1.8,1.6)))

ppt <- sysu_add_cards(ppt, "8 卡片页",
  list(list(tag="①", head="方法 A", body="简述核心机制。"),
       list(tag="②", head="方法 B", body="简述核心机制。"),
       list(tag="③", head="方法 C", body="简述核心机制。")),
  intro = block_list(prose(bd("引言　"), tx("真正并列的 3-4 项才用卡片。"))))

ppt <- sysu_add_code(ppt, "9 代码 / 示例",
  c("library(rms)", "fit <- ols(y ~ rcs(x, 4), data = dat)", "Predict(fit, x)  # 剂量-反应曲线"),
  intro = block_list(prose(bd("示例　"), tx("用 rms 拟合限制性立方样条。"))))

out <- file.path(here, "_tmp", "demo.pptx")
sysu_save(ppt, out, genre = "meeting")
cat("Demo saved:", out, " slides =", length(ppt), "\n")
