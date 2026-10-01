# R 代码组织与可读性规范

> 本文件用于在不影响正确性和复现性的前提下保持 R 代码清楚、紧凑，并与项目既有写法协调。若既有脚本存在明显的可读性、复现性或正确性问题，不照搬原写法。
> 项目没有相反的既有规范时，tidyverse 是正式研究代码的整体默认表达方式，而不是仅用于局部清洗的可选风格。代码应先让研究者看见数据如何变成分析集、模型和表图，再看见必要的文件调度与失败条件。与项目编号、表图登记、结果来源、实际运行和异常处理要求冲突时，以这些必需要求为准。

目录：1 脚本开头 · 2 管道主线 · 3 读入与类型 · 4 连接与分组的防错 · 5 函数边界 · 6 中间对象与命名 · 7 purrr 批处理 · 8 模型结果提取 · 9 检查位置与控制流 · 10 正文与构建脚本 · 11 版面 · 12 注释 · 13 常用包 · 14 反模式对照 · 15 自动风格检查 · 16 冲突与终审

以下写法已在 R 4.5、dplyr 1.1、purrr 1.2、tidyr 1.3 下实跑验证。项目锁定的旧版本不支持某项时，沿用该版本可用的等价写法并在代码旁简短说明。

## 1 脚本开头

- 每个实际使用的包直接写一行 `library()`，让依赖一眼可见；只调用一两个函数的包可以直接写 `pkg::fun()`，不必加载。
- 不用 `suppressPackageStartupMessages({ ... })` 包裹包加载，也不为整段脚本统一静音。
- 只加载本脚本实际使用的包；不要把技术栈清单机械复制到每个脚本。
- 不写 `rm(list = ls())`、`setwd()` 或绝对路径。脚本由 `run_pipeline.R` 从项目根启动，路径一律相对项目根。

```r
library(tidyverse)
library(broom)
library(survival)
```

## 2 管道作为主线

清洗、筛选、连接、重编码、汇总和整理默认使用 `dplyr`、`tidyr` 与一条连续管道推到目标对象，每步独立成行。字符串、分类、读写和批处理分别优先使用 `stringr`、`forcats`、`readr` 与 `purrr`。不要仅为了“分步骤展示”把同一条变换链拆成多个对象，也不要在没有项目既有约束、包接口或经验证性能需要时，把整段分析改写成 `data.table`、大量基础 R 拼装或标量控制流。

- 新脚本使用原生管道 `|>` 和匿名函数 `\(x)`；维护使用 `%>%` 的旧脚本时跟随原文件。只有需要 `.` 占位符放到非首参数等 `|>` 做不到的写法时才用 `%>%`。
- 列的批量变换用 `across()`，按条件筛行用 `if_any()` / `if_all()`；二分支用 `if_else()`，多分支用 `case_when(..., .default = )`，值到值的映射用 `case_match()`。
- 分组汇总优先用 `.by` 参数（`summarise(..., .by = group)`、`mutate(..., .by = id)`），结果不会残留分组；必须多步分组时用 `group_by()`，并在该段结束处 `ungroup()`。
- 宽长转换用 `pivot_longer()` / `pivot_wider()`，不用 `gather()` / `spread()` / `reshape()`。
- 字符串拼接用 `str_glue()`，不用 `paste0()` 嵌套多层。

```r
# 好：从原始数据连续得到分析数据
data_neat <- data_raw |>
  mutate(
    disease_days = as.numeric(assess_date - onset_date),
    across(starts_with("is_"), \(x) factor(x, levels = 0:1, labels = c("No", "Yes"))),
    age_group = case_when(
      age < 60 ~ "<60",
      age >= 60 ~ ">=60",
      .default = NA_character_
    )
  ) |>
  filter(first(disease_days) <= 180, .by = patient_id)

# 差：同一条链被说明性中间对象切碎
data_joined <- left_join(data, ref, by = "patient_id")
data_grouped <- filter(data_joined, !is.na(group))
data_complete <- filter(data_grouped, if_all(all_of(vars), ~ !is.na(.x)))
```

