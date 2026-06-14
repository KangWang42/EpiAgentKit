# 个人 R 代码风格（软约束 · 服从工作流）

> 定位：写出读起来像本人手写的 R 代码。**这是风格偏好，不是硬红线**——与可复现性、正确性、项目结构红线（编号/registry/单源/实跑验证）冲突时**一律服从红线**，风格让路。
> 提炼自用户真实脚本。目标：管道为主线、中间变量少而短、命名语义化、输出干净、注释适度。

目录：1 管道为主线 · 2 中间变量（少 + 命名）· 3 map 优先 · 4 输出干净 · 5 版面缩进 · 6 注释规范 · 7 生态偏好 · 8 与红线的张力

## 1 管道为主线

清洗/变换用一条连续 `%>%`(或 `|>`) 链推进，每步独立成行；不为每个中间结果起名。

```r
# 好：一条链到底，意图连续可读
data_neat <- data |>
  mutate(病程 = floor(as.numeric(difftime(测评时间, 首次发病时间, units = "days")))) |>
  group_by(病历号) |>
  filter(first(病程) <= 180) |>
  ungroup() |>
  rename(年龄 = `年龄（岁）`) |>
  mutate(across(starts_with("是否"), ~ factor(., 0:1, c("否", "是"))))

# 差：每步都落一个临时变量，命名无信息、占满环境
d1 <- mutate(data, 病程 = ...); d2 <- group_by(d1, 病历号); d3 <- filter(d2, ...); d4 <- ungroup(d3)
```

## 2 中间变量：少而短、命名语义化

- **少**：能进管道就不另起变量；只有"要复用"或"链太长该断开"时才落一个中间对象。
- **命名**：用语义化短名，体现"是什么/到哪一步"，不用 `df1/tmp/x2`。本人惯用：`data`(原始)→`data_neat`(清洗后)→`data_completed`/`data_neat_imputed`(插补后)→`data_baseline`/`data_repeat`(分析用子集)。
- 一个长流程拆 2–4 个有意义的里程碑对象即可，不堆十几个。

```r
# 好：少数几个语义里程碑
data_baseline <- data_neat_imputed |> group_by(身份证号) |> slice_min(病程, n = 1, with_ties = FALSE) |> ungroup()
# 差：mid1 / mid2 / temp_df / result3
```

## 3 map / 向量化优先于循环与分支

- 批量读文件、批量建表、列表变换 → `purrr::map` / `map_dfr`，配匿名函数 `\(x){}` 或 `~ .x$field`；**少写 `for`**。
- 批量列操作 → `across() + starts_with()/matches()/paste0()`；多分支重编码 → `case_when()`，少写连串 `if/else`。
- 真正必要（带副作用、顺序依赖、写多文件）才用 `for`。

```r
# 好：map 批量读 + 合并
recs <- dir_ls("raw", type = "directory") |>
  map(\(p) import(path(p, "明细.xls")) |> mutate(id = path_file(p), .before = 1))
all <- map_dfr(recs, identity)

# 好：across + case_when 取代逐列 if
df <- df |>
  mutate(across(c(收缩压, 舒张压, starts_with("NIHSS_")), as.numeric),
         风险 = case_when(评分 >= 5 ~ "高", 评分 >= 3 ~ "中", TRUE ~ "低"))
```

## 4 输出干净

- 最终脚本**不留调试 `cat()`/`print()`**；噪声用 `suppressWarnings()` / `printFlag = FALSE` / `quietly` 静音。
- 注意与红线的张力：**实跑验证 + 全量扫 error/warning 是必须的**，但那在"运行/检查"环节做（控制台或临时检查），**不是往交付脚本里塞 print**。交付脚本保持安静。

## 5 版面与缩进

- 长向量、多参数函数调用一参一行、对齐；每个管道步骤独立成行。
- 遵 tidyverse 风格缩进（2 空格），`<-` 赋值，运算符两侧空格。

```r
费用指标 <- c(
  "西药", "诊查费", "护理费", "化验费",
  "中成药", "理疗", "总金额", "自费"
)
```

## 6 注释规范

- **分节**用 RStudio 折叠标记：`# 数据导入 --------------`、`# 可视化 --------------`（`----` 触发可折叠 section）。
- **关键步骤**一句话 inline 注释，说明"为什么这样切/为什么选它"，不解释语法、不写废话。
- 注释中文，简短；**NEVER** 堆逐行注释、**NEVER** 留 `# print(x)` 之类调试残留或大段被注释掉的死代码（死代码进 `09_backup/`，不留正文）。

```r
# 数据清洗 --------------
data_neat <- data |>
  filter(first(病程) <= 180) |>          # 仅纳入 180 天内首评
  mutate(年龄段 = if_else(年龄 < 60, "<60", ">=60"))
```

## 7 生态偏好（可选，不强制）

本人惯用 `fs`(path/dir_ls/path_file)、`str_glue()` 拼路径、`factor(..., ordered = TRUE)` 有序因子；描述统计常用 `compareGroups::descrTable`。
**但**：包选择以"可复现 + 团队可读"为先——r-biostats §四 默认栈（tidyverse/here/readxl/writexl/gtsummary）是基线，个人偏好包在不牺牲可移植性时可用；`bruceR::set_wd()`/`import` 等便利函数若引入重依赖或路径魔法，优先用 `here::here()` + `readxl`/`writexl` 等显式写法。

## 8 与硬红线的张力（红线优先）

| 个人习惯 | 冲突点 | 处理 |
|---|---|---|
| `rm(list = ls())` 开头 | 交互习惯 | 脚本化复现不必依赖，可保留但不作为复现前提 |
| `descrTable() |> export2word(.doc)` | 交付物 = xlsx 不 doc、Table{N} 命名 | 服从红线：导 xlsx、走 registry `table_path()` |
| 干净无 cat | 须实跑扫 error/warning | 验证在运行环节做，最终脚本仍干净 |
| 混用 `%>%` / `|>` | 一致性 | 任选其一、全脚本统一即可 |

风格服务可读，不与"编号连续 / registry 单源 / config·conventions 单源 / results.yaml 单源 / 实跑验证"任一红线对抗。
