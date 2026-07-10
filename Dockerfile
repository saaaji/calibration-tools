# BUILDER
FROM debian:trixie-slim AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    build-essential \
    cmake \
    ninja-build \
    python3-dev \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# apriltag
WORKDIR /build/apriltag
RUN git clone --depth=1 --branch v3.4.5 https://github.com/AprilRobotics/apriltag.git .
COPY image-patches/tag36h11_kalibr.patch .
RUN git apply tag36h11_kalibr.patch && \
    cmake -B build -GNinja -DCMAKE_BUILD_TYPE=Release && \
    cmake --build build --target install

# BASE
FROM debian:trixie-slim AS base
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive

# python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# copy apriltag from builder
COPY --from=builder /usr/local/lib/libapriltag.so.3.4.5 /usr/local/lib/
RUN --mount=type=bind,from=builder,source=/usr/local/lib/python3.13/site-packages,target=/builder-site-packages \
    cp /builder-site-packages/apriltag*.so $(python3 -c "import sysconfig; print(sysconfig.get_path('platlib'))")
RUN ln -s /usr/local/lib/libapriltag.so.3.4.5 /usr/local/lib/libapriltag.so.3 && \
    ln -s /usr/local/lib/libapriltag.so.3 /usr/local/lib/libapriltag.so && \
    ldconfig

# mrcal
RUN echo "deb [trusted=yes] http://mrcal.secretsauce.net/packages/trixie/public/ trixie main" \
    > /etc/apt/sources.list.d/mrcal.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    mrcal \
    python3-mrcal \
    python3-mrgingham \
    && rm -rf /var/lib/apt/lists/*

# pip requirements
COPY requirements.txt .
RUN pip install --break-system-packages --ignore-installed \
    -r requirements.txt

COPY . .
RUN pip install -e . --break-system-packages

# TARGETS
FROM base AS dev
CMD ["sleep", "infinity"]