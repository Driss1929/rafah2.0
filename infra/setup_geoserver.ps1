# GeoServer portable pour Rafah, limité à cette machine (127.0.0.1:8085). PostGIS doit tourner sur le port 5544.
# Le mot de passe admin reste celui par défaut de GeoServer : à ne jamais exposer sur un réseau.
param([string]$Tools = "C:\Users\hp\rafah-tools")
$ErrorActionPreference = "Stop"
$dl = "$Tools\downloads"; $gs = "$Tools\geoserver"; $jre = "$Tools\jre"
if (-not (Test-Path "$jre\bin\java.exe")) {
    New-Item -ItemType Directory -Force $jre | Out-Null
    tar.exe -xf "$dl\jre.zip" -C $jre --strip-components=1
}
if (-not (Test-Path "$gs\start.jar")) {
    New-Item -ItemType Directory -Force $gs | Out-Null
    tar.exe -xf "$dl\geoserver.zip" -C $gs
    Get-ChildItem $gs | Select-Object -First 12 Name | Out-String | Write-Output
}
$ini = "$gs\start.ini"
if ((Get-Content $ini -Raw) -notmatch "(?m)^jetty\.http\.host=127\.0\.0\.1") {
    Add-Content $ini "`njetty.http.host=127.0.0.1`njetty.http.port=8085`n"
}
if (-not (Get-NetTCPConnection -LocalPort 8085 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath "$jre\bin\java.exe" -WorkingDirectory $gs -WindowStyle Hidden -RedirectStandardOutput "$Tools\geoserver.log" -RedirectStandardError "$Tools\geoserver.err" `
        -ArgumentList "-Xmx1g", "-DGEOSERVER_DATA_DIR=$gs\data_dir", "-Djetty.base=$gs", "-Djetty.home=$gs", "--add-opens=java.base/java.util=ALL-UNNAMED", "--add-opens=java.base/java.lang=ALL-UNNAMED", "--add-opens=java.base/java.net=ALL-UNNAMED", "--add-opens=java.desktop/javax.imageio.stream=ALL-UNNAMED", "--add-opens=java.desktop/sun.awt.image=ALL-UNNAMED", "--add-opens=java.naming/com.sun.jndi.ldap=ALL-UNNAMED", "--add-opens=java.desktop/javax.imageio.spi=ALL-UNNAMED", "-jar", "start.jar"
}
$base = "http://127.0.0.1:8085/geoserver"
$ok = $false
foreach ($i in 1..60) {
    Start-Sleep -Seconds 3
    if ((curl.exe -s -o NUL -w "%{http_code}" -u admin:geoserver "$base/rest/about/version.json") -eq "200") { $ok = $true; break }
}
if (-not $ok) { Get-Content "$Tools\geoserver.log" -Tail 15; Get-Content "$Tools\geoserver.err" -Tail 15; throw "GeoServer n'a pas démarré" }

function Rest($method, $path, $file, $type) {
    $code = curl.exe -s -o "$Tools\rest.out" -w "%{http_code}" -u admin:geoserver -X $method -H "Content-Type: $type" --data-binary "@$file" "$base/rest/$path"
    "$method $path -> $code"
}
$tmp = "$Tools\rest.json"
$utf8 = New-Object Text.UTF8Encoding $false
if ((curl.exe -s -o NUL -w "%{http_code}" -u admin:geoserver "$base/rest/workspaces/rafah.json") -ne "200") {
    [IO.File]::WriteAllText($tmp, '{"workspace":{"name":"rafah"}}', $utf8); Rest POST "workspaces" $tmp "application/json"
    [IO.File]::WriteAllText($tmp, '{"dataStore":{"name":"rafah_postgis","connectionParameters":{"entry":[{"@key":"dbtype","$":"postgis"},{"@key":"host","$":"localhost"},{"@key":"port","$":"5544"},{"@key":"database","$":"rafah"},{"@key":"user","$":"rafah"},{"@key":"schema","$":"public"}]}}}', $utf8); Rest POST "workspaces/rafah/datastores" $tmp "application/json"
    [IO.File]::WriteAllText($tmp, '{"featureType":{"name":"territoires_scores","nativeName":"territoires_scores","title":"Rafah : scores par territoire (non officiel)","srs":"EPSG:4326","nativeBoundingBox":{"minx":-17.6,"maxx":-0.9,"miny":20.6,"maxy":36.1,"crs":"EPSG:4326"},"latLonBoundingBox":{"minx":-17.6,"maxx":-0.9,"miny":20.6,"maxy":36.1,"crs":"EPSG:4326"}}}', $utf8); Rest POST "workspaces/rafah/datastores/rafah_postgis/featuretypes" $tmp "application/json"
    Get-Content "$Tools\rest.out" -Raw
}
"--- WFS : nombre d'objets"
curl.exe -s "$base/rafah/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=rafah:territoires_scores&resultType=hits" | Select-String -Pattern 'numberMatched="(\d+)"' | ForEach-Object { $_.Matches[0].Value }
"--- WFS : premier du classement"
curl.exe -s "$base/rafah/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=rafah:territoires_scores&outputFormat=application/json&count=1&cql_filter=national_rank=1&propertyName=name,rafah_score,national_rank"
""
"--- WMS : image de la carte"
curl.exe -s -o "$Tools\wms.png" -w "%{http_code} %{content_type} %{size_download}`n" "$base/rafah/wms?service=WMS&version=1.1.1&request=GetMap&layers=rafah:territoires_scores&bbox=-17.6,20.6,-0.9,36.1&width=500&height=460&srs=EPSG:4326&format=image/png"
