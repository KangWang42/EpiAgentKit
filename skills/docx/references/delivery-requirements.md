# DOCX 生成与交付验收要求

新建或大幅重建 Word 文件、完整正式文件首次装配，或用户提出严格格式要求时，使用本参考。已有 Word 的局部纠正、局部图片替换或普通重新保存不单独触发整份要求；只选择本次修改可能影响的条目。内容 skill 仍决定正文、表图功能和科学含义；本参考只把已经确认的文件要求转成可重复执行的 Word 检查。

## 建立当前任务验收清单

把用户、模板和内容 skill 已经确认的要求合并为一份当前任务清单。简单任务可只保留在当前上下文；需要传给脚本时，在任务 workbench 写 UTF-8 JSON，不默认建立项目级状态文件。首次生成或大幅重建时执行整份适用清单；后续局部修改只复查本轮可能受到影响的内容，并沿用仍然适用的最近成功检查。重新生成整份 Word 的脚本或方法改变了文档结构或装配顺序时，重新检查包结构、内容顺序和页面显示；只替换一张在 Word 中位置和显示尺寸均不变的图片时，不自动复查无关表格、公式、页眉页脚或其它图片。

清单只写已经确认且可检查的内容：

- 最终文件格式和稳定文件名；
- 每个既有 Word 的路径、角色及判定依据；作为版式母版时，母版基线、确认变化和比较证据位置按 `layout-master-inheritance.md` 记录；
- 模板来源，以及允许的文字、底纹和边框颜色；
- 每张正式表的稳定编号、内容功能、数据来源、正文或附录位置、完整题注、题注对齐、正文引用及 `academic_display` 或 `official_form` 类型；
- 统计表的稳定行键、唯一内部字段 ID、显示标签、来源字段、Word 中的列位置，以及按最终显示值逐字段对账的证据位置；存在分组、父子或连续行时同时记录最终显示行层级；
- 每张正式图的稳定编号、内容功能、图件来源、正文或附录位置、完整图题、图题对齐、正文引用和替代文字；
- 任务专属文字的出现条件与允许范围；
- 页面大小、页边距、页眉页脚、分页、表格续页和字体等仍需渲染确认的项目。

表数、颜色、时点、题注对齐和状态小节均从当前内容 skill、已确认的版式母版与任务清单取得，并按该清单验收。

`audit_docx.py` 的任务清单核验已明确的颜色、文字、题注、表图和字段结构；`layout-master-inheritance.md` 的角色记录和逐项差异证据核验文首结构、标题层级、页眉页脚和整体表格语言。使用版式母版时，两组证据共同构成文件验收。

连续黑白学术版式必须把 `allowed_text_colors` 明确设为 `["000000"]`；不能因为该字段省略后审计没有报错，就把颜色要求视为已满足。Pandoc 可能在 `w:hyperlink` 的运行或 `Hyperlink` 字符样式中保留 `THEME:ACCENT1` 等主题颜色，因此颜色审计要覆盖正文、题注、页眉页脚、表格和超链接的有效运行颜色及被使用样式。图像包内的像素颜色不参与这项检查。

## 机器可读格式

```json
{
  "schema_version": 2,
  "allowed_text_colors": ["000000"],
  "allowed_fill_colors": ["FFFFFF", "AUTO"],
  "allowed_border_colors": ["000000", "AUTO"],
  "require_all_tables_listed": true,
  "require_all_figures_listed": true,
  "required_text": [],
  "forbidden_text": ["<用户明确不要保留的完整文字或稳定片段>"],
  "tables": [
    {
      "id": "table-1",
      "role": "<该表在报告中的内容功能>",
      "source": "<已经核对的表格或结果来源>",
      "placement": "body",
      "table_kind": "academic_display",
      "caption": "表1 <完整题注>",
      "alignment": "center",
      "references": ["见表1"],
      "row_keys": [{"field_id": "term", "source_field": "term", "column_index": 0}],
      "row_hierarchy": {
        "header_rows": 1,
        "label_column_index": 0,
        "indent_twips_per_level": 200,
        "rows": [
          {"row_key": "variable", "row_role": "parent", "display_label": "<父级变量>", "indent_level": 0},
          {"row_key": "variable.level", "row_role": "level", "parent_key": "variable", "display_label": "<分类水平>", "indent_level": 1}
        ]
      },
      "columns": [
        {"field_id": "estimate", "label": "OR（95% CI）", "source_field": "estimate_display", "column_index": 1},
        {"field_id": "model_p", "label": "P 值", "source_field": "model_p_display", "column_index": 2}
      ],
      "reconciliation_evidence": "<逐字段对账结果 JSON>"
    }
  ],
  "figures": [
    {
      "id": "figure-1",
      "role": "<该图在论文或报告中的内容功能>",
      "source": "<已经核对的统计图或真实图像来源>",
      "placement": "body",
      "caption": "图1 <完整图题>",
      "alignment": "center",
      "references": ["见图1"],
      "alt_text": "<准确描述图中对象和比较内容的替代文字>"
    }
  ]
}
```

