$ErrorActionPreference = "Stop"
$key = "HKCU:\Control Panel\Cursors"
Set-ItemProperty -Path $key -Name "IBeam" -Value "%SystemRoot%\cursors\beam_r.cur"
Set-ItemProperty -Path $key -Name "(default)" -Value "Windows 默认" -ErrorAction SilentlyContinue
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class CurR {
  [DllImport("user32.dll", SetLastError=true)]
  public static extern bool SystemParametersInfo(uint a, uint b, IntPtr c, uint d);
}
"@
[void][CurR]::SystemParametersInfo(0x0057, 0, [IntPtr]::Zero, 0x0001 -bor 0x0002)
"restored -> beam_r.cur"