只在以下情况断开管道：该对象是用户要求的明确产物；后续分析存在真实分支并会复用它；或模型、图、表等对象类型发生实质转换。不要先制造不必要的导出或检查，再以“需要复用”为由保留中间对象。

## 3 读入与类型

原始数据的问题大多在读入时产生，读入写法本身就是数据核对的一部分。

- `readr::read_csv()` 显式写 `col_types`，至少为标识符、日期和容易被猜错的列指定类型；ID 类列读为字符，保留前导零。
- 缺失码写进 `na = c("", "NA", ...)`，只放已从原始数据字典或数据来源核实的编码（如 `999`、`-9`）；不确定是否为缺失码时先回原始来源核对，不直接替换。
- SPSS/Stata 数据用 `haven::read_*()` 读入，值标签用 `haven::as_factor()` 或 `labelled` 包转换，不手工重写对照表。
- 新项目在读入后紧接一次 `rename()`，把代码中使用的列名统一为英文 `snake_case`；中文原名保留在变量标签、因子水平和表图标签中。这样可避免 Windows 编码与 `lintr` 的问题，也方便跨工具复用。已有项目沿用原有列名语言，不为统一命名扩大修改范围。
- 日期用 `as.Date()` 或 `lubridate` 按实际格式解析，解析失败产生的 `NA` 数量要在运行检查中核对，不能与真实缺失混在一起。

```r
data_raw <- read_csv(
  "01_data/rawdata/cohort.csv",
  col_types = cols(.default = col_character(), 年龄 = col_double(), 随访天数 = col_double()),
  na = c("", "NA", "999")
) |>
  rename(patient_id = 患者编号, sex = 性别, age = 年龄, follow_days = 随访天数)
```

## 4 连接与分组的防错

连接和分组出错通常不会报错，只会静默改变行数，所以用参数把预期关系写进代码：

- 连接键用 `join_by()` 写明。
- 给每条记录挂接查找表（每条记录都必须恰好匹配一行）时，使用 `inner_join(x, lookup, by = join_by(key), relationship = "many-to-one", unmatched = c("error", "drop"))`：键重复或有记录匹配不上都会立即报错。
- 确实允许匹配不上的记录保留为缺失时，使用 `left_join(..., relationship = "many-to-one")`，并在运行检查中报告未匹配的记录数。注意 `left_join()` 的 `unmatched = "error"` 检查的是查找表中未被使用的键，不是左表中未匹配的记录。
- 一对多或多对多连接只在研究设计确实需要时使用，并写明 `relationship = "one-to-many"` 或 `"many-to-many"`。

```r
data_linked <- data_neat |>
  inner_join(
    hospital,
    by = join_by(hospital_id),
    relationship = "many-to-one",
    unmatched = c("error", "drop")
  )
```

## 5 函数边界

R 分析脚本默认按数据导入、清洗、分析、导出等顺序分节，不把每一段一次性代码命名成函数。不要沿用 Python 式“所有步骤先定义函数、最后统一调用”的组织方式。

仅在以下情况抽取具名函数：

- 同一逻辑会被调用多次；
- 需要由 `map*()` / `walk*()` 对不同参数重复执行；
- 是跨脚本复用的稳定工具，如结果渲染或统一出图；
- 算法本身复杂，独立测试边界能明显降低错误风险。

只调用一次的格式化、清洗或导出步骤优先直接写入管道。匿名函数 `\(x) ...` 是批处理语法，不等于过度函数化。像“定义一次绘图函数，再用 `map2()` / `walk2()` 批量生成”属于合理复用。函数只通过参数获得输入、通过返回值交付结果，不读写全局变量，不用 `<<-`。

同一稳定工具在多个主脚本重复出现时，保留一份经过测试的实现并由各脚本明确加载；不要让 `atomic_write_csv()`、SQL 转义、结果读取或统一格式化函数各自复制演变。只在脚本必须独立分发且用户明确接受重复时保留副本，并核对行为一致。

## 6 中间对象与命名

