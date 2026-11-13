FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && printf '%s\n' 'whatshap==2.8 --hash=sha256:073ee7946d563e0125dbce58d9fc86a7a3fae377f27859dacb398309374b2cbe --hash=sha256:4a43afda9a47223da3feb0f39239998111053327a6bf905976e2c98a6848d90e' > /tmp/source.txt \
    && python -m pip wheel --no-deps --require-hashes -r /tmp/source.txt -w /wheels

FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

COPY whatshap-linux.txt /tmp/whatshap-linux.txt
COPY --from=build /wheels /tmp/wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends samtools=1.21-1 \
    && grep -v '^whatshap==' /tmp/whatshap-linux.txt > /tmp/deps.txt \
    && python -m pip install --no-cache-dir --only-binary=:all: -r /tmp/deps.txt \
    && python -m pip install --no-cache-dir --no-deps /tmp/wheels/*.whl \
    && python -m pip check \
    && whatshap --version \
    && rm -rf /var/lib/apt/lists/* /tmp/wheels /tmp/deps.txt /tmp/whatshap-linux.txt
