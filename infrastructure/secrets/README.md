# Secrets Management

This directory manages sensitive configuration values for the RTSTT project using Docker secrets for local development and GitHub Secrets for CI/CD pipelines.

## Overview

Secrets are sensitive values that should never be committed to version control. This includes:
- API tokens (HuggingFace, OpenAI, etc.)
- Database passwords
- JWT signing keys
- Service credentials

## Secrets Inventory

### 1. HF_TOKEN (HuggingFace Token)
- **Used by**: `nlp-service`, `summary-service`
- **Purpose**: Download models from HuggingFace Hub (Mistral, Llama, sentence transformers)
- **Required**: Optional (models can be cached locally)
- **How to obtain**:
  1. Create account at https://huggingface.co
  2. Go to Settings → Access Tokens
  3. Create a read token

### 2. REDIS_PASSWORD
- **Used by**: All services connecting to Redis
- **Purpose**: Redis authentication
- **Required**: Optional for development (currently empty)
- **How to generate**: `openssl rand -base64 32`

### 3. JWT_SECRET_KEY
- **Used by**: Backend API (future authentication feature)
- **Purpose**: Sign JWT tokens for user authentication
- **Required**: Not yet (planned feature)
- **How to generate**: `openssl rand -hex 32`

### 4. GRAFANA_ADMIN_PASSWORD
- **Used by**: Grafana monitoring service
- **Purpose**: Admin panel login
- **Required**: Yes
- **Default**: `admin` (should be changed in production)

## Local Development Setup

### Option 1: Docker Secrets (Recommended)

1. **Create secret files** from templates:
   ```bash
   # Run the setup script
   bash scripts/setup-secrets.sh

   # Or manually create files:
   echo "your_huggingface_token_here" > infrastructure/secrets/hf_token.txt
   echo "your_redis_password_here" > infrastructure/secrets/redis_password.txt
   echo "your_jwt_secret_here" > infrastructure/secrets/jwt_secret.txt
   echo "your_grafana_password" > infrastructure/secrets/grafana_admin_password.txt

   # Set proper permissions (important!)
   chmod 600 infrastructure/secrets/*.txt
   ```

2. **Start services with secrets**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
   ```

3. **Verify secrets are mounted**:
   ```bash
   docker exec rtstt-summary-service cat /run/secrets/hf_token
   ```

### Option 2: Environment Variables (Backward Compatible)

Continue using `.env` file as before:
```bash
cp .env.example .env
# Edit .env with your values
docker-compose up -d
```

Services will automatically fallback to environment variables if Docker secrets are not available.

## Docker Secrets vs GitHub Secrets

### Docker Secrets (Local Development)
- **Location**: `infrastructure/secrets/*.txt`
- **Mounted at**: `/run/secrets/` inside containers
- **Permissions**: 600 (read/write for owner only)
- **Advantages**:
  - Not exposed in `docker inspect`
  - Not visible in environment variables
  - Files stored outside containers

### GitHub Secrets (CI/CD)
- **Location**: Repository Settings → Secrets and variables → Actions
- **Access**: Injected as environment variables during workflow runs
- **Advantages**:
  - Encrypted at rest
  - Masked in logs
  - Scoped per environment (production, staging, etc.)

## GitHub Actions Integration

For CI/CD pipelines, configure these secrets in your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `HF_TOKEN`
   - `REDIS_PASSWORD`
   - `JWT_SECRET_KEY`
   - `GRAFANA_ADMIN_PASSWORD`

Workflows will inject these as environment variables:
```yaml
env:
  HF_TOKEN: ${{ secrets.HF_TOKEN }}
  REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
```

## Security Best Practices

### DO:
✅ Use the setup script to generate secrets
✅ Keep secret files at permission `600`
✅ Use strong, randomly generated values
✅ Rotate secrets periodically
✅ Use different secrets for each environment
✅ Document which services use which secrets

### DON'T:
❌ Commit secret files to Git (they're .gitignored)
❌ Share secrets in plain text (Slack, email, etc.)
❌ Use default/weak passwords in production
❌ Reuse secrets across projects
❌ Log secret values
❌ Hardcode secrets in source code

## Troubleshooting

### Secret not found in container
```bash
# Check if secret is mounted
docker exec <container-name> ls -la /run/secrets/

# Check secret content (careful in production!)
docker exec <container-name> cat /run/secrets/hf_token
```

### Permission denied
```bash
# Fix file permissions
chmod 600 infrastructure/secrets/*.txt

# Ensure files are not world-readable
ls -la infrastructure/secrets/
```

### Service can't read secret
- Verify the secret file exists and has content
- Check docker-compose.secrets.yml has the correct secret name
- Ensure service is configured to read from `/run/secrets/`
- Check service logs: `docker logs <container-name>`

## Migration Guide

Migrating from `.env` to Docker secrets:

1. **Backup your current `.env`**:
   ```bash
   cp .env .env.backup
   ```

2. **Run setup script**:
   ```bash
   bash scripts/setup-secrets.sh
   ```

3. **Update docker-compose command**:
   ```bash
   # Old way
   docker-compose up -d

   # New way
   docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d
   ```

4. **Verify services start correctly**

5. **Keep `.env` as fallback** (services support both methods)

## Template Files

This directory contains `.template` files that show the expected format:
- `hf_token.template` - HuggingFace token format
- `redis_password.template` - Redis password format
- `jwt_secret.template` - JWT secret format
- `grafana_admin_password.template` - Grafana password format

Copy these to `.txt` files and fill in your actual values.

## Support

For issues or questions:
1. Check service logs: `docker logs <container-name>`
2. Verify secret files exist and have correct permissions
3. Review docker-compose.secrets.yml configuration
4. Consult the main README.md for project setup

---

**Last Updated**: 2025-11-23
**Maintainer**: RTSTT Development Team
