# EpiClaude

面向流行病学 / 卫生统计研究的 Claude Code 全局规则与技能集（R + Python），覆盖从项目初始化、统计分析、发表级图表、论文写作、咨询交付到项目审查的完整研究流程。

A Claude Code global-rules file and skill ecosystem for epidemiology / biostatistics research, covering the full workflow: project scaffolding, statistical analysis, publication-quality figures, manuscript writing, consulting deliverables, and project auditing.

## 仓库内容

```
CLAUDE.md          全局规则（每个 session 加载的跨任务硬红线，< 120 行）
skills/            技能集（按需加载，渐进披露）
```

## 技能架构

技能按依赖关系分五层，上游约束下游：

| 层 | 技能 | 作用 |
|---|---|---|
| 原则层 | `biostat-principles` | 六条底层行为原则（先问口径、最小实现、只改必要、可验证、可追溯、可复现）+ 探索新方法的隔离试验工作流。所有分析类任务开工前先对齐 |
| 执行层 | `project-init` | 一键创建七层标准项目结构 + 表图编号 registry（研究 / 咨询双模式） |
| | `r-biostats` | R 统计分析执行层：PLAN-CODE-RUN-VERIFY-DOC 五阶状态机，描述统计 / 回归 / 生存 / 中介 / Meta |
| | `publication-figures` | 发表级图件规范（mm 尺寸 / 字体嵌入 / 期刊配色）+ 约 180 种图选型画廊 + 170 余套配方代码 |
| 产出层 | `academic-publishing` | 中英双语论文生成（GB/T 7713 / IMRaD）+ 投稿材料（Cover Letter / 审稿回复 / Highlights），逐部件门控写作 |
| | `consulting-delivery` | 咨询交付包标准：自包含、一键复现、空 session 实测、终检清单 |
| | `sysu-ppt` | 组会汇报 PPT 代码化生成（R officer，含可复用模板与工具库） |
| 质控层 | `humanizer-zh` | 中文文本去 AI 痕迹：grep 黑名单扫描 - 最小改写 - 复扫归零，困惑度 / 突发性双杠杆 |
| | `epi-project-audit` | 六层项目审查状态机：骨架 / 数据链 / 代码 / 结果一致性 / 科学合理性 / 交付一致性，带数字一致性矩阵 |
| 工具层 | `docx` `pdf` `pptx` `xlsx` `skill-creator` `git-commit-helper` | 文档处理与技能维护（前五个源自 Anthropic 官方技能库，保留各自 LICENSE） |

## 安装

把本仓库内容放入 Claude Code 的用户配置目录：

```bash
# Windows
git clone git@github.com:KangWang42/EpiClaude.git "%USERPROFILE%\.claude-epiclaude"
copy "%USERPROFILE%\.claude-epiclaude\CLAUDE.md" "%USERPROFILE%\.claude\CLAUDE.md"
xcopy /E /I "%USERPROFILE%\.claude-epiclaude\skills" "%USERPROFILE%\.claude\skills"

# macOS / Linux
git clone git@github.com:KangWang42/EpiClaude.git ~/.claude-epiclaude
cp ~/.claude-epiclaude/CLAUDE.md ~/.claude/CLAUDE.md
cp -r ~/.claude-epiclaude/skills ~/.claude/skills
```

也可只挑选需要的单个技能目录复制到 `~/.claude/skills/`。各技能自包含（`SKILL.md` + `references/` + `scripts/` + `assets/`），互相之间只有声明式的上下游依赖。

注意：`sysu-ppt` 的字体与部分路径按 Windows 编写（`USERPROFILE` 环境变量、`C:/Windows/Fonts`），macOS / Linux 使用需按 `SKILL.md` 内注释调整。

## 推荐 Hook 配置（可选，把硬红线交给 harness 强制）

规则靠模型自觉遵守；其中五条可机械化的，建议用 Claude Code hook **强制执行**（比"提醒模型"可靠一个量级）。脚本在仓库 `hooks/`，把它复制到 `~/.claude/hooks/`，再把下面片段并入你自己的 `~/.claude/settings.json`（个人配置，本仓库**不含** settings.json），然后开一次 `/hooks` 或重启 Claude Code 生效。

- `protect_rawdata.sh`（PreToolUse）：拦截对 `01_data/rawdata/` 原始数据的写改，直接 deny。
- `check_r_syntax.sh`（PostToolUse）：`.R` 文件存盘即 `parse()` 语法检查，出错当场反馈给模型修。
- `scan_ai_trace.sh`（PostToolUse）：扫文本里 emoji 与 AI 痕迹字样（AI辅助 / 机辅 / 待人工复核…）；放过 `✅`（BACKLOG 状态标记），跳过 `.claude/` 自身。
- `fig_selfcheck.sh`（PostToolUse / Bash）：检测 `04_figures/` 新生成或修改的图，注入 `publication-figures §12ter` 逐元素自检清单（图例不遮数据 / 比例 / 裁切 / 数值溯源 / 风格一致），逼模型 Read 图逐条判。hook 只负责"逮事件 + 强制自检"，视觉判断仍由主模型完成。
- `check_results_rds.sh`（PostToolUse / Bash）：检测 `06_results/` 新写入的 `.rds`，提醒"表格化数据应存 `.xlsx`，`.rds` 仅限模型/ggplot/MCA 等非表格对象"。

