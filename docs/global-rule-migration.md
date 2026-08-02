# 全局规则维护位置对照

本表说明原有全局规则现在由哪个文件维护。目标是减少每次会话需要读取的内容，同时保留有效要求。

| 原规则组 | 当前维护位置 | 保留的行为 |
| --- | --- | --- |
| 研究者视角、书面语、口径先问、交付自检 | `CLAUDE.md` §1、§2、§5、§7 | 保留为跨任务规则 |
| skill 触发表 | `CLAUDE.md` §1 与各 skill description | 全局保留日常主流程，具体触发边界按需加载 |
| rawdata 只读、相对路径、工作区安全、凭证保护 | `CLAUDE.md` §2 | 保留为必须遵守的安全要求 |
| 当前版单一、整组归档、`MANIFEST.json` 和 `INDEX.md` | `project-init/references/project-hygiene.md` §1–2；各产出 skill 终检 | 具体归档步骤由目录规范说明，全局规则只保留适用条件和来源 |
| `02_code/` 语言、连续编号、脚本数量和一次性脚本 | `project-hygiene.md` §3；`r-biostats/references/code-style.md`；`epi-project-audit` Layer 1/3 | 生成与审查双重覆盖 |
| Table/Fig 命名、supplementary、xlsx 与表图编号表 | `project-hygiene.md` §4–5；`project-init/references/registry.md`；`epi-project-audit` | 规则与实现分离 |
| `results/results.yaml`、`DECISIONS.md`、自动运行记录和 `conventions` | `CLAUDE.md` §3；`biostat-principles/references/result-summary-schema.md` | 结果由实际生成结果的分析脚本写入，运行情况自动记录，R 与 Python 使用同一文件结构 |
| BACKLOG | `CLAUDE.md` §3；`project-init` 模板 | 只保存需要后续补充材料、外部资源或用户决定的未决事项，当轮问题不另建记录 |
| error/warning/NaN 全量核验 | `CLAUDE.md` §4“执行与异常处理”；执行 skill 的运行与核对步骤 | 保留为跨任务必须执行的检查 |
| 数据缺陷、清洗痕迹与论断强度 | `CLAUDE.md` §3；`academic-publishing`、`academic-humanizer` | 保留科学表达要求 |
| 项目目录结构与探索实验 | `project-hygiene.md`；`biostat-principles` 探索工作流 | 具体步骤由相应 skill 和 reference 说明 |
| Git 收尾 | `CLAUDE.md` §7；`git-commit-helper` | 保留用户偏好与安全边界 |
| 双端同步与仓库维护 | `epiagentkit-maintenance`、`AGENTS.md` | 仅维护仓库时按需加载，不注入日常研究会话 |
| 完成前的详细检查项目 | `CLAUDE.md` §7 完成条件；`project-hygiene.md`；`epi-project-audit` | 通用完成要求常驻，只有正式发布才加载完整检查清单 |
| 多处重复的优先级和规则说明 | 仅 `CLAUDE.md` §6 定义优先级；其他 skill 直接引用 | 删除相互矛盾的排序，所有任务采用同一优先级 |
