#!/bin/bash

# =============================================================================
# RTSTT - Setup Secrets Script
# =============================================================================
# This script helps you set up Docker secrets for local development.
# It will guide you through creating all necessary secret files.
#
# Usage:
#   bash scripts/setup-secrets.sh
#
# What it does:
#   1. Creates infrastructure/secrets/ directory if needed
#   2. Prompts for secret values (or generates them)
#   3. Creates secret files with proper permissions (600)
#   4. Validates the setup
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SECRETS_DIR="infrastructure/secrets"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if a secret file already exists
check_existing_secret() {
    local secret_file="$1"
    if [ -f "$secret_file" ]; then
        return 0  # exists
    else
        return 1  # doesn't exist
    fi
}

# Generate a random password
generate_password() {
    openssl rand -base64 32 | tr -d '\n'
}

# Generate a random hex key
generate_hex_key() {
    openssl rand -hex 32 | tr -d '\n'
}

# Create a secret file with proper permissions
create_secret_file() {
    local secret_file="$1"
    local secret_value="$2"

    echo -n "$secret_value" > "$secret_file"
    chmod 600 "$secret_file"
    print_success "Created: $secret_file"
}

# =============================================================================
# Main Setup
# =============================================================================

print_header "RTSTT Docker Secrets Setup"

echo
echo "This script will help you set up Docker secrets for local development."
echo "You'll be prompted for various secret values."
echo

# Create secrets directory if it doesn't exist
if [ ! -d "$SECRETS_DIR" ]; then
    print_info "Creating secrets directory..."
    mkdir -p "$SECRETS_DIR"
    print_success "Created $SECRETS_DIR"
fi

echo

# =============================================================================
# 1. HuggingFace Token
# =============================================================================

print_header "1. HuggingFace Token (HF_TOKEN)"
echo
echo "Used by: NLP service, Summary service"
echo "Purpose: Download models from HuggingFace Hub"
echo "Required: Optional (models can be cached locally)"
echo
echo "To obtain:"
echo "  1. Create account at https://huggingface.co"
echo "  2. Go to Settings → Access Tokens"
echo "  3. Create a token with 'Read' permissions"
echo

HF_TOKEN_FILE="$SECRETS_DIR/hf_token.txt"

