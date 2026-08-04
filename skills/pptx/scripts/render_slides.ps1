[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [ValidateRange(320, 7680)]
    [int]$Width = 1280,

    [ValidateRange(180, 4320)]
    [int]$Height = 720
)

$ErrorActionPreference = "Stop"

$inputFile = (Resolve-Path -LiteralPath $InputPath).Path
if ([System.IO.Path]::GetExtension($inputFile).ToLowerInvariant() -ne ".pptx") {
    throw "InputPath must point to a .pptx file: $inputFile"
}

if ([System.IO.Path]::IsPathRooted($OutputDir)) {
    $outputPath = [System.IO.Path]::GetFullPath($OutputDir)
} else {
    $outputPath = [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutputDir))
}

if (Test-Path -LiteralPath $outputPath) {
    $existing = Get-ChildItem -LiteralPath $outputPath -Force
    if ($existing.Count -gt 0) {
        throw "OutputDir must be absent or empty to prevent overwriting or mixing stale renders: $outputPath"
    }
} else {
    New-Item -ItemType Directory -Path $outputPath | Out-Null
}

$runningPowerPoint = Get-Process -Name POWERPNT -ErrorAction SilentlyContinue
if ($null -ne $runningPowerPoint) {
    throw "Microsoft PowerPoint is already running. Close it before rendering so this script cannot affect presentations already open by the user."
}

$powerPoint = $null
$presentation = $null
$slideCount = 0

try {
    try {
        $powerPoint = New-Object -ComObject PowerPoint.Application
    } catch {
        throw "Microsoft PowerPoint COM could not be started. Confirm that PowerPoint is installed or use another renderer already available on this machine. Original error: $($_.Exception.Message)"
    }

    $presentation = $powerPoint.Presentations.Open($inputFile, $true, $false, $false)
    $slideCount = $presentation.Slides.Count
    if ($slideCount -lt 1) {
        throw "The PPTX contains no renderable slides: $inputFile"
    }
    $presentation.Export($outputPath, "PNG", $Width, $Height)
} finally {
    if ($null -ne $presentation) {
        try { $presentation.Close() } catch {}
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($presentation) | Out-Null
    }
    if ($null -ne $powerPoint) {
        try { $powerPoint.Quit() } catch {}
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$rendered = @(Get-ChildItem -LiteralPath $outputPath -File -Filter *.png)
if ($rendered.Count -ne $slideCount) {
    throw "PowerPoint exported an unexpected number of slides: source=$slideCount, rendered=$($rendered.Count)."
}

Write-Output "Rendered $slideCount slide(s) to $outputPath"
