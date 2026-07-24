---
name: evidence-research
description: |
  科研决策的证据检索、来源身份核验、证据评价与适用性判断技能。触发场景：(1) 快速核验单个事实、单篇引文、标题、DOI 或 PMID；(2) 查找最新证据、指南、方法依据或真实引文；(3) 构建结局指标、选择量表、制定异常值规则；(4) 试新方法、比较指标或判断跨领域方法能否迁移。
  自动选择 rapid verification 或 formal evidence review。两种模式均核验来源身份；只有 formal 模式强制完整检索协议和证据矩阵。不负责统计模型实跑或论文正文生成，不得以文献替代项目数据核验，不得编造来源或研究结论。
---

# 科研证据调研

先选择最小充分模式，再核验来源身份、正文论断和当前项目适用性。搜索结果片段与二手转述只用于发现候选来源。

## 1. 选择工作模式

### Rapid verification

用于单个事实、单篇引文、DOI/PMID、标题或少量依据。执行：

1. 按 [references/source-routing.md](references/source-routing.md) 选择主源；
2. 核对题名、作者、年份、期刊、DOI/PMID 及更正或撤稿关联；
3. 需要引用具体结论时打开摘要或全文核对原句语境；
4. 输出简短结论、来源标识、核验层级和未核验项。

Rapid 模式不强制预注册协议或完整证据矩阵。元数据正确不等于正文论断已核验。

### Formal evidence review

用于结局指标、量表、异常值规则、新方法、多个候选方案或跨领域迁移。执行完整流程：问题卡 → 预注册协议 → 分层检索 → 来源核验 → 证据矩阵 → 直接性与可迁移性判断 → 决策留痕。

定义不清的分组、终点、纳排或主分析方法先问用户，文献不能替用户决定研究口径。

## 2. 核验来源身份

读取 [references/source-routing.md](references/source-routing.md)。可用确定性脚本核验 DOI、PMID 或标题：

```bash
python scripts/verify_sources.py "10.xxxx/xxxx"
python scripts/verify_sources.py "12345678" "article title" --pretty
```

脚本通过 PubMed E-utilities 与 Crossref 核对元数据和更正/撤稿关系，输出 `evidence_id`、`metadata_verified`、`full_text_status`、`claim_verified` 与 `retrieved_at`。网络失败或来源冲突保留未核验状态并返回非零退出码；不得用脚本的元数据结果替代全文论断核验。

无法取得全文或无法核对关键结论时标记“未核验”，不得作为正式论断依据。发现 DOI/PMID 冲突、撤稿或来源不明时剔除或降级，并记录原因。

## 3. Formal 检索协议

仅 formal 模式在检索前填写 [references/search-protocol.md](references/search-protocol.md)：

1. 数据库、权威网站、检索日期与覆盖时间；
2. 逐库检索式、语言、人群、研究类型和全文纳排条件；
3. 去重、筛选方法和停止条件。

保留奠基方法论文，同时重点检索近 3–5 年的指南、验证、更新和系统综述。“最新”不等于只取最近文章。

## 4. 组织证据

按问题组合证据层级：

- 指南、标准与共识用于定义规范和报告要求；
- 系统综述与 Meta 分析用于总体证据与异质性；
- 奠基方法论文用于方法定义、假设和估计目标；
- 目标领域验证研究用于性能、复现性和适用人群；
- 相邻领域研究仅作间接证据，必须降低论断强度。

Formal 模式按 [references/evidence-matrix.md](references/evidence-matrix.md) 一条来源一行提取。每条来源使用脚本生成或人工确定的稳定 `evidence_id`；在 `DECISIONS.md` 的方法决策中引用这些 ID，形成“证据 → 变量/指标/模型选择”的可追溯链。

来源不一致时比较人群、定义、测量、模型、时间窗和偏倚，不按篇数投票。

## 5. 跨领域可迁移性评估

逐项判断：

1. 构念是否相同，而非名称相似；
2. 测量尺度、采样过程与数据生成机制是否兼容；
3. 方法假设能否在目标数据中检验；
4. 能否做内部验证、校准或复现；
5. 间接性如何降低论断强度。

关键项无法判断时，只登记为隔离验证候选，不直接并入主流程。文献只能说明合理范围或核查方向，不能单独证明某个观测值应改成多少。

## 6. 输出与衔接

Rapid 输出：核验对象、来源身份、元数据状态、全文/论断状态、更正或撤稿关系及简短结论。

Formal 输出：检索协议、来源清单、证据矩阵、候选比较、直接性与可迁移性、降级后的论断强度、推荐决策及所引用的 `evidence_id`。

进入分析时把方法假设和验证要求交给 `biostat-principles`，再按项目主语言交给 `r-biostats` 或 `python-biostats`；进入写作时把已核验引文和证据边界交给 `academic-publishing`。本 skill 不代跑模型，也不代写论文正文。
