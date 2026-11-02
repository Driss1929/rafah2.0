#!/bin/sh
# Publie la couche Rafah dans GeoServer. Sans effet si elle existe déjà.
set -eu
apk add --no-cache curl >/dev/null
BASE=http://geoserver:8080/geoserver/rest
AUTH="$GEOSERVER_ADMIN_USER:$GEOSERVER_ADMIN_PASSWORD"
i=0
until [ "$(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" "$BASE/about/version.json")" = 200 ]; do
  i=$((i + 1)); [ "$i" -lt 80 ] || { echo "GeoServer ne répond pas"; exit 1; }; sleep 5
done
post() { curl -sf -o /dev/null -u "$AUTH" -H 'Content-Type: application/json' -X POST -d "$2" "$BASE/$1"; }
if [ "$(curl -s -o /dev/null -w '%{http_code}' -u "$AUTH" "$BASE/workspaces/rafah.json")" != 200 ]; then
  post workspaces '{"workspace":{"name":"rafah"}}'
  post workspaces/rafah/datastores "{\"dataStore\":{\"name\":\"rafah_postgis\",\"connectionParameters\":{\"entry\":[{\"@key\":\"dbtype\",\"\$\":\"postgis\"},{\"@key\":\"host\",\"\$\":\"db\"},{\"@key\":\"port\",\"\$\":\"5432\"},{\"@key\":\"database\",\"\$\":\"rafah\"},{\"@key\":\"user\",\"\$\":\"rafah\"},{\"@key\":\"passwd\",\"\$\":\"$DB_PASSWORD\"},{\"@key\":\"schema\",\"\$\":\"public\"}]}}}"
  post workspaces/rafah/datastores/rafah_postgis/featuretypes '{"featureType":{"name":"territoires_scores","nativeName":"territoires_scores","title":"Rafah : scores par territoire (non officiel)","srs":"EPSG:4326","nativeBoundingBox":{"minx":-17.6,"maxx":-0.9,"miny":20.6,"maxy":36.1,"crs":"EPSG:4326"},"latLonBoundingBox":{"minx":-17.6,"maxx":-0.9,"miny":20.6,"maxy":36.1,"crs":"EPSG:4326"}}}'
fi
echo "Couche rafah:territoires_scores publiée"
