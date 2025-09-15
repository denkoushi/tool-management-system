#!/usr/bin/env bash
# Raspberry Pi / Debian 系で Docker Engine + Compose v2 を導入するスクリプト
# 目的: 公式Dockerリポジトリを追加し、docker と docker compose を確実に使える状態にする
# 使い方: sudo bash scripts/install_docker.sh
set -euo pipefail

# ===== ユーティリティ =====
log() { echo -e "\033[1;32m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR ]\033[0m $*" >&2; }

if [[ $EUID -ne 0 ]]; then
  err "root権限で実行してください: sudo bash scripts/install_docker.sh"
  exit 1
fi

TARGET_USER="${SUDO_USER:-$USER}"
ARCH="$(dpkg --print-architecture)"  # 例: arm64
CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"  # 例: bookworm, bullseye

log "Target user       : ${TARGET_USER}"
log "Debian codename   : ${CODENAME}"
log "Architecture      : ${ARCH}"

# ===== 事前ツール =====
log "Install prerequisites (ca-certificates, curl, gnupg, lsb-release)..."
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release

# ===== GPGキー & repo 追加 =====
log "Add Docker official GPG key..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

log "Add Docker APT repository for Debian/${CODENAME}..."
cat >/etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian ${CODENAME} stable
EOF

apt-get update -y

# 競合し得る古いパッケージを先に除去（存在してもOK/なくてもOK）
log "Remove conflicting old packages if any..."
apt-get remove -y docker docker.io docker-doc docker-compose podman-docker containerd runc || true

# ===== Docker 本体 + Compose v2 =====
log "Install docker-ce, docker-ce-cli, containerd.io, buildx, compose plugin..."
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# ===== 起動 & 自動起動 =====
log "Enable and start docker service..."
systemctl enable --now docker

# ===== ユーザーを docker グループへ =====
if id -nG "${TARGET_USER}" | grep -qw docker; then
  log "User ${TARGET_USER} is already in 'docker' group."
else
  log "Add ${TARGET_USER} to 'docker' group..."
  usermod -aG docker "${TARGET_USER}"
  warn "グループ反映のため、${TARGET_USER} は一度ログアウト/ログイン（または再起動）してください。"
fi

# ===== 簡易テスト =====
log "Docker version:"
docker --version || true
log "Docker Compose version:"
docker compose version || true

log "Run hello-world (pull & run)..."
docker run --rm hello-world || {
  warn "hello-world 実行に失敗しました。ネットワークやプロキシ設定を確認してください。"
}

log "DONE. 次回からは 'docker' と 'docker compose' が利用できます。"
