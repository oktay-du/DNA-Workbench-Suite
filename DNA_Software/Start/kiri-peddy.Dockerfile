FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

COPY peddy-linux.txt /tmp/peddy-linux.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools=1.21-1 \
    && grep -v '^peddy==' /tmp/peddy-linux.txt > /tmp/peddy-deps.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/peddy-deps.txt \
    && printf '%s\n' 'peddy==0.4.8 --hash=sha256:1d998f0e387a15c7e270ced4bba8c19cc164c916fdcf397e90215cc9fc6bf04f' > /tmp/peddy-source.txt \
    && python -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/peddy-source.txt \
    && python -m pip check \
    && bcftools --version \
    && peddy --help \
    && rm -rf /var/lib/apt/lists/* /tmp/peddy-linux.txt /tmp/peddy-deps.txt /tmp/peddy-source.txt
