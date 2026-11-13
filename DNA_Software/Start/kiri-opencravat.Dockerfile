FROM docker.io/library/python:3.12-slim-trixie@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

RUN printf '%s\n' 'open-cravat==3.2.4 --hash=sha256:1cf4a59aec23ee373397393b2b98448be3f257de26fc70985aacf5a8df6d5dcd' > /tmp/opencravat.txt \
    && python -m pip download --no-deps --require-hashes -r /tmp/opencravat.txt -d /tmp \
    && python -m pip install --no-cache-dir /tmp/open_cravat-3.2.4.tar.gz \
    && python -m pip check \
    && oc version \
    && rm /tmp/opencravat.txt /tmp/open_cravat-3.2.4.tar.gz
