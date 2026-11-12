param(
 [string]$OutputName,
 [ValidateSet('x64','arm64')][string]$Architecture='x64'
)
if (-not $OutputName) {
 $OutputName=if($Architecture-eq'arm64'){'DNA_Launcher_ARM64.exe'}else{'DNA_Launcher.exe'}
}
$ErrorActionPreference='Stop'
$taskRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Add-Type -AssemblyName System.Drawing
$taskBitmap=New-Object Drawing.Bitmap(64,64)
$taskGraphics=[Drawing.Graphics]::FromImage($taskBitmap)
$taskGraphics.SmoothingMode=[Drawing.Drawing2D.SmoothingMode]::AntiAlias
$taskGraphics.Clear([Drawing.Color]::FromArgb(20,34,51))
$taskPen=New-Object Drawing.Pen([Drawing.Color]::FromArgb(25,205,182),4)
$taskOther=New-Object Drawing.Pen([Drawing.Color]::White,4)
$taskGraphics.DrawBezier($taskPen,20,8,62,22,2,42,44,56)
$taskGraphics.DrawBezier($taskOther,44,8,2,22,62,42,20,56)
foreach($taskY in @(14,24,34,44,52)){$taskGraphics.DrawLine($taskPen,24,$taskY,40,$taskY)}
$taskIcon=[Drawing.Icon]::FromHandle($taskBitmap.GetHicon())
$taskStream=[IO.File]::Create((Join-Path $PSScriptRoot 'dna.ico'))
$taskIcon.Save($taskStream);$taskStream.Close();$taskGraphics.Dispose();$taskBitmap.Dispose()
$taskCompiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
$taskPythonPath=$null;$taskPythonDir=Join-Path $taskRoot 'DNA_Software/Windows/Python'
if(Test-Path $taskPythonDir){$taskPythonPath=Get-ChildItem -LiteralPath $taskPythonDir -Filter python.exe -Recurse|Where-Object FullName -NotMatch '\\venv\\'|Select-Object -First 1 -ExpandProperty FullName}
if(-not$taskPythonPath){$taskPythonCommand=Get-Command python.exe -ErrorAction SilentlyContinue;if($taskPythonCommand){$taskPythonPath=$taskPythonCommand.Source}}
if(-not$taskPythonPath){throw "Python is needed for building."}
if ($Architecture -eq 'arm64') {
 $armSdk=Join-Path $PSScriptRoot 'WebView2-arm64/WebView2Loader.dll'
 if (-not (Test-Path -LiteralPath $armSdk)) {
  & $taskPythonPath (Join-Path $PSScriptRoot 'fetch_webview_sdk.py') --arch arm64
  if ($LASTEXITCODE -ne 0) { throw "The ARM64 WebView2 SDK could not load." }
 }
 & $taskPythonPath (Join-Path $PSScriptRoot 'public_package.py') --payload --arch arm64
 if ($LASTEXITCODE -ne 0) { throw "The ARM64 core payload could not be built." }
 $armOutput=Join-Path $PSScriptRoot 'bin/arm64-publish'
 & dotnet build (Join-Path $PSScriptRoot 'DNAWorkbench.csproj') --configuration Release --output $armOutput -p:DnaArchitecture=arm64
 if ($LASTEXITCODE -ne 0) { throw "The ARM64 launcher could not be compiled." }
 Copy-Item -LiteralPath (Join-Path $armOutput 'DNAWorkbench.exe') -Destination (Join-Path $taskRoot $OutputName) -Force
 $armConfig=Join-Path $armOutput 'DNAWorkbench.exe.config'
 if (Test-Path -LiteralPath $armConfig) {
  Copy-Item -LiteralPath $armConfig -Destination (Join-Path $taskRoot ($OutputName+'.config')) -Force
 }
 Write-Output ($OutputName + ' built.')
 return
}
if(-not(Test-Path (Join-Path $PSScriptRoot 'WebView2/Microsoft.Web.WebView2.Core.dll'))){& $taskPythonPath (Join-Path $PSScriptRoot 'fetch_webview_sdk.py');if($LASTEXITCODE-ne 0){throw "WebView2 SDK could not load."}}
& $taskPythonPath (Join-Path $PSScriptRoot 'public_package.py') --payload
if($LASTEXITCODE-ne 0){throw "The core package could not be built."}
foreach($taskDll in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll')){$taskInput=Join-Path $PSScriptRoot ('WebView2\'+$taskDll);$taskOutput=Join-Path $taskRoot $taskDll;if(-not(Test-Path $taskOutput)-or(Get-FileHash $taskInput).Hash-ne(Get-FileHash $taskOutput).Hash){Copy-Item -LiteralPath $taskInput -Destination $taskOutput -Force}}
& $taskCompiler /nologo /codepage:65001 /target:winexe /optimize+ /platform:x64 ('/out:'+(Join-Path $taskRoot $OutputName)) ('/win32manifest:'+(Join-Path $PSScriptRoot 'app.manifest')) ('/win32icon:'+(Join-Path $PSScriptRoot 'dna.ico')) ('/resource:'+(Join-Path $PSScriptRoot 'core-payload.zip')+',DNA.Core.zip') /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll /reference:System.Core.dll /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll ('/reference:'+(Join-Path $taskRoot 'Microsoft.Web.WebView2.Core.dll')) ('/reference:'+(Join-Path $taskRoot 'Microsoft.Web.WebView2.WinForms.dll')) (Join-Path $PSScriptRoot 'Launcher.cs') (Join-Path $PSScriptRoot 'Startup.cs') (Join-Path $PSScriptRoot 'LegacyLayout.cs') (Join-Path $PSScriptRoot 'Dependencies.cs') (Join-Path $PSScriptRoot 'OnDemand.cs') (Join-Path $PSScriptRoot 'VisualTools.cs') (Join-Path $PSScriptRoot 'ModernShell.cs')
if($LASTEXITCODE -ne 0){throw "Launcher could not be compiled."}
Write-Output 'DNA_Launcher.exe built.'
