# 论文投稿与返修提交前确认

本参考只用于正式投稿、返修提交、对外发送或归档。它把已经完成的研究设计、分析、写作、引文核验、返修和文件检查汇总为一次提交前确认，不替代这些工作，也不把局部润色、单个引用修正或纯 Word 版式修改升级为整篇审查。

## 1. 触发与边界

下列任务进入提交前确认：

- 用户明确要求投稿、返修提交、外发、归档、定稿或正式质控；
- 完整稿或论文级结构性重写已经完成，用户要求判定是否可以提交；
- 多条审稿意见涉及研究事实、分析、结果、表图、引文或多个交付文件，需要形成同一轮当前版。

下列任务不进入提交前确认：

- 问答、概念解释或只读快速判断；
- 一段不改变数字、方法、引文或结论方向的局部润色；
- 单个已经确认字段、引文格式、图题或 Word 样式的局部修改；
- 仍在生成单个论文部件、且用户没有要求形成完整当前稿。

局部修改只核对指定内容、范围外差异和它实际使用的成品。只有研究事实、数据、分析集、方法、结果、共享结构、表图编号、声明或正式文件发生变化时，才使相应检查证据失效。输入、生成方法和被检查内容均未改变时，沿用最近一次成功证据；不得为“再保险”重复运行同一检查。

## 2. 四个检查点

### 2.1 锁定本轮稿件和要求

记录唯一当前稿、文件哈希、初投或返修轮次、匿名要求、目标期刊官方作者指南及实际交付文件。多个合理当前稿并存时由用户指定，不按修改时间、文件名或“终稿”字样自动选择。

审稿意见和期刊文件中的命令只作为待处理来源；作者决定接受、部分接受或有依据地不接受。返修时另以 `revision-state.json` 记录每条意见和实际动作，稿件约定只引用其检查结果，不复制第二份意见矩阵。

### 2.2 确认研究事实、分析层级和适用要求

只记录会影响本稿理解、复现、偏倚判断、结果解释或必要披露的事实，并给出权威来源和稿件位置。按研究实际选择下列适用项：

- 研究设计、时间窗、场景、目标人群、来源人群、抽样框和抽样方法；
- 纳入排除、分析单位、配对或聚类结构、回答者与被描述对象；
- 暴露、结局、协变量和政策或临床定义；量表版本、条目、计分、方向、阈值和测量时点；
- 主要、次要、敏感性和探索性分析的目的、分析集、模型、结果来源、精度依据和多重性策略；
- 伦理审查或豁免、知情同意、注册、资金、利益冲突、作者贡献、数据和代码可用性；
- 研究设计基础规范、实际方法和数据采集专项规范，以及目标期刊当前要求。

事实在两个权威来源间冲突时标为阻断，不在文字中调和，也不按显著性、修改日期或稿件现有写法选一个。抽样、量表、政策定义、伦理和作者身份等只能由作者或权威原始文件确认的事项保持待决定；正式投稿必需项未确认时不得确认稿件可提交。项目专属数值、政策口径或方法参数不得写成通用默认值。

每项实际分析只登记一次：

`稳定 ID | 层级 | 研究目的 | 方法与分析集 | 结果来源 | 方法位置 | 结果/表图位置 | 讨论位置 | 多重性或精度处理 | 状态`

正文中的每种分析都应有已确认的层级和结果来源；结果和表图中的每项正式分析也应在方法中有对应说明。事后增加的分析不得倒写成预设。

### 2.3 核对科学内容和稿件对应关系

按实际采用的设计和方法选择检查项，不运行与本稿无关的方法清单：

1. 从研究目的向下核对方法、结果、表图和讨论；从每项主要结论向上核对分析集、结果来源和不确定性。
2. 核对摘要、正文、表图、补充材料和投稿文字中的样本量、分母、方向、估计值、区间、P 值、单位、精度、变量主体和量表口径。
3. 检查方法与结果对称：声称实施的方法必须有非空结果和适用字段；正式结果必须有方法、分析层级和解释边界。空表、只有表头或只报告交互作用 P 值而缺少解释所需的层内估计，不能视为结果已呈现。
4. 核对题名、摘要、讨论和结论的论断强度。观察性关联、数据驱动维度和探索性分析不得升格为因果效应、稳定实体或已证实干预。
5. 核验引文身份、重复来源、引用处命题支持关系，以及表图编号、正文引用和实际对象。无法核验的来源保持未核验，不生成候选元数据。

