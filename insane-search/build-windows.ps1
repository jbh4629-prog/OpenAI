$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not [Environment]::Is64BitOperatingSystem) {
  throw "Windows x64 is required for this release target."
}

$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  try {
    & py -3.12 -c "import sys; assert sys.version_info >= (3, 11)"
    if ($LASTEXITCODE -eq 0) { $Python = @("py", "-3.12") }
  } catch {}
}
if (-not $Python -and (Get-Command python -ErrorAction SilentlyContinue)) {
  & python -c "import sys; assert sys.version_info >= (3, 11)"
  if ($LASTEXITCODE -eq 0) { $Python = @("python") }
}
if (-not $Python) {
  throw "Python 3.11+ is required on the build machine. Install Python 3.12 x64, then rerun this script."
}

$Venv = Join-Path $Root ".build-venv"
if (Test-Path $Venv) { Remove-Item -Recurse -Force $Venv }

if ($Python.Count -eq 2) {
  & $Python[0] $Python[1] -m venv $Venv
} else {
  & $Python[0] -m venv $Venv
}
$Vpy = Join-Path $Venv "Scripts\python.exe"

& $Vpy -m pip install --upgrade pip
& $Vpy -m pip install -r requirements-build.txt
& $Vpy scripts\build_release.py --clean

$Exe = Join-Path $Root "dist\insane-search-windows-x64\runtime\insane-search-mcp.exe"
if (-not (Test-Path $Exe)) { throw "Build completed without expected executable: $Exe" }

$Requests = @(
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"windows-build-smoke","version":"1"}}}',
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"insane_search_capabilities","arguments":{}}}',
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"insane_search_fetch","arguments":{"url":"https://example.com/","content_max_chars":1200}}}'
)
$Smoke = ($Requests -join "`n") | & $Exe
if ($LASTEXITCODE -ne 0) { throw "Frozen MCP smoke test failed." }
if ($Smoke -notmatch '"serverInfo"' -or $Smoke -notmatch 'Example Domain') {
  throw "Frozen MCP smoke test returned unexpected output."
}

$Zip = Join-Path $Root "dist\insane-search-windows-x64.zip"
$Hash = (Get-FileHash -Algorithm SHA256 $Zip).Hash.ToLowerInvariant()
Set-Content -Encoding ASCII (Join-Path $Root "dist\insane-search-windows-x64.sha256") "$Hash  insane-search-windows-x64.zip"

Write-Host ""
Write-Host "PASS: Windows x64 MCP + Skill release built and smoke-tested."
Write-Host "ZIP:    $Zip"
Write-Host "SHA256: $Hash"
