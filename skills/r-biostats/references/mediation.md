# 中介与调节效应

## 核心包

```r
library(mediation)     # 反事实框架的中介分析与敏感性分析
library(lavaan)        # 多中介或潜变量的结构方程模型
library(interactions)  # 简单斜率与交互图
```

## 中介分析前确认

中介效应是因果估计量。正式分析前在 SAP 或 `DECISIONS.md` 中写明，并在论文局限中如实讨论：

1. 暴露—结局、中介—结局、暴露—中介之间均无未测混杂，已调整变量足以控制这些混杂；
2. 中介—结局的混杂因素不受暴露影响（存在时需要改用干预效应等其它估计量）；
3. 时间顺序成立：暴露先于中介，中介先于结局。横断面数据只能称为“统计上的间接关联”，不能宣称中介机制；
4. 是否存在暴露—中介交互。存在时自然直接效应与自然间接效应随暴露水平变化，必须在结局模型中纳入交互项。

观察性研究的结果写作避免“通过……导致”等因果措辞，除非上述假设有充分依据。

## 反事实框架中介分析

```r
med_fit <- lm(mediator ~ exposure + age + sex, data = data)
out_fit <- lm(outcome ~ exposure * mediator + age + sex, data = data)   # 含暴露—中介交互

res <- mediate(med_fit, out_fit,
               treat = "exposure", mediator = "mediator",
               boot = TRUE, sims = 5000)
summary(res)   # ACME（间接效应）、ADE（直接效应）、总效应；有交互时分别给出 control/treated
```

- 结局为二分类时，结局模型用 `glm(..., family = binomial())`，`mediate()` 在概率差尺度上报告效应；不能用系数相乘法（a × b）计算 logistic 模型的间接效应。
- 随机种子在调用前用 `set.seed()` 固定并记录；正式分析的 `sims` 不少于 1000。

## 敏感性分析

```r
res_noint <- mediate(med_fit, lm(outcome ~ exposure + mediator + age + sex, data = data),
                     treat = "exposure", mediator = "mediator", sims = 1000)
sens <- medsens(res_noint, rho.by = 0.05, effect.type = "indirect")
summary(sens)   # 使间接效应为 0 的中介—结局残差相关系数 rho
```

`medsens()` 仅支持不含暴露—中介交互的连续中介模型；报告使间接效应消失所需的未测混杂强度，并按研究背景判断其是否合理。

## 多中介或潜变量（SEM）

```r
model <- '
  outcome  ~ c*exposure + b*mediator
  mediator ~ a*exposure
  indirect := a*b
  total    := c + a*b
'
fit <- lavaan::sem(model, data = data, se = "bootstrap", bootstrap = 5000)
lavaan::parameterEstimates(fit, boot.ci.type = "bca.simple")
```

系数相乘法只适用于连续中介和连续结局且无交互的线性模型；因果解释仍需满足上述假设。

## 调节效应

```r
model <- lm(outcome ~ exposure * moderator + age + sex, data = data)

sim_slopes(model, pred = exposure, modx = moderator)     # 调节变量不同水平下的暴露效应
interact_plot(model, pred = exposure, modx = moderator)  # 最终样式按 publication-figures
```

连续调节变量先确定有意义的取值（如临床切点或均值 ± 1 SD），不要只报告交互项 P 值。二分类结局在 logistic 模型中检验的是相乘尺度交互；公共卫生问题常需要相加尺度交互（RERI、AP、S），两者结论可能不同，应按研究问题选择并写明尺度。

## 结果报告

| 效应 | 估计值 | 95% CI |
|------|--------|--------|
| 总效应 | | |
| 自然直接效应 | | |
| 自然间接效应 | | |
| 中介比例 | | |

中介比例只在直接效应与间接效应同向且总效应不接近 0 时报告；方向相反或总效应很小时比例不稳定，不报告。数值均从模型对象按 `results/results.yaml` 的固定名称取数。
