param([string]$Archive)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$destination = Join-Path $repoRoot 'vendor\ffmpeg'
$expected = @{
    'ffmpeg.exe' = '3256173F3F8BFFD7DF12227C68ADF68025EDB1832273A9530688A7BB1ED8EDEC'
    'ffprobe.exe' = 'F0D36ECBBDD3BCFAC3EFA078C96C7271C2E68B3810595552AC3B7F17E9A65C52'
}
$complete = $true
foreach ($name in $expected.Keys) {
    $file = Join-Path $destination $name
    if (-not (Test-Path -LiteralPath $file)) { $complete = $false }
    elseif ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $expected[$name]) {
        $complete = $false
    }
}
if ($complete -and (Test-Path -LiteralPath (Join-Path $destination 'LICENSE'))) {
    Write-Output 'FFmpeg 9.0.2 is ready (SHA256 verified).'
    exit 0
}
$work = Join-Path $repoRoot ('.tools\ffmpeg-setup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work -Force | Out-Null
if (-not $Archive) {
    $Archive = Join-Path $work 'ffmpeg.zip'
    $uri = 'https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-9.0.2-essentials_build.zip'
    Invoke-WebRequest -Uri $uri -OutFile $Archive -UseBasicParsing
}
$zipHash = '60F467265B1E312373DBCD92200C2618A74850F98D3D078E94296BB3FA2047BA'
if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ne $zipHash) {
    throw 'Unexpected FFmpeg archive SHA256. No executable was installed.'
}
Expand-Archive -LiteralPath $Archive -DestinationPath $work
$bundle = Join-Path $work 'ffmpeg-9.0.2-essentials_build'
foreach ($name in $expected.Keys) {
    $source = Join-Path $bundle ('bin\' + $name)
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $expected[$name]) {
        throw "Unexpected SHA256 for $name"
    }
}
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($name in $expected.Keys) {
    Copy-Item -LiteralPath (Join-Path $bundle ('bin\' + $name)) -Destination $destination
}
Copy-Item -LiteralPath (Join-Path $bundle 'LICENSE') -Destination $destination
Write-Output 'FFmpeg 9.0.2 installed and verified.'
