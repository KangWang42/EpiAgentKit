#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ggplot2)
  library(patchwork)
  library(showtext)
  library(survival)
  library(sysfonts)
})

file_arg <- grep("^--file=", commandArgs(), value = TRUE)
script_path <- normalizePath(
  sub("^--file=", "", file_arg[[1]]),
  winslash = "/",
  mustWork = TRUE
)
demo_dir <- dirname(script_path)
data_path <- file.path(demo_dir, "survival-demo-data.csv")
output_dir <- file.path(demo_dir, "output", "publication-figures")
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

set.seed(20260802)
n <- 1200L
age <- pmin(pmax(round(rnorm(n, mean = 62, sd = 11)), 35), 85)
sex <- sample(c("女性", "男性"), n, replace = TRUE, prob = c(0.48, 0.52))
stage <- sample(
  c("I", "II", "III"),
  n,
  replace = TRUE,
  prob = c(0.30, 0.45, 0.25)
)
biomarker <- rnorm(n) + 0.018 * (age - 60) +
  ifelse(stage == "II", 0.20, ifelse(stage == "III", 0.55, 0))
treatment_probability <- plogis(
  -0.35 + 0.012 * (age - 60) +
    0.30 * (stage == "III") - 0.18 * biomarker
)
treatment <- rbinom(n, size = 1, prob = treatment_probability)
linear_predictor <- log(0.72) * treatment +
  0.026 * (age - 60) +
  0.25 * (sex == "男性") +
  log(1.45) * (stage == "II") +
  log(2.10) * (stage == "III") +
  0.28 * biomarker
event_time <- rexp(n, rate = 0.0125 * exp(linear_predictor))

dat <- data.frame(
  id = sprintf("P%04d", seq_len(n)),
  age = age,
  sex = sex,
  stage = stage,
  biomarker = round(biomarker, 4),
  treatment = treatment,
  time_months = round(pmin(event_time, 36), 4),
  event = as.integer(event_time <= 36),
  stringsAsFactors = FALSE
)
write.csv(
  dat,
  data_path,
  row.names = FALSE,
  fileEncoding = "UTF-8",
  quote = TRUE
)

dat$sex <- factor(dat$sex, levels = c("女性", "男性"))
dat$stage <- factor(dat$stage, levels = c("I", "II", "III"))
dat$treatment_label <- factor(
  dat$treatment,
  levels = c(0, 1),
  labels = c("常规方案", "强化方案")
)
dat$age_10 <- (dat$age - 60) / 10
dat$biomarker_sd <- as.numeric(scale(dat$biomarker))

cox_fit <- coxph(
  Surv(time_months, event) ~
    treatment_label + age_10 + sex + stage + biomarker_sd,
  data = dat
)
cox_summary <- summary(cox_fit)
ph_test <- cox.zph(cox_fit, transform = "km")
treatment_row <- match(
  "treatment_label强化方案",
  rownames(cox_summary$coefficients)
)
write.csv(
  data.frame(
    n = nrow(dat),
    events = sum(dat$event),
    hazard_ratio = cox_summary$conf.int[treatment_row, "exp(coef)"],
    ci_lower = cox_summary$conf.int[treatment_row, "lower .95"],
    ci_upper = cox_summary$conf.int[treatment_row, "upper .95"],
    p_value = cox_summary$coefficients[treatment_row, "Pr(>|z|)"]
  ),
  file.path(output_dir, "survival-demo-results.csv"),
  row.names = FALSE,
  fileEncoding = "UTF-8",
  quote = TRUE
)

