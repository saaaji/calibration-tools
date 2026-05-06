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

# targets
FROM base AS dev
CMD ["sleep", "infinity"]

FROM base AS cli
ENTRYPOINT ["calib"]