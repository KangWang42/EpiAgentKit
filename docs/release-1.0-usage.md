# EpiAgentKit release 1.0 使用说明

本压缩包提供 17 个可安装到 Claude Code 或 Codex 的流行病学与生物统计 skills，以及两端共用的 `CLAUDE.md`。它不包含运行时、统计软件、用户配置、凭据、研究数据或机构模板。

## 一、推荐交给当前 Agent 安装

通常不需要自己解压后逐个复制文件。把 release 页面或已经下载的 ZIP 路径告诉当前使用的 Agent 即可。

在 Claude Code 中发送：

```text
请把这个 EpiAgentKit release 安装到当前 Claude Code：https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.0。保留我现有的个人配置，安装完成后检查 skills 是否可用。
```

在 Codex 中发送：

```text
请把这个 EpiAgentKit release 安装到当前 Codex：https://github.com/KangWang42/EpiAgentKit/releases/tag/v1.0。保留我现有的个人配置，安装完成后检查 skills 是否可用。
```

如果 ZIP 已经下载，把提示词中的 release 地址替换为本地 ZIP 路径。默认只安装到当前客户端；只有明确需要时才要求同时处理 Claude Code 与 Codex。下载、解压、备份、安装位置和完成检查由 Agent 按包内说明处理。

## 二、解压位置

把 release 解压到普通、版本化目录，例如：

```text
D:\tools\EpiAgentKit\1.0\EpiAgentKit-release-1.0\
```

不要把解压目录直接当作 `~/.claude`、`~/.codex` 或 `~/.agents`，也不要在运行目录中继续开发。源仓库、release 和实际安装目录应彼此分开。

<details>
<summary><strong>Agent 无法代为安装时的人工备用命令</strong></summary>

### 安装到 Claude Code

以下命令只用于 Agent 无法代为执行、需要人工审计具体文件操作或恢复自动安装失败的场景。Claude Code 读取 `~/.claude/CLAUDE.md` 和 `~/.claude/skills/`；命令先备份本次会覆盖的文件，再按清单安装：

```powershell
$releaseRoot = (Resolve-Path ".\EpiAgentKit-release-1.0").Path
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
$releaseRoot = (Resolve-Path ".\EpiAgentKit-release-1.0").Path
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

回退时先关闭 Claude Code 和 Codex 会话，确认要恢复的备份批次，再删除该批次所对应的 17 个当前 skill 目录，并把备份目录中的同名文件和 skill 复制回原位置。若备份中不存在某个 skill，表示安装前没有该目录，回退时不应凭空补建。

## 四、本版未提供的能力

- `docx`、`pdf`、`pptx`、`xlsx` 未随包分发。实际操作 Word、PDF、PowerPoint 或 Excel 时，使用平台已经提供且使用者有权使用的文件处理能力。
- `sysu-ppt` 未随包分发。需要中山大学或其他机构模板时，由使用者在本地配置其有权使用的模板。
- `research-visuals` 可以调用平台提供的 `imagegen`，本包不复制系统 imagegen skill，也不包含图像生成服务。
- 本包不安装 R、Python、Node、Java、LibreOffice、TeX、Git 或统计分析包。运行环境和项目依赖仍按项目隔离规则处理。

本仓库当前没有覆盖全部自有内容的统一公开许可证。本文件说明本地安装与回退方法，不构成公开再分发授权；公开发布前应由权利人另行确认许可范围。
