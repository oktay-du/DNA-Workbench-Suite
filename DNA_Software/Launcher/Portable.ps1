# Shared portable paths. Dot-source this file, then call Initialize-DnaPortable.
function Initialize-DnaPortable([string]$AppRoot){
 $script:DnaRoot=[IO.Path]::GetFullPath($AppRoot);$base=Join-Path $script:DnaRoot 'DNA_Software/UserData'
 $dirs=@{TEMP='Temp';TMP='Temp';TMPDIR='Temp';XDG_CACHE_HOME='Cache';XDG_DATA_HOME='Data';XDG_CONFIG_HOME='Config';PIP_CACHE_DIR='Cache/pip';UV_CACHE_DIR='Cache/uv';HF_HOME='Cache/huggingface';TORCH_HOME='Cache/torch';MPLCONFIGDIR='Cache/matplotlib';npm_config_cache='Cache/npm';APPDATA='AppData/Roaming';LOCALAPPDATA='AppData/Local';JUPYTER_CONFIG_DIR='Jupyter/config';JUPYTER_DATA_DIR='Jupyter/data';JUPYTER_RUNTIME_DIR='Jupyter/runtime'}
 foreach($key in $dirs.Keys){$path=Join-Path $base $dirs[$key];New-Item -ItemType Directory -Path $path -Force|Out-Null;[Environment]::SetEnvironmentVariable($key,$path,'Process')}
 $env:DNA_SUITE_ROOT=$script:DnaRoot;$env:PYTHONNOUSERSITE='1'
 Set-Location -LiteralPath $script:DnaRoot
}
function Get-DnaLinuxRoot([string]$AppRoot){
 $path=[IO.Path]::GetFullPath($AppRoot)
 if($path -notmatch '^[A-Za-z]:\\'){throw 'WSL requires a local Windows drive path.'}
 return ('/mnt/'+$path.Substring(0,1).ToLowerInvariant()+'/'+$path.Substring(3).Replace('\','/').TrimEnd('/')).TrimEnd('/')
}
function Get-DnaDistroName([string]$AppRoot){
 $expected=[IO.Path]::GetFullPath((Join-Path $AppRoot 'DNA_Linux/DNA-SSD')).TrimEnd('\')
 $registry='HKCU:/Software/Microsoft/Windows/CurrentVersion/Lxss'
 if(Test-Path $registry){foreach($child in Get-ChildItem $registry){$entry=Get-ItemProperty $child.PSPath;$base=([string]$entry.BasePath)-replace '^\\\\\?\\','';if($base -and [IO.Path]::GetFullPath($base).TrimEnd('\') -ieq $expected){return [string]$entry.DistributionName}}}
 $canonical=[IO.Path]::GetFullPath($AppRoot).TrimEnd([char[]]'\/').ToLowerInvariant();$sha=[Security.Cryptography.SHA256]::Create()
 try{$hash=[BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canonical))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 return 'DNA-WB-'+$hash.Substring(0,12)
}
function Set-DnaSwapFile([string]$AppRoot,[string]$HostConfig=(Join-Path $env:USERPROFILE '.wslconfig')){
 $target=Join-Path ([IO.Path]::GetFullPath($AppRoot)) 'DNA_Linux/WSL_Swap/dna-swap.vhdx';New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force|Out-Null
 $old=if(Test-Path -LiteralPath $HostConfig){[IO.File]::ReadAllText($HostConfig)}else{''};$escaped=$target.Replace('\','\\');$lines=New-Object 'Collections.Generic.List[string]';$inside=$false;$found=$false;$section=$false
 foreach($line in ($old -split '\r?\n')){
  if($line -match '^\s*\['){if($inside -and -not$found){$lines.Add('swapFile='+$escaped);$found=$true};$inside=$line -match '^\s*\[wsl2\]\s*$';if($inside){$section=$true}}
  if($inside -and $line -match '^\s*swapFile\s*='){if(-not$found){$lines.Add('swapFile='+$escaped);$found=$true}}else{$lines.Add($line)}
 }
 if(-not$section){$lines.Add('[wsl2]')};if(-not$found){$lines.Add('swapFile='+$escaped)}
 $new=($lines -join "`r`n").TrimEnd()+"`r`n"
 if($old.TrimEnd() -ne $new.TrimEnd()){
  $backup=Join-Path $AppRoot ('DNA_Software/UserData/HostBackups/wslconfig_'+(Get-Date -Format yyyyMMdd_HHmmss_fff)+'.txt');New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force|Out-Null
  if(Test-Path -LiteralPath $HostConfig){Copy-Item -LiteralPath $HostConfig -Destination $backup}
  [IO.File]::WriteAllText($HostConfig,$new,(New-Object Text.UTF8Encoding($false)))
  return @{path=$target;changed=$true;restart_required=$true;scope='All WSL2 distributions; no running distribution was stopped';backup=$backup}
 };return @{path=$target;changed=$false;restart_required=$false;scope='All WSL2 distributions'}
}
function Get-DnaPortableStatus([string]$AppRoot){
 $name=Get-DnaDistroName $AppRoot;$disk=Join-Path $AppRoot 'DNA_Linux/DNA-SSD/ext4.vhdx';$hostReady=$false
 if(Get-Command wsl.exe -ErrorAction SilentlyContinue){& wsl.exe --status *> $null;$hostReady=$LASTEXITCODE-eq 0}
 return @{root=[IO.Path]::GetFullPath($AppRoot);mount=(Get-DnaLinuxRoot $AppRoot).TrimEnd('/');distro=$name;wsl_host_ready=$hostReady;disk=$disk;disk_present=(Test-Path -LiteralPath $disk);cache=(Join-Path $AppRoot 'DNA_Software/UserData/Cache');swap=(Join-Path $AppRoot 'DNA_Linux/WSL_Swap/dna-swap.vhdx')}
}
