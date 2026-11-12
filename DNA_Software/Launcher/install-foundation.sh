#!/usr/bin/env bash
set -euo pipefail
ssd="${1:?App mountpoint required}"
mkdir -p /opt/dna/build /opt/dna/bin /opt/dna/tools /opt/dna/cache/pip
for tool in samtools bcftools; do
 if [ ! -x "/opt/dna/tools/$tool-1.25/bin/$tool" ]; then
  tar -xjf "$ssd/DNA_Software/Downloads/$tool-1.25.tar.bz2" -C /opt/dna/build
  cd "/opt/dna/build/$tool-1.25";./configure --prefix="/opt/dna/tools/$tool-1.25";make -j2;make install
 fi
 ln -sfn "/opt/dna/tools/$tool-1.25/bin/$tool" "/opt/dna/bin/$tool"
done
if [ "$(uname -m)" = aarch64 ]; then
 apt-get update
 apt-get install -y --no-install-recommends mosdepth
else
 install -m755 "$ssd/DNA_Software/Downloads/mosdepth" /opt/dna/bin/mosdepth
fi
export PIP_CACHE_DIR=/opt/dna/cache/pip
/opt/dna/envs/analysis/bin/python -m pip install --require-hashes -r "$ssd/DNA_Software/Launcher/Locks/foundation-linux.txt"
/opt/dna/envs/analysis/bin/python -m pip freeze > /opt/dna/cache/installed-python-lock.txt
chown -R dna:dna /opt/dna
