$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $env:LOCALAPPDATA "InsaneSearch"
$CodexPlugin = Join-Path $HOME ".codex\plugins\insane-search"
$RuntimeTarget = Join-Path $Target "runtime"
$SkillTarget = Join-Path $CodexPlugin "skills\insane-search"

New-Item -ItemType Directory -Force -Path $Target, $CodexPlugin | Out-Null
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $RuntimeTarget, $SkillTarget
New-Item -ItemType Directory -Force -Path $RuntimeTarget, (Split-Path -Parent $SkillTarget) | Out-Null
Copy-Item -Recurse -Force (Join-Path $Here "runtime\*") $RuntimeTarget
Copy-Item -Recurse -Force (Join-Path $Here "skill\insane-search") $SkillTarget
Copy-Item -Force (Join-Path $Here "plugin.json") (Join-Path $CodexPlugin "plugin.json")
Copy-Item -Force (Join-Path $Here "skill.zip") (Join-Path $Target "skill.zip")

$Bin = Join-Path $RuntimeTarget "insane-search-mcp.exe"
if (-not (Test-Path $Bin)) {
  $Bin = (Get-ChildItem -Recurse -File $RuntimeTarget | Where-Object { $_.Name -eq "insane-search-mcp.exe" } | Select-Object -First 1).FullName
}
if (-not $Bin) { throw "insane-search-mcp.exe not found" }

$Mcp = @{
  mcpServers = @{
    insane_search = @{
      command = $Bin
      args = @("--transport", "stdio", "--profile", "auto")
    }
  }
} | ConvertTo-Json -Depth 6
Set-Content -Encoding UTF8 (Join-Path $CodexPlugin ".mcp.json") $Mcp

Write-Host "Installed MCP runtime: $Target"
Write-Host "Installed Codex plugin + Skill: $CodexPlugin"
Write-Host "ChatGPT Skill package: $(Join-Path $Target 'skill.zip')"

$Node = Get-Command node -ErrorAction SilentlyContinue
$Npm = Get-Command npm -ErrorAction SilentlyContinue
$ChromeCandidates = @()
foreach ($Base in @(${env:ProgramFiles}, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA)) {
  if ($Base) {
    $Candidate = Join-Path $Base "Google\Chrome\Application\chrome.exe"
    if (Test-Path $Candidate) { $ChromeCandidates += $Candidate }
  }
}
if ($Node -and $Npm -and $ChromeCandidates.Count -gt 0) {
  Write-Host "Browser escalation: available (Node.js + Chrome detected)"
} else {
  Write-Host "Browser escalation: optional dependencies not detected; HTTP/reader routes still work"
}