- 能进入管道就不另起对象。确需单独保存时，名称应说明研究对象、时间或分析角色，不用 `df1`、`tmp`、`mid2`、`result3`。
- 对象名和列名使用小写 `snake_case`。外层对象沿用项目已经形成的命名语言；没有既有规则时，按 `<对象>_<主题>_<时间>_<阶段>` 组合真正有区分作用的部分，例如 `data_demo_2018`、`data_health_all`、`data_baseline`、`model_primary`、`table_baseline`；不要求每个名称机械包含全部部分。
- 同类对象按同一顺序命名，使年份、数据模块和处理阶段能够并排辨认。常用阶段后缀包括 `_raw`、`_neat`、`_baseline`、`_repeat`、`_long`、`_wide` 和 `_imputed`，只在对象确有该含义时使用。
- 顶层数据、模型和成品不用 `required_inputs`、`result_document`、`expected_variables`、`row_index`、`value_columns` 等只说明程序实现的名称代替研究含义。这类名称只适合短小局部代码或稳定工具的参数，且离开所在语句后不再承担研究对象的角色。
- 函数名用动词说明动作，数据与结果对象用名词说明内容；单个变量用单数，集合或向量用复数。局部迭代参数可以简短，但不得与外层研究对象混淆。
- 不为每个筛选、连接、格式化和核验步骤各留一个对象。模型、最终表、最终图或被真实分支复用的数据可以保留。

```r
data_baseline <- data_neat_imputed |>
  slice_min(disease_days, n = 1, with_ties = FALSE, by = patient_id)
```

## 7 purrr 批处理：先定义控制向量或参数表，再直接迭代

- 单输入并返回对象用 `map()`，成对输入用 `map2()`，多参数用 `pmap()` 遍历一张参数表（每列对应一个参数名），需要名称或位置用 `imap()`。
- 返回单个原子值时用类型稳定的 `map_dbl()`、`map_chr()`、`map_lgl()`、`map_int()`；不用 `sapply()`，它的返回类型随输入变化。
- 逐项得到数据框再合并用 `map() |> list_rbind()`（需要来源列时加 `names_to =`）；`map_dfr()` / `map_dfc()` 已被取代，不再使用。
- 保存文件、写表等只产生副作用的任务用 `walk()`、`walk2()`、`pwalk()` 或 `iwalk()`，不要先生成无用返回列表。
- 分组建模用 `nest(.by = group)` 加 `mutate(fit = map(data, ...))`，模型、结果和分组信息保存在同一张表中，不散落成多个对象。
- 批量任务中个别元素可能合理失败（如某亚组事件过少）时，用 `possibly(f, otherwise = NULL)` 包装，事后统计并报告失败的元素，不让失败被静默跳过；元素不应失败时不要包装，purrr 报错会指出出错的位置。
- 批处理前集中定义变量向量、标签向量或参数表；迭代体直接完成目标，不堆中间过程。
- `for` 并非禁用。顺序依赖前一步结果时 `for` 更清楚，使用 `seq_along()` 遍历预先定义的向量或列表；避免 `1:n`、循环内连串 `if` 和逐步增长的对象。

```r
# 多个模型设定：参数表 + map，结果留在同一张表中
models <- tibble(
  model = c("crude", "adjusted"),
  formula = list(death ~ smoking, death ~ smoking + age + sex)
) |>
  mutate(
    fit = map(formula, \(f) glm(f, family = poisson(link = "log"), data = data_neat)),
    estimates = map(fit, \(m) tidy(m, exponentiate = TRUE, conf.int = TRUE))
  )

# 分组建模，个别亚组失败时记录而不中断
safe_fit <- possibly(\(d) coxph(Surv(follow_years, death) ~ smoking, data = d), otherwise = NULL)
models_by_region <- data_neat |>
  nest(.by = region) |>
  mutate(fit = map(data, safe_fit), failed = map_lgl(fit, is.null))

# 批量出图：命名向量控制变量与标签，walk2 只产生文件
vars_to_plot <- c(icf_total = "ICF-RS 总分", icf_body = "ICF-身体功能")
walk2(names(vars_to_plot), vars_to_plot, \(var_name, var_label) {
  save_fig(plot_line(data_neat, var_name, var_label), str_glue("fig_line_{var_name}"), type = "wide")
})
```

## 8 模型结果提取

