#!/usr/bin/env bash
set -euo pipefail
export DOCKER_HOST=unix:///run/docker-dna.sock
if /usr/bin/docker info >/dev/null 2>&1; then exit 0; fi
mkdir -p /opt/dna/docker /run/dna-docker
nohup /usr/bin/dockerd --data-root=/opt/dna/docker --exec-root=/run/dna-docker --pidfile=/run/dna-docker.pid --host=unix:///run/docker-dna.sock > /opt/dna/ssd/DNA_Software/Logs/docker-dna.log 2>&1 < /dev/null &
for _ in $(seq 1 45); do
 if /usr/bin/docker info >/dev/null 2>&1; then exit 0; fi
 sleep 2
done
tail -n 35 /opt/dna/ssd/DNA_Software/Logs/docker-dna.log
exit 1
