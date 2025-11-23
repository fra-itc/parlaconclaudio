# Secrets Management Guide

Complete guide to secrets management in the RTSTT (Real-Time Speech-to-Text Transcription) project.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Secrets Inventory](#secrets-inventory)
4. [Local Development](#local-development)
5. [Production Deployment](#production-deployment)
6. [CI/CD Integration](#cicd-integration)
7. [Security Best Practices](#security-best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Architecture](#architecture)

---

## Overview

### Why Secrets Management?

Secrets (API tokens, passwords, keys) should never be:
- Hardcoded in source code
- Committed to version control
- Exposed in logs or error messages
- Shared through insecure channels

### Our Approach

**RTSTT uses a dual-strategy approach**:

| Environment | Method | Priority |
|-------------|--------|----------|
| **Local Development** | Docker Secrets → `.env` files | Flexibility + Security |
| **CI/CD Pipelines** | GitHub Secrets → Environment Variables | Encrypted + Auditable |
| **Production** | External Secret Manager (Vault, AWS Secrets Manager) | Enterprise-grade |

**Key Benefits**:
- ✅ Never commit secrets to Git
- ✅ Secrets isolated from containers
- ✅ Backward compatible with existing `.env` workflow
- ✅ Environment-specific configurations
- ✅ Automatic fallback mechanisms

---

## Quick Start

### 30-Second Setup

```bash
# 1. Clone repository (if not already)
git clone <repo-url> && cd RTSTT

# 2. Run setup script
bash scripts/setup-secrets.sh

# 3. Start services with secrets
docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d

# 4. Verify
docker exec rtstt-summary-service cat /run/secrets/hf_token
```

### Traditional Setup (Backward Compatible)

```bash
# Use .env files as before
cp .env.example .env
# Edit .env with your values
docker-compose up -d
```

---

## Secrets Inventory

### Required Secrets

| Secret | Services | Purpose | Required | How to Obtain |
|--------|----------|---------|----------|---------------|
| `HF_TOKEN` | NLP, Summary | Download ML models from HuggingFace | Optional* | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| `REDIS_PASSWORD` | All | Redis authentication | Optional (dev) | `openssl rand -base64 32` |
| `JWT_SECRET_KEY` | Backend API | Sign JWT auth tokens | Future | `openssl rand -hex 32` |
| `GRAFANA_ADMIN_PASSWORD` | Grafana | Monitoring dashboard | Yes | User-defined |

*Optional if models are pre-cached locally

### Secret Specifications

#### HF_TOKEN (HuggingFace Token)
```yaml
Format: hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Length: ~37 characters
Type: Read-only token
Used by:
  - src/core/nlp_insights/server.py
  - src/core/summary_generator/server.py
Models downloaded:
  - mistralai/Mistral-7B-Instruct-v0.2
  - google/flan-t5-base
  - all-MiniLM-L6-v2
  - pyannote/speaker-diarization-3.1
```

#### REDIS_PASSWORD
```yaml
Format: Base64 string (any length)
Recommendation: 32+ characters
Generator: openssl rand -base64 32
Used by: All services (redis_client.py)
Note: Empty string disables authentication (dev only!)
```

#### JWT_SECRET_KEY
```yaml
Format: Hexadecimal string
Length: 64 characters (256 bits)
Generator: openssl rand -hex 32
Used by: Backend API (future auth feature)
Rotation: Every 90 days recommended
```

#### GRAFANA_ADMIN_PASSWORD
```yaml
Format: Any strong password
Minimum: 12 characters
Default: admin (NEVER use in production!)
Access: http://localhost:3001
Username: admin
```

---

## Local Development

### Method 1: Docker Secrets (Recommended)

**Advantages**:
- Secrets not visible in `docker inspect`
- Proper separation of secrets from config
- Best practice for production-like environments

**Setup**:

1. **Run setup script** (interactive):
   ```bash
   bash scripts/setup-secrets.sh
   ```

2. **Or create manually**:
   ```bash
   # Create secret files
   echo "hf_YOUR_TOKEN" > infrastructure/secrets/hf_token.txt
   openssl rand -base64 32 > infrastructure/secrets/redis_password.txt
   openssl rand -hex 32 > infrastructure/secrets/jwt_secret.txt
   echo "MySecurePassword123!" > infrastructure/secrets/grafana_admin_password.txt

   # Set permissions (important!)
   chmod 600 infrastructure/secrets/*.txt
   ```

3. **Start with secrets**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
   ```

4. **Verify mounting**:
   ```bash
   # Check secrets are mounted
   docker exec rtstt-nlp-service ls -la /run/secrets/

   # View secret content (careful!)
   docker exec rtstt-nlp-service cat /run/secrets/hf_token
   ```

### Method 2: Environment Variables (Backward Compatible)

**Advantages**:
- Simple and familiar
- No additional docker-compose files
- Good for quick local testing

**Setup**:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env  # or your preferred editor

# Start normally
docker-compose up -d
```

### How Services Read Secrets

Services automatically check in this order:

1. **Docker secret file**: `/run/secrets/{secret_name}`
2. **Environment variable file**: Path from `{SECRET_NAME}_FILE`
3. **Environment variable**: `{SECRET_NAME}`
4. **Default value**: Specified in code

**Example** (from `src/shared/secrets.py`):
```python
from src.shared.secrets import get_hf_token

# Automatically tries:
# 1. /run/secrets/hf_token
# 2. File at $HF_TOKEN_FILE path
# 3. $HF_TOKEN environment variable
# 4. Returns None if not found
hf_token = get_hf_token(required=False)
```

---

## Production Deployment

### Deployment Checklist

- [ ] Use unique secrets per environment (never reuse dev secrets!)
- [ ] Store secrets in dedicated secret manager (Vault, AWS Secrets Manager, Azure Key Vault)
- [ ] Enable encryption at rest
- [ ] Restrict secret access via IAM/RBAC
- [ ] Enable audit logging
- [ ] Set up secret rotation schedule
- [ ] Document secret locations and owners
- [ ] Test secret rotation procedures
- [ ] Monitor for exposed secrets (GitHub, logs)
- [ ] Have incident response plan

### Docker Swarm Secrets

```bash
# Create Docker Swarm secrets
echo "hf_TOKEN_VALUE" | docker secret create hf_token -
echo "REDIS_PASSWORD" | docker secret create redis_password -

# Deploy stack
docker stack deploy -c docker-compose.yml -c docker-compose.secrets.yml rtstt
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: rtstt-secrets
type: Opaque
stringData:
  hf_token: "hf_YOUR_TOKEN"
  redis_password: "YOUR_REDIS_PASSWORD"
  jwt_secret: "YOUR_JWT_SECRET"
---
apiVersion: v1
kind: Pod
metadata:
  name: nlp-service
spec:
  containers:
  - name: nlp
    image: rtstt/nlp-service
    volumeMounts:
    - name: secrets
      mountPath: "/run/secrets"
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: rtstt-secrets
```

### External Secret Managers

#### AWS Secrets Manager
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

# Use in application
hf_token = get_secret('rtstt/prod/hf_token')
```

#### HashiCorp Vault
```bash
# Store secret
vault kv put secret/rtstt/prod/hf_token value="hf_TOKEN"

# Retrieve in application
vault kv get -field=value secret/rtstt/prod/hf_token
```

---

## CI/CD Integration

### GitHub Actions Setup

**1. Configure Repository Secrets**

Navigate to: `Settings → Secrets and variables → Actions → New repository secret`

Add these secrets:
- `HF_TOKEN`
- `REDIS_PASSWORD`
- `JWT_SECRET_KEY`
- `GRAFANA_ADMIN_PASSWORD`

**2. Use in Workflow**

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
          JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
        run: |
          docker-compose up -d
          docker-compose exec -T backend pytest tests/
```

**3. Environment-Specific Secrets**

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # or staging, development

    steps:
      - name: Deploy
        env:
          # These come from environment-specific secrets
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
```

### GitLab CI/CD

```yaml
variables:
  HF_TOKEN: $HF_TOKEN
  REDIS_PASSWORD: $REDIS_PASSWORD

build:
  script:
    - docker-compose build
  only:
    - main
```

---

## Security Best Practices

### DO ✅

1. **Generate Strong Secrets**
   ```bash
   # Good
   openssl rand -base64 32
   openssl rand -hex 32

   # Avoid
   "password123"
   "admin"
   ```

2. **Use Different Secrets Per Environment**
   - Development: Can use weaker/shared secrets
   - Staging: Use production-like secrets
   - Production: Unique, strong, rotated secrets

3. **Set Proper Permissions**
   ```bash
   # Secret files should be read-only by owner
   chmod 600 infrastructure/secrets/*.txt

   # Verify
   ls -la infrastructure/secrets/
   # Should show: -rw------- (600)
   ```

4. **Rotate Regularly**
   - JWT secrets: Every 90 days
   - Passwords: Every 180 days
   - API tokens: When compromised or annually

5. **Monitor and Audit**
   - Enable secret access logging
   - Monitor for exposed secrets (GitGuardian, GitHub Secret Scanning)
   - Review secret usage quarterly

### DON'T ❌

1. **Never Commit Secrets**
   ```bash
   # Check before committing
   git diff | grep -i "token\|password\|secret\|key"

   # If accidentally committed:
   # 1. Rotate the secret immediately
   # 2. Remove from Git history:
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Never Log Secrets**
   ```python
   # Bad
   logger.info(f"Using token: {hf_token}")

   # Good
   logger.info("Using HuggingFace token: ****")
   ```

3. **Never Share via Insecure Channels**
   - ❌ Slack, Email, SMS
   - ✅ 1Password, LastPass, HashiCorp Vault

4. **Never Hardcode**
   ```python
   # Bad
   HF_TOKEN = "hf_abc123xyz"

   # Good
   from src.shared.secrets import get_hf_token
   hf_token = get_hf_token(required=True)
   ```

---

## Troubleshooting

### Common Issues

#### 1. Secret Not Found

**Symptoms**:
```
ValueError: Required secret 'hf_token' not found
```

**Solutions**:
```bash
# Check Docker secret is mounted
docker exec rtstt-nlp-service ls -la /run/secrets/

# Check secret file exists locally
ls -la infrastructure/secrets/

# Check environment variable
docker exec rtstt-nlp-service env | grep HF_TOKEN

# Recreate secret
bash scripts/setup-secrets.sh
```

#### 2. Permission Denied

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: '/run/secrets/hf_token'
```

**Solutions**:
```bash
# Fix local file permissions
chmod 600 infrastructure/secrets/*.txt

# Check Docker secret permissions
docker exec rtstt-nlp-service ls -la /run/secrets/
# Should show: -r--r--r-- (444) - this is correct for Docker secrets

# Verify user can read
docker exec rtstt-nlp-service cat /run/secrets/hf_token
```

#### 3. Empty Secret Value

**Symptoms**:
```
logger.warning("HF_TOKEN is empty, model downloads may fail")
```

**Solutions**:
```bash
# Check secret content
cat infrastructure/secrets/hf_token.txt

# Ensure no trailing newlines/spaces
echo -n "hf_YOUR_TOKEN" > infrastructure/secrets/hf_token.txt

# Restart services
docker-compose restart
```

#### 4. Secret Not Updated

**Symptoms**:
Service still uses old secret after update

**Solutions**:
```bash
# For Docker Compose
docker-compose down
docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d

# For Docker Swarm (secrets are immutable!)
docker service update --secret-rm old_secret --secret-add new_secret service_name
```

### Debug Mode

Enable debug logging:

```python
# In your service
from src.shared.secrets import log_secrets_status
import logging

logging.basicConfig(level=logging.DEBUG)
log_secrets_status()
```

Output:
```
Secrets availability:
  Docker secrets dir: ✓
  HF_TOKEN: ✓
  REDIS_PASSWORD: ✗ (using empty)
  JWT_SECRET_KEY: ✗ (not set)
  GRAFANA_ADMIN_PASSWORD: ✓
```

---

## Architecture

### File Structure

```
RTSTT/
├── infrastructure/
│   └── secrets/
│       ├── .gitignore              # Ignores *.txt files
│       ├── README.md               # Local secrets documentation
│       ├── hf_token.template       # Template files
│       ├── redis_password.template
│       ├── jwt_secret.template
│       └── grafana_admin_password.template
│       # Real secrets (*.txt) are gitignored
│
├── scripts/
│   └── setup-secrets.sh            # Interactive secret setup
│
├── src/
│   └── shared/
│       └── secrets.py              # Secret loading utility
│
├── .env.example                    # Environment template
├── .env.template                   # Enhanced with secrets info
├── docker-compose.yml              # Base configuration
├── docker-compose.secrets.yml      # Secrets overlay
├── SECRETS.md                      # This file
└── .github/
    └── workflows/
        └── README.md               # GitHub Secrets documentation
```

### Secret Loading Flow

```
┌─────────────────────────────────────────────────┐
│          Service starts                         │
│   (e.g., nlp_service, summary_service)          │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│     src/shared/secrets.get_secret()             │
└─────────────────┬───────────────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐ ┌──────────┐ ┌──────────┐
│ Docker  │ │   ENV    │ │ Default  │
│ Secret  │ │ Variable │ │  Value   │
│  File   │ │          │ │          │
└────┬────┘ └────┬─────┘ └────┬─────┘
     │           │            │
     │  Found?   │  Found?    │  Found?
     │  Return   │  Return    │  Return
     ▼           ▼            ▼
┌─────────────────────────────────────────────────┐
│           Secret value returned                 │
│        (or error if required=True)              │
└─────────────────────────────────────────────────┘
```

### Docker Secrets Mounting

```
Host Machine                        Container
━━━━━━━━━━━━━                      ━━━━━━━━━━━━
infrastructure/secrets/
├── hf_token.txt ─────────────────> /run/secrets/hf_token
├── redis_password.txt ───────────> /run/secrets/redis_password
├── jwt_secret.txt ───────────────> /run/secrets/jwt_secret
└── grafana_admin_password.txt ──> /run/secrets/grafana_admin_password

                                    (mounted as read-only)
                                    (permissions: 444)
                                    (not visible in docker inspect)
```

---

## Additional Resources

- **Local Secrets**: [`infrastructure/secrets/README.md`](infrastructure/secrets/README.md)
- **GitHub Secrets**: [`.github/workflows/README.md`](.github/workflows/README.md)
- **Setup Script**: [`scripts/setup-secrets.sh`](scripts/setup-secrets.sh)
- **Secrets Utility**: [`src/shared/secrets.py`](src/shared/secrets.py)

### External Documentation

- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App - Config](https://12factor.net/config)

---

**Last Updated**: 2025-11-23
**Version**: 1.0.0
**Maintainer**: RTSTT DevOps Team
**License**: Internal Use Only
