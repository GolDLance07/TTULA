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

# Install Kali tools (legba, tookie-osint, uro)
RUN apt-get update && (apt-get install -y --no-install-recommends legba tookie-osint uro || true) && rm -rf /var/lib/apt/lists/*

# Setup workspace
WORKDIR /app
COPY pyproject.toml README.md /app/
COPY ttula /app/ttula

# Install dependencies and TTULA into system environment
RUN pip install --break-system-packages --no-cache-dir \
    uro \
    pyyaml \
    streamlit \
    && pip install --break-system-packages --no-cache-dir -e /app

EXPOSE 8501

ENTRYPOINT ["ttula", "ui", "--host", "0.0.0.0", "--port", "8501"]
