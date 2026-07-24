# 结果单一真源 schema

`07_paper/results.yaml` 是正式项目的语言中性结果机器单源。R 与 Python helper 必须写入相同字段；`0_result_summaries.md` 只由该文件派生。轻量任务不为满足本合同补建项目结构。

## 字段

```yaml
meta:
  project: "项目名"
  updated: "2026-07-24"
results:
  stable_key:
    label: "人读标签"
    section: "主要结果"
    source: "02_code/03_main.py"
    table: "03_tables/Table2_main.xlsx"
    raw: {est: 1.45, ci_low: 1.12, ci_high: 1.87, p: 0.004, unit: ""}
    rendered:
      est: "1.45"
      ci: "（95%CI：1.12，1.87）"
      p: "P = 0.004"
      est_ci: "1.45（95%CI：1.12，1.87）"
      full: "1.45（95%CI：1.12，1.87），P = 0.004"
    interp: "与参照组相比，该暴露与较高风险相关。"
    interp_review: false
    raw_sig: "1.45|1.12|1.87|0.004|"
conclusion: "跨结果总结论，由研究者复核。"
```

- `key` 是稳定英文标识，下游按键读取，不随表图编号改名。
- `raw` 保留可审计数值；`rendered` 由 helper 统一格式化，下游不得再次格式化或手敲。
- `source` 和 `table` 指向实际生产者与消费者；没有对应表时 `table` 可空。
- `interp` 与 `conclusion` 是经研究者复核的解释，不由数值自动推断。
- 数字变化但没有同步提供新解释时，helper 保留原解释并把 `interp_review` 设为 `true`。签发前 `stale_interps()` 必须为空。

## 写入与读取

R 使用 `r-biostats/scripts/emit_summary.R`：

```r
source("02_code/vendored/emit_summary.R", encoding = "UTF-8")
add_result("07_paper/results.yaml", "exposure_hr",
           label = "暴露与结局的关联", est = 1.45,
           ci_low = 1.12, ci_high = 1.87, p = 0.004,
           source = "02_code/03_main.R")
render_summary_md("07_paper/results.yaml", "07_paper/0_result_summaries.md")
val("07_paper/results.yaml", "exposure_hr")
```

Python 使用 `python-biostats/scripts/emit_summary.py`：

```python
from emit_summary import add_result, render_summary_md, val

add_result(
    "07_paper/results.yaml",
    "exposure_hr",
    label="暴露与结局的关联",
    est=1.45,
    ci_low=1.12,
    ci_high=1.87,
    p=0.004,
    source="02_code/03_main.py",
)
render_summary_md("07_paper/results.yaml", "07_paper/0_result_summaries.md")
val("07_paper/results.yaml", "exposure_hr")
```

`add_result()` 的 `digits`、P 值精度或阈值、`unit` 和 `style="zh"|"en"` 控制统一渲染；百分比单位不加空格。下游可用 `val(path, key, which="est|ci|p|est_ci|full")` 读取所需分量，但不得重新格式化。

## 数字与解读闭环

数字变化后若没有同步提供新解释，helper 保留旧解释并设置 `interp_review: true`。按以下顺序闭环：

1. 用 `stale_interps(path)` 列出全部待复核键；
2. 研究者核对方向、显著性、效应量级和证据强度后，用 `confirm_interp(path, key, interp=...)` 写入或确认解释；
3. 跨结果总结论变化时用 `set_conclusion(path, text)` 更新；
4. 重新运行 `render_summary_md()`，确认 `stale_interps(path)` 为空后才能签发。

R 与 Python helper 使用相同函数名和行为。不得仅为清除标记而调用 `confirm_interp()`，也不得由数值自动生成结论。

## 一致性合同

1. 结果由分析脚本通过 helper 写入 `results.yaml`，再生成派生 Markdown。
2. 论文、报告、PPT、表图注释和审计按稳定键取 `rendered`；发现差异时回到生产脚本与 `results.yaml` 修正后重生全部消费者。
3. 不把探索性峰值、调参结果或未经确认的解释写入主结果单源。
4. 方法变化同步 `DECISIONS.md`，运行记录同步 `SESSION_LOG.md`，待补信息同步 `BACKLOG.md`。
