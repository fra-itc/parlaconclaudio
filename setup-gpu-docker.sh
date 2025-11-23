#!/usr/bin/env bash
# Setup NVIDIA Container Toolkit for Docker in WSL
# Run this script in WSL with: bash setup-gpu-docker.sh

set -e

echo "========================================="
echo "NVIDIA Container Toolkit Setup for Docker"
echo "========================================="
echo

# Step 1: Add NVIDIA repository
echo "[1/5] Adding NVIDIA GPG key..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

echo "[2/5] Adding NVIDIA repository..."
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Step 2: Install toolkit
echo "[3/5] Updating apt and installing nvidia-container-toolkit..."
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Step 3: Configure Docker
echo "[4/5] Configuring Docker runtime..."
sudo nvidia-ctk runtime configure --runtime=docker

# Step 4: Restart Docker
echo "[5/5] Restarting Docker..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart docker
    echo "Docker restarted with systemctl"
elif command -v service &> /dev/null; then
    sudo service docker restart
    echo "Docker restarted with service"
else
    echo "⚠️  Cannot restart Docker automatically."
    echo "   Please run: wsl --shutdown (from Windows PowerShell)"
    echo "   Then reopen WSL and run: sudo dockerd &"
fi

echo
echo "========================================="
echo "Testing GPU access in Docker..."
echo "========================================="
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

echo
echo "✅ GPU setup complete!"
echo "   You can now start the ML services."
