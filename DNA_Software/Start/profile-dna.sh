# shellcheck shell=bash
export PATH=/opt/dna/envs/analysis/bin:/opt/dna/bin:$PATH
export PIP_CACHE_DIR=/opt/dna/cache/pip
export NXF_HOME=/opt/dna/cache/nextflow
export NXF_ASSETS=/opt/dna/sources/nextflow-assets
export NXF_VER=26.10.5
export DOCKER_HOST=unix:///run/docker-dna.sock
export R_LIBS_USER=/opt/dna/R/library
if [ -f /opt/dna/portable-env.sh ]; then source /opt/dna/portable-env.sh; fi
