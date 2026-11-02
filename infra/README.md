# Services locaux de Rafah

Tout tourne sur cette machine uniquement et ne fait pas partie du site public. Les outils sont dans `C:\Users\hp\rafah-tools`, hors du dépôt. Le service PostgreSQL déjà installé n'est pas modifié.

| Service | Adresse | Lancement |
|---|---|---|
| API FastAPI | http://127.0.0.1:8000/docs | `python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000` |
| PostGIS 3.6 sur PostgreSQL 18 | localhost:5544, base `rafah`, utilisateur `rafah` | `infra/setup_postgis.ps1` |
| GeoServer | http://127.0.0.1:8085/geoserver | `infra/setup_geoserver.ps1`, après PostGIS |

Dépendances de l'API : `pip install -r backend/requirements.txt`, puis `python -m pytest backend/test_api.py`.

Exemples GeoServer, couche `rafah:territoires_scores` :

- WMS : http://127.0.0.1:8085/geoserver/rafah/wms?service=WMS&version=1.1.1&request=GetMap&layers=rafah:territoires_scores&bbox=-17.6,20.6,-0.9,36.1&width=500&height=460&srs=EPSG:4326&format=image/png
- WFS : http://127.0.0.1:8085/geoserver/rafah/ows?service=WFS&version=2.0.0&request=GetFeature&typeNames=rafah:territoires_scores&outputFormat=application/json&count=5

## Sécurité

Ces réglages conviennent à un essai local, pas à une mise en ligne.

- PostgreSQL accepte les connexions locales sans mot de passe.
- GeoServer garde le mot de passe administrateur par défaut, `admin` / `geoserver`.
- GeoServer est une compilation quotidienne de la branche 3.0.x, pas une version publiée. SourceForge refusait le téléchargement par script.

Ne les exposez jamais sur un réseau. Toute diffusion publique attend aussi la validation des licences.

## Arrêt

```bash
C:/Users/hp/rafah-tools/pgsql/bin/pg_ctl.exe -D C:/Users/hp/rafah-tools/pgdata stop
```

GeoServer s'arrête en fermant son processus `java.exe`, dans le Gestionnaire des tâches.

`data/api/v1` et `infra/rafah_postgis.sql` sont régénérés par `build_api.py` et `export_postgis.py`.