cohort_summary <- do.call(
  rbind,
  lapply(levels(dat$treatment_label), function(group_name) {
    group_data <- dat[dat$treatment_label == group_name, , drop = FALSE]
    data.frame(
      group = group_name,
      n = nrow(group_data),
      events = sum(group_data$event),
      age_mean = mean(group_data$age),
      age_sd = sd(group_data$age),
      male_n = sum(group_data$sex == "男性"),
      male_pct = mean(group_data$sex == "男性") * 100,
      stage_i_n = sum(group_data$stage == "I"),
      stage_i_pct = mean(group_data$stage == "I") * 100,
      stage_ii_n = sum(group_data$stage == "II"),
      stage_ii_pct = mean(group_data$stage == "II") * 100,
      stage_iii_n = sum(group_data$stage == "III"),
      stage_iii_pct = mean(group_data$stage == "III") * 100,
      biomarker_mean = mean(group_data$biomarker),
      biomarker_sd = sd(group_data$biomarker),
      stringsAsFactors = FALSE
    )
  })
)
write.csv(
  cohort_summary,
  file.path(output_dir, "manuscript-cohort-summary.csv"),
  row.names = FALSE,
  fileEncoding = "UTF-8",
  quote = TRUE
)

diagnostic_summary <- data.frame(
  statistic = c(
    "global_ph_test_p",
    "concordance",
    "concordance_se"
  ),
  value = c(
    ph_test$table["GLOBAL", "p"],
    unname(cox_summary$concordance[["C"]]),
    unname(cox_summary$concordance[["se(C)"]])
  )
)
write.csv(
  diagnostic_summary,
  file.path(output_dir, "model-diagnostics.csv"),
  row.names = FALSE,
  fileEncoding = "UTF-8",
  quote = TRUE
)

forest_data <- data.frame(
  term = rownames(cox_summary$coefficients),
  estimate = cox_summary$conf.int[, "exp(coef)"],
  conf_low = cox_summary$conf.int[, "lower .95"],
  conf_high = cox_summary$conf.int[, "upper .95"],
  p_value = cox_summary$coefficients[, "Pr(>|z|)"],
  stringsAsFactors = FALSE
)
forest_data$label <- unname(c(
  "treatment_label强化方案" = "强化方案（与常规方案比较）",
  "age_10" = "年龄（每增加 10 岁）",
  "sex男性" = "男性（与女性比较）",
  "stageII" = "疾病分期 II（与 I 期比较）",
  "stageIII" = "疾病分期 III（与 I 期比较）",
  "biomarker_sd" = "生物标志物（每增加 1 SD）"
)[forest_data$term])
if (anyNA(forest_data$label)) {
  stop("森林图存在未映射的模型项")
}
forest_data$estimate_label <- sprintf(
  "%.2f（%.2f～%.2f）",
  forest_data$estimate,
  forest_data$conf_low,
  forest_data$conf_high
)
forest_data$label <- factor(
  forest_data$label,
  levels = rev(forest_data$label)
)
write.csv(
  forest_data,
  file.path(output_dir, "cox-forest-results.csv"),
  row.names = FALSE,
  fileEncoding = "UTF-8",
  quote = TRUE
)
newdata <- data.frame(
  treatment_label = factor(
    c("常规方案", "强化方案"),
    levels = levels(dat$treatment_label)
  ),
  age_10 = 0,
  sex = factor(c("女性", "女性"), levels = levels(dat$sex)),
  stage = factor(c("II", "II"), levels = levels(dat$stage)),
  biomarker_sd = 0
)

times <- seq(0, 36, by = 0.5)
fit <- summary(survfit(cox_fit, newdata = newdata), times = times, extend = TRUE)
curve_data <- data.frame(
  time = rep(times, times = 2),
  survival = as.vector(fit$surv),
  lower = as.vector(fit$lower),
  upper = as.vector(fit$upper),
  group = factor(
    rep(c("常规方案", "强化方案"), each = length(times)),
    levels = c("常规方案", "强化方案")
  )
)

risk_times <- c(0, 12, 24, 36)
risk_data <- expand.grid(
  time = risk_times,
  group = levels(dat$treatment_label),
  stringsAsFactors = FALSE
)
risk_data$n <- mapply(
  function(time, group) {
    sum(dat$treatment_label == group & dat$time_months >= time)
  },
  risk_data$time,
  risk_data$group
)
risk_data$group <- factor(
  risk_data$group,
  levels = c("强化方案", "常规方案")
)
risk_data$row <- as.numeric(risk_data$group)
risk_data$hjust <- ifelse(
  risk_data$time == min(risk_times),
  0,
  ifelse(risk_data$time == max(risk_times), 1, 0.5)
)

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
font_add("epi_demo_sans", regular = font_path, bold = bold_path)
showtext_auto()
showtext_opts(dpi = 300)

