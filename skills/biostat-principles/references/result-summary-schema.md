# 结果数据文件

新正式项目把关键结果、显示格式和来源统一保存在 `results/results.yaml`，R 与 Python 使用同一文件结构。实际生成结果的分析脚本，或导入已确认外部结果的专门脚本，是唯一写入者。写入时先在同一目录生成临时文件，成功后再替换现有文件，避免中断时留下不完整内容。旧项目的 `07_paper/results.yaml` 仍可读取。

## 第 2 版文件结构

```yaml
meta:
  schema_version: 2
  project: cohort_example
  updated_at: "2026-08-02T12:15:00+08:00"
results:
  exposure_hr:
    label: 暴露与结局的关联
    section: 主要结果
    estimate:
      value: 1.45
      ci_low: 1.12
      ci_high: 1.87
      p_value: 0.004
      unit: ""
    display:
      term_label: 连续指标（每 10 单位）
      short_label: "连续指标\n（每 10 单位）"
      scale_label: 每 10 单位
      estimate: "1.45"
      interval: "（95% CI：1.12，1.87）"
      p_value: "P = 0.004"
      full: "1.45（95% CI：1.12，1.87），P = 0.004"
    provenance:
      producer: 02_code/03_main.R
      source: model_main$coefficients
      input:
        - 01_data/rawdata/cohort.csv
      input_hash: "sha256:..."
      analysis_set: primary_complete_case
      run_id: 20260802T121500+0800_ab12cd34
    consumers:
      - 03_tables/Table2_main.xlsx
      - paper/manuscript.docx
```

每项结果必须符合以下要求：

- 每项结果使用固定英文名称，不随表图编号变化。
- `producer` 填写实际生成或导入该结果的脚本；`source` 填写脚本中提取结果的对象、查询，或已确认外部结果的标识。
- `input` 至少列出一个可以定位的输入文件；无法共享路径时提供不可逆的 `input_hash`。两者可以同时存在。
- `analysis_set` 使用项目已经确认的分析集名称；`run_id` 对应一次成功的自动运行记录。
- `consumers` 只列出实际读取这项结果的文件，不预填尚不存在的论文、报告、PPT 或表图。
- `consumers` 是内部技术字段。面向研究者说明时写“结果使用位置”“实际使用该结果的文件”，或直接列出相应表图和正文，不得把该字段译为“消费者”；原始数据或专业分类中确实表示人的 `consumer` 不受此表达规则影响。
- `estimate` 保存用于核对的原始数值；`display` 由共用函数按照项目规定的精度生成，后续文件不应再次自行调整格式。
- 同一结果需要在正文、表格和图形中反复展示变量名称、效应缩放或变化定义时，使用可选的 `display.term_label`、`display.short_label`、`display.scale_label` 和 `display.change_definition`。`term_label` 用于完整公开名称，`short_label` 只用于最终尺寸受限的图内短标签；不得让正文、表格和绘图脚本各自拼接单位、增量或变化方向。用户或模板要求独立单位列时仍可保留，但各位置必须读取同一字段。
- 内部变量名、模型项名和程序对象名留在 `source` 或分析代码；不得写入公开展示字段。展示字段只保存中性定义，不保存结果解释、显著性判断或推荐结论。

`results/results.yaml` 不保存解释、因果判断、显著性结论或跨结果总结。数字变化后，应检查所有实际使用该结果的文件，并根据需要更新 `DECISIONS.md` 和正文；不得让程序根据数值变化自动推断研究结论。

## 写入

R 使用 `r-biostats/scripts/emit_summary.R`：

```r
source("02_code/vendored/emit_summary.R", encoding = "UTF-8")
add_result(
  "results/results.yaml", "exposure_hr",
  label = "暴露与结局的关联", est = 1.45,
  ci_low = 1.12, ci_high = 1.87, p = 0.004,
  term_label = "连续指标（每 10 单位）",
  short_label = "连续指标\n（每 10 单位）",
  scale_label = "每 10 单位",
  producer = "02_code/03_main.R", source = "model_main$coefficients",
  input = "01_data/rawdata/cohort.csv",
  analysis_set = "primary_complete_case", run_id = Sys.getenv("EPI_RUN_ID"),
  consumers = "03_tables/Table2_main.xlsx"
)
render_summary_md("results/results.yaml", "results/result_summaries.md")
```

Python 使用 `python-biostats/scripts/emit_summary.py`，参数名和写入内容相同。调用脚本必须提供 `producer`、`source`、`analysis_set`、非空 `run_id`、`consumers`，并提供 `input` 或 `input_hash`。缺少任一必要来源信息时，写入函数停止，不生成内容不完整的文件。

`val(path, key, which="full")` 按固定结果名称读取 `display`；数值可选 `estimate|interval|p_value|full`，已写入展示合同的结果还可读取 `term_label|short_label|scale_label|change_definition`。`render_summary_md()` 只生成便于人工核对的数字和来源摘要，并在文件中注明内容由 `results/results.yaml` 自动生成、不可单独修改。

## 兼容与一致性

1. `val()` 和 `render_summary_md()` 可读取旧版的 `raw` / `rendered` 字段；`add_result()` 只写第 2 版结构。
2. 旧路径若存在可继续读取，但新项目和新的分析脚本统一写入 `results/results.yaml`。
3. 探索中得到的最佳数值、调参结果和未经确认的解释不得写入正式结果数据文件。
4. 发现正文、表图或报告与结果数据文件不一致时，回到 `producer` 所指的脚本和相应运行记录，重新运行后再生成受影响文件；不得直接修改 YAML 或成品中的数字。
