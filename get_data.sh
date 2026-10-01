#!/bin/bash
set -e
UA="Mozilla/5.0 (research use)"
for y in $(seq 2015 2026); do
  [ -f ${y}_qtrly_singlefile.zip ] || curl -L -A "$UA" -o ${y}_qtrly_singlefile.zip "https://data.bls.gov/cew/data/files/${y}/csv/${y}_qtrly_singlefile.zip"
done
