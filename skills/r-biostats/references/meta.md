# Meta 分析

检索、筛选、偏倚风险评价和报告规范（PRISMA 等）先按 `evidence-research` 确认。本文件只处理已提取数据的合并与解释。

## 核心包

```r
library(meta)      # 常规合并、森林图、发表偏倚
library(metafor)   # 复杂模型、多水平与 meta 回归
```

## 合并前确认

- 效应尺度：二分类用 RR、OR 或 RD，连续变量用 MD（同一量表）或 SMD（不同量表）。尺度按研究问题和结局频率选择，不因显著与否更换。
- 模型：研究间存在临床或方法学差异时默认随机效应。tau² 用 REML；研究数较少（约少于 10 项）时置信区间用 Hartung-Knapp 调整。
- 稀有事件或零事件研究：固定效应部分用 Mantel-Haenszel 法，零事件的连续性校正方式要写明；双臂均为零事件的研究不能提供 OR/RR 信息。

## 二分类结局

```r
m <- metabin(
  event.e, n.e, event.c, n.c,
  studlab = study, data = data,
  sm = "RR", method = "MH",
  common = FALSE, random = TRUE,
  method.tau = "REML", method.random.ci = "HK",
  prediction = TRUE
)
summary(m)
```

## 连续结局

```r
m <- metacont(
  n.e, mean.e, sd.e, n.c, mean.c, sd.c,
  studlab = study, data = data,
  sm = "SMD",
  common = FALSE, random = TRUE,
  method.tau = "REML", method.random.ci = "HK",
  prediction = TRUE
)
```

## 异质性

同时报告 tau²、I² 及其置信区间和 95% 预测区间。I² 只表示研究间变异占总变异的比例，受研究精度影响，不用固定阈值（如 50%、75%）机械分级；判断异质性是否重要要结合效应方向、大小和预测区间。预测区间跨过无效值时，要说明新研究中的效应可能方向不同。

## 森林图

```r
forest(m,
  leftcols = c("studlab", "event.e", "n.e", "event.c", "n.c"),
  rightcols = c("effect", "ci", "w.random")
)
```

`forest()` 使用基础图形设备，按 `publication-figures` 的最终尺寸打开设备后绘制，导出方式见 [visualization.md](visualization.md)。

## 发表偏倚与小研究效应

```r
funnel(m)
metabias(m, method.bias = "Peters", k.min = 10)   # 二分类 OR/RR；连续结局用 "Egger"
```

研究数少于 10 项时检验效能很低，不做正式检验，只描述漏斗图。漏斗图不对称不等于发表偏倚，也可能来自真实异质性或小研究的方法学差异。

## 亚组分析与 meta 回归

```r
m_sub <- update(m, subgroup = region)
m_sub                      # 查看亚组间差异检验
metareg(m, ~ year)
```

亚组和协变量应事先设定；研究数少时（通常每个协变量少于 10 项研究）结果不稳定。亚组间差异只是研究层面的观察性比较，不能按个体层面的效应修饰解释。
