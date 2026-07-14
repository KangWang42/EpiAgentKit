# EpiAgentKit

面向流行病学 / 卫生统计研究的 Claude Code 与 Codex 共用规则和技能集（R + Python），覆盖从项目初始化、统计分析、发表级图表、论文写作、咨询交付到项目审查的完整研究流程。

完整项目框架按需启用：简单作业、单次处理、快速核验或少量输出使用轻量任务模式，只执行必要 skill 与最小验证，不自动创建七层目录、项目账本或运行项目签发；明确初始化、投稿/咨询交付，或已位于标准项目中时才采用完整契约。

A shared Claude Code and Codex rule/skill ecosystem for epidemiology and biostatistics research, covering project scaffolding, statistical analysis, publication-quality figures, manuscript writing, consulting deliverables, and project auditing.

## 仓库内容

```
CLAUDE.md          双平台全局规则源（安装为 Claude 的 CLAUDE.md / Codex 的 AGENTS.md）
AGENTS.md          本仓库 contributor guide
skills/            Agent Skills 标准技能集（按需加载，渐进披露）
hooks/             Claude Code / Codex 共用的确定性检查脚本
scripts/           双平台安装、同步与验收工具
```

## 技能架构

技能按职责分层；安装预设中的依赖只决定安装闭包，不表示运行时必须同时调用：

| 层 | 技能 | 作用 |
|---|---|---|
| 原则层 | `biostat-principles` | 六条底层行为原则（先问口径、最小实现、只改必要、可验证、可追溯、可复现）+ 探索新方法的隔离试验工作流。所有分析类任务开工前先对齐 |
| 证据层 | `evidence-research` | 文献检索、来源核验、证据矩阵与跨领域适用性判断；不代跑模型或代写论文正文 |
| 执行层 | `project-init` | 一键创建标准项目结构、PROTOCOL/SAP 前置门禁、探索实验索引与表图 registry（研究 / 咨询双模式） |
| | `r-biostats` | R 统计分析执行层：PLAN-CODE-RUN-VERIFY-DOC 五阶状态机，描述统计 / 回归 / 生存 / 中介 / Meta |
| | `python-ecg-analysis` | 通用 Python ECG 预处理、质量控制、纵向对齐、临床结局连接与患者级建模门禁 |
| | `publication-figures` | 发表级图件规范（mm 尺寸 / 字体嵌入 / 期刊配色）+ 约 180 种图选型画廊 + 170 余套配方代码 |
| | `svg-diagrams` | 论文、报告与 PPT 的 SVG 原生流程图、结构图、技术路线、包含关系图和机制示意，含对齐、比例与载体适配规范 |
| 产出层 | `academic-publishing` | 中英双语论文生成（GB/T 7713 / IMRaD）+ 投稿材料（Cover Letter / 审稿回复 / Highlights），逐部件门控写作 |
| | `consulting-delivery` | 咨询交付包标准：自包含、一键复现、空 session 实测、终检清单 |
| | `sysu-ppt` | 组会汇报 PPT 代码化生成（R officer，含可复用模板与工具库） |
| 质控层 | `academic-humanizer` | 中英文学术文本的事实锁、论断证据、作者声纹与学术语体审校 |
| | `epi-project-audit` | 六层项目审查状态机：骨架 / 数据链 / 代码 / 结果一致性 / 科学合理性 / 交付一致性，带数字一致性矩阵 |
| 工具层 | `docx` `pdf` `pptx` `xlsx` `skill-creator` `git-commit-helper` | 文档处理与技能维护（前五个源自 Anthropic 官方技能库，保留各自 LICENSE） |

组合路由遵循“内容主流程 → 实际文件操作 → 终审”：论文从零生成用 `academic-publishing → academic-humanizer`，需要 Word 时再加 `docx`；已有学术文本编辑以 `academic-humanizer` 为主；报告用 `report-writing → docx`；中大学术汇报用 `sysu-ppt → pptx`；统计分析用 `biostat-principles → r-biostats`，仅实际出图时加 `publication-figures`。`consulting-delivery` 仅用于分析完成后的最终外发打包。

