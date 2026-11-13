FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl openjdk-21-jre-headless \
    && mkdir -p /opt/beagle \
    && curl --fail --silent --show-error --location \
        https://faculty.washington.edu/browning/beagle/beagle.27Feb25.75f.jar \
        --output /opt/beagle/beagle.jar \
    && echo '7319f4af9638be05c18dcc1bfb8fb41a58a09293507ebf0d54617d0e40df5a70  /opt/beagle/beagle.jar' | sha256sum --check --strict \
    && java -jar /opt/beagle/beagle.jar help \
    && rm -rf /var/lib/apt/lists/*