- 系数、区间和 P 值用 `broom::tidy()`（比值类加 `exponentiate = TRUE, conf.int = TRUE`），模型整体指标用 `glance()`，逐行预测与残差用 `augment()`；多重插补的合并结果用 `mice::pool()` 后再 `tidy()`。
- 不用 `summary(fit)$coefficients[2, 4]` 这类按位置取值的写法；按 `term` 名称筛选，参照水平或变量顺序变化时不会取错行。
- 统计表优先用 `gtsummary` 或 `compareGroups` 从模型对象直接生成，关键数字同时按固定名称写入 `results/results.yaml`，不在两处各算一遍。

```r
table_rr <- models |>
  select(model, estimates) |>
  unnest(estimates) |>
  filter(term == "smokingYes")
```

## 9 检查位置与控制流

检查不是越多越安全。先判断检查保护的是什么，再放到对应位置：

| 检查类型 | 应放位置 | 保留条件 |
|---|---|---|
| 文件、参数、运行时与调用顺序 | `run_pipeline.R`、命令行入口或确定性构建器的开头 | 一次集中检查，能指出实际缺少的输入或参数 |
| 会改变科学有效性的稳定不变量 | 最接近该风险的数据处理或分析位置 | 失败后不能得到有效结果，且错误信息说明实际研究含义 |
| 本次运行的样本量、范围、文件和显示核验 | 测试、运行检查、表图验收或审计记录 | 用于确认本次产物，不混入正式分析主线 |

- 普通清洗、分析和统计表脚本直接读取已经声明的输入。不要在每个脚本重复建立 `required_inputs`，再用 `if (any(!file.exists(...))) stop(...)` 预检；读取函数本身能够报告具体缺失文件，标准项目的整批输入检查由总运行入口集中完成。
- `if` 只处理真正的单个执行分支，例如可选分析是否启用；数据列的逐记录判断使用 `if_else()` 或 `case_when()`，批量对象差异使用命名配置和 `map*()`。保留的标量 `if` 应短小、少嵌套，并让读者直接看出它控制的研究步骤。
- `stop()`、`stopifnot()` 或 `rlang::abort()` 只用于命令行入口无法继续，或稳定科学不变量被破坏而无法产生有效结果的情况。不要用它们重复包装读取、写入和包加载本来就会给出的错误，也不要为每个单元格、字段或中间对象建立独立失败分支。连接关系优先用第 4 节的参数表达，而不是事后比较行数。
- 同一项结果只读取一个已经确定的正式来源；一个成品可以按需要读取不同结果对象，但不要仅为证明一致而同时读取同一结果的两套重复来源并逐项比较。重复来源确需核对时，在结果写入测试或本次运行检查中完成，发现差异再回到最早来源。
- 生成脚本只负责形成产物；重新打开文件核对结构、样式和显示属于该产物的验收步骤。验收必须实际执行，但应放在专门的检查脚本、测试或运行阶段，不用第二套嵌套循环淹没生成逻辑。
- 必须在运行与核对阶段实际执行脚本、核对样本量与关键范围并全量扫描异常，但不默认把核对过程展示成分析正文。
- 不为“证明检查过”在交付脚本中堆硬编码样本量的 `stopifnot(nrow(...) == 678)`。这类当前批次核验放在运行检查中；只有研究设计要求长期保护的稳定不变量才保留在脚本里，并优先写成关系约束而非冻结行数。
- 最终脚本不留调试 `cat()` / `print()`、逐步对象展示或被注释掉的检查代码。长批处理确需进度提示时只保留简短且有用的信息。
- 顶层调用若返回数据库影响行数、写入状态或其他无须展示的值，应显式赋值、用 `invisible()` 处理或由封装函数统一检查，避免日志出现孤立的 `[1] 0`、行数或对象打印。需要核验的值使用带语义的断言或消息，不依赖偶然回显。
- 不用全局 `suppressWarnings()` 掩盖异常。只有已定位、确认不影响结果且范围明确的已知警告，才在具体调用处窄范围静音；警告原因及处理结果仍需写入验证记录。

完成组织后，从上到下阅读脚本应能连续回答“读入什么、如何形成分析对象、进行了什么分析、生成了什么产物”。若必须先穿过大段路径检查、重复结果核对、通用工作簿实现或失败分支才能找到这些内容，应移动检查、复用稳定工具或缩短控制流，而不是只增加注释。

