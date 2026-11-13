FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools=1.21-1 \
    && bcftools --version \
    && rm -rf /var/lib/apt/lists/*

LABEL org.dnaworkbench.bcftools-recipe="debian-trixie-1.21-1"
