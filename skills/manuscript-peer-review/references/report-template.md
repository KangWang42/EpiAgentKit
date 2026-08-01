# 完整审稿报告模板

先服从期刊表单。期刊未指定时使用本结构；删除不适用的空标题，但保留审查范围、major/minor、覆盖矩阵和未核验项。输出语言跟随用户或期刊要求。

```markdown
# Reviewer report

## Review basis and scope

- Manuscript/version: [唯一输入与轮次]
- Article type/design: [实际判断]
- Materials reviewed: [正文、表图、补充材料、方案、注册、数据、代码]
- Journal criteria/rubric: [来源；未提供则写未提供]
- Reporting guideline(s): [当前规范与适用扩展]
- Not assessed: [专业范围外、未提供或未实际复核事项]
- Confidentiality/AI policy: [公开或获准范围；需披露时写明]

## Overall assessment

[一段。说明研究问题、总体科学价值、最重要的可靠之处、决定可解释性的核心问题和当前可评审程度。不在无期刊标准时给录用结论。]

## Summary of the manuscript

[用审稿人自己的话概括对象、设计、主要方法、主结果和作者主张。只复述，不在此处批评。]

## Strengths

1. [有稿件位置或证据的优点及其意义]
2. [...]

## Major comments

### M1. [问题标题]

- Type: [reporting gap / inconsistency / method/statistics / interpretation]
- Location: [页码、章节、段落、表、图或补充材料]
- Observation: [稿件实际写了什么或缺了什么]
- Basis: [方法学理由、内部核对或已核验标准]
- Why it matters: [对主要结论、偏倚、解释或复现的影响]
- Requested action: [最小且可执行的说明、分析、修订或降级表述]
- Verification status: [稿件内已核对 / 外部来源已核验 / 需作者澄清 / 未取得原始数据]

[M2...]

## Minor comments

### m1. [问题标题]

- Location: [...]
- Observation and impact: [...]
- Requested action: [...]

[m2...]

## Questions requiring clarification

1. [回答后可能改变严重度或判断的问题；说明对应 issue ID]

## Coverage matrix

| 维度 | 结论 | 关键 issue IDs | 未核验边界 |
| --- | --- | --- | --- |
| 研究问题与贡献 | [充分/有问题/无法判断] | [...] | [...] |
| 数据与稿内一致性 | [...] | [...] | [...] |
| 研究设计与偏倚 | [...] | [...] | [...] |
| 统计方法与不确定性 | [...] | [...] | [...] |
| 结果、讨论与结论 | [...] | [...] | [...] |
| 报告透明度与可复现性 | [...] | [...] | [...] |
| 语言、结构与表图 | [...] | [...] | [...] |
| 伦理与完整性 | [...] | [...] | [...] |

## Confidential comments to the editor

[仅在期刊要求或存在真实敏感事项时保留。陈述事实、位置、需要编辑核查的事项和不确定性；不得与作者可见的科学评价矛盾。]

## Recommendation

[仅在期刊表单或用户明确要求时保留。使用该期刊的原始类别或量表，并把科学有效性、可修复性与期刊优先级分别说明。]

## Reviewer limitations and disclosures

- Expertise limits: [...]
- Materials not available: [...]
- Calculations/code/data not independently verified: [...]
- AI assistance disclosure required by journal: [...]
```

## 写作规则

- 用唯一 ID 让 summary、问题、作者请求和 recommendation 可追溯，但不要在报告中暴露内部工作过程。
- 合并同一根因的重复问题；一个 major comment 可以列多个位置，但必须给一个共同影响和一个清楚请求。
- 先写最影响有效性和解释的问题。页码不稳定时使用章节、段落首句、表图号或补充材料位置。
- 每条意见包含“事实、依据、影响、动作”。避免“统计不够严谨”“语言需要润色”等不可执行句子。
- 对 reporting gap 使用“稿件未说明，因此目前无法判断”；对已证实方法问题说明稿件证据和成立条件。
- 额外研究明确标注 essential 或 optional。若降级论断、补充限制或提供现有分析即可解决，不要求新实验。
- 推荐结论必须与 major comments 一致；未审完整稿或关键输入缺失时降低信心并说明，不用虚构精确分数。
- 若某维度在实际范围内未发现问题，在覆盖矩阵中写“已审范围内未见实质问题”，不要写成绝对保证。

## 交付前检查

1. 从每个 recommendation 或 overall judgment 反向找到支持它的 major comments。
2. 从每个 major comment 反向找到稿件位置、事实和影响。
3. 删除无证据的揣测、重复问题、个人风格偏好和不必要的引文要求。
4. 确认作者可见意见与编辑保密意见不矛盾，伦理信号没有被写成定罪。
5. 核对所有数字、术语、指南名称、版本和来源；无法核验的明确标记。
6. 确认报告涵盖用户要求的数据、方法、统计、解释、语言、伦理和透明度，并列出未覆盖部分。
