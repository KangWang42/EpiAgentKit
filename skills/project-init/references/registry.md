# 表图编号 registry 实现指南

全局规则要求：表图编号唯一来源 = registry 有序清单，编号 = 清单中的位置；产出脚本一律
`table_path(stem)` / `fig_path(stem, ext)` 取路径，禁止写死 `Table6` / `Fig3` 数字。
本文件给出落地实现。新项目初始化时即建空 registry，不要等表图堆起来再补救。

## 原理

编号最易因增删 / 退役而断号、重号，且散落各脚本难同步。正解是把编号集中到一个有序清单：
增删表图 / 改顺序 / 退役 → 只编辑这一个清单，文件名 + 编号 + 附录索引自动顺延一致，永不断号。
退役某号后续号自动前移补齐，不留空号。本质等价于 Quarto / LaTeX 的 `@tbl-label` 自动编号，
只是作用对象是产物文件。

## 实现一：纯 R 项目（写进 config.R）

```r
# config.R ----------------------------------------------------
TABLE_REGISTRY <- c(          # 顺序 = 论文行文顺序 = 编号
  "baseline",                 # Table1
  "regression_main",          # Table2
  "subgroup"                  # Table3
)
TABLE_S_REGISTRY <- c("sensitivity_e1")   # TableS1（写入 supplementary/）

FIG_REGISTRY <- c("flowchart", "forest")  # Fig1, Fig2
FIG_S_REGISTRY <- c("calibration")        # FigS1

table_path <- function(stem) {
  i <- match(stem, TABLE_REGISTRY)
  if (!is.na(i)) return(sprintf("03_tables/Table%d_%s.xlsx", i, stem))
  i <- match(stem, TABLE_S_REGISTRY)
  if (!is.na(i)) return(sprintf("03_tables/supplementary/TableS%d_%s.xlsx", i, stem))
  stop("stem 不在 registry：", stem)
}

fig_path <- function(stem, ext = "png") {
  i <- match(stem, FIG_REGISTRY)
  if (!is.na(i)) return(sprintf("04_figures/Fig%d_%s.%s", i, stem, ext))
  i <- match(stem, FIG_S_REGISTRY)
  if (!is.na(i)) return(sprintf("04_figures/supplementary/FigS%d_%s.%s", i, stem, ext))
  stop("stem 不在 registry：", stem)
}
```

纯 Python 项目同理：registry 列表 + `table_path` / `fig_path` 函数放进 `config.py`。

## 实现二：R + Python 混合项目（registry.json 唯一来源）

一份 `02_code/registry.json` 作唯一来源，两语言各写薄 helper 读它：

```json
{
  "tables":   ["baseline", "regression_main", "subgroup"],
  "tables_s": ["sensitivity_e1"],
  "figs":     ["flowchart", "forest"],
  "figs_s":   ["calibration"]
}
```

R 端 `jsonlite::read_json()`、Python 端 `json.load()` 后实现同名 `table_path` / `fig_path`。

## 配套：TABLE_FIG_INDEX.md 生成器

写一个小脚本由 registry 生成 `TABLE_FIG_INDEX.md`（编号 → 文件名 → 一句话内容），
论文正文与项目 CLAUDE.md 的表图引用以该索引为准，杜绝四处手改漂移。

## 操作规则

- 新增表图：在 registry 对应位置插入 stem → 重跑产出脚本，下游编号自动顺延。
- 退役表图：从 registry 删除 stem → 重跑，后续编号自动前移；同时删除旧文件（或移 `09_backup/`）。
- 调整顺序：只在 registry 里移动位置，不动任何脚本。
- 任何脚本里出现写死的 `Table\d` / `Fig\d` 路径字符串 = 违规，grep 检查：
  `grep -rEn 'Table[0-9]|Fig[0-9]' 02_code/ --include="*.R" --include="*.py"`
  （命中应只在 config / registry helper 内部）。
