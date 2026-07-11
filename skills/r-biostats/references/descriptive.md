# 描述性统计与基线表

## 核心包

```r
library(gtsummary)
library(skimr)
```

## Table 1 (按分组)

```r
data |>
  select(age, sex, bmi, group) |>
  tbl_summary(
    by = group,
    statistic = list(
      all_continuous() ~ "{mean} ({sd})",
      all_categorical() ~ "{n} ({p}%)"
    ),
    label = list(age ~ "年龄", sex ~ "性别"),
    missing = "ifany"
  ) |>
  add_p() |>
  add_overall()
```

## 统计检验选择

| 变量 | 组数 | 正态 | 检验 |
|------|------|------|------|
| 连续 | 2 | 是 | t.test |
| 连续 | 2 | 否 | wilcox.test |
| 连续 | ≥3 | 是 | aov |
| 连续 | ≥3 | 否 | kruskal.test |
| 分类 | - | - | chisq.test/fisher.test |

## 导出

```r
# 先在 config.R 的 TABLE_REGISTRY 注册 "baseline"；主表一律 xlsx。
tbl |>
  gtsummary::as_tibble() |>
  writexl::write_xlsx(table_path("baseline"))
```
