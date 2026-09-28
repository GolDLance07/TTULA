FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install Kali baseline tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    nmap \
    curl \
    git \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Legba binary
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        curl -sSL "https://github.com/evilsocket/legba/releases/latest/download/legba-linux-amd64.tar.gz" | tar -xz -C /usr/local/bin legba; \
    fi || true

# Setup workspace
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY ttula /app/ttula

# Install dependencies and TTULA into system environment
RUN pip install --break-system-packages --no-cache-dir \
    tookie-osint \
    uro \
    pyyaml \
    streamlit \
    && pip install --break-system-packages --no-cache-dir -e /app

EXPOSE 8501

ENTRYPOINT ["ttula", "ui", "--host", "0.0.0.0", "--port", "8501"]
