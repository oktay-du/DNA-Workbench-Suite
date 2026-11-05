param(
    [ValidateSet('Start','Docker','StopAll','Status','Gramps','GrampsWeb','Admixtools','Haplogrep','IGV','JBrowse','Jupyter','OpenCRAVAT','Linux','Stop','Export')]
    [string]$Action='Status'
)
$ErrorActionPreference='Stop'
$taskSsd=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

. (Join-Path $taskSsd 'DNA_Software/Launcher/Portable.ps1')
Initialize-DnaPortable $taskSsd
$taskMount=(Get-DnaLinuxRoot $taskSsd).TrimEnd('/')
$taskDistro=Get-DnaDistroName $taskSsd
$taskSoftware=Join-Path $taskSsd 'DNA_Software'
$taskUser=Join-Path $taskSoftware 'UserData'
New-Item -ItemType Directory -Path $taskUser -Force | Out-Null
$env:PYTHONNOUSERSITE='1'
$env:XDG_CACHE_HOME=Join-Path $taskUser 'Cache'
$env:TEMP=Join-Path $taskUser 'Temp'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
$taskPython=Get-ChildItem -LiteralPath (Join-Path $taskSoftware 'Windows/Python') -Filter python.exe -Recurse | Select-Object -First 1
$env:PYTHONPATH=Join-Path $taskSoftware 'Windows/PythonPackages'
$env:JUPYTER_CONFIG_DIR=Join-Path $taskUser 'Jupyter/config'
$env:JUPYTER_DATA_DIR=Join-Path $taskUser 'Jupyter/data'
$env:JUPYTER_RUNTIME_DIR=Join-Path $taskUser 'Jupyter/runtime'
$taskJava=Get-ChildItem -LiteralPath (Join-Path $taskSoftware 'Windows/Java21') -Filter java.exe -Recurse | Select-Object -First 1
if($taskJava){$env:JAVA_HOME=Split-Path -Parent (Split-Path -Parent $taskJava.FullName);$env:PATH=(Join-Path $env:JAVA_HOME 'bin')+';'+$env:PATH}
function Ensure-DnaWsl {
    & (Join-Path $taskSsd 'DNA_Software/Launcher/setup.ps1') -Root $taskSsd -Mode Linux -InstallWslHost
    if($LASTEXITCODE -ne 0){throw 'Portable Ubuntu-Einrichtung fehlgeschlagen. Siehe Setup-Protokoll.'}
    $script:taskDistro=Get-DnaDistroName $taskSsd
}
switch($Action){
    'Start' {
        Ensure-DnaWsl
        $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
        & wsl.exe -d $taskDistro -u dna -- true
        if($LASTEXITCODE -ne 0){throw 'Ubuntu konnte nicht gestartet werden.'}
        Write-Output 'Ubuntu DNA-SSD ist gestartet.'
    }
    'Docker' {
        Ensure-DnaWsl
        $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
        & wsl.exe -d $taskDistro -u root -- bash ($taskMount+'/DNA_Software/Start/docker-dna.sh')
        if($LASTEXITCODE -ne 0){throw 'Die angeforderte Containerlaufzeit ist nicht bereit.'}
    }
    'StopAll' {
        & $PSCommandPath -Action Stop
        & wsl.exe --shutdown
        if($LASTEXITCODE -ne 0){throw 'WSL konnte nicht vollstaendig beendet werden.'}
        Write-Output 'Alle WSL-Distributionen und die WSL-Auslagerungsdatei sind geschlossen.'
    }
    'Gramps' {
        $env:GRAMPSHOME=Join-Path $taskUser 'Gramps'
        $env:PYTHONUSERBASE=Join-Path $taskUser 'GrampsPython'
        & (Join-Path $taskSoftware 'Windows/Gramps-6.0.8/grampsw.exe')
    }
    'GrampsWeb' {
        Ensure-DnaWsl
        $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
        & wsl.exe -d $taskDistro -u root -- bash ($taskMount+'/DNA_Software/Start/docker-dna.sh')
        if($LASTEXITCODE -ne 0){throw 'Die SSD-Containerlaufzeit konnte nicht gestartet werden.'}
        & wsl.exe -d $taskDistro -u dna -- /usr/bin/docker -H unix:///run/docker-dna.sock compose -f ($taskMount+'/DNA_Software/Start/containers-compose.yaml') up -d --force-recreate
        if($LASTEXITCODE -ne 0){throw 'Gramps Web konnte nicht gestartet werden.'}
        Start-Process 'http://localhost:5055'
    }
    'Admixtools' {
        Ensure-DnaWsl
        $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
        Write-Output 'ADMIXTOOLS: http://localhost:7070 im Browser oeffnen. Mit Strg+C beenden.'
        & wsl.exe -d $taskDistro -u dna -- Rscript ($taskMount+'/DNA_Software/Start/admixtools-gui.R')
    }
    'Haplogrep' {
        Ensure-DnaWsl
        Write-Output 'Haplogrep: http://localhost:7001 im Browser oeffnen. Mit Strg+C beenden.'
        & wsl.exe -d $taskDistro -u dna -- /opt/dna/bin/haplogrep server
    }
    'IGV' {
        $taskIgv=Join-Path $taskSoftware 'Windows/IGV/IGV_2.19.8'
        $taskIgvHome=Join-Path $taskUser 'IGV'
        New-Item -ItemType Directory -Path $taskIgvHome -Force | Out-Null
        Push-Location $taskIgv
        try { & $taskJava.FullName ('-Duser.home='+$taskIgvHome) '-Xmx8g' '-Dproduction=true' '--module-path=lib' '@igv.args' '--module=org.igv/org.broad.igv.ui.Main' } finally {Pop-Location}
    }
    'JBrowse' { & (Join-Path $taskSoftware 'Windows/JBrowse-4.3.0/jbrowse-desktop.exe') ('--user-data-dir='+ (Join-Path $taskUser 'JBrowse')) }
    'Jupyter' { & $taskPython.FullName -m jupyterlab ('--ServerApp.root_dir='+ (Join-Path $taskSsd 'Projects')) '--ServerApp.ip=127.0.0.1' '--ServerApp.port=8890' '--no-browser' }
    'OpenCRAVAT' {
        Ensure-DnaWsl
        $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
        & wsl.exe -d $taskDistro -u dna -- bash ($taskMount+'/DNA_Software/Start/linux-launch.sh') opencravat $taskMount
    }
    'Linux' {
        Ensure-DnaWsl
        & wsl.exe -d $taskDistro -u dna
    }
    'Stop' {
        $taskInitialRunning=(@(& wsl.exe --list --running --quiet) -join "`n").Replace([string][char]0,'')
        if(($taskInitialRunning -split "`n") -contains $taskDistro){
            $taskDrive=([IO.Path]::GetPathRoot($taskSsd)).Substring(0,1).ToLowerInvariant()
            & wsl.exe -d $taskDistro -u dna -- /usr/bin/docker -H unix:///run/docker-dna.sock compose -f ($taskMount+'/DNA_Software/Start/containers-compose.yaml') stop
        }
        & wsl.exe --terminate $taskDistro
        $taskRunning=(@(& wsl.exe --list --running --quiet) -join "`n").Replace([string][char]0,'').Trim()
        if([string]::IsNullOrWhiteSpace($taskRunning)){
            & wsl.exe --shutdown
            Write-Output 'Linux und die gemeinsame WSL-Auslagerungsdatei wurden geschlossen.'
        } else {
            Write-Output ('Weitere WSL-Distributionen laufen: '+$taskRunning)
            Write-Output 'Die gemeinsame WSL-Auslagerungsdatei liegt auf dieser SSD. Vor dem Abziehen auch diese Distributionen beenden und wsl --shutdown ausfuehren.'
        }
        Write-Output 'Vor dem Abziehen auch Windows-DNA-Programme und Downloads schliessen und die SSD sicher auswerfen.'
    }
    'Export' {
        Ensure-DnaWsl
        & wsl.exe --terminate $taskDistro
        $taskBackup=Join-Path $taskSsd 'DNA_Linux/Backups'
        New-Item -ItemType Directory -Path $taskBackup -Force | Out-Null
        $taskExport=Join-Path $taskBackup ('DNA-SSD-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.tar')
        & wsl.exe --export $taskDistro $taskExport
        if($LASTEXITCODE -ne 0){throw 'Linux-Export fehlgeschlagen.'}
        Get-FileHash -LiteralPath $taskExport -Algorithm SHA256 | ConvertTo-Json | Set-Content -LiteralPath ($taskExport+'.sha256.json')
        Write-Output $taskExport
    }
    'Status' {
        Write-Output ('SSD: '+$taskSsd)
        Write-Output 'Windows-Programme: Gramps, IGV, JBrowse. Python: JupyterLab/Plotly/snps/MultiQC.'
        Write-Output 'Linux: separate Distribution DNA-SSD. Downloadstatus siehe Logs.'
        Get-ChildItem -LiteralPath (Join-Path $taskSoftware 'Logs') -Filter '*status.json' | ForEach-Object {
            $taskRows=Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
            Write-Output ($_.Name+': '+@($taskRows | Where-Object { $_.status -eq 'complete' }).Count+' fertig, '+@($taskRows | Where-Object { $_.status -eq 'failed' }).Count+' fehlgeschlagen')
        }
    }
}
