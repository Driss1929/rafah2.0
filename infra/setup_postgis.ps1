# Base PostGIS portable pour Rafah : dossier séparé, port 5544, accessible depuis cette machine seulement.
# Ne touche pas au service PostgreSQL déjà installé. Les zips doivent être dans $Tools\downloads.
param([string]$Tools = "C:\Users\hp\rafah-tools")
$ErrorActionPreference = "Stop"
$dl = "$Tools\downloads"; $pg = "$Tools\pgsql"; $data = "$Tools\pgdata"; $sqlDir = $PSScriptRoot
if (-not (Test-Path "$pg\bin\psql.exe")) {
    Expand-Archive "$dl\postgresql.zip" $Tools -Force
    $tmp = "$Tools\_postgis"; Expand-Archive "$dl\postgis.zip" $tmp -Force
    $bundle = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName
    Copy-Item "$bundle\*" $pg -Recurse -Force
    Remove-Item $tmp -Recurse -Force -Confirm:$false
}
if (-not (Test-Path "$data\PG_VERSION")) {
    & "$pg\bin\initdb.exe" -D $data -U rafah -E UTF8 --locale=C --auth=trust | Out-Null
    Add-Content "$data\postgresql.conf" "`nport = 5544`nlisten_addresses = 'localhost'`n"
}
& "$pg\bin\pg_ctl.exe" -D $data status *> $null
# Lancé à part : postgres hérite sinon de la sortie du script, qui ne se terminerait jamais.
if ($LASTEXITCODE -ne 0) { Start-Process -FilePath "$pg\bin\pg_ctl.exe" -ArgumentList "-D", "`"$data`"", "-l", "`"$Tools\pg.log`"", "-w", "start" -WindowStyle Hidden -Wait }
$psql = "$pg\bin\psql.exe"
$exists = & $psql -h localhost -p 5544 -U rafah -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='rafah'"
if ($exists -ne "1") { & $psql -h localhost -p 5544 -U rafah -d postgres -q -c "CREATE DATABASE rafah" }
# Les avis de psql arrivent sur stderr : ils ne doivent pas interrompre le script, seul son code de sortie compte.
$ErrorActionPreference = "Continue"
$env:PGOPTIONS = "-c client_min_messages=warning"
& $psql -h localhost -p 5544 -U rafah -d rafah -q -v ON_ERROR_STOP=1 -f "$sqlDir\rafah_postgis.sql" *> "$Tools\load.log"
if ($LASTEXITCODE -ne 0) { Get-Content "$Tools\load.log" -Tail 8; throw "Échec du chargement" }
& $psql -h localhost -p 5544 -U rafah -d rafah -f "$sqlDir\check_postgis.sql"
