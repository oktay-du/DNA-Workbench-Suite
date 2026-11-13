FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools=1.21-1 curl \
    && curl -fsSL https://codeload.github.com/23andMe/yhaplo/tar.gz/a705c35023d3c7bd3bb2ff54ceebd5fd7b7ca3f6 -o /tmp/yhaplo.tar.gz \
    && echo 'ab3bb610f876759f99a108563c57e0d1da06a387f384a5d664a8b591cbe7e9f8  /tmp/yhaplo.tar.gz' | sha256sum --check --strict \
    && python -m pip install --no-cache-dir --only-binary=:all: numpy==2.5.4 pandas==3.1.1 pysam==0.24.1 pyyaml==6.0.3 rich==15.0.0 \
    && SETUPTOOLS_SCM_PRETEND_VERSION_FOR_YHAPLO=2.1.17 python -m pip install --no-cache-dir --no-deps /tmp/yhaplo.tar.gz \
    && python -m pip check \
    && yhaplo --help \
    && rm -rf /var/lib/apt/lists/* /tmp/yhaplo.tar.gz
