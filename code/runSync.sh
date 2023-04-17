#!/bin/sh
while true
do
  echo "Running aniplanrr.py"
  python ./aniplanrr.py
  echo "Sleeping for ${INTERVAL} seconds"
  sleep "${INTERVAL}"
done