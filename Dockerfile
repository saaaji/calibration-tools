# NGC base image
FROM nvcr.io/nvidia/cuda:13.1.2-cudnn-devel-ubuntu22.04 AS base
WORKDIR /workspace
ENV DEBIAN_FRONTEND=noninteractive

# python (jammy pins 3.10 as default)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# MRCAL
RUN echo "deb [trusted=yes] http://mrcal.secretsauce.net/packages/jammy/public/ jammy main" \
    > /etc/apt/sources.list.d/mrcal.list

RUN apt-get update && apt-get install -y \
    mrcal \
    libmrcal-dev \
    python3-mrcal \
    && rm -rf /var/lib/apt/lists/*

# virtual environment with high priority
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# pip requirements
RUN pip install --upgrade pip
COPY constraints.txt .
COPY requirements.txt .
RUN pip install -c constraints.txt -r requirements.txt

# targets
FROM base AS dev
CMD ["sleep", "infinity"]

FROM base AS cli
COPY . .
