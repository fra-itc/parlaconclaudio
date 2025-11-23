#!/bin/bash
#
# WSL2 Setup Script for RTSTT
#
# Automated setup for running RTSTT in WSL2 environment.
# Installs dependencies, configures Docker, and prepares the environment.
#
# Usage:
#   ./scripts/setup-wsl2.sh [--skip-docker] [--skip-cuda]
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SKIP_DOCKER=false
SKIP_CUDA=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --skip-cuda)
            SKIP_CUDA=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-docker] [--skip-cuda]"
            echo ""
            echo "Options:"
            echo "  --skip-docker    Skip Docker installation"
            echo "  --skip-cuda      Skip CUDA/GPU setup"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_wsl2() {
    print_header "Checking WSL2 Environment"

    # Check if running in WSL
    if ! grep -qi microsoft /proc/version; then
        print_error "Not running in WSL"
        exit 1
    fi

    # Check if WSL2 (not WSL1)
    if grep -qi "microsoft-standard" /proc/version || grep -qi "wsl2" /proc/version; then
        print_success "Running in WSL2"
        return 0
    else
        print_error "Running in WSL1, please upgrade to WSL2"
        print_warning "Run: wsl --set-version <distro-name> 2"
        exit 1
    fi
}

check_os() {
    print_header "Checking Operating System"

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        print_success "OS: $NAME $VERSION"

        # Check if Ubuntu/Debian
        if [[ "$ID" != "ubuntu" ]] && [[ "$ID" != "debian" ]]; then
            print_warning "This script is optimized for Ubuntu/Debian"
            print_warning "You may need to adjust package manager commands"
        fi
    else
        print_warning "Cannot detect OS version"
    fi
}

update_system() {
    print_header "Updating System Packages"

    sudo apt-get update
    print_success "Package list updated"
}

install_dependencies() {
    print_header "Installing Dependencies"

    local packages=(
        "curl"
        "wget"
        "git"
        "build-essential"
        "ca-certificates"
        "gnupg"
        "lsb-release"
        "python3"
        "python3-pip"
        "python3-venv"
    )

    print_warning "Installing: ${packages[*]}"
    sudo apt-get install -y "${packages[@]}"
    print_success "Dependencies installed"
}

install_docker() {
    if [ "$SKIP_DOCKER" = true ]; then
        print_warning "Skipping Docker installation (--skip-docker)"
        return 0
    fi

    print_header "Installing Docker"

    # Check if Docker is already installed
    if command -v docker &> /dev/null; then
        print_success "Docker already installed: $(docker --version)"
        return 0
    fi

    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    # Set up the repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add user to docker group
    sudo usermod -aG docker $USER

    print_success "Docker installed: $(docker --version)"
    print_warning "You may need to log out and back in for group changes to take effect"
}

