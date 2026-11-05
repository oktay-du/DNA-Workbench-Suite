#!/usr/bin/env bash
set -euo pipefail
ssd="${1:?App mountpoint required}"
mkdir -p /opt/dna/cache/tmp /opt/dna/cache/apt
export TMPDIR=/opt/dna/cache/tmp
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl python3-venv python3-pip
if ! id dna >/dev/null 2>&1; then useradd -m -s /bin/bash dna; fi
mkdir -p /opt/dna/bin /opt/dna/tools /opt/dna/cache /opt/dna/envs
if [ ! -x /opt/dna/envs/analysis/bin/python ]; then python3 -m venv /opt/dna/envs/analysis; fi
cat >/etc/wsl.conf <<'EOF'
[user]
default=dna
[automount]
enabled=true
options="metadata,umask=022"
EOF
cat >/etc/profile.d/dna-ssd.sh <<'EOF'
export PATH=/opt/dna/envs/analysis/bin:/opt/dna/bin:$PATH
export PIP_CACHE_DIR=/opt/dna/cache/pip
EOF
chown -R dna:dna /opt/dna
python3 "$ssd/DNA_Software/Start/relocate-linux.py" "$ssd"
printf '\nsource /opt/dna/portable-env.sh\n' >>/etc/profile.d/dna-ssd.sh
printf 'Base setup finished at %s\n' "$ssd"
