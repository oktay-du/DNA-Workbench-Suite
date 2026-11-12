param([string]$Root=(Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),[ValidateSet('Plan','Core','Linux','Tools','References','Sources')][string]$Mode='Plan',[switch]$InstallWslHost)
$ErrorActionPreference='Stop'
$Root=[IO.Path]::GetFullPath($Root)
. (Join-Path $PSScriptRoot 'Portable.ps1')
Initialize-DnaPortable $Root
$taskDistro=Get-DnaDistroName $Root
$manifest=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'install-lock.json') -Raw | ConvertFrom-Json
$nativeArchitecture=if($env:PROCESSOR_ARCHITEW6432){$env:PROCESSOR_ARCHITEW6432}else{$env:PROCESSOR_ARCHITECTURE}
$armDesktop=$env:DNA_WORKBENCH_WINDOWS_ARCH -eq 'arm64' -or (-not $env:DNA_WORKBENCH_WINDOWS_ARCH -and $nativeArchitecture -eq 'arm64')
$armPackages=if($armDesktop -or $nativeArchitecture -eq 'arm64'){Get-Content -LiteralPath (Join-Path $PSScriptRoot 'windows-arm64-packages.json') -Raw | ConvertFrom-Json}
$corePython=if($armDesktop){$armPackages.'python-windows'}else{$manifest.items|Where-Object id -eq 'python-windows'}
$ubuntuPackage=if($nativeArchitecture -eq 'arm64'){$armPackages.'ubuntu-wsl'}else{$manifest.items|Where-Object id -eq 'ubuntu-wsl'}
$logDir=Join-Path $Root 'DNA_Software/Logs/Setup';New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stateFile=Join-Path $logDir 'status.json'
function State([string]$stage,[string]$detail){@{stage=$stage;detail=$detail;mode=$Mode;updated=(Get-Date).ToString('o');root=$Root}|ConvertTo-Json|Set-Content -LiteralPath $stateFile -Encoding UTF8;Write-Host ($stage+': '+$detail)}
function Target([string]$relative){if([IO.Path]::IsPathRooted($relative)-or$relative.Split([char[]]'/\').Contains('..')){throw "Inadmissible destination path."};$p=[IO.Path]::GetFullPath((Join-Path $Root $relative));if(-not$p.StartsWith($Root.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Target outside of the app folder."};return $p}
function Get-DnaArchiveHash([string]$Path,[string]$Algorithm){
 $stream=[IO.File]::OpenRead($Path);$hash=[Security.Cryptography.HashAlgorithm]::Create($Algorithm)
 try{return [BitConverter]::ToString($hash.ComputeHash($stream)).Replace('-','')}finally{$hash.Dispose();$stream.Dispose()}
}
function Fetch($item){
 $target=Target $item.relative_path;New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target)|Out-Null
 if(-not $item.expected_sha256 -and -not $item.expected_md5){throw ("No specified test value for:"+$item.name+"Check the source in the dependency menu.")}
 if(Test-Path -LiteralPath $target){$algorithm=if($item.expected_sha256){'SHA256'}else{'MD5'};$expected=if($item.expected_sha256){$item.expected_sha256}else{$item.expected_md5};if((Get-DnaArchiveHash $target $algorithm) -ieq $expected){return $target};throw ("Existing file differs; no override:"+$target)}
 State 'Download' $item.name;$part=$target+'.part'
 & curl.exe --fail --location --retry 3 --connect-timeout 30 --continue-at - --output $part $item.url
 if($LASTEXITCODE-ne 0){throw ('Download fehlgeschlagen: '+$item.name)}
 if($item.expected_bytes -and (Get-Item -LiteralPath $part).Length-ne [long]$item.expected_bytes){throw "Download size is not true."}
 $algorithm=if($item.expected_sha256){'SHA256'}else{'MD5'};$expected=if($item.expected_sha256){$item.expected_sha256}else{$item.expected_md5}
 if((Get-DnaArchiveHash $part $algorithm) -ine $expected){throw ("Checksum is not correct:"+$item.name)}
 Move-Item -LiteralPath $part -Destination $target;return $target
}
function InstallCore{
 $items=@($corePython)
 if(-not $armDesktop){$items+=@($manifest.items|Where-Object id -eq 'webview2-runtime')}
 foreach($item in $items){
  $id=$item.id
  $dest=Target $item.target
  $probe=if($id-eq'python-windows'){Join-Path $dest 'python.exe'}else{if(Test-Path $dest){Get-ChildItem -LiteralPath $dest -Filter msedgewebview2.exe -Recurse|Select-Object -First 1 -ExpandProperty FullName}}
  if($probe -and(Test-Path -LiteralPath $probe)){State 'Vorhanden' $id;continue}
  $archive=Fetch $item;New-Item -ItemType Directory -Force -Path $dest|Out-Null
  if($id-eq'python-windows'){& tar.exe -xzf $archive --strip-components=1 -C $dest}else{& expand.exe '-F:*' $archive $dest|Out-Null}
  if($LASTEXITCODE-ne 0){throw ('Entpacken fehlgeschlagen: '+$id)}
 }
}
function EnsureLinux{
 $wsl=Get-Command wsl.exe -ErrorAction SilentlyContinue
 if(-not$wsl){throw "WSL is not available on this Windows."}
 & wsl.exe --status *> $null
 if($LASTEXITCODE-ne 0){
  if(-not$InstallWslHost){throw "WSL host missing. Start setup with WSL installation enabled; administrative privileges and restart required if applicable."}
  $p=Start-Process -FilePath wsl.exe -ArgumentList '--install','--no-distribution' -Verb RunAs -WindowStyle Hidden -Wait -PassThru
  if($p.ExitCode-notin @(0,3010)){throw ('WSL-Hostinstallation: '+$p.ExitCode)}
  State "Check the restart" "WSL system components are set up. After a required restart, restart the app."
  & wsl.exe --status *> $null;if($LASTEXITCODE-ne 0){throw "Windows restart required. No distribution overwritten."}
 }
 $swapState=Set-DnaSwapFile $Root
 if($swapState.changed){State 'WSL-Swap' "Path is in the app folder. Change applies Windows-wide; current distributions are not terminated."}
 $pending=Join-Path $Root 'DNA_Software/UserData/Launcher/swap-restart.json'
 if($swapState.changed -or (Test-Path -LiteralPath $pending)){
  $active=(@(& wsl.exe --list --running --quiet)-join "`n").Replace([string][char]0,'').Trim()
  if($active){New-Item -ItemType Directory -Force -Path (Split-Path -Parent $pending)|Out-Null;@{swap=$swapState.path;reason='Windows-wide WSL restart pending'}|ConvertTo-Json|Set-Content -LiteralPath $pending;throw "WSL swap path has been prepared. Please quit ongoing WSL work and restart WSL; third-party distributions are not automatically stopped."}
  & wsl.exe --shutdown
  if($LASTEXITCODE-ne 0){throw "WSL configuration could not be reloaded."}
  if(Test-Path -LiteralPath $pending){Remove-Item -LiteralPath $pending}
 }
 $target=Target 'DNA_Linux/DNA-SSD';$disk=Join-Path $target 'ext4.vhdx'
 $existing=@();$reg='HKCU:/Software/Microsoft/Windows/CurrentVersion/Lxss'
 if(Test-Path $reg){$existing=@(Get-ChildItem $reg|ForEach-Object{Get-ItemProperty $_.PSPath}|Where-Object DistributionName -eq $taskDistro)}
 if($existing.Count){$base=([string]$existing[0].BasePath)-replace '^\\\\\?\\','';if([IO.Path]::GetFullPath($base).TrimEnd('\')-ine$target.TrimEnd('\')){throw 'DNA-SSD ist an einem anderen Ort registriert. Nichts wurde entfernt.'}}
 elseif(Test-Path -LiteralPath $disk){& wsl.exe --import-in-place $taskDistro $disk;if($LASTEXITCODE-ne 0){throw "Existing SSD distribution could not be registered."}}
 else{$archive=Fetch $ubuntuPackage;New-Item -ItemType Directory -Force -Path $target|Out-Null;& wsl.exe --import $taskDistro $target $archive --version 2;if($LASTEXITCODE-ne 0){throw 'Ubuntu-Import fehlgeschlagen.'}}
 $guestArchitecture=& wsl.exe -d $taskDistro -u root -- dpkg --print-architecture
 if($LASTEXITCODE-ne 0 -or ([string]$guestArchitecture).Trim() -ine $(if($nativeArchitecture -eq 'arm64'){'arm64'}else{'amd64'})){
  throw "The existing Ubuntu workspace does not match the host CPU architecture. Use a separate workspace folder for this architecture."
 }
 $mount=(Get-DnaLinuxRoot $Root).TrimEnd('/')
 & wsl.exe -d $taskDistro -u root -- test -x /opt/dna/envs/analysis/bin/python
 if($LASTEXITCODE-ne 0){& wsl.exe -d $taskDistro -u root -- bash ($mount+'/DNA_Software/Launcher/setup-linux-public.sh') $mount;if($LASTEXITCODE-ne 0){throw 'Linux-Basiseinrichtung fehlgeschlagen. Siehe Installationsprotokoll.'}}
 & wsl.exe -d $taskDistro -u root -- python3 ($mount+'/DNA_Software/Start/relocate-linux.py') $mount
 if($LASTEXITCODE-ne 0){throw "Portable Linux shortcut could not be set up."}
}
try{
 State "Test test" ('App-Verzeichnis '+$Root)
 if($Mode-eq'Plan'){@{root=$Root;mode='Plan';actions=@("Core: portable Python and WebView2",'Linux: WSL-Host bei Bedarf, Ubuntu-VHDX unter App-Verzeichnis','Tools: Linux-Basiswerkzeuge',"References / Sources: versioned public downloads");host_changes="WSL system components and registry are host-side. Linux setup only puts swapFile in .wslconfig on the app folder; backup and obtaining other settings. No stopping ongoing outside WSL work.";artifacts=$manifest.items.Count}|ConvertTo-Json -Depth 5;exit 0}
 if($Mode-in @('Core','Linux','Tools')){InstallCore}
 if($Mode-in @('Linux','Tools')){EnsureLinux}
 if($Mode-eq'Tools'){
  $py=Join-Path (Target $corePython.target) 'python.exe'
  & $py (Join-Path $PSScriptRoot 'dependency_manager.py') install-foundation
  if($LASTEXITCODE-ne 0){throw "tool device not completely."}
 }
 if($Mode-in @('References','Sources')){$group=if($Mode-eq'References'){'references'}else{'sources'};foreach($item in $manifest.items|Where-Object group -eq $group){if($item.license_notice){State 'Ausgelassen' ($item.name+': '+$item.license_notice);continue};$null=Fetch $item}}
 State 'Complete' "Setup completed; optional tools remain selectable separately."
}catch{State 'Failed' $_.Exception.Message;Write-Error $_;exit 1}
