-- Contrôles après chargement. Chaque ligne doit afficher le résultat attendu indiqué.
SELECT 'territoires (75)' AS controle, count(*)::text AS resultat FROM territories
UNION ALL SELECT 'géométries valides (75)', count(*)::text FROM territories WHERE ST_IsValid(geom)
UNION ALL SELECT 'SRID (4326)', string_agg(DISTINCT ST_SRID(geom)::text, ',') FROM territories
UNION ALL SELECT 'scores de dimensions (450)', count(*)::text FROM territory_dimensions
UNION ALL SELECT 'scores d''indicateurs (1350)', count(*)::text FROM territory_indicators
UNION ALL SELECT 'premier du classement (Rabat)', name FROM territories WHERE national_rank = 1
UNION ALL SELECT 'chef-lieu Figuig dans son contour (Figuig)', name FROM territories WHERE ST_Contains(geom, ST_SetSRID(ST_Point(-1.97, 32.49), 4326))
UNION ALL SELECT 'recouvrements de plus de 1 % (0)', count(*)::text FROM territories a JOIN territories b ON a.id < b.id AND ST_Intersects(a.geom, b.geom)
  WHERE ST_Area(ST_Intersection(a.geom, b.geom)) > 0.01 * LEAST(ST_Area(a.geom), ST_Area(b.geom))
UNION ALL SELECT 'voisins à plus de 5 degrés entre centres (0)', count(*)::text FROM territories a JOIN territories b ON a.id < b.id AND ST_DWithin(a.geom, b.geom, 0.01)
  WHERE ST_Distance(ST_Centroid(a.geom), ST_Centroid(b.geom)) > 5
UNION ALL SELECT 'version PostGIS', PostGIS_Lib_Version();
-- Exemple de requête spatiale : les voisins de Figuig (contours simplifiés, à lire comme une indication).
SELECT b.name AS voisin_de_figuig, b.rafah_score FROM territories a JOIN territories b ON a.id <> b.id AND ST_DWithin(a.geom, b.geom, 0.01) WHERE a.name = 'Figuig' ORDER BY b.name;