颜色使用 OOXML 十六进制值、`AUTO` 或 `THEME:<主题色名>`。只有清单包含对应字段时才检查颜色。`alignment` 只接受 `left`、`center`、`right` 或 `justify`。schema 2 的每张正式表声明 `table_kind`：`academic_display` 验证表顶线、表头分隔线、表底线及内部边框拓扑，`official_form` 按已确认模板验收。schema 1 既有清单继续兼容。`role`、`source` 和 `placement` 由内容 skill 确认；DOCX 审计要求这些字段存在，并验证题注文本、顺序、有效对齐、与下一张表的相邻关系、正文引用和表格总数。

统计表的 `columns` 使用唯一 `field_id` 标识真实统计字段，`label` 仅表示可见表头，因此多个列可以合法显示同一文字。`column_index` 使用从 0 开始的表格列位置；`source_field` 指向内容 skill 已确认的最终显示值来源。`audit_docx.py` 只检查清单结构、字段 ID 唯一性和列位置边界，不能证明数值正确；交付前仍需把 Word 表提取为矩阵，并以行键和字段 ID 对来源执行逐字段对账，把结果写入 `reconciliation_evidence` 指向的位置。

`row_hierarchy` 只在表格存在阅读层级时填写，并按 Word 中的最终顺序列出全部正文行。`row_role` 使用 `group`、`parent`、`level`、`data` 或 `continuation`；子级与连续行通过 `parent_key` 指向已经出现的父级。`indent_twips_per_level` 来自当前模板或任务确认的缩进单位。审计按稳定行键核对显示标签、父级先后和实际缩进；`continuation` 使用空显示标签，并与首次标签行保持同一级缩进，同时保留独立行键和完整统计字段。

`figures` 的 `role`、`source` 和 `placement` 由内容 skill 确认；审计验证图题文本、顺序、对齐、前一非空段落中的图形、正文引用和可选 `alt_text`。设置 `require_all_figures_listed` 时，每张列入清单的正式图必须对应一个嵌入图形，且文档中不得多出未登记图形；文档本来包含徽标、签名或装饰图时不要误设该开关，或把这些合法图形明确纳入任务清单。

`forbidden_text` 只记录用户或文档用途已经明确排除的稳定片段。研究设计、缺失处理、局限性、证据强度及期刊、机构、伦理、合同和法规要求的真实披露按内容要求完整保留。

## 执行检查

在 skill 目录运行：

```bash
python scripts/office/validate.py report.docx
python scripts/audit_docx.py report.docx --requirements task-workbench/docx-requirements.json --json
```

审计会检查活动正文、页眉、页脚、脚注和尾注中的有效文字颜色，活动样式中的显式颜色，直接底纹和边框颜色，以及清单中的题注、三线表拓扑、行层级、表图和文字要求。数值正确性继续由稳定行键与字段 ID 的逐字段对账证明；页面显示由按页渲染证明。

首次装配或覆盖已有稳定文件时，先对 workbench 候选执行上述检查和适用渲染，再用同卷原子替换提升当前版。候选检查失败、目标被占用或替换返回权限错误时，保留候选并停止；不得删除原当前版、强制关闭用户程序或把未通过的候选写入稳定路径。

## 页面风险与渲染关口

先判断本轮是否会影响分页或最终页面显示。新建或大幅重建、严格分页、复杂分节、目录、浮动对象、密集跨页表格、全局样式、页眉页脚、正式归档或用户明确要求所见即所得时，才需要页面级渲染，并优先复用当前环境中已经确认可用的 LibreOffice 和 Poppler。普通 L 修改若只替换一张在 Word 中位置和显示尺寸均不变的图片、修改一个普通段落或一个局部表格单元格，先检查包结构、授权范围、媒体关系或目标内容、重新打开结果，以及相应图题、正文引用或表格内容；没有页面显示风险时不为探测能力调用 `soffice`。

需要页面级渲染时，在当前会话首次使用前只做一次轻量能力判定；判定不可用后不重复调用或等待。渲染不可用或超时时，仍执行适用的静态检查，并在交付说明中明确哪些分页、字体替换、孤行、跨页表格或最终显示属性未验证。不得把静态检查称为完整视觉验收。

如果文档依赖复杂分节、密集跨页表格、浮动对象、目录或严格归档版式，静态检查不能合理覆盖风险时，停止正式发布并说明需要可用渲染环境。不要自行安装系统级 LibreOffice、Word 或其它运行时，也不要自动启动或关闭用户现有的 Word 进程。
