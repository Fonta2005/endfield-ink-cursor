$ErrorActionPreference = "Stop"
$src = "D:\deepseek\out\scroll-assets\ScrollText.cur"
$dir = Join-Path $env:LOCALAPPDATA "Cursors"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$dst = Join-Path $dir "ScrollText.cur"
Copy-Item -LiteralPath $src -Destination $dst -Force

$key = "HKCU:\Control Panel\Cursors"
if (-not (Test-Path $key)) { New-Item -Path $key -Force | Out-Null }
Set-ItemProperty -Path $key -Name "IBeam" -Value $dst
Set-ItemProperty -Path $key -Name "(default)" -Value "ScrollText" -ErrorAction SilentlyContinue

Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Cur {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool SystemParametersInfo(uint a, uint b, IntPtr c, uint d);
}
"@
[void][Cur]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 0x0001 -bor 0x0002)

"installed -> $dst"
"reg IBeam = " + (Get-ItemProperty -Path $key -Name IBeam).IBeam
"exists = " + (Test-Path $dst) + " size = " + (Get-Item $dst).Length