## 10 正文与构建脚本

- 分析脚本保存研究计算、结果对象和生成逻辑，不把整篇论文或长篇报告写成数百行 `lines <- c(...)` 字符向量。正式正文写在 Markdown、Quarto、R Markdown 或专门的文本来源中；构建脚本只读取已经确认的正文与结果值并完成装配。
- Quarto 或 R Markdown 本身是正文来源时，可以在同一文件中组合文字和代码，但仍应把数据处理与可复用分析逻辑放在独立脚本中，避免正文段落承担计算逻辑。
- 自动生成文字只用于结构稳定、可逐项核对的短内容，如表注、结果摘要或固定声明。论文的引言、结果取舍和讨论论证必须经过 `academic-publishing` 与 `academic-humanizer` 的内容检查，不能把数字插值成功当作论文完成。
- `02_code/` 只保存正式数据处理、统计分析、结果写入和直接统计表图生成代码。论文来源及确有长期需要的装配脚本放在 `paper/`，长期自动检查放在 `tests/` 或 `checks/`，本次产物验收和一次性脚本放在 `09_backup/workbench/`。总分析入口只按明确清单调用正式分析代码；脚本编号、函数化或被唯一入口调用不能改变其职责。

## 11 版面与缩进

- 遵循 tidyverse 风格指南：2 空格缩进，`<-` 赋值，运算符和逗号后留空格，行宽不超过 120 字符。
- 每个管道步骤独立成行；长向量和多参数调用按语义换行，一个参数一行时右括号单独成行。
- 用 `TRUE` / `FALSE`，不用 `T` / `F`。

```r
cost_items <- c(
  "western_medicine", "consultation", "nursing", "laboratory",
  "chinese_patent_medicine", "physiotherapy", "total", "out_of_pocket"
)
```

## 12 注释规范

- 分节使用 RStudio 折叠标记，如 `# 数据导入 --------------`、`# 可视化 --------------`。
- 注释简短、中文，解释为什么采用该口径或步骤；不逐行翻译语法，不写“定义变量”“调用函数”“保存结果”这类代码已说明的废话。
- 不留 `# print(x)`、大段注释掉的旧代码或生成过程说明。被当前版替代且需要恢复的正式项目旧实现进入 `09_backup/archive/`；临时试验代码进入 `09_backup/workbench/`。

```r
# 数据清洗 --------------
data_neat <- data_raw |>
  filter(first(disease_days) <= 180, .by = patient_id) |>  # 仅纳入 180 天内首评
  mutate(age_group = if_else(age < 60, "<60", ">=60"))
```

## 13 常用包与兼容性

需要为新功能选择包、替换现有包或准备编写通用函数时，执行 [包选择与复用](package-selection.md)。先沿用项目中已经验证且能满足当前口径的包，再核对成熟包的公开接口；不要用长篇自定义函数重复 tidyverse、bruceR、compareGroups、gtsummary 或领域专用包已经稳定提供的能力，也不要把包内未导出的实现复制进项目。

tidyverse 继续承担默认的数据整理与批处理主线；bruceR 可以在其便利接口与已确认方法完全一致时使用；描述性表格按 `descriptive.md` 选择 compareGroups、gtsummary 或兼容的既有包。便利函数不能隐藏正式项目的相对路径、字段类型、标签、缺失码、方法默认值或结果来源。

## 14 反模式对照

| 不要这样写 | 改为 | 原因 |
|---|---|---|
| `sapply(x, f)` | `map_dbl(x, f)` 等类型稳定版本 | 返回类型随输入变化 |
| `map_dfr(x, f)` | `map(x, f) \|> list_rbind()` | 已被取代 |
| `df$col[df$g == "a"] <- ...` 逐列赋值 | `mutate(col = if_else(g == "a", ..., col))` | 保持在管道主线中 |
| `ifelse()` | `if_else()` 或 `case_when()` | 类型检查更严格，缺失处理明确 |
| `group_by() \|> summarise()` 后忘记 `ungroup()` | `summarise(..., .by = g)` | 不残留分组 |
| `left_join()` 后对比行数 | `join_by()` + `relationship` / `unmatched` | 在连接处直接报错 |
| `summary(fit)$coefficients[2, 4]` | `tidy(fit) \|> filter(term == ...)` | 不依赖行列位置 |
| `gather()` / `spread()` | `pivot_longer()` / `pivot_wider()` | 已被取代 |
| `setwd()`、绝对路径、`attach()` | 从项目根运行、相对路径、显式 `data =` | 可复现、无隐藏状态 |
| `<<-`、在函数中修改全局对象 | 参数输入、返回值输出 | 避免隐藏依赖 |
| `T` / `F` | `TRUE` / `FALSE` | `T`、`F` 可被重新赋值 |

