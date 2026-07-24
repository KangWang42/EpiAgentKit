# 全局规则下沉对照

本表记录 2026-07-13 的功能保持型瘦身。目标是减少每会话注入量，不删除有效约束。

| 原规则组 | 当前保留或下沉位置 | 行为保持 |
| --- | --- | --- |
| 研究者视角、书面语、口径先问、交付自检 | `CLAUDE.md` §1、§6 | 保留为跨任务规则 |
| skill 触发表 | `CLAUDE.md` §2 与各 skill description | 增加主流程、文件伴随、终审顺序 |
| rawdata 只读、相对路径、工作区安全、凭证保护 | `CLAUDE.md` §3 | 保留为硬红线 |
| 当前版单一、整组归档、MANIFEST/INDEX | `project-init/references/project-hygiene.md` §1–2；各产出 skill 终检 | 细节下沉，入口保留指针 |
| `02_code/` 语言、连续编号、脚本数量和一次性脚本 | `project-hygiene.md` §3；`r-biostats/references/code-style.md`；`epi-project-audit` Layer 1/3 | 生成与审查双重覆盖 |
| Table/Fig 命名、supplementary、xlsx 与 registry | `project-hygiene.md` §4–5；`project-init/references/registry.md`；`epi-project-audit` | 规则与实现分离 |
| results.yaml、DECISIONS、SESSION_LOG、conventions | `CLAUDE.md` §4、§7；`biostat-principles/references/result-summary-schema.md` | 单源指针常驻，schema 下沉且由 R/Python 共用 |
| BACKLOG 四列、状态与移出流程 | `project-hygiene.md` §6；`project-init` 模板 | 完整格式下沉，发现即记仍为硬红线 |
| error/warning/NaN 全量核验 | `CLAUDE.md` §5“执行与异常闭环”；执行 skill 的 RUN/VERIFY | 保留为跨任务硬红线 |
| 数据缺陷、清洗痕迹与论断强度 | `CLAUDE.md` §4；`academic-publishing`、`academic-humanizer` | 保留科学表达要求 |
| 目录骨架与探索实验 | `project-hygiene.md`；`biostat-principles` 探索工作流 | 细节下沉 |
| Git 收尾与双端同步 | `CLAUDE.md` §9；`git-commit-helper` | 保留用户偏好与安全边界 |
| 完成前长清单 | `CLAUDE.md` §9 最短完成条件；`project-hygiene.md` §7；`epi-project-audit` | 通用完成要求常驻，领域终检按需加载 |
| 多套优先级与记忆锚点 | 仅 `CLAUDE.md` §8 定义优先级；其他 skill 引用 | 消除相反排序，锚点由单源指针覆盖 |
