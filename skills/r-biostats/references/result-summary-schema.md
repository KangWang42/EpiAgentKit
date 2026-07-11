# 结果单一真源 schema 与工作流（P0-A1 / C1）

目录：1 为什么 · 2 results.yaml schema · 3 写入（add_result）· 4 渲染 md · 5 下游取数 val() · 6 双向一致性铁律 · 7 结论与解读（改数字≠改完）

## 1 为什么

数字散落在论文 / 报告 / PPT 里各自手敲 → 改一处漏多处。固化为：**results.yaml = 机器可读单源**，数字在 `emit_summary.R` 里**渲染一次**（口径单源），存 raw 分量 + rendered 成品串；下游一律 `val()` 读 rendered，不再格式化、不再手敲。`0_result_summaries.md` 由 results.yaml 派生。

脚本：`scripts/emit_summary.R`（source 即用）。

## 2 results.yaml schema

```yaml
meta:
  project: "项目名"
  updated: "2026-06-14"          # add_result 自动写
results:
  <key>:                         # 稳定英文键，下游 val("<key>") 引用，勿改名
    label: "人读标签"             # 用于 md 标题
    section: "主要结果"           # md 分节归类
    source: "02_code/03_main.R"  # 产出脚本
    table: "<table_path('main_effect') 的返回值>"  # 由 registry 生成（可空）
    raw: {est, ci_low, ci_high, p, unit}   # 原始数值（审计/重渲染用）
    rendered:                    # 成品串（下游只读这层）
      est: "−1.82 kg"
      ci:  "（95%CI：−3.29，−0.36）"
      p:   "P = 0.015"
      est_ci: "−1.82 kg（95%CI：−3.29，−0.36）"
      full:   "−1.82 kg（95%CI：−3.29，−0.36），P = 0.015"
    interp: "S2 反弹显著小于 S1，提示联合方案有助于体重维持。"  # 结论/效应解读（人写）
    interp_review: false         # 数字变过、解读未跟上 = true（待复核）
    raw_sig: "-1.82|-3.29|-0.36|0.015|kg"   # 数值指纹，用于检测数字是否变了
conclusion: "主分析与敏感性分析方向一致，支持 S2 优于 S1。"   # 跨结果总结论（人写）
```

## 3 写入：add_result()

每个产出脚本算完一个指标即写一行（**不要手敲 rendered，由函数渲染**）：

```r
source("02_code/vendored/emit_summary.R", encoding = "UTF-8")
source("02_code/config.R", encoding = "UTF-8")
yp <- "07_paper/results.yaml"
add_result(yp, "S2_vs_S1_diff", label = "S2 vs S1 组间反弹差异",
           est = -1.82, ci_low = -3.29, ci_high = -0.36, p = 0.015, unit = "kg",
           section = "主要结果", source = "02_code/03_rebound.R",
           table = table_path("main_effect"))
```

口径常量（小数位 / P 阈值 / CI 样式）是 `emit_summary.R` 的单一真源；若项目 `conventions.R` 已定义 `DIGITS_EST` / `DIGITS_P` / `P_FLOOR`，函数自动采用之。百分比传 `unit="%"`（紧贴无空格，按需 `digits=1`）。英文期刊传 `style="en"` 得 `(95% CI: ...)`。

## 4 渲染 0_result_summaries.md

```r
render_summary_md("07_paper/results.yaml", "07_paper/0_result_summaries.md")
```

按 section 分节列出每条 `label（key）：full（来源：source；table）`。**md 是派生物，勿手改**；改数字改 results.yaml 再重渲染。

## 5 下游取数：val()

论文 / 报告 / PPT 引用数字一律取键，禁手敲：

- R（出图 / sysu-ppt toolkit / 分析内联）：`val("07_paper/results.yaml", "S2_vs_S1_diff")` → `"−1.82 kg（95%CI：−3.29，−0.36），P = 0.015"`；`which="est_ci"/"p"/"est"/"ci"` 取分量。
- Python（report-writing `build_report.py`）：`from build_report import val; val("07_paper/results.yaml", "S2_vs_S1_diff")`。

## 6 双向一致性铁律

- 数字**只在 results.yaml（或其产出脚本的 add_result）改**；改完重跑 render_summary_md，下游重生成即同步。
- **NEVER** 在论文 / 报告 / PPT 里直接敲数字或就地改数字。若发现下游数字与源不符，回到 results.yaml 改、再向所有下游传播——任何"只改一处"视为缺陷。
- 审计：`epi-project-audit` 的一致性脚本双向比对（文中数字 vs results.yaml），既报"文中≠源"也报"文中有源无"。

## 7 结论与解读（改数字 ≠ 改完）

results.yaml 不只是数字——每条结果可带 `interp`（结论/效应解读），跨结果可带 `conclusion`（总结论），二者是**人写散文**，
随数字一起作为单源、由 render_summary_md 一并渲染进 0_result_summaries.md。

关键：**数字一变，解读往往要跟着变**（方向、显著性、效应量级变了，结论措辞就不再成立）。机制自动守这条：

- `add_result()` 用 `raw_sig`（数值指纹）检测某键数字是否变化。若数字变了、本次又没给新 `interp` → 自动把该键标
  `interp_review: true`（待复核）并 `warning`。
- `render_summary_md()` 在 md 顶部与该条解读旁打 `[解读待复核]`，把过时解读和新数字并列显示，使矛盾一眼可见。
- 复核后调 `confirm_interp(path, key, interp="新的解读")` 写新解读并清除标记；总结论用 `set_conclusion(path, text)`。
- `stale_interps(path)` 列出所有待复核键，可在交付前 gate（非空则不许定稿）。

写解读的话术规范（沿用 academic-publishing / chinese-style-audit / academic-humanizer）：客观、有依据、不夸大；
无依据的"最佳/证明"不写，数字、统计方向和证据位置保持锁定。

> 这解决了"只改数字改不掉解读"的问题：解读与数字同源、同渲染，且数字变动会**强制**提示复核解读，杜绝陈旧结论残留。
