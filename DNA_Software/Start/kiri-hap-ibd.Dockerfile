FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2 AS build

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl openjdk-21-jdk-headless \
    && mkdir -p /build/source /build/classes \
    && curl --fail --silent --show-error --location \
        https://codeload.github.com/browning-lab/hap-ibd/tar.gz/a3fdd2d6294903387ee29d2f67ce6260593b681f \
        --output /build/source.tar.gz \
    && echo 'c3719bee47dd3a60349a10becb12531587a91463a88ba9abe3356a58880fa88b  /build/source.tar.gz' | sha256sum --check --strict \
    && tar -xzf /build/source.tar.gz --strip-components=1 -C /build/source \
    && find /build/source/src -name '*.java' -print > /build/sources.txt \
    && javac --release 8 -d /build/classes @/build/sources.txt \
    && jar cfe /build/hap-ibd.jar hapibd.HapIbdMain -C /build/classes .

FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-21-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /build/hap-ibd.jar /opt/hap-ibd/hap-ibd.jar
COPY --from=build /build/source/LICENSE-2.0.txt /opt/hap-ibd/LICENSE-2.0.txt
RUN java -jar /opt/hap-ibd/hap-ibd.jar
