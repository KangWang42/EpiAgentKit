# 交付包模板集

SKILL.md 定流程与验收条件；本文件存四个落地模板：run_all.R、包内脚本头部、00_客户说明.md、01_方法与结果.docx 结构。

## 目录

1. run_all.R 模板
2. 包内脚本头部模板
3. 00_客户说明.md 模板
4. 01_方法与结果.docx 结构与要求（内容强制要求 / 绝对禁止出现 / 结构默认）

---

## 1. run_all.R 模板

客户/复现者只运行这一个脚本，就能跑完全部分析。模板内禁用 emoji，状态用文字。

```r
# ============================================================
# 结果-4-20-训练测试集 · 一键复现脚本
# 使用方法：
#   1. 在 RStudio 打开本文件
#   2. 点 Session → Set Working Directory → To Source File Location
#   3. Ctrl+Shift+Enter 运行全文
# ============================================================

# 检查工作目录 -----------------------------------------------
if (!file.exists("run_all.R")) {
  stop("工作目录不对。请 Set Working Directory → To Source File Location")
}

# 检查 R 版本和依赖 ------------------------------------------
if (getRversion() < "4.2.0") {
  warning("建议使用 R ≥ 4.2.0；当前：", getRversion())
}

required_pkgs <- character()  # 按包内脚本实际依赖填写，不凭模板猜包
missing_pkgs <- setdiff(required_pkgs, rownames(installed.packages()))
if (length(missing_pkgs) > 0) {
  stop("缺少依赖包：", paste(missing_pkgs, collapse = ", "),
       "。请根据交付包依赖清单自行准备 R 环境；本脚本不会自动安装。")
}

# 顺序执行脚本 -----------------------------------------------
scripts <- list.files("code", pattern = "^[0-9]{2}_.*\\.R$", full.names = TRUE) |> sort()

# 如脚本含随机过程，由对应脚本按 SAP 固定并记录 seed；入口不无条件重置。

for (script in scripts) {
  message("执行：", script)
  source(script, encoding = "UTF-8", echo = FALSE)
}

writeLines(capture.output(sessionInfo()), "environment.txt")
message("全部分析已复现完成；表格见 tables/，图件见 figures/")
```

`required_pkgs` 按包内脚本实际依赖增删。

## 2. 包内脚本头部模板

```r
# ============================================================
# code/02_baseline.R
# 目的：生成基线表（按分组对比）
# 输入：results/cohort.xlsx
# 输出：由 code/config.R 的 table_path("baseline") 生成
# ============================================================

library(tidyverse)
library(gtsummary)
library(flextable)
source("code/config.R", encoding = "UTF-8")

# 路径全部用相对路径（以交付包根目录为工作目录）
cohort <- readxl::read_excel("results/cohort.xlsx")  # 中间数据 xlsx，禁 rds

# ... 分析代码 ...

# 输出
writexl::write_xlsx(tbl, table_path("baseline"))
```

**禁止出现**：
- `setwd(...)`（绝对路径）
- `source("../02_code/...")`（回读项目根）；读包外任何文件
- `readRDS(...)` / `.rds` / `.RData`（中间数据一律 xlsx）

## 3. 00_客户说明.md 模板

目标读者是不懂代码的客户/导师/合作方，不超过一页 A4。
**核心 = 文件清单**：逐个文件一行说明"是什么"，不写"这份文件夹是什么/怎么看结果"之类导览段落。
复现方法压缩为文末一两句。

```markdown
# 文件清单

| 文件 | 内容 |
|------|------|
| `01_方法与结果.docx` | 方法、结果与结论（图表已嵌入正文） |
| `run_all.R` | 一键复现脚本：依次运行 code/01-NN |
| `data/01_xxx.xlsx` | [该数据文件是什么，N 多少] |
| `code/01_xxx.R` | [该脚本做什么，产出哪些表图] |
| `tables/Table1_xxx.xlsx` | [该表内容，多 sheet 时说明各 sheet] |
| `figures/Fig1_xxx` | [该图内容] |
| `results/` | 脚本运行的中间数据（自动生成） |

图件均为 PDF 与 PNG 双格式。复现方法：RStudio 打开 `run_all.R`，
Session - Set Working Directory - To Source File Location，全选运行。
```

**要求**：每个实体文件（含 data 子目录内每个文件、每张表、每张图）都有自己的行，
不许用"`tables/` 所有表格"一笔带过。

## 4. 01_方法与结果.docx 结构与要求

### 内容强制要求

- 字数 ≥ 3000 中文字符；复杂分析继续扩写
- 真实插入图和表，不能只写"见图 1"而图不在文档里
- 段落顺序：文字引出 → 插入图/表 → 图题/表题 → 读图/读表结论
- 方法部分详细到别人能重复做（样本量、纳排、变量定义、模型、软件版本）
- 结果部分数字与 `tables/` 一致，精度与 `0_result_summaries.md` 一致

### 绝对禁止出现

| 禁止内容 | 原因 | 改为 |
|---------|------|------|
| "3-28 版"、"最新版"、版本号 | 暴露工作流 | 删除 |
| `ln_mtv`、`exp_cat` 等内部变量名 | 不专业 | 用学术全称"对数转换 MTV"、"暴露分组" |
| "枚举所有方案"、"试了很多次" | 暴露调试过程 | 删除 |
| "相比旧版更好" | 内部决策 | 删除 |
| "本次分析"、"本工作" | 口语化 | 用"研究"/"分析" |
| 模板化套话（academic-humanizer 审计模式） | 文风失真 | 对照改写并核对不可变事实清单 |

### 结构默认

```
1 研究背景
2 数据与方法
  2.1 数据来源
  2.2 纳入与排除
  2.3 变量定义
  2.4 统计方法
3 结果
  3.1 基线特征（插入 Table 1）
  3.2 主要发现（插入 Table 2 + Fig 1）
  3.3 敏感性分析
4 结论
5 局限性
6 附表附图
```

若交付**论文初稿**而非方法结果文档：按 `academic-publishing` 规范生成
（python-docx 直出、黑体标题/宋体五号正文/Times 西文双字体、三线表、首行缩进 2 字符、
1.5 倍行距、结构式摘要 300-500 字、核心正文 ≥ 5000 字、文献用 `[待补充引用]` 占位）。
