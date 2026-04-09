#!/bin/bash
# ============================================================
# Experiment 8: EC2 Deployment Script
# ============================================================
# Run this on a fresh Ubuntu EC2 instance to set up the service.
# Usage: ssh into EC2 and run:
#   bash deploy_ec2.sh <DOCKERHUB_USERNAME>
#
# Prerequisites:
#   - EC2 instance with Ubuntu 22.04+
#   - Security group allows inbound on port 8000 (or 80)
#   - SSH access configured

set -euo pipefail

DOCKER_USER="${1:-your-dockerhub-username}"
IMAGE_NAME="${DOCKER_USER}/mlops-student-predictor:latest"
CONTAINER_NAME="mlops-predictor"

echo "========================================"
echo " MLOps Deployment — EC2 Setup"
echo "========================================"

# --------------------------------------------------
# 1. Install Docker (if not already installed)
# --------------------------------------------------
if ! command -v docker &> /dev/null; then
    echo "[1/5] Installing Docker..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo "[1/5] Docker installed successfully."
else
    echo "[1/5] Docker already installed: $(docker --version)"
fi

# --------------------------------------------------
# 2. Pull latest image
# --------------------------------------------------
echo "[2/5] Pulling image: ${IMAGE_NAME}"
sudo docker pull "${IMAGE_NAME}"

# --------------------------------------------------
# 3. Stop old container if exists
# --------------------------------------------------
echo "[3/5] Stopping existing container..."
sudo docker stop "${CONTAINER_NAME}" 2>/dev/null || true
sudo docker rm "${CONTAINER_NAME}" 2>/dev/null || true

# --------------------------------------------------
# 4. Run new container
# --------------------------------------------------
echo "[4/5] Starting container..."
sudo docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p 8000:8000 \
    -e API_KEY="${API_KEY:-mlops-demo-key-2024}" \
    -e JWT_SECRET_KEY="${JWT_SECRET_KEY:-change-this-in-production}" \
    "${IMAGE_NAME}"

# --------------------------------------------------
# 5. Verify
# --------------------------------------------------
echo "[5/5] Waiting for service to start..."
sleep 5

if curl -sf http://localhost:8000/health > /dev/null; then
    PUBLIC_IP=$(curl -sf http://checkip.amazonaws.com || echo "unknown")
    echo ""
    echo "========================================"
    echo " DEPLOYMENT SUCCESSFUL"
    echo "========================================"
    echo " API:    http://${PUBLIC_IP}:8000"
    echo " Docs:   http://${PUBLIC_IP}:8000/docs"
    echo " Health: http://${PUBLIC_IP}:8000/health"
    echo "========================================"
else
    echo "ERROR: Service health check failed!"
    sudo docker logs "${CONTAINER_NAME}"
    exit 1
fi