plot_family <- "epi_demo_sans"
palette <- c("常规方案" = "#5B4B8A", "强化方案" = "#0F766E")
ink <- "#172033"
muted <- "#64748B"
grid_colour <- "#DCE4EC"

survival_plot <- ggplot(
  curve_data,
  aes(x = time, y = survival, colour = group, fill = group)
) +
  geom_ribbon(
    aes(ymin = lower, ymax = upper),
    alpha = 0.14,
    linewidth = 0,
    show.legend = FALSE
  ) +
  geom_step(linewidth = 1.05) +
  scale_colour_manual(values = palette) +
  scale_fill_manual(values = palette) +
  scale_x_continuous(
    limits = c(0, 36),
    breaks = risk_times,
    expand = c(0.01, 0.01)
  ) +
  scale_y_continuous(
    limits = c(0.35, 1),
    breaks = seq(0.4, 1, by = 0.2),
    labels = function(x) sprintf("%d%%", round(100 * x)),
    expand = c(0, 0)
  ) +
  labs(x = NULL, y = "无事件生存率", colour = NULL) +
  guides(colour = "none") +
  theme_minimal(base_size = 8.5, base_family = plot_family) +
  theme(
    panel.grid.minor = element_blank(),
    panel.grid.major = element_line(colour = grid_colour, linewidth = 0.4),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    axis.title = element_text(colour = ink, size = 9),
    axis.text.y = element_text(colour = "#334155", size = 8),
    plot.margin = margin(2, 10, 0, 8)
  )

legend_plot <- ggplot() +
  annotate(
    "segment",
    x = c(0.36, 0.54),
    xend = c(0.40, 0.58),
    y = 0.5,
    yend = 0.5,
    colour = unname(palette[c("常规方案", "强化方案")]),
    linewidth = 0.9
  ) +
  annotate(
    "text",
    x = c(0.415, 0.595),
    y = 0.5,
    label = c("常规方案", "强化方案"),
    hjust = 0,
    size = 2.8,
    family = plot_family,
    colour = ink
  ) +
  coord_cartesian(xlim = c(0, 1), ylim = c(0, 1), clip = "off") +
  theme_void(base_family = plot_family) +
  theme(plot.margin = margin(0, 0, 0, 0))
legend_plot <- wrap_elements(full = legend_plot)

risk_plot <- ggplot(
  risk_data,
  aes(x = time, y = row, label = n, colour = group, hjust = hjust)
) +
  geom_text(size = 3.0, family = plot_family, show.legend = FALSE) +
  scale_colour_manual(values = palette) +
  scale_x_continuous(
    limits = c(0, 36),
    breaks = risk_times,
    expand = c(0.01, 0.01)
  ) +
  scale_y_continuous(
    limits = c(0.6, 2.4),
    breaks = c(1, 2),
    labels = c("强化方案", "常规方案")
  ) +
  labs(x = "随访时间（月）", y = "风险集") +
  theme_minimal(base_size = 8.5, base_family = plot_family) +
  theme(
    panel.grid = element_blank(),
    axis.ticks.y = element_blank(),
    axis.title = element_text(colour = ink, size = 9),
    axis.title.y = element_text(angle = 0, vjust = 0.5, margin = margin(r = 14)),
    axis.text = element_text(colour = "#334155", size = 8),
    plot.margin = margin(0, 10, 6, 8)
  )

figure_body <- legend_plot / survival_plot / risk_plot +
  plot_layout(heights = c(0.38, 4.2, 1.15))