## 双平台兼容

技能主体遵循 Agent Skills 目录结构：每个 skill 必有 `SKILL.md`（`name` + `description`），可带 `scripts/`、`references/`、`assets/` 与 Codex 可选的 `agents/openai.yaml`。Claude Code 与 Codex 读取同一份技能内容，不维护两套正文。

| 项目 | Claude Code | Codex |
|---|---|---|
| 全局规则 | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` |
| 用户 skills | `~/.claude/skills/` | `~/.agents/skills/` |
| hooks | `~/.claude/hooks/` + `settings.json` | `~/.codex/hooks/` + `hooks.json` |
| 安装清单 | `~/.claude/.epiagentkit-install.json` | `~/.codex/.epiagentkit-install.json` |
| 显式调用 | `/skill-name` | `$skill-name`（或 `/skills` 选择） |
| 自动触发 | 按 `description` | 按 `description` |

Codex 的目录和调用约定见官方 [Build skills](https://learn.chatgpt.com/docs/build-skills) 与 [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。`skill-creator` 已由 Codex 内置，向 Codex 同步时默认跳过仓库同名副本，避免重复技能。

## 安装与同步

克隆后运行统一入口。交互式安装会询问目标平台和导入范围，安装完成后自动执行 `doctor` 验收：

```bash
git clone git@github.com:KangWang42/EpiAgentKit.git ~/epiagentkit
python ~/epiagentkit/scripts/epiagentkit.py install
```

常用命令：

```bash
# 只为 Codex 安装 PPT + SVG 图解技能包，不覆盖共享规则与 hooks
python ~/epiagentkit/scripts/epiagentkit.py install --target codex --preset ppt --yes

# 为 Claude 与 Codex 完整安装，覆盖同名 EpiAgentKit 规则/skills/hooks，保留无关个人配置
python ~/epiagentkit/scripts/epiagentkit.py install --target all --preset full --yes

# 自选 skills；依赖项会自动补齐
python ~/epiagentkit/scripts/epiagentkit.py install --target all --preset custom \
  --skills sysu-ppt,report-writing --with-rules --yes

# 从仓库同步已安装内容并复核双端一致性
python ~/epiagentkit/scripts/epiagentkit.py sync --target all
python ~/epiagentkit/scripts/epiagentkit.py doctor --target all

# 查看预设与可安装技能
python ~/epiagentkit/scripts/epiagentkit.py list

# 对研究项目运行确定性签发预检
python ~/epiagentkit/scripts/epiagentkit.py check-project <项目根>

# 只同步部分 Codex skills
python ~/epiagentkit/scripts/epiagentkit.py sync --target codex \
  --components skills --skills sysu-ppt,svg-diagrams