setup_docker_wsl2() {
    print_header "Configuring Docker for WSL2"

    # Create Docker daemon config for WSL2
    sudo mkdir -p /etc/docker

    if [ ! -f /etc/docker/daemon.json ]; then
        cat <<EOF | sudo tee /etc/docker/daemon.json
{
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
        print_success "Docker daemon configuration created"
    else
        print_success "Docker daemon configuration already exists"
    fi
}

check_cuda() {
    if [ "$SKIP_CUDA" = true ]; then
        print_warning "Skipping CUDA setup (--skip-cuda)"
        return 0
    fi

    print_header "Checking NVIDIA GPU Support"

    # Check if nvidia-smi is available in WSL2
    if command -v nvidia-smi &> /dev/null; then
        print_success "NVIDIA GPU detected:"
        nvidia-smi --query-gpu=name,driver_version --format=csv,noheader

        # Check if nvidia-docker2 is installed
        if dpkg -l | grep -q nvidia-docker2; then
            print_success "nvidia-docker2 already installed"
        else
            print_warning "nvidia-docker2 not installed"
            install_nvidia_docker
        fi
    else
        print_warning "No NVIDIA GPU detected or drivers not installed"
        print_warning "GPU acceleration will not be available"
        print_warning "Install NVIDIA drivers in Windows and ensure WSL2 GPU support is enabled"
    fi
}

install_nvidia_docker() {
    print_header "Installing NVIDIA Container Toolkit"

    # Add the package repositories
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
        sudo tee /etc/apt/sources.list.d/nvidia-docker.list

    sudo apt-get update
    sudo apt-get install -y nvidia-docker2

    # Restart Docker daemon
    sudo service docker restart

    print_success "NVIDIA Container Toolkit installed"
}

setup_python_environment() {
    print_header "Setting up Python Environment"

    cd "$PROJECT_ROOT"

    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_success "Virtual environment already exists"
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi

    # Activate and install requirements
    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Python requirements installed"
    else
        print_warning "No requirements.txt found"
    fi

    deactivate
}

setup_environment_variables() {
    print_header "Setting up Environment Variables"

    cd "$PROJECT_ROOT"

    # Check if .env file exists
    if [ -f ".env" ]; then
        print_success ".env file already exists"
    else
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please edit .env to configure your settings"
        else
            # Create basic .env file
            cat <<EOF > .env
# RTSTT Environment Configuration

# WebSocket URL for audio bridge
RTSTT_WEBSOCKET_URL=ws://localhost:8000/ws

# Audio configuration
RTSTT_SAMPLE_RATE=16000
RTSTT_CHANNELS=1
RTSTT_BUFFER_SECONDS=2.0

# Logging
RTSTT_LOG_LEVEL=INFO

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# GPU
CUDA_VISIBLE_DEVICES=0
EOF
            print_success "Created default .env file"
        fi
    fi
}

download_models() {
    print_header "Downloading ML Models"

    cd "$PROJECT_ROOT"

    if [ -f "scripts/download_models.py" ]; then
        python3 scripts/download_models.py
        print_success "Models downloaded"
    else
        print_warning "Model download script not found, skipping"
    fi
}

build_docker_images() {
    print_header "Building Docker Images"

    cd "$PROJECT_ROOT"

    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found"
        return 1
    fi

    # Build images
    docker-compose build
    print_success "Docker images built successfully"
}

verify_installation() {
    print_header "Verifying Installation"

    cd "$PROJECT_ROOT"

    # Check Docker
    if ! docker --version &> /dev/null; then
        print_error "Docker not working"
        return 1
    fi
    print_success "Docker: $(docker --version)"

    # Check Docker Compose
    if ! docker-compose --version &> /dev/null; then
        print_error "Docker Compose not working"
        return 1
    fi
    print_success "Docker Compose: $(docker-compose --version)"

    # Check Python
    if ! python3 --version &> /dev/null; then
        print_error "Python not working"
        return 1
    fi
    print_success "Python: $(python3 --version)"

    # Check GPU (if not skipped)
    if [ "$SKIP_CUDA" = false ]; then
        if nvidia-smi &> /dev/null; then
            print_success "GPU: Available"
        else
            print_warning "GPU: Not available"
        fi
    fi

    print_success "All verifications passed!"
}

print_next_steps() {
    print_header "Setup Complete!"

    echo -e "Next steps:\n"
    echo -e "1. ${GREEN}Configure secrets:${NC}"
    echo -e "   ./scripts/setup-secrets.sh\n"
    echo -e "2. ${GREEN}Start the services:${NC}"
    echo -e "   docker-compose up -d\n"
    echo -e "3. ${GREEN}Test the audio bridge:${NC}"
    echo -e "   python -m src.host_audio_bridge.main --driver mock --test-duration 10\n"
    echo -e "4. ${GREEN}Check service health:${NC}"
    echo -e "   docker-compose ps"
    echo -e "   python scripts/health_check.py\n"

    if [ "$SKIP_CUDA" = false ] && ! nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}Note:${NC} GPU acceleration is not available."
        echo -e "Install NVIDIA drivers in Windows and ensure WSL2 GPU support is enabled."
        echo -e "See: https://docs.nvidia.com/cuda/wsl-user-guide/index.html\n"
    fi

    if groups $USER | grep -q docker; then
        echo -e "${YELLOW}Note:${NC} Group changes detected."
        echo -e "You may need to log out and back in for Docker permissions to take effect.\n"
    fi
}

# Main execution
main() {
    print_header "RTSTT WSL2 Setup Script"
    echo "This script will set up your WSL2 environment for RTSTT"
    echo ""

    # Run setup steps
    check_wsl2
    check_os
    update_system
    install_dependencies
    install_docker
    setup_docker_wsl2
    check_cuda
    setup_python_environment
    setup_environment_variables
    download_models
    build_docker_images
    verify_installation
    print_next_steps

    print_success "WSL2 setup completed successfully!"
}

# Run main function
main
