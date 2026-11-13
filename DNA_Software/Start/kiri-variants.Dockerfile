FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN apt-get update \
    && apt-get install -y --no-install-recommends samtools=1.21-1 \
    && python -m pip install --no-cache-dir --only-binary=:all: \
        pysam==0.24.1 snps==2.12.1 numpy==2.5.4 pandas==3.1.1 atomicwrites==1.4.1 \
    && python -m pip check \
    && rm -rf /var/lib/apt/lists/*
