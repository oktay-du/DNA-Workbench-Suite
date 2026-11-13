FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl unzip openjdk-21-jre-headless samtools=1.21-1 \
    && mkdir -p /opt/gatk \
    && curl -fsSL https://github.com/broadinstitute/gatk/releases/download/4.7.0.0/gatk-4.7.0.0.zip -o /tmp/gatk.zip \
    && echo 'd093d2693b1626361a413ca59d6d4a0bf968717f280a8fd9ce060b25eb2ed1db  /tmp/gatk.zip' | sha256sum --check --strict \
    && unzip -j /tmp/gatk.zip '*/gatk-package-4.7.0.0-local.jar' -d /opt/gatk \
    && java -jar /opt/gatk/gatk-package-4.7.0.0-local.jar --version \
    && rm -rf /var/lib/apt/lists/* /tmp/gatk.zip
