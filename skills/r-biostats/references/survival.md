# 生存分析

## 核心包

```r
library(survival)
library(survminer)
library(gtsummary)
```

## 分析前确认

- 时间零点、时间尺度（随访时间或年龄）、删失定义和随访截止日期。以年龄为时间尺度或存在延迟进入时，使用计数过程格式 `Surv(entry_time, exit_time, event)`，不要把进入前的时间计为暴露期。
- 结局是否存在竞争事件。存在时先确定估计目标，再选方法（见“竞争风险”）。
- `event` 编码为 0/1 或逻辑值，1 表示事件；多类结局使用因子，删失为第一水平。

## Kaplan-Meier

曲线组件与最终样式服从 `publication-figures`，R 实现与导出见 [visualization.md](visualization.md)。正式生存推断默认保留风险表；只有页面相邻位置已可靠提供风险集信息且不影响解释时才省略。log-rank 检验、置信带和中位生存只在回答研究问题且可估时启用。

```r
fit <- survfit(Surv(time, event) ~ group, data = data)
```

中位生存时间及其 95% CI 用 `quantile()`，单组和多组都适用；随访期内生存率未降到 50% 时结果为 `NA`，应如实报告为“未达到”：

```r
quantile(fit, probs = 0.5)
```

## Cox 回归

```r
cox <- coxph(Surv(time, event) ~ exposure + age + sex, data = data)

tbl_regression(cox, exponentiate = TRUE)  # HR 与 95% CI
```

需要多水平分类变量的整体检验时再加 `add_global_p()`。结点处理默认 Efron 法，不需要另行设置。

## 比例风险假设

```r
zph <- cox.zph(cox)
zph            # 各变量与整体检验
plot(zph)      # Schoenfeld 残差随时间的变化，必须同时查看
```

检验不显著只表示没有检出违反，不能证明比例风险成立；大样本中轻微偏离也可能显著。结合残差图和研究问题判断偏离是否足以影响解释。

发现违反时按研究问题选择：

- 非研究关注的协变量：按该变量分层，`coxph(Surv(time, event) ~ exposure + age + strata(sex), data = data)`。
- 需要描述随时间变化的效应：必须同时写出主效应和明确的时间函数；不写 `tt` 函数时 `tt(x)` 等同于 `x`，模型不会报错但没有意义。

```r
coxph(Surv(time, event) ~ exposure + tt(exposure) + age + sex, data = data,
      tt = function(x, t, ...) x * log(t))
```

- 也可以按时间分段报告不同时段的 HR（`survSplit()` 后加入交互项），或改用限制平均生存时间（RMST）等不依赖比例风险的指标。

## 竞争风险

先确定估计目标，两种方法回答不同的问题：

- **病因研究**（暴露是否影响目标事件的发生速率）：病因别 Cox 模型，把竞争事件视为删失。

```r
coxph(Surv(time, event_type == "death") ~ exposure + age + sex, data = data)
```

- **预测或描述累积发生风险**：累积发生函数（CIF）与 Fine-Gray 部分分布风险模型。`event_type` 必须是以删失为第一水平的因子。

```r
data$event_type <- factor(data$event_type, levels = c("censor", "death", "other"))
tidycmprsk::cuminc(Surv(time, event_type) ~ exposure, data = data)      # CIF 与 Gray 检验
tidycmprsk::crr(Surv(time, event_type) ~ exposure + age, data = data)  # 部分分布 HR
```

存在竞争事件时不用 1 − KM 估计累积发生率，它会高估风险。部分分布 HR 不能解释为病因别风险比。
