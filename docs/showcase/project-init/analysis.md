# cohort_analysis_demo 初始化成果

- profile：analysis
- 研究设计：cohort
- 分析语言：r
- Git：未初始化
- 生成来源：skills/project-init/scripts/init_project.R 实际运行

## 目录与文件

```text
cohort_analysis_demo/
  .epiagentkit-layout.json
  .epiagentkit-raw-roots
  .gitignore
  01_data
  01_data/rawdata
  01_data/rawdata/.gitkeep
  01_data/README.md
  02_code
  02_code/00_setup.R
  02_code/01_data_cleaning.R
  02_code/vendored
  02_code/vendored/.gitkeep
  02_code/vendored/data_readiness.R
  02_code/vendored/emit_summary.R
  02_code/vendored/fig_setup.R
  03_tables
  03_tables/.gitkeep
  04_figures
  04_figures/.gitkeep
  09_backup
  09_backup/archive
  09_backup/workbench
  AGENTS.md
  BACKLOG.md
  CLAUDE.md
  cohort_analysis_demo.Rproj
  DECISIONS.md
  PROTOCOL.md
  README.md
  results
  results/derived
  results/derived/.gitkeep
  results/runs
  results/runs/.gitkeep
  run_pipeline.R
  SAP.md
```

## 验收

- 已创建所选 profile 的最小正式研究结构。
- 01_data/rawdata/ 仅含保护占位文件，未写入研究数据。
- 总运行脚本与 02_code/00_setup.R 已生成；数据准备与正式分析分别登记，后者受分析就绪状态检查约束。
- 项目设置与数据说明保留权威分析输入、格式、工作表或对象及镜像角色的待确认合同，不预设 Excel、RDS 或文件名。
- .epiagentkit-layout.json 仅声明目录和正式产物类别。
- 09_backup/ 两个本地分支均已创建，目录内无 .gitkeep，且由 .gitignore 整体排除。
- 尚未提前创建 results/results.yaml、SESSION_LOG.md、EXPERIMENTS.md。
