$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$vtuberRoot = Join-Path $projectRoot "ai-vtuber-mvp"
$port = if ($env:PORT) { $env:PORT } else { "3000" }

if (-not (Test-Path -LiteralPath $vtuberRoot)) {
  throw "Cannot find ai-vtuber-mvp at $vtuberRoot"
}

Set-Location -LiteralPath $vtuberRoot

Write-Host "Dashboard: http://localhost:$port"
Write-Host "Linked city game: http://localhost:$port/game/"
Write-Host "Mika Brain v3 memory: $projectRoot\brain_core\data\mika_v3_memory.json"
Write-Host "Set `$env:PORT before running this script if port 3000 is already occupied."

$hasPnpm = [bool](Get-Command pnpm -ErrorAction SilentlyContinue)
$hasNodeModules = Test-Path -LiteralPath (Join-Path $vtuberRoot "node_modules")
$distEntry = Join-Path $vtuberRoot "dist\index.js"

if ($hasPnpm) {
  if (-not $hasNodeModules) {
    pnpm install
  }
  pnpm dev
  exit $LASTEXITCODE
}

if (-not $hasNodeModules) {
  throw "pnpm was not found and node_modules is missing. Install pnpm or run Corepack first."
}

if (-not (Test-Path -LiteralPath $distEntry)) {
  & ".\node_modules\.bin\tsc.cmd"
}

node $distEntry
