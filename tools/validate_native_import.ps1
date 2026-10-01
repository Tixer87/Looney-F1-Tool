param([string]$AppDir,[string]$ExportDir)
$ErrorActionPreference='Stop'
foreach($n in @('RacingLeagueTools.Interfaces','RacingLeagueTools.SharedLibrary','RacingLeagueTools.DAL','RacingLeagueTools.Core')){
    [void][Reflection.Assembly]::LoadFrom((Join-Path $AppDir "bin\$n.dll"))
}
$a=[Reflection.Assembly]::LoadFrom((Join-Path $AppDir 'RacingLeagueTools.dll'))
$t=$a.GetType('RacingLeagueTools.MainApp.Services.ExternalSessionResults.ResultsProcessorRltV2.Models.RltV2Root',$true)
$options=[System.Text.Json.JsonSerializerOptions]::new()
$options.PropertyNameCaseInsensitive=$true
$report=@(Get-ChildItem -LiteralPath $ExportDir -Filter *.json | ForEach-Object{
    $raw=Get-Content -LiteralPath $_.FullName -Raw
    $expected=$raw|ConvertFrom-Json
    $parsed=[System.Text.Json.JsonSerializer]::Deserialize($raw,$t,$options)
    if($parsed.Metadata.FormatVersion -ne 1 -or $parsed.Session.Drivers.Count -ne $expected.session.drivers.Count){throw 'Native import mismatch'}
    for($i=0;$i -lt $parsed.Session.Drivers.Count;$i++){
        $x=$parsed.Session.Drivers[$i]
        $e=$expected.session.drivers[$i]
        if($x.DriverName -ne $e.driverName -or $x.DriverInfo.RaceNumber -cne $e.driverInfo.raceNumber -or $x.ClassificationPosition -ne $e.classificationPosition -or $x.Status -cne $e.status -or $x.GapMs -ne [long]$e.gapMs -or $x.TotalTimeMs -ne [long]$e.totalTimeMs -or $x.DriverPoints -ne $e.driverPoints){throw "Driver mismatch: $($e.driverName)"}
    }
    [pscustomobject]@{File=$_.Name;Drivers=$parsed.Session.Drivers.Count;Session=$parsed.Session.SessionInfo.SessionType;Result='Parsed and compared with installed RLT V2 import DTOs; no database changes'}
})
$report|ConvertTo-Json -Depth 4