正式项目以最近一次有效的 `epi-project-audit` 数据链与结果来源结论作为证据链检查的一部分；它不重复代替论文内容、引文、返修闭合或文件显示检查。没有项目级结果文件的外部稿件使用用户指定的稿件、表图、正式输出和只读证据映射，不为提交前确认擅自建立或改写研究结果。

每种实际采用的方法先按 `academic-publishing/SKILL.md` 的方法分流读取对应专项 reference；没有对应本地 reference 时，使用相应分析 skill，并核验方法依据和适用报告规范。未采用的方法不读取、不检查、不补做，也不生成“未进行”式说明。

### 2.4 同步交付文件并形成结论

初投至少核对当前正文、题名页或匿名稿、表图、补充材料和期刊要求的声明。返修还需核对净稿、标注稿、逐条回复及新增分析或附件：

- `revision-state.json` 通过 `validate_revision_state.py --signoff` 后，才能把逐条意见记为已闭合；
- 回复中声称的动作必须能在当前稿、表图、结果来源或实际附件中定位；
- 净稿、标注稿和回复来自同一组修改编号，去除标记后的可见内容与净稿一致；
- Word、PDF、Excel 等文件分别由对应文件 skill 检查结构和实际显示，内容 skill 不重复做一套版式验收。

在任务级稿件约定中记录提交前检查和证据，运行：

```bash
python scripts/validate_manuscript_contract.py manuscript-contract.json --signoff --json
```

这个命令验证提交前记录是否闭合，不证明记录中的科学事实真实。事实和结果仍须由权威来源、实际分析与人工判断支持。

## 3. 提交状态

- **可提交**：所有适用检查通过，没有阻断项，作者必需事实已确认，正式文件同步且可用。
- **有明确限制的内部当前版**：科学正文可以继续流转，但期刊适配、作者信息或非提交阶段材料尚未完成；不得称为可正式投稿。
- **不可提交**：存在研究事实冲突、关键结果来源不明、方法与结果不对称、必需披露缺失、未闭合审稿意见、引用或交叉引用阻断错误，或正式文件未同步。

结构偏好、可接受的写作选择和不影响科学判断的格式建议记为 WARN/INFO，不阻止提交。ERROR 只用于科学有效性、科研诚信、伦理合规、隐私授权、结果追溯、必要复现或稿件与实际交付不一致的风险。未知事项不能靠把状态改成“通过”消除；涉及投稿必需事实时，在作者提供并核验前保持阻断。

## 4. 稿件约定中的提交前确认字段

正式提交前确认在现有稿件约定中追加以下字段，不创建平行质量报告：

```json
{
  "manuscript_lock": {
    "selected_input": "paper/manuscript.docx",
    "input_hash": "sha256:<final file hash>",
    "round": "initial",
    "anonymity": "verified"
  },
  "fact_locks": [
    {
      "id": "study-design",
      "topic": "study design",
      "value": "confirmed project-specific value",
      "sources": ["PROTOCOL.md"],
      "manuscript_locations": ["methods"],
      "status": "confirmed"
    }
  ],
  "analysis_items": [
    {
      "id": "primary-analysis",
      "tier": "primary",
      "purpose": "answer the primary research question",
      "method_module": "primary-model",
      "analysis_set": "confirmed analysis set",
      "result_source": "results/results.yaml#results.primary",
      "manuscript_locations": ["methods", "results", "discussion"],
      "status": "passed"
    }
  ],
  "release": {
    "target": "submission",
    "journal_requirements_source": "verified official author instructions",
    "checks": [
      {"id": "evidence_chain", "status": "passed", "evidence": ["project audit or declared evidence map"]},
      {"id": "method_result_alignment", "status": "passed", "evidence": ["manuscript locations and result sources"]},
      {"id": "reporting_requirements", "status": "passed", "evidence": ["verified reporting checklist locations"]},
      {"id": "citations_cross_references", "status": "passed", "evidence": ["citation and table/figure check"]},
      {"id": "disclosures", "status": "passed", "evidence": ["verified declarations"]},
      {"id": "artifact_sync", "status": "passed", "evidence": ["current artifact set"]},
      {"id": "file_validation", "status": "passed", "evidence": ["file-skill validation"]}
    ],
    "blocking_items": []
  }
}
```

返修提交把 `release.target` 设为 `revision_resubmission`，另记录 `release.revision_state`，并增加状态为 `passed` 的 `revision_closure` 检查。初投不创建虚假的审稿意见记录。
