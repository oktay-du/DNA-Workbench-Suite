param([string]$Executable=(Join-Path (Split-Path -Parent $PSScriptRoot) 'DNA_Launcher.exe'))
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Web.Extensions
$assembly=[Reflection.Assembly]::LoadFrom([IO.Path]::GetFullPath($Executable))
$serializer=New-Object Web.Script.Serialization.JavaScriptSerializer
$type=$assembly.GetType('DnaWorkbench.Catalog',$true)
$sample='{"version":1,"categories":["Synthetic"],"tasks":[{"id":"demo","title":"Synthetic task","fields":[{"key":"vcf","kind":"file","default":"","required":true,"multi":false,"choices":["GRCh38"]}]}]}'
$catalog=$serializer.Deserialize($sample,$type)
if($catalog.tasks[0].id -ne 'demo' -or $catalog.tasks[0].fields[0].key -ne 'vcf' -or -not $catalog.tasks[0].fields[0].required){throw 'Native catalog deserialization changed'}
$roundtrip=$serializer.DeserializeObject($serializer.Serialize($catalog))
if($roundtrip.tasks[0].fields[0]['default'] -ne '' -or $roundtrip.tasks[0].fields[0].choices[0] -ne 'GRCh38'){throw 'Native catalog roundtrip changed'}
$startup=New-Object ($assembly.GetType('DnaWorkbench.StartupContext',$true))
if($startup.Url -ne '' -or $startup.Python -ne '' -or $startup.LinuxStatus -ne 'Not started'){throw 'Startup defaults changed'}
$screen=[Activator]::CreateInstance($assembly.GetType('DnaWorkbench.StartupScreen',$true),[object[]]@($null,$false))
try{if($null -eq $screen.Context){throw 'Default startup context was not initialized'}}finally{$screen.Dispose()}
Write-Output 'Native catalog, field and startup contracts passed.' 
