#!/bin/sh
# Vérifie le service en ligne depuis l'extérieur. Usage : sh smoke_test.sh DOMAINE
set -u
D=$1; fail=0
check() { got=$(curl -s -o /dev/null -m 30 -w '%{http_code}' -X "${3:-GET}" "$2"); if [ "$got" = "$1" ]; then echo "OK   $got $2"; else echo "ÉCHEC $got (attendu $1) $2"; fail=1; fi; }
check 200 "https://api.$D/v1/metadata"
check 200 "https://api.$D/docs"
check 200 "https://api.$D/v1/territories/2251"
check 404 "https://api.$D/v1/territories/99999"
check 405 "https://api.$D/v1/metadata" POST
check 200 "https://geoserver.$D/geoserver/rafah/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=rafah:territoires_scores&resultType=hits"
check 200 "https://geoserver.$D/geoserver/rafah/wms?service=WMS&version=1.1.1&request=GetMap&layers=rafah:territoires_scores&bbox=-17.6,20.6,-0.9,36.1&width=500&height=460&srs=EPSG:4326&format=image/png"
check 403 "https://geoserver.$D/geoserver/web/"
check 403 "https://geoserver.$D/geoserver/rest/about/version.json"
n=$(curl -s -m 30 "https://geoserver.$D/geoserver/rafah/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=rafah:territoires_scores&resultType=hits" | grep -o 'numberMatched="[0-9]*"')
[ "$n" = 'numberMatched="75"' ] && echo "OK   75 territoires" || { echo "ÉCHEC WFS : $n"; fail=1; }
nc -z -w 5 "api.$D" 5432 2>/dev/null && { echo "ÉCHEC : PostGIS est exposé"; fail=1; } || echo "OK   PostGIS non exposé"
exit $fail
