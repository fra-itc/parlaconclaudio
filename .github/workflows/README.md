# GitHub Actions Secrets Configuration

This document describes the required secrets for CI/CD workflows in the RTSTT project.

## Required Secrets

Configure these secrets in your GitHub repository to enable automated builds, tests, and deployments.

### Navigation

**Repository Settings** → **Secrets and variables** → **Actions** → **New repository secret**

---

## Secret Inventory

### 1. HF_TOKEN

**Description**: HuggingFace Hub access token
**Used by**: ML model download workflows, NLP service, Summary service
**Required for**: Building Docker images with model dependencies
**Environment**: All (development, staging, production)

**How to obtain**:
1. Sign up at https://huggingface.co
2. Navigate to **Settings** → **Access Tokens**
3. Click **New token**
4. Select **Read** permissions
5. Copy the token value

**Format**: `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 2. REDIS_PASSWORD

**Description**: Redis authentication password
**Used by**: All services connecting to Redis in deployed environments
**Required for**: Production and staging deployments
**Environment**: Staging, Production (optional for development)

**How to generate**:
```bash
openssl rand -base64 32
```

**Format**: Base64 string (e.g., `yX9k2Lp8mN3qR7tV5wZ1aB6cD4eF0gH8iJ2kL6mN9pQ=`)

**Important**: Use different passwords for each environment:
- Development: Can be empty or use a simple password
- Staging: Generate a strong password
- Production: Generate a unique, strong password

---

### 3. JWT_SECRET_KEY

**Description**: Secret key for signing JWT authentication tokens
**Used by**: Backend API authentication (future feature)
**Required for**: Production deployments with authentication enabled
**Environment**: Staging, Production

**How to generate**:
```bash
openssl rand -hex 32
```

**Format**: 64-character hexadecimal string

**Important**:
- **NEVER** reuse across environments
- **NEVER** reuse across projects
- Rotate periodically (recommended: every 90 days)
- Store securely and restrict access

---

### 4. GRAFANA_ADMIN_PASSWORD

**Description**: Grafana admin panel password
**Used by**: Grafana monitoring service
**Required for**: All environments with monitoring enabled
**Environment**: All (development, staging, production)

**How to set**:
- Use a strong, unique password
- Consider using a password manager
- Share with team members securely

**Format**: Any strong password (minimum 12 characters recommended)

**Default**: `admin` (DO NOT use in production!)

---

### 5. DOCKER_HUB_USERNAME (Optional)

**Description**: Docker Hub username for pushing images
**Used by**: Docker image build and push workflows
**Required for**: Publishing images to Docker Hub
**Environment**: Production

---

### 6. DOCKER_HUB_TOKEN (Optional)

**Description**: Docker Hub access token
**Used by**: Docker image build and push workflows
**Required for**: Publishing images to Docker Hub
**Environment**: Production

**How to obtain**:
1. Log in to Docker Hub
2. Navigate to **Account Settings** → **Security**
3. Click **New Access Token**
4. Set description and permissions
5. Copy the token value

---

## Environment-Specific Secrets

### Development Environment
```yaml
HF_TOKEN: <optional>
REDIS_PASSWORD: <optional or empty>
JWT_SECRET_KEY: <optional>
GRAFANA_ADMIN_PASSWORD: admin
```

### Staging Environment
```yaml
HF_TOKEN: <required>
REDIS_PASSWORD: <strong password>
JWT_SECRET_KEY: <generated key>
GRAFANA_ADMIN_PASSWORD: <strong password>
```

### Production Environment
```yaml
HF_TOKEN: <required>
REDIS_PASSWORD: <unique strong password>
JWT_SECRET_KEY: <unique generated key>
GRAFANA_ADMIN_PASSWORD: <unique strong password>
DOCKER_HUB_USERNAME: <if publishing>
DOCKER_HUB_TOKEN: <if publishing>
```

---

## Using Secrets in Workflows

### Example: Docker Build Workflow

```yaml
name: Build and Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build services
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
        run: |
          docker-compose build

      - name: Run tests
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
          JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
        run: |
          docker-compose up -d
          docker-compose exec -T backend pytest tests/
```

### Example: Deployment Workflow

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_HUB_USERNAME }}
          password: ${{ secrets.DOCKER_HUB_TOKEN }}

      - name: Build and push
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          docker-compose build
          docker-compose push

      - name: Deploy to server
        env:
          REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
          JWT_SECRET_KEY: ${{ secrets.JWT_SECRET_KEY }}
          GRAFANA_ADMIN_PASSWORD: ${{ secrets.GRAFANA_ADMIN_PASSWORD }}
        run: |
          # Deploy commands here
          echo "Deploying with secrets..."
```

---

## Secret Rotation Strategy

### When to Rotate

- **Immediately**: If a secret is exposed or compromised
- **Regular schedule**: Every 90 days for JWT keys
- **Team changes**: When team members with access leave
- **Incident response**: After any security incident

### How to Rotate

1. **Generate new secret**:
   ```bash
   openssl rand -hex 32  # For JWT
   openssl rand -base64 32  # For passwords
   ```

2. **Update in GitHub**:
   - Go to repository secrets
   - Edit the secret
   - Paste new value
   - Save changes

3. **Deploy with new secret**:
   - Trigger deployment workflow
   - Or manually update on servers

4. **Verify services**:
   - Check service health
   - Monitor logs for auth errors
   - Test functionality

5. **Revoke old secret**:
   - Update any external systems
   - Document the rotation

---

## Security Best Practices

### DO ✅

- Use environment-specific secrets (different for dev/staging/prod)
- Rotate secrets regularly
- Use strong, randomly generated values
- Limit secret access to necessary team members
- Use GitHub Environments for additional protection
- Enable audit logging
- Document secret purposes and owners

### DON'T ❌

- Hard-code secrets in workflow files
- Echo or print secrets in logs
- Share secrets via unsecured channels (Slack, email)
- Reuse secrets across environments or projects
- Store secrets in code or documentation
- Use weak or default passwords

---

## Troubleshooting

### Secret not available in workflow

**Symptoms**: `Error: Secret HF_TOKEN not found`

**Solution**:
1. Verify secret exists in repository settings
2. Check secret name matches exactly (case-sensitive)
3. Ensure workflow has permission to access secrets
4. Check if using GitHub Environments with restrictions

### Secret value seems incorrect

**Symptoms**: Authentication errors, connection failures

**Solution**:
1. Verify secret was copied completely (no truncation)
2. Check for extra whitespace or line breaks
3. Regenerate and re-upload the secret
4. Test secret value locally first

### Secrets exposed in logs

**Symptoms**: Secret values visible in workflow logs

**Solution**:
1. GitHub automatically masks registered secrets
2. If exposed, **immediately rotate the secret**
3. Review workflow for explicit echo/print commands
4. Use `::add-mask::` for derived values

---

## Support and Documentation

- **Local secrets**: See `infrastructure/secrets/README.md`
- **Comprehensive guide**: See `SECRETS.md` in project root
- **GitHub Docs**: https://docs.github.com/en/actions/security-guides/encrypted-secrets
- **Security policy**: See `SECURITY.md`

---

**Last Updated**: 2025-11-23
**Maintained by**: RTSTT DevOps Team
