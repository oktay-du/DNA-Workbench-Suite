FROM docker.io/library/eclipse-temurin:25.0.5_8-jre-noble@sha256:e3b6f7887a50f20d8f07abf279d8a81a5953fb398a9555bd9edd56b9bd15968c

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && mkdir -p /opt/pharmcat \
    && curl -fsSL https://github.com/PharmGKB/PharmCAT/releases/download/v3.4.0/pharmcat-3.4.0-all.jar -o /opt/pharmcat/pharmcat.jar \
    && echo '9317ef632bf6c9786ff0d9d455d4c9f6d2882ebd66ad7256b4ae958ddf454741  /opt/pharmcat/pharmcat.jar' | sha256sum --check --strict \
    && java -jar /opt/pharmcat/pharmcat.jar -h \
    && rm -rf /var/lib/apt/lists/*