```

只安装一个平台时用 `--target claude` 或 `--target codex`。`--components` 可选 `rules,skills,hooks` 的任意组合，`--skills` 可列出部分技能；部分同步不会删除先前安装的其它托管 skills。Codex skills 布局由 `--codex-layout` 控制：默认 `auto` 与 `agents` 均只使用官方 `~/.agents/skills/`；`codex` 使用兼容目录 `~/.codex/skills/`，`both` 双写，后二者会显示重复技能风险警告，不作为默认安装或验收基线。

首次按默认布局同步时，同步器会列出旧 `~/.codex/skills/` 中由 EpiAgentKit manifest 管理的技能；与仓库源重复的旧根副本会直接删除，`.system` 与无冲突的非受管技能保持原位。可先演练迁移：

```bash
python scripts/epiagentkit.py sync --target codex --components skills --dry-run
```

每次安装或同步 `skills` 前都会遍历 Claude Code 与 Codex 的 Skill 发现目录，检查两类冲突：①与待安装权威 Skill 同名但内容不同；②名称不同，但 `description` 命中同一广义触发场景。已经明确写成“停用 / 委派 / 仅在特定条件下使用”的后备 Skill 不判为冲突。

同名或触发范围冲突的旧 Skill 会在安装前直接、永久删除，不保留内容副本。同步器只在 `~/.epiagentkit/skill-conflict-reports/<UTC批次>/manifest.json` 写入一份小型删除记录，登记原路径、冲突类型、命中的触发词和委派目标。目标目录中与仓库完全一致的当前版不处理；使用 `--dry-run` 时只显示拟删除项和报告位置，不删除文件。正式执行前应自行备份需要保留的个人 Skill。

安装前建议先运行：

```bash
python scripts/epiagentkit.py install --target codex --preset full --yes --dry-run
```

默认 `doctor` 会扫描两个 Codex 发现根，同名技能跨根重复时验收失败。需要临时回退到旧布局时，可显式运行带警告的 `--codex-layout codex` 或 `--codex-layout both` 重新同步；恢复默认布局后再次同步即可安全迁回官方目录。

仓库是唯一配置源。同步器只覆盖同名 EpiAgentKit 文件并合并受管 hook，不改认证、模型、密钥或无关个人配置；每个平台的安装清单记录组件、skills 目录和来源，供 `doctor` 逐文件验收。原命令 `configure_user.py`、`sync_user_configs.py` 与 `epiclaude.py` 保留兼容，但新文档与自动化统一使用 `epiagentkit.py`。

也可只挑选单个技能目录复制到相应 `skills/` 目录。修改技能后若界面未刷新，重启对应客户端。

注意：`sysu-ppt` 的字体与部分路径按 Windows 编写（`USERPROFILE` 环境变量、`C:/Windows/Fonts`），macOS / Linux 使用需按 `SKILL.md` 内注释调整。

## 维护校验

修改规则或 skills 后运行：

```bash
python scripts/audit_workflow_contracts.py
python scripts/epiagentkit.py doctor --target all
```

该检查覆盖全部 skill 元数据、`CLAUDE.md` / `AGENTS.md` 的 200 行预算，以及初始化、探索隔离、vendored helper 和提交授权等跨 skill 契约。行为发生变化时仍须对相关 R / Python / Bash 脚本做语法检查与最小实跑。

## 推荐 Hook 配置（可选，把硬红线交给 harness 强制）

客户端只注册三个聚合 hook：一个 PreToolUse 原始数据保护、一个编辑后代码/文本检查、一个命令后图件/结果检查。同步器会复制脚本并自动合并配置：Claude Code 写入 `~/.claude/settings.json`，Codex 写入 `~/.codex/hooks.json`，不会覆盖模型、权限或无关自定义 hook。修改前会在同目录保留第一次变更前的稳定 `.epiagentkit.bak` 配置备份。Codex 修改 hook 后需在 `/hooks` 中重新审查并信任；其发现和信任规则见官方 [Hooks](https://learn.chatgpt.com/docs/hooks)。

安装或同步 hooks 前会按事件、matcher、命令名和本地脚本内容遍历现有注册，识别原始数据保护、R 语法、AI 痕迹、图件自检和 `.rds` 检查五类功能冲突。冲突注册以 EpiAgentKit 为准并从本地配置删除；冲突脚本只有位于对应客户端 `hooks/` 目录、未被保留注册引用且不属于待安装文件时才永久删除，不保留脚本内容副本。Codex 的非冲突 inline hooks 会从 `config.toml` 迁移到 `hooks.json`，避免同一配置层同时加载两种 Hook 来源；无关 Hook 和其他配置保持不变。删除清单写入 `~/.epiagentkit/hook-conflict-reports/<UTC批次>/manifest.json`，`--dry-run` 只预览。

- `protect_rawdata.sh`（PreToolUse）：canonicalize 编辑路径并拦截 `01_data/rawdata/` 及项目 `.epiagentkit-raw-roots` 声明的额外原始根。声明文件每行一个项目相对路径，支持中文、空格、反斜杠与 `../` 归一化。该 hook 不解析任意 shell/Python/PowerShell 写入，不能替代 ACL、只读副本和终检。
- `check_r_syntax.sh`（PostToolUse）：`.R` 文件存盘即 `parse()` 语法检查，出错当场反馈给模型修。
- `scan_ai_trace.sh`（PostToolUse）：按明确字符集扫描生成过程痕迹与 emoji；允许科研符号 `→ ↔ ↑ ↓ ± × ≥ ≤ ℃`，`✅` 只允许出现在 `BACKLOG.md` 状态列。
- `fig_selfcheck.sh`（PostToolUse / Bash）：用“项目绝对标识 + 文件内容指纹”检测 `04_figures/` 新生成或修改的图，不依赖 120 秒窗口；注入 `publication-figures §12ter` 自检清单，视觉判断仍由主模型完成。
- `check_results_rds.sh`（PostToolUse / Bash）：同样按项目隔离的内容指纹检测 `06_results/` 新写入或修改的 `.rds`，提醒表格化数据改存 `.xlsx`。

客户端配置不分别注册上述四个 PostToolUse 检查，而由 `post_edit_checks.sh` 聚合 R 语法 + 文本规范、`post_bash_checks.sh` 聚合图件 + `.rds` 检查。一次“修改出图脚本 + 执行出图”最多显示两个 PostToolUse hook；两类命令后提醒同时命中时合并为一条消息。原检查脚本仍可单独运行，便于诊断与兼容旧调用。

交付前另运行确定性终检，不注册为自动修复 hook：

```bash
python scripts/epiagentkit.py check-project <项目根>
```

它检查原始目录的 Git 工作区修改、编号/stem、合法 helper、旧版本命名、provenance receipt 或降级 mtime 提示、日志异常，以及疑似凭证或高熵秘密。秘密检查只报告文件、键路径和行号，不输出值；raw roots、`09_backup`、`.git` 与大型缓存会在进入目录前剪枝。双端 Stop hook 的一致行为尚未作为稳定契约验证，因此默认不注册 Stop，不在失败后自动循环修复；PostToolUse 仅报告已发生事件，不能撤销副作用。

（"多行 `Rscript -e` 会 segfault、须写成 `.R` 文件运行"这条已直接写进 `CLAUDE.md` 的代码必跑红线，常驻每会话上下文，无需单设 hook。）

安装或修复 hook：

```bash
# 仅安装并注册 hooks
python scripts/epiagentkit.py sync --target all --components hooks