（"多行 `Rscript -e` 会 segfault、须写成 `.R` 文件运行"这条已直接写进 `CLAUDE.md` 的代码必跑红线，常驻每会话上下文，无需单设 hook。）

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Write|Edit|MultiEdit", "hooks": [
        { "type": "command", "command": "bash ~/.claude/hooks/protect_rawdata.sh", "timeout": 15 } ] }
    ],
    "PostToolUse": [
      { "matcher": "Write|Edit|MultiEdit", "hooks": [
        { "type": "command", "command": "bash ~/.claude/hooks/check_r_syntax.sh", "timeout": 30 },
        { "type": "command", "command": "bash ~/.claude/hooks/scan_ai_trace.sh", "timeout": 15 } ] },
      { "matcher": "Bash", "hooks": [
        { "type": "command", "command": "bash ~/.claude/hooks/fig_selfcheck.sh", "timeout": 20 },
        { "type": "command", "command": "bash ~/.claude/hooks/check_results_rds.sh", "timeout": 15 } ] }
    ]
  }
}
```

每个 hook 都先做轻量判断、**只在命中各自触发条件时才动作**（非目标文件类型、无 `04_figures/` / `06_results/` 目录等即刻零成本退出），平时不干扰。需 Git Bash（Windows）或 bash（macOS/Linux）；无 `jq` 也可用（脚本用环境变量 + python 兜底解析 stdin）。让 AI 据本仓库安装时，可一并据此节自动配好这几道闸。

## 设计原则

本仓库的写法遵循几条经验规则，也是它区别于"把所有规范堆进 CLAUDE.md"的地方：

1. **删除测试**：CLAUDE.md 每条规则都要回答"删了 Claude 会犯什么具体错误"，答不出就删。全文控制在 120 行内——指令越多，单条遵循率越低。
2. **规则与流程分离**：CLAUDE.md 只放每个 session 都需要的硬红线与路由表；多步骤工作流全部下沉到技能，按需加载不占上下文。
3. **渐进披露**：技能正文只放核心流程与门禁，模板、句式库、配方代码放 `references/`，由模型在需要时自行读取。
4. **单一真源**：表图编号走 registry（编号 = 清单位置，脚本经 `table_path()` / `fig_path()` 取路径）；口径常量集中 `config.R` + `conventions.R`；论文数字机器单源 `07_paper/results.yaml`（脚本渲染一次写入、`render_summary_md()` 派生 `0_result_summaries.md`、下游 `val()` 取数禁手敲）。
5. **门禁状态机**：分析（PLAN-CODE-RUN-VERIFY-DOC）、写作（逐部件自检）、交付（八阶段）、审查（六层）都是"不过检不许进下一步"的状态机，而非建议清单。
6. **强制实跑与全量扫错**：代码写完必须实际执行，输出全量 grep error / warning，每条报错三选一去向（修复 / 记录豁免 / 核实可忽略），不允许沉默放过。

## 目录约定

技能围绕一套七层项目结构工作（由 `project-init` 创建）：

```
01_data/rawdata/   只读原始数据
02_code/           编号脚本（连续编号，<= 10 个，一脚本一阶段）
03_tables/         Table{N}_*.xlsx（附表进 supplementary/）
04_figures/        Fig{N}_*.{pdf,png}
05_reports/        对外交付包
06_results/        中间对象（按内容命名不编号）
07_paper/          论文 + results.yaml（数字机器单源）+ 0_result_summaries.md（由其派生）
09_backup/         旧版 / 一次性脚本 / 探索实验
```

## 适用范围与使用须知

- **面向流行病学 / 卫生统计，但不限于此**：规则与技能以流行病学、临床与真实世界数据研究为蓝本编写，其底层做法（项目分层、单一真源、门禁状态机、发表级图表、去 AI 味写作）是通用的研究工程实践。其他定量研究领域（基础医学、社会科学、生态、经济计量等）可直接参考，并按本领域的口径、报告规范与文献格式自行拓展、改写技能内容。
- **项目处理流程为个人经验，按需取舍**：七层目录、脚本编号、表图 registry、交付包形态等约定，是作者在自身研究与咨询中沉淀的个人偏好，并非领域标准或唯一正确做法。认同则用，不认同的条目可直接删改，介意者请勿套用。
- **AI 改动框架的权限较大，使用前请知情**：CLAUDE.md 授予 Claude 较大的自主整理权限——它会按规则移动 / 归档 / 重排文件、改写脚本输出路径、归并代码、调整表图编号等。这能省去大量手工整理，但也意味着会主动改动你的项目结构。建议在版本控制（git）下使用，重要数据先备份；原始数据目录 `01_data/rawdata/` 被设为只读红线，但其余目录的整理动作请在了解上述行为后再启用。

## 说明

- `docx` / `pdf` / `pptx` / `xlsx` / `skill-creator` 来自 [anthropics/skills](https://github.com/anthropics/skills)，各目录内保留原始 LICENSE；本仓库对 `skill-creator` 做了 Windows 中文环境的编码修复。
- `sysu-ppt` 内置的两套 PPT 模板版权归中山大学所有，仅供学习参考；如有顾虑请删除 `skills/sysu-ppt/assets/` 后使用自己的模板。
- 中文技能（原则 / 分析 / 论文 / 交付 / 审查 / 去 AI 味）为本仓库原创，针对中文学术写作与中文期刊投稿场景做了大量特化。
