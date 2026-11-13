FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        plink1.9=1.90~b7.7-241022-2 plink2=2.00~a6.9-250129+dfsg-1+b1 bcftools=1.21-1 \
    && ln -s /usr/bin/plink1.9 /usr/local/bin/plink19 \
    && plink19 --version \
    && plink2 --version \
    && bcftools --version \
    && rm -rf /var/lib/apt/lists/*
