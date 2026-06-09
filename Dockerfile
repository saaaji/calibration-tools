# BASE
FROM debian:trixie-slim AS base
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive

# python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# mrcal
RUN echo "deb [trusted=yes] http://mrcal.secretsauce.net/packages/trixie/public/ trixie main" \
    > /etc/apt/sources.list.d/mrcal.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    mrcal \
    libmrcal-dev \
    python3-mrcal \
    && rm -rf /var/lib/apt/lists/*

# pip requirements
COPY requirements.txt .
RUN pip install --break-system-packages --ignore-installed \
    -r requirements.txt

COPY . .
RUN pip install -e . --break-system-packages

# BUILD
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    cmake \ 
    pkg-config \
    ninja-build \
    mawk \
    perl \
    mrbuild \
    libopencv-dev \ 
    libboost-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# apriltag
WORKDIR /build/apriltag
RUN git clone --depth=1 https://github.com/AprilRobotics/apriltag.git .

COPY image-patches/tag36h11_kalibr.patch .
RUN git apply tag36h11_kalibr.patch

RUN cmake -B build -DCMAKE_BUILD_TYPE=Release
RUN cmake --build build --target install

# mrgingham
WORKDIR /build/mrgingham
RUN git clone --depth=1 https://github.com/dkogan/mrgingham.git .

RUN make mrgingham$(python3-config --extension-suffix)
RUN PLATLIB=$(python3 -c "import sysconfig; print(sysconfig.get_paths()['platlib'])") && \
    cp mrgingham*.so $PLATLIB/

RUN ldconfig

# TARGETS
FROM base AS dev
CMD ["sleep", "infinity"]

FROM base AS cli
ENTRYPOINT ["calib"]