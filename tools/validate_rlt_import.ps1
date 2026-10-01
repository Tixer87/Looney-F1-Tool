param([string]$AppDir,[string]$ExportDir)
$ErrorActionPreference='Stop'
$app=(Resolve-Path -LiteralPath $AppDir).Path
foreach($n in @('RacingLeagueTools.Interfaces','RacingLeagueTools.SharedLibrary','RacingLeagueTools.DAL','RacingLeagueTools.Core')){
    [void][Reflection.Assembly]::LoadFrom((Join-Path $app "bin\$n.dll"))
}
$assembly=[Reflection.Assembly]::LoadFrom((Join-Path $app 'RacingLeagueTools.dll'))
$rootType=$assembly.GetType('RacingLeagueTools.MainApp.Services.ExternalSessionResults.ResultsProcessorRlt.Root',$true)
$options=[System.Text.Json.JsonSerializerOptions]::new()
$options.Converters.Add([System.Text.Json.Serialization.JsonStringEnumConverter]::new())
$rows=Get-ChildItem -LiteralPath $ExportDir -Recurse -Filter '*.json'|ForEach-Object{
    $raw=Get-Content -LiteralPath $_.FullName -Raw
    $session=[System.Text.Json.JsonSerializer]::Deserialize($raw,$rootType,$options)
    $expected=$raw|ConvertFrom-Json
    if($session.Drivers.Count -ne $expected.Drivers.Count){throw 'Driver count mismatch'}
    if($session.QualType.ToString() -ne $expected.QualType){throw 'QualType mismatch'}
    [pscustomobject]@{File=$_.Name;Drivers=$session.Drivers.Count;Session=$session.SessionType.ToString();QualType=$session.QualType.ToString();Result='Parsed by actual RLT 0.9.8 legacy import model'}
}
$rows|ConvertTo-Json