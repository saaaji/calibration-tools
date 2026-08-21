FROM debian:trixie-slim
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# mrcal
RUN echo "deb [trusted=yes] http://mrcal.secretsauce.net/packages/trixie/public/ trixie main" \
    > /etc/apt/sources.list.d/mrcal.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    mrcal \
    python3-mrcal \
    python3-mrgingham \
    && rm -rf /var/lib/apt/lists/*

# rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

CMD ["sleep", "infinity"]