## 15 自动风格检查

项目环境已有 `styler` 和 `lintr` 时，修改后对受影响脚本做一次只读检查，不自动改写用户文件：

```r
styler::style_file("02_code/03_models.R", dry = "on")   # 只报告会调整的格式，不修改文件
lintr::lint("02_code/03_models.R",
            linters = lintr::linters_with_defaults(
              line_length_linter = lintr::line_length_linter(120),
              object_name_linter = NULL   # 允许已有项目的中文列名
            ))
```

逐条处理报告的问题；确属项目既有约束的，不为消除提示而改写。没有这两个包时按本文件人工检查，不自行安装。

## 16 冲突与终审

| 个人习惯 | 冲突点 | 处理 |
|---|---|---|
| `rm(list = ls())` 开头 | 脚本化复现不应依赖清空交互环境 | 可跟随既有脚本，但不作为复现前提 |
| 只用 `descrTable() \|> export2word()` | 同一张表需要反复调整或同时输出 Excel 与 Word | 使用 `compareGroups()` → `createTable()` 计算一次并同源导出，仍服从项目表图编号和文件验收 |
| 最终脚本简洁且不展示核对过程 | 必须实际运行并扫描 error / warning | 在运行与核对阶段完成检查；仅保留必要的长期不变量 |
| 线性长脚本 | 可维护性 | 按分析逻辑分节；不以行数为由自动函数化或拆成多文件 |

风格服务可读性，不与原始数据只读、口径确认、结果数字唯一来源、相对路径、实跑验证和异常处理对抗。

每次新增、修改或重构 R 代码后，在运行前逐个检查受影响脚本：

- 依赖、输入和输出位置明确，分析顺序可从上到下阅读；适合连续变换的数据处理没有被无意义对象切碎。
- 读入写明了关键列类型和已核实的缺失码；连接写明了键和预期关系；分组汇总没有残留分组。
- 外层对象按研究主题、时间、分析角色或产物命名；同类名称的组成和顺序一致，没有用程序实现概念遮住研究含义。
- RStudio 分节标记覆盖主要阶段；函数只用于重复、高风险、批处理或复杂算法，跨脚本稳定工具没有无故复制。
- 批处理使用类型稳定的 purrr 函数；模型结果按名称提取，没有按位置索引。
- 文件与参数检查、稳定科学不变量和本次运行核验已经放在各自位置；普通分析脚本没有重复的输入预检、逐项结果互证或被嵌套 `if` 与 `stop()` 主导。
- 无调试输出、偶然返回值、注释掉的旧代码或与研究逻辑无关的说明；日志只保留能帮助判断运行状态和异常的信息。
- 分析代码没有承载长篇正式正文；需要生成论文或报告时，内容文件与装配逻辑职责清楚。
- 项目没有相反的既有规范时，数据变换和批处理已经采用一致的 tidyverse 表达；使用基础 R、循环、`data.table` 或标量分支的地方具有清楚的局部理由，没有改变整条分析主线的语言风格。
- `02_code/`、论文来源、长期检查和一次性验收按实际职责放置；总分析入口没有通过通配符自动发现编号脚本。
- 2 空格缩进、赋值符号、换行和同一脚本的管道风格一致；环境中有 `styler` / `lintr` 时第 15 节的检查已完成。是否使用管道按实际变换判断，不用管道出现次数代替代码审查。

任一项不通过时先修改代码或明确说明项目既有约束，不得仅因脚本成功执行而把代码工作项标为完成。
