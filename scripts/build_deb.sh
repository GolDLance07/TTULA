#!/bin/bash
set -euo pipefail

echo "====================================================="
echo "  TTULA - Debian Package (.deb) Build Script"
echo "====================================================="

# Ensure build tools are installed
if ! command -v dpkg-buildpackage &>/dev/null; then
    echo "[!] dpkg-buildpackage not found. Please run:"
    echo "    sudo apt update && sudo apt install -y build-essential debhelper dh-python python3-all python3-setuptools"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

echo "[*] Building binary package (architecture independent)..."
dpkg-buildpackage -us -uc -b

echo "[+] Build complete! Generated package files located in parent directory:"
ls -la ../ttula_*.deb || true
