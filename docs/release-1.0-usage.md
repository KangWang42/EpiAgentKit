# EpiAgentKit release 1.0 使用说明

本压缩包提供 17 个可直接复制到 Claude Code 或 Codex 的流行病学与生物统计 skills，以及两端共用的 `CLAUDE.md`。它不包含运行时、统计软件、用户配置、凭据、研究数据或机构模板。

## 一、先核对压缩包

压缩包外侧的 `.zip.sha256` 保存整个 ZIP 的 SHA-256。解压后，包内 `SHA256SUMS` 保存除自身以外每个文件的 SHA-256；`SOURCE_COMMIT` 记录生成该包的源提交，`SKILLS_INCLUDED.txt` 列出本版包含的 skills。

Windows PowerShell 可核对 ZIP：

```powershell
$zip = Resolve-Path ".\EpiAgentKit-release-1.0.zip"
Get-FileHash -Algorithm SHA256 -LiteralPath $zip
Get-Content -LiteralPath "$zip.sha256" -Encoding utf8
```

两处哈希应一致。哈希不一致时不要安装，重新取得压缩包。

## 二、解压位置

把 release 解压到普通、版本化目录，例如：

```text
D:\tools\EpiAgentKit\1.0\EpiAgentKit-release-1.0\
```

不要把解压目录直接当作 `~/.claude`、`~/.codex` 或 `~/.agents`，也不要在运行目录中继续开发。源仓库、release 和实际安装目录应彼此分开。

## 三、安装到 Claude Code

Claude Code 读取 `~/.claude/CLAUDE.md` 和 `~/.claude/skills/`。以下 PowerShell 命令先备份本次会覆盖的文件，再按清单安装：

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

## 四、安装到 Codex

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

需要双端安装时，依次执行第三、四节。复制前应先关闭正在修改这些配置文件的编辑器或 Agent 会话，安装完成后新开会话验证 skill 是否可见。

## 五、更新与回退

更新时把新 release 解压到新的版本目录，核对哈希，再按上面的安装流程备份并替换清单内的 skills。不要覆盖旧的解压目录；旧 release 与安装前备份共同用于回退。

回退时先关闭 Claude Code 和 Codex 会话，确认要恢复的备份批次，再删除该批次所对应的 17 个当前 skill 目录，并把备份目录中的同名文件和 skill 复制回原位置。若备份中不存在某个 skill，表示安装前没有该目录，回退时不应凭空补建。

## 六、本版未提供的能力

- `docx`、`pdf`、`pptx`、`xlsx` 未随包分发。实际操作 Word、PDF、PowerPoint 或 Excel 时，使用平台已经提供且使用者有权使用的文件处理能力。
- `sysu-ppt` 未随包分发。需要中山大学或其他机构模板时，由使用者在本地配置其有权使用的模板。
- `research-visuals` 可以调用平台提供的 `imagegen`，本包不复制系统 imagegen skill，也不包含图像生成服务。
- 本包不安装 R、Python、Node、Java、LibreOffice、TeX、Git 或统计分析包。运行环境和项目依赖仍按项目隔离规则处理。

本仓库当前没有覆盖全部自有内容的统一公开许可证。本文件说明本地安装与回退方法，不构成公开再分发授权；公开发布前应由权利人另行确认许可范围。
