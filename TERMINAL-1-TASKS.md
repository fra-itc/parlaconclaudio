# TERMINAL 1: Docker Secrets Management

**Branch:** `feature/docker-secrets`
**Worktree:** `/home/frisco/projects/RTSTT-secrets`
**Estimated Time:** 2-3 hours
**Priority:** HIGH

## Objective
Implement Docker secrets for local development and prepare GitHub Secrets integration for CI/CD.

---

## Task Checklist

### Phase 1: Infrastructure Setup (30 min)

- [ ] Create secrets directory structure
  ```bash
  mkdir -p infrastructure/secrets
  ```

- [ ] Create `.gitignore` for secrets directory
  ```bash
  cat > infrastructure/secrets/.gitignore << 'EOF'
  # Ignore all secret files
  *

  # Except the README and templates
  !.gitignore
  !README.md
  !*.template
  EOF
  ```

- [ ] Create README documentation
  - Document local development setup
  - Explain Docker secrets vs GitHub Secrets
  - Provide secret file templates

### Phase 2: Docker Secrets Configuration (45 min)

- [ ] Identify all secrets currently used:
  - `HF_TOKEN` (HuggingFace token)
  - `REDIS_PASSWORD` (if any)
  - `JWT_SECRET_KEY` (for future auth)
  - Grafana admin password

- [ ] Create `docker-compose.secrets.yml` override file
  - Define Docker secrets section
  - Configure secret file paths
  - Set up secret mounts for each service

- [ ] Update service definitions to read from `/run/secrets/`
  - Modify environment variable reading logic
  - Add fallback to `.env` for backward compatibility

### Phase 3: Local Development Setup (30 min)

- [ ] Create `.env.template` file
  ```bash
  # Copy from .env.example and add secret documentation
  cp .env.example .env.template
  ```

- [ ] Create secret file templates in `infrastructure/secrets/`:
  - `hf_token.template`
  - `redis_password.template`
  - `jwt_secret.template`

- [ ] Write setup script `scripts/setup-secrets.sh`
  - Prompt user for secrets
  - Generate secret files
  - Set proper permissions (600)

### Phase 4: GitHub Secrets Documentation (30 min)

- [ ] Create `.github/workflows/README.md`
  - Document required GitHub Secrets
  - List secret names and descriptions
  - Provide CI/CD setup instructions

- [ ] Create secret injection strategy:
  - How secrets flow from GitHub → Docker
  - Environment-specific configurations
  - Production vs staging secret handling

### Phase 5: Testing & Validation (30 min)

- [ ] Test local development workflow:
  ```bash
  # Stop services
  docker-compose down

  # Run setup script
  bash scripts/setup-secrets.sh

  # Start with secrets
  docker-compose -f docker-compose.yml -f docker-compose.secrets.yml up -d

  # Verify services can read secrets
  docker exec rtstt-summary-service cat /run/secrets/hf_token
  ```

- [ ] Verify backward compatibility (without secrets)
- [ ] Document migration guide for existing users

### Phase 6: Documentation & Commit (15 min)

- [ ] Update main README.md with secrets setup section
- [ ] Create SECRETS.md comprehensive guide
- [ ] Commit all changes:
  ```bash
  git add -A
  git commit -m "feat: Implement Docker secrets management for local dev

  - Add infrastructure/secrets/ with templates
  - Create docker-compose.secrets.yml override
  - Implement setup script for secret generation
  - Document GitHub Secrets integration for CI/CD
  - Maintain backward compatibility with .env files

  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>"
  ```

---

## Files to Create

### New Files:
```
infrastructure/secrets/
├── .gitignore
├── README.md
├── hf_token.template
├── redis_password.template
└── jwt_secret.template

scripts/
└── setup-secrets.sh

.github/workflows/
└── README.md (secrets documentation)

docker-compose.secrets.yml
.env.template
SECRETS.md
```

### Files to Modify:
```
docker-compose.yml (optional - add secrets reference)
README.md (add secrets setup section)
```

---

## Key Secrets Inventory

1. **HF_TOKEN** (HuggingFace)
   - Used by: Summary service, NLP service
   - Purpose: Download models from HuggingFace Hub
   - Required: No (models can be cached)

2. **REDIS_PASSWORD**
   - Used by: All services connecting to Redis
   - Purpose: Redis authentication
   - Required: No (currently empty)

3. **JWT_SECRET_KEY**
   - Used by: Backend API (future)
   - Purpose: Sign JWT tokens for authentication
   - Required: No (future feature)

4. **GRAFANA_ADMIN_PASSWORD**
   - Used by: Grafana service
   - Purpose: Admin login
   - Required: Yes (currently hardcoded)

---

## Testing Checklist

- [ ] Services start successfully with secrets
- [ ] Secrets are not exposed in logs
- [ ] Environment variables fallback works
- [ ] Docker secrets mounted at `/run/secrets/`
- [ ] Secret files have correct permissions (600)
- [ ] Documentation is clear and comprehensive

---

## Completion Criteria

✅ Docker secrets infrastructure created
✅ Local development workflow documented
✅ GitHub Secrets integration guide written
✅ All services tested with secrets
✅ Backward compatibility maintained
✅ Changes committed to branch

---

**Next Steps After Completion:**
1. Wait for other terminals to complete
2. Participate in Wave 2 Sync Agent
3. Merge to develop after sync validation
