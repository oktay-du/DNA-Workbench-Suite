#!/usr/bin/env bash
set -euo pipefail
export DOCKER_HOST=unix:///run/docker-dna.sock
unset DOCKER_CONTEXT DOCKER_TLS_VERIFY DOCKER_CERT_PATH
if [ ! -x /usr/bin/docker ] || [ ! -x /usr/bin/dockerd ]; then
    printf '%s\n' 'Install Docker through the tool library before starting the workspace engine.' >&2
    exit 1
fi
log=/opt/dna/ssd/DNA_Software/Logs/docker-dna.log
mkdir -p /opt/dna/docker /run/dna-docker "$(dirname "$log")"
exec 9>/run/dna-docker/start.lock
flock 9
if ! /usr/bin/docker info >/dev/null 2>&1; then
    nohup /usr/bin/dockerd --data-root=/opt/dna/docker --exec-root=/run/dna-docker --pidfile=/run/dna-docker.pid --host=unix:///run/docker-dna.sock > "$log" 2>&1 < /dev/null 9>&- &
fi
for _ in $(seq 1 45); do
    if /usr/bin/docker info >/dev/null 2>&1; then
        if runuser -u dna -- /usr/bin/docker info >/dev/null 2>&1; then exit 0; fi
        printf '%s\n' 'The workspace account cannot access the workspace Docker socket. Reinstall Docker through the tool library.' >&2
        exit 1
    fi
    sleep 2
done
tail -n 35 "$log"
exit 1