if check_existing_secret "$HF_TOKEN_FILE"; then
    print_warning "HuggingFace token already exists at $HF_TOKEN_FILE"
    read -p "Do you want to replace it? (y/N): " replace
    if [[ ! "$replace" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing HuggingFace token"
        echo
    else
        read -p "Enter your HuggingFace token (or press Enter to skip): " hf_token
        if [ -n "$hf_token" ]; then
            create_secret_file "$HF_TOKEN_FILE" "$hf_token"
        else
            print_info "Skipped HuggingFace token"
        fi
        echo
    fi
else
    read -p "Enter your HuggingFace token (or press Enter to skip): " hf_token
    if [ -n "$hf_token" ]; then
        create_secret_file "$HF_TOKEN_FILE" "$hf_token"
    else
        print_info "Skipped HuggingFace token"
        print_warning "NLP and Summary services may fail to download models"
    fi
    echo
fi

# =============================================================================
# 2. Redis Password
# =============================================================================

print_header "2. Redis Password"
echo
echo "Used by: All services connecting to Redis"
echo "Purpose: Redis authentication"
echo "Required: Optional for development"
echo

REDIS_PASSWORD_FILE="$SECRETS_DIR/redis_password.txt"

if check_existing_secret "$REDIS_PASSWORD_FILE"; then
    print_warning "Redis password already exists at $REDIS_PASSWORD_FILE"
    read -p "Do you want to replace it? (y/N): " replace
    if [[ ! "$replace" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing Redis password"
        echo
    else
        read -p "Generate random password? (Y/n): " generate
        if [[ "$generate" =~ ^[Nn]$ ]]; then
            read -s -p "Enter Redis password: " redis_password
            echo
            create_secret_file "$REDIS_PASSWORD_FILE" "$redis_password"
        else
            redis_password=$(generate_password)
            create_secret_file "$REDIS_PASSWORD_FILE" "$redis_password"
            print_info "Generated random password"
        fi
        echo
    fi
else
    read -p "Generate random Redis password? (Y/n): " generate
    if [[ "$generate" =~ ^[Nn]$ ]]; then
        read -s -p "Enter Redis password (or press Enter to skip): " redis_password
        echo
        if [ -n "$redis_password" ]; then
            create_secret_file "$REDIS_PASSWORD_FILE" "$redis_password"
        else
            # Create empty password file for optional use
            create_secret_file "$REDIS_PASSWORD_FILE" ""
            print_info "Created empty Redis password (authentication disabled)"
        fi
    else
        redis_password=$(generate_password)
        create_secret_file "$REDIS_PASSWORD_FILE" "$redis_password"
        print_info "Generated random password"
    fi
    echo
fi

# =============================================================================
# 3. JWT Secret Key
# =============================================================================

print_header "3. JWT Secret Key"
echo
echo "Used by: Backend API (future authentication)"
echo "Purpose: Sign JWT tokens"
echo "Required: Not yet (planned feature)"
echo

JWT_SECRET_FILE="$SECRETS_DIR/jwt_secret.txt"

if check_existing_secret "$JWT_SECRET_FILE"; then
    print_warning "JWT secret already exists at $JWT_SECRET_FILE"
    read -p "Do you want to replace it? (y/N): " replace
    if [[ ! "$replace" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing JWT secret"
        echo
    else
        jwt_secret=$(generate_hex_key)
        create_secret_file "$JWT_SECRET_FILE" "$jwt_secret"
        print_info "Generated new JWT secret key"
        echo
    fi
else
    print_info "Generating JWT secret key..."
    jwt_secret=$(generate_hex_key)
    create_secret_file "$JWT_SECRET_FILE" "$jwt_secret"
    echo
fi

# =============================================================================
# 4. Grafana Admin Password
# =============================================================================

print_header "4. Grafana Admin Password"
echo
echo "Used by: Grafana monitoring service"
echo "Purpose: Admin panel login"
echo "Required: Yes"
echo "Access at: http://localhost:3001"
echo "Username: admin"
echo

GRAFANA_PASSWORD_FILE="$SECRETS_DIR/grafana_admin_password.txt"

if check_existing_secret "$GRAFANA_PASSWORD_FILE"; then
    print_warning "Grafana password already exists at $GRAFANA_PASSWORD_FILE"
    read -p "Do you want to replace it? (y/N): " replace
    if [[ ! "$replace" =~ ^[Yy]$ ]]; then
        print_info "Keeping existing Grafana password"
        echo
    else
        read -p "Generate random password? (Y/n): " generate
        if [[ "$generate" =~ ^[Nn]$ ]]; then
            read -s -p "Enter Grafana admin password: " grafana_password
            echo
            create_secret_file "$GRAFANA_PASSWORD_FILE" "$grafana_password"
        else
            grafana_password=$(generate_password)
            create_secret_file "$GRAFANA_PASSWORD_FILE" "$grafana_password"
            print_info "Generated random password: $grafana_password"
            print_warning "Save this password! You'll need it to login to Grafana"
        fi
        echo
    fi
else
    read -p "Generate random Grafana password? (Y/n): " generate
    if [[ "$generate" =~ ^[Nn]$ ]]; then
        read -s -p "Enter Grafana admin password: " grafana_password
        echo
        create_secret_file "$GRAFANA_PASSWORD_FILE" "$grafana_password"
    else
        grafana_password=$(generate_password)
        create_secret_file "$GRAFANA_PASSWORD_FILE" "$grafana_password"
        print_info "Generated random password: $grafana_password"
        print_warning "Save this password! You'll need it to login to Grafana"
    fi
    echo
fi

# =============================================================================
# Summary
# =============================================================================

print_header "Setup Complete!"
echo
print_success "All secret files created in $SECRETS_DIR"
echo
print_info "File permissions have been set to 600 (read/write for owner only)"
echo

# Verify permissions
echo "Verifying permissions:"
ls -la "$SECRETS_DIR"/*.txt 2>/dev/null || print_warning "No secret files found"
echo

# Next steps
print_header "Next Steps"
echo
echo "1. Start services with secrets:"
echo "   ${GREEN}docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d${NC}"
echo
echo "2. Verify secrets are mounted:"
echo "   ${GREEN}docker exec rtstt-summary-service cat /run/secrets/hf_token${NC}"
echo
echo "3. Check service logs:"
echo "   ${GREEN}docker-compose logs -f${NC}"
echo
echo "For more information, see:"
echo "  - infrastructure/secrets/README.md"
echo "  - SECRETS.md (when created)"
echo

print_success "Done!"
