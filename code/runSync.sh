#!/bin/sh
while true
do
  echo "Running AniListSonarrSync.py"
  python ./AniListSonarrSync.py
  echo "Sleeping for ${INTERVAL} seconds"
  sleep "${INTERVAL}"
done