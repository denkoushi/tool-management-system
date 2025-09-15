#!/usr/bin/env bash
# One-shot setup for a fresh Raspberry Pi (Bookworm).
# - Installs system deps, pcscd, Python venv, requirements
# - Starts Postgres via Docker Compose
# Usage: bash scripts/setup_pi.sh
set -euo pipefail

if [[ "${EUID}" -eq 0 ]]; then
  echo "[ERR ] Do not run as root. Run as normal user." >&2
  exit 1
fi

log() { echo -e "\033[1;32m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR ]\033[0m $*" >&2; }

ROOT_DIR=$(cd -- "$(dirname -- "$0")/.."; pwd)
cd "$ROOT_DIR"

log "Update apt packages"
sudo apt update -y
sudo apt upgrade -y

log "Install base packages"
sudo apt install -y python3-venv python3-pip python3-dev git curl \
  pcscd pcsc-tools libccid libpcsclite1 libpcsclite-dev opensc swig

log "Enable pcscd"
sudo systemctl enable --now pcscd

log "Create Python venv"
python3 -m venv venv
source venv/bin/activate

log "Install Python requirements"
pip install --upgrade pip
pip install -r requirements.txt || {
  warn "Retry pyscard install with --break-system-packages";
  pip install --break-system-packages pyscard;
}

log "Install Docker Engine (if missing)"
if ! command -v docker >/dev/null 2>&1; then
  sudo bash scripts/install_docker.sh || {
    warn "Docker install script failed. Install manually later.";
  }
fi

log "Start Postgres via Docker Compose"
if command -v docker >/dev/null 2>&1; then
  docker compose up -d
else
  warn "Docker not available; skip DB startup."
fi

log "Done. Start app with:"
echo "  source venv/bin/activate && python -m app.main"

