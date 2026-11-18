param(
  [string]$KeyPath = "HKCU:\Control Panel\Cursors",
  [switch]$NoApply,
  [switch]$Quiet
)
$ErrorActionPreference = "Stop"
$names = @("Arrow","Help","AppStarting","Wait","Crosshair","IBeam","NWPen","No","Hand")
if (-not $Quiet) {
  Write-Host ""
  Write-Host "  Si . Ink Brush  cursor set  ->  restore Windows default" -ForegroundColor Cyan
  Write-Host ""
}
if (-not (Test-Path $KeyPath)) { New-Item -Path $KeyPath -Force | Out-Null }
foreach ($n in $names) { try { Set-ItemProperty -Path $KeyPath -Name $n -Value "" } catch { } }
try { Set-ItemProperty -Path $KeyPath -Name "(default)" -Value "Windows default" } catch { }
if (-not $NoApply) {
  Add-Type -Namespace SiCursor -Name Native -MemberDefinition '[DllImport("user32.dll")] public static extern bool SystemParametersInfo(uint a, uint b, System.IntPtr c, uint d);'
  [void][SiCursor.Native]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 0)
}
if (-not $Quiet) {
  Write-Host "  restored." -ForegroundColor Green
  Read-Host "press enter to close"
}
