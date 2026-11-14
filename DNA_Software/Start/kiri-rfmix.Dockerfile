FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2 AS build

COPY rfmix.tar.gz /tmp/rfmix.tar.gz
COPY rfmix-march.sh /tmp/rfmix-march.sh
RUN echo '1ca6db8b3e7abb64c7b0e3af44ade69244cf813468c24d687ea26f88a70a4f17  /tmp/rfmix.tar.gz' | sha256sum -c - \
    && apt-get update \
    && apt-get install -y --no-install-recommends build-essential autoconf automake libtool zlib1g-dev \
    && mkdir /src \
    && tar -xzf /tmp/rfmix.tar.gz --strip-components=1 -C /src \
    && cd /src && sh /tmp/rfmix-march.sh \
    && autoreconf --force --install \
    && ./configure --prefix=/usr/local && make -j2 && make install

FROM docker.io/library/debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

COPY --from=build /usr/local/bin/rfmix /usr/local/bin/rfmix
COPY RFMIX-LICENSE.txt /usr/local/share/doc/rfmix/LICENSE.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools=1.21-1 libstdc++6 libgomp1 zlib1g \
    && rm -rf /var/lib/apt/lists/*
