#!/bin/sh
while true
do
  echo "Running AniListSonarrSync.py"
  python ./AniListSonarrSync.py
  sleep "${INTERVAL}"
  echo "Sleeping for ${INTERVAL} seconds"
done