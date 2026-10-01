# 可视化规范

所有真实数据图先执行 `publication-figures` 的图前说明、最终尺寸和验收规则。本文件只保留 R 实现片段，不另设配色、字体或导出规则；这些统一由 `publication-figures/scripts/fig_setup.R` 提供。新项目由 `project-init` 把它复制到 `02_code/vendored/fig_setup.R`。

## 主题、字体、配色与导出

```r
source("02_code/vendored/fig_setup.R", encoding = "UTF-8")  # 旧项目按实际位置调整

p <- p +
  theme_pub(language = "english") +   # 英文图：Times New Roman；中文或中英混排用 "mixed"
  scale_color_pub()                   # 项目设置中有 PALETTE 时优先使用，否则 Okabe-Ito

save_fig(p, "fig_forest", type = "forest")          # 默认只导出 PNG 工作预览
save_fig(p, "fig_forest", type = "forest", formats = c("png", "pdf"))
```

`fig_dim()` 给出各图型推荐尺寸（mm）；正式投稿的尺寸、格式、分辨率和字体嵌入服从目标期刊当前要求。连续变量配色可用 `scale_fill_viridis_c()`。

## 常用图表

### 森林图

```r
ggplot(data, aes(x = estimate, y = term)) +
  geom_point() +
  geom_errorbar(aes(xmin = conf.low, xmax = conf.high), width = 0.2, orientation = "y") +
  geom_vline(xintercept = 1, linetype = "dashed") +
  scale_x_log10() +
  theme_pub(language = "english")
```

比值类效应量（OR、RR、HR）使用对数横轴，参照线为 1；差值类效应量使用线性横轴，参照线为 0。ggplot2 4.0 起 `geom_errorbarh()` 已弃用，不再使用。

### KM 曲线

```r
fit <- survival::survfit(survival::Surv(time, status) ~ group, data = data)
km <- survminer::ggsurvplot(fit, data = data, risk.table = TRUE, conf.int = TRUE,
                            palette = pub_palette(2), legend.labs = c("A", "B"),
                            font.family = pub_family("english"), fontsize = 3,
                            ggtheme = theme_pub(language = "english"),
                            tables.theme = survminer::theme_cleantable())

# ggsurvplot 结果不是单个 ggplot，不能交给 save_fig；用 ragg 设备导出，基础 png() 在 Windows 上找不到注册字体
ragg::agg_png("fig_km.png", width = 120, height = 120, units = "mm", res = 300)
print(km)
invisible(dev.off())
```

当前 survminer 依赖的 ggpubr 会提示 `size` 美学已弃用；这是上游包的提示，不影响结果，保留在运行日志中并注明来源即可，不在项目代码中压制。

是否保留风险表、置信带和删失标记，按 `publication-figures` 与最终论文、报告或演示页面判断；竞争风险场景改用累积发生函数图。

### 箱线图

```r
ggplot(data, aes(x = group, y = value, fill = group)) +
  geom_boxplot(outlier.shape = NA) +
  geom_jitter(width = 0.15, size = 0.8, alpha = 0.5) +
  scale_fill_pub() +
  theme_pub(language = "english")
```

样本量较小时同时显示个体点；样本量很大且点严重重叠时去掉抖动点。
