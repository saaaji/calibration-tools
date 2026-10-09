FROM debian:forky-slim
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
    python3-scipy \
    python3-opencv \
    python3-sklearn \
    python3-skimage \
    python3-matplotlib \
    python3-pandas \
    python3-pydantic \
    python3-tqdm \
    pybind11-dev \
    libeigen3-dev \
    libopencv-dev \
    mrcal \
    python3-mrcal \
    python3-mrgingham \
    python3-ipykernel \
    python3-ipywidgets \
    && rm -rf /var/lib/apt/lists/*

# build libraries
COPY . .

RUN cmake -S . -B build -G Ninja \
 && cmake --build build -j \
 && cmake --install build \
 && ldconfig

# configure env
ENV PYTHONPATH=/workspace/src

CMD ["sleep", "infinity"]