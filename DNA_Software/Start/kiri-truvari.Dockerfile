FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b AS build

COPY truvari-linux.txt /tmp/truvari-linux.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential zlib1g-dev \
    && python -m pip wheel --no-deps -r /tmp/truvari-linux.txt -w /wheels

FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

COPY truvari-linux.txt /tmp/truvari-linux.txt
COPY --from=build /wheels /tmp/wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools=1.21-1 samtools=1.21-1 \
    && python -m pip install --no-cache-dir --no-index --find-links /tmp/wheels -r /tmp/truvari-linux.txt \
    && python -m pip check \
    && truvari bench --help \
    && rm -rf /var/lib/apt/lists/* /tmp/wheels /tmp/truvari-linux.txt
