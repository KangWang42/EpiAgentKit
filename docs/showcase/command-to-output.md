# 从命令到输出

本页把 README 中不适合用单张效果图表达的 skill，整理为可执行入口和真实输出位置。没有固定项目输入的 skill 不伪造研究结果，直接链接到它的格式规范或参考模板。

| Skill | 命令或请求示例 | 当前可查看输出 |
| --- | --- | --- |
| `biostat-principles` → `r-biostats` | `Rscript docs/demo/generate_survival_demo.R` | [模拟数据](../demo/survival-demo-data.csv)、[结果清单](../demo/output/publication-figures/survival-demo-results.csv) |
| `evidence-research` | 核验一条 DOI、方法依据或最新指南 | [证据矩阵规范](../../skills/evidence-research/references/evidence-matrix.md)、[检索协议](../../skills/evidence-research/references/search-protocol.md) |
| `epi-study-design` | 把研究想法转成 PROTOCOL / SAP | [方案规格](../../skills/epi-study-design/references/protocol-sap-specification.md) |
| `python-biostats` | 明确指定 Python 后执行同一研究口径 | [Python 执行边界](../../skills/python-biostats/SKILL.md)；本仓库不把 R 结果冒充 Python 示例 |
| `academic-humanizer` | 修订已有论文、报告或投稿文本 | [中文稿 Word](../demo/output/academic-publishing/manuscript-preview-zh.docx) · [英文稿 Word](../demo/output/academic-publishing/manuscript-preview-en.docx) |
| `report-writing` | 把已核验结果整理成报告正文 | [报告写作流程](../../skills/report-writing/SKILL.md) · [报告构建参考](../../skills/report-writing/references/build_report.py) |
| `consulting-delivery` | 把已完成分析整理为外发交付包 | [咨询项目结构示例](project-init/consulting.md) · [交付模板](../../skills/consulting-delivery/references/templates.md) |
| `manuscript-peer-review` | 以同行评审人身份生成可定位审稿报告 | [审稿标准](../../skills/manuscript-peer-review/references/review-criteria.md) · [报告模板](../../skills/manuscript-peer-review/references/report-template.md) |
| `epi-project-audit` | `python <skill>/scripts/run_check_project.py <项目根> --json` | [审查清单](../../skills/epi-project-audit/references/audit-checklist.md) · [论断校准](../../skills/epi-project-audit/references/claim-calibration.md) |
| `docx` / `pdf` | 打开、渲染、验证或转换实际文件 | [Word](../demo/output/academic-publishing/manuscript-preview-zh.docx) · [PDF](../demo/output/academic-publishing/manuscript-preview-zh.pdf) |
| `xlsx` | 读取、清洗、创建或核验工作簿 | [工作簿操作规范](../../skills/xlsx/SKILL.md)；需绑定用户数据后生成，不放虚构表格 |
| `workflow-retrospective` | 根据会话纠正生成 `workflow.txt` | [维护流程说明](../../README.md#维护与贡献)；现场报告只保留在对应 workbench |
| `epiagentkit-maintenance` / `skill-creator` | 修改 skill、规则或同步规范 | [维护约定](../../AGENTS.md#skill-maintenance) · [skill 编写指南](../../skills/skill-creator/SKILL.md) |
| `git-commit-helper` | 审查完整差异并创建 Conventional Commit | [提交历史](https://github.com/KangWang42/EpiAgentKit/commits/main) |
