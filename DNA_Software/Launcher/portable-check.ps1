param([string]$Root=(Split-Path -Parent (Split-Path -Parent $PSScriptRoot)))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'Portable.ps1')
Initialize-DnaPortable $Root
Get-DnaPortableStatus $Root | ConvertTo-Json -Depth 6