figure <- figure_body +
  plot_annotation(
    title = "调整后无事件生存曲线",
    theme = theme(
      plot.title = element_text(
        family = plot_family,
        face = "bold",
        size = 11,
        colour = ink,
        hjust = 0.5,
        margin = margin(b = 4)
      ),
      plot.background = element_rect(fill = "white", colour = NA)
    )
  )

forest_plot <- ggplot(
  forest_data,
  aes(y = label, x = estimate, xmin = conf_low, xmax = conf_high)
) +
  geom_vline(xintercept = 1, colour = "#94A3B8", linewidth = 0.55) +
  geom_errorbar(
    orientation = "y",
    width = 0,
    linewidth = 0.75,
    colour = "#0F766E"
  ) +
  geom_point(
    shape = 21,
    size = 3.1,
    stroke = 0.8,
    colour = "#0F766E",
    fill = "white"
  ) +
  geom_text(
    aes(x = 3.15, label = estimate_label),
    hjust = 0,
    size = 2.75,
    family = plot_family,
    colour = ink
  ) +
  annotate(
    "text",
    x = 3.15,
    y = 6.7,
    label = "风险比（95% 置信区间）",
    hjust = 0,
    size = 2.9,
    fontface = "bold",
    family = plot_family,
    colour = ink
  ) +
  scale_x_log10(
    limits = c(0.45, 5.4),
    breaks = c(0.5, 0.75, 1, 1.5, 2, 3),
    labels = c("0.50", "0.75", "1.00", "1.50", "2.00", "3.00")
  ) +
  scale_y_discrete(drop = FALSE) +
  coord_cartesian(clip = "off") +
  labs(
    title = "多变量 Cox 回归森林图",
    x = "风险比（对数刻度）",
    y = NULL
  ) +
  theme_minimal(base_size = 8.5, base_family = plot_family) +
  theme(
    panel.grid.major.y = element_line(colour = "#E8EDF2", linewidth = 0.4),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.text.x = element_text(colour = "#334155", size = 8),
    axis.text.y = element_text(colour = ink, size = 8.4, hjust = 0),
    axis.title.x = element_text(colour = ink, size = 9, margin = margin(t = 6)),
    plot.title = element_text(
      family = plot_family,
      face = "bold",
      size = 11,
      colour = ink,
      hjust = 0.5,
      margin = margin(b = 12)
    ),
    plot.margin = margin(10, 20, 8, 10),
    plot.background = element_rect(fill = "white", colour = NA)
  )

pdf_path <- file.path(output_dir, "adjusted-survival.pdf")
png_path <- file.path(output_dir, "adjusted-survival.png")
mobile_path <- file.path(output_dir, "adjusted-survival-mobile.png")
paper_path <- file.path(output_dir, "adjusted-survival-paper.png")
forest_pdf_path <- file.path(output_dir, "cox-forest.pdf")
forest_png_path <- file.path(output_dir, "cox-forest.png")

cairo_pdf(pdf_path, width = 160 / 25.4, height = 105 / 25.4, onefile = TRUE)
showtext_begin()
print(figure)
showtext_end()
invisible(dev.off())

ragg::agg_png(
  png_path,
  width = 160,
  height = 105,
  units = "mm",
  res = 300,
  background = "white"
)
print(figure)
invisible(dev.off())

cairo_pdf(forest_pdf_path, width = 170 / 25.4, height = 105 / 25.4, onefile = TRUE)
showtext_begin()
print(forest_plot)
showtext_end()
invisible(dev.off())

ragg::agg_png(
  forest_png_path,
  width = 170,
  height = 105,
  units = "mm",
  res = 300,
  background = "white"
)
print(forest_plot)
invisible(dev.off())

ragg::agg_png(
  paper_path,
  width = 150,
  height = 92,
  units = "mm",
  res = 300,
  background = "white"
)
print(figure_body)
invisible(dev.off())

ragg::agg_png(
  mobile_path,
  width = 108,
  height = 102,
  units = "mm",
  res = 260,
  background = "white"
)
print(figure)
invisible(dev.off())
