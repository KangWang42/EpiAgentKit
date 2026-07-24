# 可视化规范

所有真实数据图先执行 `publication-figures` 的图前合同、最终尺寸和验收规则。本文件只保留 R 实现片段，不另设配色、字体或 KM 硬规则。

## 配色

```r
# 项目语义色优先；无项目配色时可从 Okabe-Ito 起步
okabe_ito <- c("#0072B2", "#D55E00", "#009E73", "#CC79A7",
               "#E69F00", "#56B4E9", "#F0E442", "#000000")
scale_fill_manual(values = okabe_ito)
scale_color_manual(values = okabe_ito)

# 连续
scale_fill_viridis_c()
```

## 中文字体 (PDF)

```r
# PLOT_FAMILY 由 publication-figures/scripts/fig_setup.R 检测当前系统字体
theme_cn <- theme_bw(base_size = 8, base_family = PLOT_FAMILY) +
  theme(
    text = element_text(family = PLOT_FAMILY),
    plot.title = element_text(hjust = 0.5),
    axis.title = element_text(family = PLOT_FAMILY),
    axis.text = element_text(family = PLOT_FAMILY),
    legend.text = element_text(family = PLOT_FAMILY)
  )
```

## 导出

```r
# PNG (推荐中文)
ggsave("Fig.png", plot, dpi = 300, device = ragg::agg_png)

# PDF
ggsave("Fig.pdf", plot, device = cairo_pdf)
```

## 常用图表

### 森林图

```r
ggplot(data, aes(x = estimate, y = term)) +
  geom_point() +
  geom_errorbarh(aes(xmin = conf.low, xmax = conf.high), height = 0.2) +
  geom_vline(xintercept = 1, linetype = "dashed") +
  scale_x_log10() +
  theme_bw()
```

### KM 曲线

```r
ggsurvplot(fit, risk.table = TRUE)  # 是否保留风险表按 publication-figures 与载体判断
```

### 箱线图

```r
ggplot(data, aes(x = group, y = value, fill = group)) +
  geom_boxplot() +
  scale_fill_manual(values = okabe_ito) +
  theme_bw()
```

## 标题规范

- 论文主图通常把题名、完整说明和来源留给图注；图内仅保留理解数据所需的标签和短注释。
- 汇报或独立图确需标题时使用 `labs(title = "...")`，并按载体层级处理；不把长段说明烧录进图内。
