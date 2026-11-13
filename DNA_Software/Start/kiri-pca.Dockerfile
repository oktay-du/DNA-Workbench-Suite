FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN --mount=type=secret,id=build_ca apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
        plink2=2.00~a6.9-250129+dfsg-1+b1 python3-pandas python3-venv \
    && python3 -m venv --system-site-packages /opt/pca \
    && printf '%s\n' \
        'plotly==6.5.2 --hash=sha256:91757653bd9c550eeea2fa2404dba6b85d1e366d54804c340b2c874e5a7eb4a4' \
        'narwhals==2.16.0 --hash=sha256:846f1fd7093ac69d63526e50732033e86c30ea0026a44d9b23991010c7d1485d' \
        'packaging==26.0 --hash=sha256:b36f1fef9334a5588b4166f8bcd26a14e521f2b55e6b9de3aaa80d3ff7a37529' \
        > /tmp/plotly-requirements.txt \
    && if [ -r /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi \
    && /opt/pca/bin/pip install --ignore-installed --no-deps --no-cache-dir \
        --only-binary=:all: --require-hashes -r /tmp/plotly-requirements.txt \
    && /opt/pca/bin/python -c 'import pandas, plotly.express; from plotly.offline import get_plotlyjs; assert get_plotlyjs()' \
    && plink2 --version \
    && rm -rf /tmp/plotly-requirements.txt /var/lib/apt/lists/*
