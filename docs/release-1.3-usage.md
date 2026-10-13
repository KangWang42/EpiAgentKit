# EpiAgentKit release 1.3 使用说明

本压缩包提供 22 个可安装到 Claude Code 或 Codex 的流行病学与生物统计 skills，以及两端共用的 `CLAUDE.md`。它不包含运行时、统计软件、用户配置、凭据、研究数据或机构模板。

本版改进学术 PPT 的场景分流：组会、文献分享、方法讲解、开题和答辩分别按汇报目的组织内容；已有 PPTX 的局部修改继续保留原模板和范围。新增可选的 SQLite 技能索引工具，先查询文件用途、标题和章节，再核对文件头并读取原文；索引随文件变更更新，不保存会话记忆或研究数据。

## 一、推荐交给当前 Agent 安装

通常不需要自己解压后逐个复制文件。把 release 页面或已经下载的 ZIP 路径告诉当前使用的 Agent 即可。

在 Claude Code 中发送：

```text
请把这个 EpiAgentKit release 安装到当前 Claude Code：https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.3。保留我现有的个人配置，安装完成后检查 skills 是否可用。
```

在 Codex 中发送：

```text
请把这个 EpiAgentKit release 安装到当前 Codex：https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.3。保留我现有的个人配置，安装完成后检查 skills 是否可用。
```

如果 ZIP 已经下载，把提示词中的 release 地址替换为本地 ZIP 路径。默认只安装到当前客户端；只有明确需要时才要求同时处理 Claude Code 与 Codex。下载、解压、备份、安装位置和完成检查由 Agent 按包内说明处理。

## 二、解压位置

把 release 解压到普通、版本化目录，例如：

```text
D:\tools\EpiAgentKit\1.3\EpiAgentKit-release-1.3\
```

不要把解压目录直接当作 `~/.claude`、`~/.codex` 或 `~/.agents`，也不要在运行目录中继续开发。源仓库、release 和实际安装目录应彼此分开。

<details>
<summary><strong>Agent 无法代为安装时的人工备用命令</strong></summary>

### 安装到 Claude Code

以下命令只用于 Agent 无法代为执行、需要人工审计具体文件操作或恢复自动安装失败的场景。Claude Code 读取 `~/.claude/CLAUDE.md` 和 `~/.claude/skills/`；命令先备份本次会覆盖的文件，再按清单安装：

```powershell
$releaseRoot = (Resolve-Path ".\EpiAgentKit-release-1.3").Path
$claudeRoot = Join-Path $env:USERPROFILE ".claude"
$backupRoot = Join-Path $env:USERPROFILE (".epiagentkit-backup\" + (Get-Date -Format "yyyyMMdd_HHmmss") + "\claude")
$skills = Get-Content -LiteralPath (Join-Path $releaseRoot "SKILLS_INCLUDED.txt") -Encoding utf8

New-Item -ItemType Directory -Force -Path $claudeRoot, (Join-Path $claudeRoot "skills"), $backupRoot | Out-Null
if (Test-Path -LiteralPath (Join-Path $claudeRoot "CLAUDE.md")) {
    Copy-Item -LiteralPath (Join-Path $claudeRoot "CLAUDE.md") -Destination $backupRoot
}
Copy-Item -LiteralPath (Join-Path $releaseRoot "CLAUDE.md") -Destination (Join-Path $claudeRoot "CLAUDE.md") -Force

foreach ($skill in $skills) {
    $source = Join-Path (Join-Path $releaseRoot "skills") $skill
    $target = Join-Path (Join-Path $claudeRoot "skills") $skill
    if (Test-Path -LiteralPath $target) {
        Copy-Item -LiteralPath $target -Destination $backupRoot -Recurse
        Remove-Item -LiteralPath $target -Recurse
    }
    Copy-Item -LiteralPath $source -Destination $target -Recurse
}
```

### 安装到 Codex

Codex 使用 `~/.codex/AGENTS.md` 作为全局规则，自定义 skills 默认位于 `~/.agents/skills/`。安装时把 release 的 `CLAUDE.md` 复制为 `AGENTS.md`：

