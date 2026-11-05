param([Parameter(Mandatory=$true)][string]$RuntimeRoot)
$ErrorActionPreference='Stop'
$checkoutRoot=Split-Path -Parent $PSScriptRoot
$destination=[IO.Path]::GetFullPath($RuntimeRoot)
if(-not(Test-Path -LiteralPath (Join-Path $destination 'DNA_Launcher.exe'))){throw 'Choose an existing DNA Workbench runtime folder.'}
if($destination.TrimEnd('\') -eq $checkoutRoot.TrimEnd('\')){throw 'Runtime and source checkout must be separate for this deployment command.'}
$target=Join-Path $destination 'DNA_Launcher.exe'
$running=Get-CimInstance Win32_Process -Filter "Name='DNA_Launcher.exe'" | Where-Object {$_.ExecutablePath -eq $target}
if($running){throw 'Close the runtime launcher before deployment.'}
& (Join-Path $checkoutRoot 'DNA_Software/Launcher/build.ps1')
if($LASTEXITCODE -ne 0){throw 'Build failed; existing installation was not changed.'}
$backupDir=Join-Path $destination 'DNA_Software/UserData/Launcher/Backups'
$layout=Get-Content -LiteralPath (Join-Path $checkoutRoot 'DNA_Software/Launcher/legacy-layout.json') -Raw | ConvertFrom-Json
foreach($entry in $layout.directories.PSObject.Properties){
    if($entry.Value -eq 'UserData'){
        $legacyData=Join-Path $destination ('DNA_Software/'+$entry.Name)
        if(Test-Path -LiteralPath $legacyData){$backupDir=Join-Path $legacyData 'Launcher/Backups'}
    }
}
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
Copy-Item -LiteralPath $target -Destination (Join-Path $backupDir ('DNA_Launcher-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.exe'))
Copy-Item -LiteralPath (Join-Path $checkoutRoot 'DNA_Launcher.exe') -Destination $target -Force
Write-Output "Deployed EXE to $target. Restart it to install the embedded source payload. Personal data was not copied."
