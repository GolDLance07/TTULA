#!/usr/bin/env bash
# ==============================================================================
# TTULA - Kali Linux Native Toolchain Installer
# Automated bootstrap installer turning TTULA into a system-wide Kali tool.
# ==============================================================================

set -euo pipefail

# Visual colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
cat << "EOF"
  _______ _______ _    _ _               
 |__   __|__   __| |  | | |        /\    
    | |     | |  | |  | | |       /  \   
    | |     | |  | |  | | |      / /\ \  
    | |     | |  | |__| | |____ / ____ \ 
    |_|     |_|   \____/|______/_/    \_\
                                         
   Security Operations Orchestration Tool
EOF
echo -e "${NC}"

# Check for root / sudo
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}[!] This installer must be run as root (or with sudo).${NC}"
    echo -e "    Usage: ${BOLD}sudo ./install.sh${NC}"
    exit 1
fi

echo -e "${CYAN}[*] Step 1: Installing system dependencies via apt...${NC}"
set +e
apt-get update -qq 2>/dev/null
APT_STATUS=$?
if [ $APT_STATUS -ne 0 ]; then
    echo -e "${YELLOW}[!] Notice: Kali mirror index mismatch or stale cache detected.${NC}"
    echo -e "${YELLOW}[*] Flushing /var/lib/apt/lists and retrying with clean state...${NC}"
    rm -rf /var/lib/apt/lists/*
    apt-get clean
    apt-get update -qq --fix-missing || true
fi
set -e

DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing -qq \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    nmap \
    build-essential \
    ca-certificates


# Step 2: Ensure Tailscale is installed
echo -e "${CYAN}[*] Step 2: Checking Tailscale...${NC}"
if ! command -v tailscale &>/dev/null; then
    echo -e "${YELLOW}[*] Installing Tailscale mesh client...${NC}"
    curl -fsSL https://tailscale.com/install.sh | sh
    systemctl enable --now tailscaled
else
    echo -e "${GREEN}[+] Tailscale is already installed.${NC}"
fi

# Step 3: Ensure Legba is installed
echo -e "${CYAN}[*] Step 3: Checking Legba...${NC}"
if ! command -v legba &>/dev/null; then
    echo -e "${YELLOW}[*] Attempting to install Legba via apt (standard on Kali Linux)...${NC}"
    if apt-get install -y -qq legba 2>/dev/null; then
        echo -e "${GREEN}[+] Legba installed via apt.${NC}"
    else
        echo -e "${YELLOW}[*] Legba not in apt cache; attempting GitHub release download...${NC}"
        TMP_DIR=$(mktemp -d)
        set +e
        # Query latest release asset from GitHub API
        LEGBA_URL=$(curl -sSL "https://api.github.com/repos/evilsocket/legba/releases/latest" 2>/dev/null | grep -o 'https://[^"]*linux[^"]*amd64[^"]*\.tar\.gz' | head -n 1)
        if [ -n "$LEGBA_URL" ]; then
            if curl -sSL --fail "$LEGBA_URL" -o "$TMP_DIR/legba.tar.gz" 2>/dev/null; then
                if tar -xzf "$TMP_DIR/legba.tar.gz" -C "$TMP_DIR" 2>/dev/null; then
                    LEGBA_BIN=$(find "$TMP_DIR" -type f -name legba -perm /111 2>/dev/null | head -n 1)
                    if [ -n "$LEGBA_BIN" ]; then
                        install -m 755 "$LEGBA_BIN" /usr/local/bin/legba
                        echo -e "${GREEN}[+] Legba installed to /usr/local/bin/legba${NC}"
                    fi
                fi
            fi
        fi
        set -e
        rm -rf "$TMP_DIR"

        if ! command -v legba &>/dev/null; then
            echo -e "${YELLOW}[!] Note: Legba binary could not be auto-downloaded.${NC}"
            echo -e "    You can install it anytime with: ${BOLD}sudo apt install legba${NC} or ${BOLD}cargo install legba${NC}"
        fi
    fi
else
    echo -e "${GREEN}[+] Legba is already installed.${NC}"
fi

# Step 3b: Ensure Tookie OSINT is installed
echo -e "${CYAN}[*] Step 3b: Checking Tookie OSINT...${NC}"
if ! command -v tookie-osint &>/dev/null && ! command -v tookie &>/dev/null; then
    echo -e "${YELLOW}[*] Attempting to install tookie-osint via apt (Kali repository)...${NC}"
    if apt-get install -y -qq tookie-osint 2>/dev/null; then
        echo -e "${GREEN}[+] tookie-osint installed via apt.${NC}"
    else
        echo -e "${YELLOW}[*] Installing tookie-osint from GitHub repository...${NC}"
        if git clone --depth 1 https://github.com/Alfredredbird/tookie-osint.git /opt/tookie-osint 2>/dev/null || (cd /opt/tookie-osint 2>/dev/null && git pull -q); then
            cat << 'EOF' > /usr/local/bin/tookie-osint
#!/usr/bin/env bash
python3 /opt/tookie-osint/tookie-osint.py "$@"
EOF
            chmod +x /usr/local/bin/tookie-osint
            echo -e "${GREEN}[+] tookie-osint installed to /usr/local/bin/tookie-osint${NC}"
        fi
    fi
else
    echo -e "${GREEN}[+] tookie-osint is already installed.${NC}"
fi

# Step 4: Setup isolated /opt/ttula environment (PEP 668 compliant)
echo -e "${CYAN}[*] Step 4: Setting up /opt/ttula application directory...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/ttula"

mkdir -p "$INSTALL_DIR"
rm -rf "$INSTALL_DIR/ttula"
find "$INSTALL_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
cp -r "$SCRIPT_DIR/ttula" "$INSTALL_DIR/ttula"
cp "$SCRIPT_DIR/pyproject.toml" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/README.md" "$INSTALL_DIR/"

# Copy Arsenal-NG cheat-files directory if present
if [ -d "$SCRIPT_DIR/cheat-files" ]; then
    echo -e "${CYAN}[*] Copying Arsenal-NG cheat playbooks to $INSTALL_DIR/cheat-files...${NC}"
    rm -rf "$INSTALL_DIR/cheat-files"
    cp -r "$SCRIPT_DIR/cheat-files" "$INSTALL_DIR/cheat-files"
fi

# Create dedicated virtual environment
if [ ! -d "$INSTALL_DIR/venv" ]; then
    echo -e "${YELLOW}[*] Creating Python virtual environment in $INSTALL_DIR/venv...${NC}"
    python3 -m venv "$INSTALL_DIR/venv"
fi

# Install dependencies and TTULA package
echo -e "${CYAN}[*] Installing TTULA and pipeline tools (Textual TUI, Uro, PyYAML, Streamlit)...${NC}"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install uro pyyaml textual streamlit -q
"$INSTALL_DIR/venv/bin/pip" install -e "$INSTALL_DIR" --no-deps --force-reinstall -q

# Step 5: Global executable symlinks (CLI and TUI)
echo -e "${CYAN}[*] Step 5: Registering global 'ttula' and 'ttula-tui' commands...${NC}"
cat << 'EOF' > /usr/local/bin/ttula
#!/usr/bin/env bash
exec /opt/ttula/venv/bin/ttula "$@"
EOF
chmod +x /usr/local/bin/ttula

cat << 'EOF' > /usr/local/bin/ttula-tui
#!/usr/bin/env bash
exec /opt/ttula/venv/bin/ttula tui "$@"
EOF
chmod +x /usr/local/bin/ttula-tui


# Step 6: Kali Linux Application Menu Entry
echo -e "${CYAN}[*] Step 6: Installing Kali Desktop Menu entry...${NC}"
if [ -d "/usr/share/applications" ]; then
    cp "$SCRIPT_DIR/debian/ttula.desktop" /usr/share/applications/ttula.desktop
    chmod 644 /usr/share/applications/ttula.desktop
fi

# Step 7: Systemd Service Registration (Optional)
echo -e "${CYAN}[*] Step 7: Configuring systemd service...${NC}"
if [ -d "/etc/systemd/system" ] && [ -f "$SCRIPT_DIR/systemd/ttula.service" ]; then
    cp "$SCRIPT_DIR/systemd/ttula.service" /etc/systemd/system/ttula.service
    systemctl daemon-reload
    echo -e "${GREEN}[+] Systemd service registered (/etc/systemd/system/ttula.service).${NC}"
fi

echo -e "\n${GREEN}${BOLD}=====================================================${NC}"
echo -e "${GREEN}${BOLD}    TTULA HAS BEEN SUCCESSFULLY INSTALLED ON KALI!${NC}"
echo -e "${GREEN}${BOLD}=====================================================${NC}"

echo -e "\n${BOLD}System Status Diagnostic:${NC}"
/usr/local/bin/ttula doctor || true

echo -e "\n${BOLD}Quick Start:${NC}"
echo -e "  - Open the Web Console:    ${CYAN}ttula ui${NC}"
echo -e "  - Search Arsenal Cheats:   ${CYAN}ttula cheats nmap${NC}"
echo -e "  - Inspect Tailscale Mesh:  ${CYAN}ttula tailscale${NC}"
echo -e "  - Run Full OSINT Pipeline: ${CYAN}ttula pipeline <username>${NC}"
echo -e "  - Run as Background Service: ${CYAN}sudo systemctl start ttula${NC}"
echo ""