# 安装 PPT 技能包并同时注册 hooks
python scripts/epiagentkit.py install --target all --preset ppt --with-hooks --yes
```

Windows 配置由同步器统一通过 `run_hook.cmd` 定位 Git Bash，不依赖 hook 进程的 `PATH`；macOS / Linux 使用 `bash`。再次执行会替换旧的 EpiAgentKit hook 命令并保持幂等，不会重复注册。图件与 `.rds` 检查属于非阻断提醒：Claude 通过 `additionalContext`、Codex 通过 `systemMessage` 接收，并以退出码 0 完成，不会显示为 hook failed；真正违反 rawdata 保护或代码门禁时仍返回阻断状态。每个 hook 只在命中目标文件或目录时动作；无 `jq` 时由 Python 解析 stdin JSON。

## 设计原则

本仓库的写法遵循几条经验规则，也是它区别于"把所有规范堆进 CLAUDE.md"的地方：

1. **删除测试 + 入口预算**：全局规则每条都要回答"删了 agent 会犯什么具体错误"，答不出就删。`CLAUDE.md` / `AGENTS.md` 控制在 200 行以内，只放跨任务红线、路由与索引；程序、模板和领域细节下沉到 skill / references。
2. **规则与流程分离**：CLAUDE.md 只放每个 session 都需要的硬红线与路由表；多步骤工作流全部下沉到技能，按需加载不占上下文。
3. **渐进披露**：技能正文只放核心流程与门禁，模板、句式库、配方代码放 `references/`，由模型在需要时自行读取。
4. **单一真源**：表图编号走 registry（编号 = 清单位置，脚本经 `table_path()` / `fig_path()` 取路径）；口径常量集中 `config.R` + `conventions.R`；论文数字机器单源 `07_paper/results.yaml`（脚本渲染一次写入、`render_summary_md()` 派生 `0_result_summaries.md`、下游 `val()` 取数禁手敲）。
5. **门禁状态机**：分析（PLAN-CODE-RUN-VERIFY-DOC）、写作（逐部件自检）、交付（八阶段）、审查（六层）都是"不过检不许进下一步"的状态机，而非建议清单。
6. **强制实跑与全量扫错**：代码写完必须实际执行，输出全量 grep error / warning，每条报错三选一去向（修复 / 记录豁免 / 核实可忽略），不允许沉默放过。
7. **预设与探索分轨**：`PROTOCOL.md` / `SAP.md` 在分析前冻结主要问题和方法；全部尝试登记在 `09_backup/EXPERIMENTS.md` 并隔离运行，只有过公平比较门禁且经确认的结果进入主线。
8. **当前版单一、旧版可检索**：工作区每种报告、PPT、论文和代码只留稳定命名的当前版；被替代的成品、对应源文件、素材与核验输出按批次移入 `09_backup/YYYY-MM-DD_HHMM_<主题>_<阶段>/`，以 `MANIFEST.md` 和 `09_backup/INDEX.md` 定位历史，不再堆叠“完善版 / 最终版 / v2”。

## 目录约定

技能围绕一套七层项目结构工作（由 `project-init` 创建）：

```
01_data/rawdata/   只读原始数据
PROTOCOL.md / SAP.md 研究方案与预设统计分析计划
02_code/           config.R / conventions.R / vendored/ + 编号脚本（连续编号，<= 10 个）
03_tables/         Table{N}_*.xlsx（附表进 supplementary/）
04_figures/        Fig{N}_*.{pdf,png,svg}（SVG 用于非统计图解）
05_reports/        对外交付包
06_results/        中间对象（按内容命名不编号）
07_paper/          论文 + results.yaml（数字机器单源）+ 0_result_summaries.md（由其派生）
09_backup/         INDEX.md + 分批旧版 / 一次性脚本 / 探索实验（EXPERIMENTS.md 索引全部尝试）
```

## 适用范围与使用须知

- **面向流行病学 / 卫生统计，但不限于此**：规则与技能以流行病学、临床与真实世界数据研究为蓝本编写，其底层做法（项目分层、单一真源、门禁状态机、发表级图表、证据约束写作）是通用的研究工程实践。其他定量研究领域（基础医学、社会科学、生态、经济计量等）可直接参考，并按本领域的口径、报告规范与文献格式自行拓展、改写技能内容。
- **项目处理流程为个人经验，按需取舍**：七层目录、脚本编号、表图 registry、交付包形态等约定，是作者在自身研究与咨询中沉淀的个人偏好，并非领域标准或唯一正确做法。认同则用，不认同的条目可直接删改，介意者请勿套用。
- **Agent 改动框架的权限较大，使用前请知情**：全局规则授予 Claude Code 与 Codex 较大的自主整理权限，可能移动 / 归档 / 重排文件、改写脚本输出路径、归并代码或调整表图编号。建议在版本控制（git）下使用并先备份重要数据；`01_data/rawdata/` 是只读红线，其余自动整理行为请在了解后启用。

## 说明

- `docx` / `pdf` / `pptx` / `xlsx` / `skill-creator` 来自 [anthropics/skills](https://github.com/anthropics/skills)，各目录内保留原始 LICENSE；本仓库对 `skill-creator` 做了 Windows 中文环境的编码修复。
- `sysu-ppt` 内置的两套 PPT 模板版权归中山大学所有，仅供学习参考；如有顾虑请删除 `skills/sysu-ppt/assets/` 后使用自己的模板。
- `sysu-ppt` 默认使用中大医学棕榈封面模板（原模板2）；原公卫学院绿色模板保留为 `模板2` 可选项。
- 中文技能（原则 / 分析 / 论文 / 交付 / 审查 / 学术审校）为本仓库原创，针对中文学术写作与中文期刊投稿场景做了大量特化。

## 贡献者

- OpenAI Codex：安装前 Skill 冲突扫描、直接清理与可审计登记流程。
