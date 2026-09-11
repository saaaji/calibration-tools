FROM debian:trixie-slim
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    cmake \
    ninja-build \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pydantic \
    pybind11-dev \
    libeigen3-dev \
    libopencv-dev \
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

# build libraries
COPY . .

RUN cmake -S . -B build -G Ninja \
 && cmake --build build -j \
 && cmake --install build \
 && ldconfig

CMD ["sleep", "infinity"]