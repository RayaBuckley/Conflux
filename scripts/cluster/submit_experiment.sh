#!/usr/bin/env sh
set -eu
if [ "$#" -ne 2 ]; then
  echo "usage: submit_experiment.sh MANIFEST OUTPUT" >&2
  exit 2
fi
python scripts/cluster_jobs.py "$1" "$2"
echo "Jobs were materialised only; submit them explicitly to the discovered scheduler."
