FROM docker.io/library/eclipse-temurin:25.0.5_8-jre-noble@sha256:e3b6f7887a50f20d8f07abf279d8a81a5953fb398a9555bd9edd56b9bd15968c

RUN apt-get update \
    && apt-get install -y --no-install-recommends bcftools curl unzip \
    && mkdir -p /opt/haplogrep/trees/phylotree-fu-rcrs/1.3 \
    && curl -fsSL https://github.com/genepi/haplogrep3/releases/download/v3.3.2/haplogrep3-3.3.2-linux.tar.gz -o /tmp/haplogrep.tar.gz \
    && echo '957165143ddd7d6ad9f34cc3af56b784fc236081e031c99bea4a574d6ad70959  /tmp/haplogrep.tar.gz' | sha256sum --check --strict \
    && tar -xzf /tmp/haplogrep.tar.gz -C /opt/haplogrep \
    && curl -fsSL https://github.com/genepi/phylotree-fu-rcrs/releases/download/1.3/phylotree-fu-rcrs-1.3.zip -o /tmp/tree.zip \
    && echo 'ffb1d30c57b2d72d4451785f6a1c7c9ecce273971d2fafaa01f0ca94c566ced1  /tmp/tree.zip' | sha256sum --check --strict \
    && unzip -q /tmp/tree.zip -d /opt/haplogrep/trees/phylotree-fu-rcrs/1.3 \
    && printf '%s\n' 'port: 7001' 'workspace: /output' 'repositories: []' 'phylotrees:' '  - trees/phylotree-fu-rcrs/1.3/tree.yaml' 'examples: []' > /opt/haplogrep/haplogrep3.yaml \
    && (cd /opt/haplogrep && java -jar haplogrep3.jar trees > /tmp/trees.txt) \
    && grep -F 'phylotree-fu-rcrs@1.3' /tmp/trees.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/haplogrep.tar.gz /tmp/tree.zip /tmp/trees.txt
