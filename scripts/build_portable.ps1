param(
    [string]$Python = (Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'),
    [switch]$SkipChecks
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$buildOutput = [IO.Path]::GetFullPath((Join-Path $repoRoot 'dist\portable'))
if (-not $buildOutput.StartsWith($repoRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Build output must stay inside the repository.'
}
$Python = (Resolve-Path -LiteralPath $Python).Path
$previousMode = $env:SYNCVIEW_BUILD_MODE
Push-Location -LiteralPath $repoRoot
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/setup_ffmpeg.ps1
    if ($LASTEXITCODE -ne 0) { throw 'FFmpeg preparation failed.' }
    if (-not $SkipChecks) {
        & $Python -m pytest -q
        if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
        & $Python -m ruff check .
        if ($LASTEXITCODE -ne 0) { throw 'Lint failed.' }
        & $Python -m ruff format --check .
        if ($LASTEXITCODE -ne 0) { throw 'Formatting checks failed.' }
    }
    $env:SYNCVIEW_BUILD_MODE = 'onedir'
    & $Python -m PyInstaller --noconfirm --distpath $buildOutput --workpath build/portable VideoMultiView.spec
    if ($LASTEXITCODE -ne 0) { throw 'Portable build failed.' }
    & $Python scripts/package_portable.py
    if ($LASTEXITCODE -ne 0) { throw 'Portable packaging failed.' }
}
finally {
    $env:SYNCVIEW_BUILD_MODE = $previousMode
    Pop-Location
}
