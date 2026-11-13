FROM docker.io/library/ubuntu:26.04@sha256:065aa8626841f16057b78b027b464cd59c4fac36c204c72dcbf48d66f5fa8a96

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        samtools=1.22.1-1 mosdepth=0.3.11+ds-3 multiqc=1.21+dfsg-3 \
    && samtools --version \
    && mosdepth --version \
    && multiqc --version \
    && rm -rf /var/lib/apt/lists/*