```powershell
$releaseRoot = (Resolve-Path ".\EpiAgentKit-release-1.3").Path
$codexRoot = Join-Path $env:USERPROFILE ".codex"
$skillRoot = Join-Path $env:USERPROFILE ".agents\skills"
$backupRoot = Join-Path $env:USERPROFILE (".epiagentkit-backup\" + (Get-Date -Format "yyyyMMdd_HHmmss") + "\codex")
$skills = Get-Content -LiteralPath (Join-Path $releaseRoot "SKILLS_INCLUDED.txt") -Encoding utf8

New-Item -ItemType Directory -Force -Path $codexRoot, $skillRoot, $backupRoot | Out-Null
if (Test-Path -LiteralPath (Join-Path $codexRoot "AGENTS.md")) {
    Copy-Item -LiteralPath (Join-Path $codexRoot "AGENTS.md") -Destination $backupRoot
}
Copy-Item -LiteralPath (Join-Path $releaseRoot "CLAUDE.md") -Destination (Join-Path $codexRoot "AGENTS.md") -Force

foreach ($skill in $skills) {
    $source = Join-Path (Join-Path $releaseRoot "skills") $skill
    $target = Join-Path $skillRoot $skill
    if (Test-Path -LiteralPath $target) {
        Copy-Item -LiteralPath $target -Destination $backupRoot -Recurse
        Remove-Item -LiteralPath $target -Recurse
    }
    Copy-Item -LiteralPath $source -Destination $target -Recurse
}
```

需要双端安装时，依次执行两个平台的命令。复制前应先关闭正在修改这些配置文件的编辑器或 Agent 会话，安装完成后新开会话验证 skill 是否可见。

</details>

## 三、更新与回退

更新或回退也优先交给当前 Agent。可以发送：

```text
请把 EpiAgentKit 更新到我指定的 release，或恢复到我指定的安装前备份。保留其它个人配置，完成后检查 skills 是否可用。
```

更新时把新 release 解压到新的版本目录，再按上面的安装流程备份并替换清单内的 skills。不要覆盖旧的解压目录；旧 release 与安装前备份共同用于回退。

回退时先关闭 Claude Code 和 Codex 会话，确认要恢复的备份批次，再删除该批次所对应的 22 个当前 skill 目录，并把备份目录中的同名文件和 skill 复制回原位置。若备份中不存在某个 skill，表示安装前没有该目录，回退时不应凭空补建。

## 四、按任务查询技能细则

本包额外提供 `tools/knowledge_index.py`，无需安装维护技能。保持 release 解压目录可访问，在该目录执行：

```bash
python tools/knowledge_index.py search "缺失数据" --skill r-biostats
python tools/knowledge_index.py peek r-biostats/references/regression.md --lines 30
```

默认查询本包的 `skills/`。如要查安装后的当前库，使用 `python tools/knowledge_index.py --root <实际skills目录> search "检索词" --skill <技能名>`；`--root` 放在子命令之前。工具保留在解压目录即可，不复制进平台系统技能或用户配置目录。Agent 安装后说明工具的实际位置；规则中的 `tools/knowledge_index.py` 指该解压目录内的文件。

缓存自动生成在所查 skills 目录的上级 `.epiagentkit-cache/`，不随包分发。每次查询检查源文件变化，默认最多返回六项；`peek` 核对源文件哈希并显示真实文件头。缓存损坏可用 `build --rebuild` 重建。查询只覆盖技能入口、细则的描述和标题；无匹配时沿用文件链接或正文搜索。已知路径直接读取，不能用候选排序代替任务分流或跳过必读规范。

工具需要现有 Python 和其 sqlite3/FTS5 能力，不新增第三方依赖；缺少环境或写权限时直接使用原有文件检索。本机测试中简单关键词用 `rg` 更快，索引的用途是控制候选数量与上下文，不保证模型准确率或整个任务耗时改善。

## 五、本版未提供的能力

- `docx`、`pdf`、`pptx`、`xlsx` 未随包分发。实际操作 Word、PDF、PowerPoint 或 Excel 时，使用平台已经提供且使用者有权使用的文件处理能力。
- `academic-ppt` 已随包分发，但不携带机构模板。使用者可提供有权使用的学校、机构或会议模板，也可明确选择无模板中性设计。
- `sysu-ppt` 未随包分发，中山大学模板亦不在本 release 中。
- `research-visuals` 可以调用平台提供的 `imagegen`，本包不复制系统 imagegen skill，也不包含图像生成服务。
- 本包不安装 R、Python、Node、Java、LibreOffice、TeX、Git 或统计分析包。运行环境和项目依赖仍按项目隔离规则处理。

本仓库当前没有覆盖全部自有内容的统一公开许可证。本文件说明本地安装与回退方法，不构成公开再分发授权；公开发布前应由权利人另行确认许可范围。
