#!/usr/bin/env bash
set -euo pipefail
action="${1:-shell}"
ssd="${2:?SSD mountpoint required}"
export DNA_SSD_ROOT="$ssd"
export PATH="/opt/dna/envs/analysis/bin:/opt/dna/bin:$PATH"
export NXF_HOME=/opt/dna/cache/nextflow
export NXF_ASSETS=/opt/dna/sources/nextflow-assets
export PIP_CACHE_DIR=/opt/dna/cache/pip
cd "$ssd/Projects"
if [ "$action" = opencravat ]; then
  /opt/dna/envs/analysis/bin/python "$ssd/DNA_Software/Start/configure-opencravat.py" "$ssd"
  exec /opt/dna/envs/analysis/bin/oc gui --headless --port 8042
fi
exec bash
