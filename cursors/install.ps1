param(
  [string]$KeyPath = "HKCU:\Control Panel\Cursors",
  [switch]$Static,
  [switch]$NoApply,
  [switch]$Quiet
)
$ErrorActionPreference = "Stop"
$dir = $PSScriptRoot
$arrow = if ($Static) { "NormalSelect.cur" } else { "NormalSelect.ani" }
$map = [ordered]@{
  "Arrow"       = $arrow
  "Help"        = "HelpSelect.cur"
  "AppStarting" = "WorkinginBackground.ani"
  "Wait"        = "Busy.ani"
  "Crosshair"   = "PrecisionSelect.cur"
  "IBeam"       = "TextSelect.cur"
  "NWPen"       = "Handwriting.cur"
  "No"          = "Unavailable.cur"
  "Hand"        = "LinkSelect.cur"
}
if (-not $Quiet) {
  Write-Host ""
  Write-Host "  Si . Ink Brush  cursor set" -ForegroundColor Cyan
  Write-Host "  dir : $dir"
  Write-Host "  arrow: $arrow"
  Write-Host ""
}
$missing = @()
foreach ($k in $map.Keys) { if (-not (Test-Path (Join-Path $dir $map[$k]))) { $missing += $map[$k] } }
if ($missing.Count -gt 0) {
  Write-Host ("  missing: " + ($missing -join ", ")) -ForegroundColor Red
  if (-not $Quiet) { Read-Host "press enter to exit" }
  exit 1
}
if (-not (Test-Path $KeyPath)) { New-Item -Path $KeyPath -Force | Out-Null }
foreach ($k in $map.Keys) {
  Set-ItemProperty -Path $KeyPath -Name $k -Value (Join-Path $dir $map[$k])
  if (-not $Quiet) { Write-Host ("    {0,-11} <- {1}" -f $k, $map[$k]) }
}
try { Set-ItemProperty -Path $KeyPath -Name "(default)" -Value "Si Ink Brush" } catch { }
if (-not $NoApply) {
  Add-Type -Namespace SiCursor -Name Native -MemberDefinition '[DllImport("user32.dll")] public static extern bool SystemParametersInfo(uint a, uint b, System.IntPtr c, uint d);'
  [void][SiCursor.Native]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 0)
}
if (-not $Quiet) {
  Write-Host ""
  Write-Host "  installed." -ForegroundColor Green
  Read-Host "press enter to close"
}
