#!/bin/sh
# Crée deploy/.env avec des mots de passe aléatoires. Usage : sh make_env.sh api-et-geoserver.exemple.ma
set -eu
[ $# -eq 1 ] || { echo "Usage : sh make_env.sh DOMAINE"; exit 1; }
cd "$(dirname "$0")"
[ ! -e .env ] || { echo ".env existe déjà"; exit 1; }
umask 077
{
  echo "DOMAIN=$1"
  echo "DB_PASSWORD=$(openssl rand -hex 24)"
  echo "GEOSERVER_ADMIN_USER=rafah_admin"
  echo "GEOSERVER_ADMIN_PASSWORD=$(openssl rand -hex 24)"
} > .env
echo ".env créé : conservez ce fichier, ne le partagez pas."
