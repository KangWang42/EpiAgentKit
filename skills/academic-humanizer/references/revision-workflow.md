# 学术文本修订规范

本文件规定已有学术文本、投稿稿件和 Word 稿件应采用哪种修订方式、何时需要 `revision-state.json`，以及局部修改不得超出的范围。从零写作与论文级结构性重写仍由 `academic-publishing` 主导；实际 Word 操作另用 `docx`。

## 1. 修订类型

| 类型 | 主流程 | 允许动作 | 默认禁止 | 验收 |
| --- | --- | --- | --- | --- |
| 从零写作 | `academic-publishing` | 按结果数字唯一来源建立章节与投稿材料 | 编造结果、引文或期刊要求 | 部件自检与全文证据链一致 |
| 结构性重写 | `academic-publishing` → `academic-humanizer` | 在明确授权的章节或全文重排论证、合并和改写 | 未经说明改变 estimand、结果方向或引文 | 新结构使研究目的、方法、结果和讨论完整对应，必须保持不变的事实均未改变 |
| 局部内容修订 | `academic-humanizer` | 只改清单中可定位的句、段、表格单元格或题注 | 扩写范围、顺手统一全文、改变范围外措辞或格式 | 目标修改完成，范围外事实、正文、表图和格式不变 |
| 纯格式修复 | 对应内容 skill → `docx` | 只修用户或正式规范点名的样式、分页、域、表格或图片版式 | 改写正文、全局套用新主题 | 可见文字和数据不变，授权格式项通过渲染核验 |
| 终审 | `academic-humanizer` | 报告事实冲突、证据强度、术语、结构和语体问题；按授权做最小修复 | 未经授权重构全文 | 不可变事实和准确术语保持，全文符合学术书面语与目标期刊要求，待确认项单列 |
| 审稿意见处理 | `academic-publishing` → `academic-humanizer`；Word 时加 `docx` | 逐条落实、定位、验证，并依据同一份修改记录生成交付文件 | 把“已读”当“已解决”、声称未执行动作 | 每条意见有状态、证据、位置和真实回复；未解决项阻止正式交付 |

用户请求同时含多种类型时先拆成内容层和格式层，分别执行和验证。只有用户明确授权或正式格式规范明确规定时，才进行全局规范化。

## 2. 决定是否需要修订记录文件

按全局任务范围控制记录量：问答只回复；单段、单个表格单元格、单个引用序号或单项格式修复只在当前任务中确认输入、范围和事实，不创建修订记录文件或项目记录文件。只有出现以下任一情形才建立名称固定的 `revision-state.json`：多轮或多条审稿意见需要持续跟踪；净稿、标注稿和回复需要由同一组修改记录生成；多人或跨会话协作；多个合理输入需要长期明确当前采用哪一份；用户或期刊要求正式确认。已有文件时只更新原文件，不创建平行版本。

正式修订使用 `revision-state.json` 时至少包含：

```json
{
  "schema_version": 1,
  "round": "<current round>",
  "input_candidates": ["<candidate path>"],
  "selected_input": "<one selected path>",
  "format_contract": "<verified journal, institution, or neutral contract>",
  "interaction_contract": {
    "answer_only": false,
    "create_document": true,
    "one_issue_at_a_time": true,
    "response_style": "direct",
    "highlight_policy": "specified_items_only"
  },
  "locked_decisions": {
    "<decision key>": {"value": "<locked value>", "source": "<user or project record>"}
  },
  "allowed_scope": ["<exact content or structure locator>"],
  "forbidden_scope": ["<protected content or structure locator>"],
  "pending_materials": [],
  "deliverables": {
    "clean": "<stable clean path>",
    "marked": "<stable marked path>",
    "response": "<stable response path>"
  },
  "review_comments": []
}
```

- `interaction_contract` 只在本来就需要 `revision-state.json`，且用户要求需要跨轮次保留时写入；用户说“直接回复”“不要做文档”“一条一条”“只改点名处”或“仅标记指定项”后持续生效，除非用户明确替代。不要只为保存这些要求而创建 JSON。
- 权威数字或口径写入 `locked_decisions` 的 `value` 与 `source`；当前采用的稿件写入 `selected_input`；允许和禁止的修改分别写入 `allowed_scope` 与 `forbidden_scope`。不再另建重复的来源表或禁止动作清单。
- `input_candidates` 有多个合理当前稿而 `selected_input` 尚未明确时停止，不按修改时间、文件名或后缀自动选择。
- 用户最新明确纠正写入 `locked_decisions`。后续轮次必须携带；改变时用 `supersedes` 记录旧值、新值、来源和原因，不得静默覆盖。
- `allowed_scope` 使用可核验位置，如章节标题、段落索引、表格—行—列或审稿意见编号。`forbidden_scope` 明确数字、引文、图表、格式或已认可表述等保护项。
- `pending_materials` 保存缺失数据、真实引文、作者信息或期刊要求；无法核验的引文继续使用统一占位符，不生成候选文献。

运行：

```bash
python scripts/validate_revision_state.py revision-state.json --previous previous-state.json --json
python scripts/validate_revision_state.py revision-state.json --signoff --json
```

第一条检查输入、允许修改的范围和已经确认的决定是否被意外改变；第二条检查是否仍有未解决的审稿意见，若有则不允许正式交付。

## 3. 可定位修改清单

执行前在当前任务中逐项记录；只有现有的 `revision-state.json` 或确定性脚本需要时才写入文件，不另建用于交付的清单：

`change id | 来源要求 | 精确位置 | 修改前摘要 | 计划动作 | 内容或格式层 | 证据来源 | 范围外保护 | 验证状态`

- 修改前先确认定位唯一。目标出现多次、跨越域或复杂 run、或候选位置无法区分时，不做模糊全文替换；列出候选位置并请求确认。
- 内容层先确认必须保持不变的事实，核对论断依据和语义；格式层随后执行，不用格式修复顺手改写正文。
- 对已有 Word，精确定位、生成净稿与标注稿，以及检查范围外差异时，使用 `docx` 的确定性脚本。脚本无法唯一定位目标或不能安全处理复杂结构时，保留原稿并说明停止原因。

## 4. 审稿意见处理

每条意见使用以下字段：

`意见编号 | 问题类型 | 所需动作 | 修改位置 | 修改前后摘要 | 证据来源 | change id | 状态 | 回复文本`

状态只用：`pending`、`modified_pending_validation`、`closed`、`needs_user_decision`。

- `closed` 必须同时具备实际动作、准确位置、修改前后摘要、证据来源和与已完成动作一致的回复。
- 新分析先同步代码、结果数字唯一来源、表图和正文，再写回复；未运行、未修改或未上传的动作不得使用完成时态。
- 净稿是本轮最终内容；净稿、标注稿与回复必须依据同一组修改编号生成。移除标注后，两版的可见文字、表格、图片、题注和顺序必须一致。
- 默认只标记本轮实际变化和用户指定待补项；颜色、作者名与标记方式由当前修订规范配置，不标记未修改内容。

## 5. 完成条件

- 问答：当前问题已直接回答，没有创建用户未要求的文件或扩展任务。
- 局部产物：唯一输入和允许范围已经确认，原文件可恢复，目标修改完成，输出可打开，范围外正文、数据、引文、表图和格式无变化；不要求同时生成净稿、标注稿和回复。
- 正式修订：轮次、格式要求、待补材料和需要交付的文件已经确认；必须保持不变的事实和已确认决定均未被意外改变；净稿、标注稿和回复按实际要求由同一组修改记录生成并可逐项核对；Word 已检查文档结构、匿名要求、范围差异和页面显示。
