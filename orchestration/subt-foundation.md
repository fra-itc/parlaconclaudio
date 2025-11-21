# ISTRUZIONI PER CLAUDE CODE CLI - FOUNDATION SETUP
## Real-Time STT Orchestrator - Inizializzazione Progetto

**IMPORTANTE**: Sei un agente autonomo Claude Code CLI. Esegui TUTTE le istruzioni in questo file dall'inizio alla fine. Usa sub-agenti (Task tool) per parallelizzare dove possibile. NON chiedere conferme, procedi autonomamente.

---

## 🎯 OBIETTIVO
Setup completo del repository RTSTT con:
- Git baseline commit
- Struttura directory (30+ folders)
- Commit scaffold con API contracts e config
- Creazione 4 git worktrees per sviluppo parallelo

## 📊 METRICHE TARGET
- **Durata**: 10-15 minuti
- **Parallelismo**: 3 ondate, max 4 sub-agenti
- **Deliverables**:
  - 1 repository inizializzato
  - 13 file generati (già presenti)
  - 30+ directory create
  - 4 worktrees attivi

---

## 🔀 STRATEGIA PARALLELIZZAZIONE

### ANALISI DIPENDENZE
```
ONDATA 1: Verifica Prerequisiti (Sequential)
  ↓
ONDATA 2: Git Baseline + Directory Structure (2 sub-agenti paralleli)
  ↓
ONDATA 3: Worktree Creation (4 sub-agenti paralleli)
```

### CONFLICT AVOIDANCE
- Ondata 1: Verifica stato
- Ondata 2: Sub-Agent 1 (git operations), Sub-Agent 2 (mkdir operations) → No overlap
- Ondata 3: 4 sub-agenti creano worktrees con branch diversi → No conflict

---

## 🚀 ONDATA 1: VERIFICA PREREQUISITI (Sequential)

### Task 1.1: Verifica Stato Repository
```bash
# Verifica di essere nella directory corretta
pwd
# Output atteso: C:\PROJECTS\RTSTT o equivalente

# Verifica che i file generati da MAIN-T esistano
ls docs/api/
# Atteso: grpc_audio_streaming.proto, websocket_schemas.json, openapi_rest.yaml, redis_streams.md

ls orchestration/workflows/
# Atteso: SUB-PLAN-AUDIO-TEAM.md, SUB-PLAN-ML-TEAM.md, etc.

# Verifica git inizializzato
git status
# Se errore "not a git repository", esegui: git init
```

### Task 1.2: Verifica File Critici
```bash
# Verifica esistenza file di configurazione
test -f pyproject.toml && echo "✓ pyproject.toml" || echo "✗ pyproject.toml MISSING"
test -f docker-compose.yml && echo "✓ docker-compose.yml" || echo "✗ docker-compose.yml MISSING"
test -f README.md && echo "✓ README.md" || echo "✗ README.md MISSING"
test -f .gitignore && echo "✓ .gitignore" || echo "✗ .gitignore MISSING"
```

**✅ CHECKPOINT 1**: Tutti i file presenti. Se qualcosa manca, STOP e segnala errore.

---

## 🚀 ONDATA 2: GIT + DIRECTORY (2 sub-agenti paralleli)

### Sub-Agent 1: Git Baseline Operations

**Lancio con Task tool**:
```
Usa il Task tool con questi parametri:
- subagent_type: 'general-purpose'
- description: 'Git baseline commit e branch setup'
- prompt: |
    Esegui le seguenti operazioni git in sequenza:

    1. Aggiungi file esistenti allo staging:
    ```bash
    git add KB/ START.md .github/ .claude/
    ```

    2. Primo commit baseline:
    ```bash
    git commit -m "chore: Initial project baseline with ORCHIDEA v1.3 specs and agent definitions

    - Knowledge base with 9 agent specifications (5,623 lines)
    - START.md architecture reference (488 lines)
    - GitHub workflows directory structure
    - Claude configuration

    Foundation for multi-agent orchestration POC Windows 11."
    ```

    3. Crea branch develop:
    ```bash
    git checkout -b develop
    ```

    4. Crea branch feature/project-scaffold:
    ```bash
    git checkout -b feature/project-scaffold
    ```

    5. Verifica stato finale:
    ```bash
    git log --oneline
    git branch
    ```

    DELIVERABLE:
    - Primo commit creato
    - Branch develop e feature/project-scaffold esistenti
    - Nessun errore git
```

---

### Sub-Agent 2: Directory Structure Creation

**Lancio con Task tool**:
```
Usa il Task tool con questi parametri:
- subagent_type: 'general-purpose'
- description: 'Create complete project directory structure'
- prompt: |
    Crea la struttura directory completa del progetto eseguendo questi comandi:

    ```bash
    # Core source structure
    mkdir -p src/core/audio_capture
    mkdir -p src/core/stt_engine
    mkdir -p src/core/nlp_insights
    mkdir -p src/core/summary_generator

    # Agents
    mkdir -p src/agents/orchestrator
    mkdir -p src/agents/audio_team
    mkdir -p src/agents/ml_team
    mkdir -p src/agents/frontend_team
    mkdir -p src/agents/integration_team

    # UI
    mkdir -p src/ui/desktop
    mkdir -p src/ui/web

    # Shared protocols
    mkdir -p src/shared/protocols

    # Testing
    mkdir -p tests/unit
    mkdir -p tests/integration
    mkdir -p tests/e2e

    # Orchestration
    mkdir -p orchestration/agent_configs
    mkdir -p orchestration/workflows
    mkdir -p orchestration/metrics

    # Infrastructure
    mkdir -p infrastructure/docker
    mkdir -p infrastructure/k8s
    mkdir -p infrastructure/monitoring

    # Documentation
    mkdir -p docs/api

    # Requirements (already exists from MAIN-T)
    # mkdir -p requirements

    # Models storage
    mkdir -p models/whisper
    mkdir -p models/silero_vad
    mkdir -p models/nlp
    mkdir -p models/tensorrt_cache

    # Logs and temp
    mkdir -p logs
    mkdir -p tmp
    mkdir -p sessions
    ```

    Dopo creazione, verifica:
    ```bash
    find src -type d | wc -l
    # Atteso: >15 directory

    ls -R src/
    ls -R tests/
    ls -R infrastructure/
    ```

    DELIVERABLE:
    - 30+ directory create
    - Struttura completa verificata
    - Nessun errore mkdir
```

---

## ⏸️ SYNC POINT 1: Attendi Completamento Ondata 2

**Verifica manualmente**:
```bash
# Verifica git operations
git log --oneline
# Dovresti vedere il commit "chore: Initial project baseline..."

git branch
# Dovresti vedere: develop, feature/project-scaffold

# Verifica directory structure
ls -d src/core/*
ls -d tests/*
ls -d infrastructure/*
```

**✅ CHECKPOINT 2**: Git OK, Directory OK → Procedi a Ondata 3

---

## 🚀 ONDATA 3: SCAFFOLD COMMIT + WORKTREE CREATION

### Task 3.1: Commit Scaffold (Sequential)

**Esegui direttamente con Bash tool**:
```bash
# Add tutti i file generati da MAIN-T
git add .

# Commit scaffold completo
git commit -m "feat: Add project scaffold with API contracts and configuration

- API contracts: gRPC, WebSocket, REST, Redis Streams (1,912 lines)
- Configuration: pyproject.toml, requirements, docker-compose (1,200 lines)
- Project structure: src/, tests/, docs/, infrastructure/ (30+ directories)
- Complete README with quick start guide (450 lines)
- .gitignore comprehensive rules (200+ patterns)
- .env.example with 90+ configuration variables

This scaffold enables 4 parallel teams to start development:
- Audio Team: WASAPI capture + VAD + Circular Buffer
- ML Team: Whisper Large V3 + NLP insights + Summary generation
- Frontend Team: Electron desktop app + React dashboard
- Integration Team: FastAPI backend + Redis orchestration

ORCHIDEA v1.3 Framework ready for multi-agent orchestration.
POC Target: Windows 11 with RTX 5080 GPU."

# Verifica commit
git log --oneline -1
git show --stat HEAD
```

**✅ CHECKPOINT 3**: Scaffold committed

---

### Task 3.2: Worktree Creation (4 sub-agenti paralleli)

**IMPORTANTE**: I 4 sub-agenti opereranno su branch diversi → Zero conflitti

#### Sub-Agent 1: Audio Worktree

**Lancio con Task tool**:
```
Usa il Task tool:
- subagent_type: 'general-purpose'
- description: 'Create audio team worktree'
- prompt: |
    Crea worktree per Audio Team:

    ```bash
    git worktree add ../RTSTT-audio -b feature/audio-capture
    ```

    Verifica:
    ```bash
    cd ../RTSTT-audio
    git branch
    pwd
    ls
    cd -
    ```

    DELIVERABLE: Worktree ../RTSTT-audio creato con branch feature/audio-capture
```

---

#### Sub-Agent 2: ML Worktree

**Lancio con Task tool**:
```
- subagent_type: 'general-purpose'
- description: 'Create ML team worktree'
- prompt: |
    Crea worktree per ML Team:

    ```bash
    git worktree add ../RTSTT-ml -b feature/ml-pipeline
    ```

    Verifica:
    ```bash
    cd ../RTSTT-ml
    git branch
    pwd
    cd -
    ```

    DELIVERABLE: Worktree ../RTSTT-ml creato con branch feature/ml-pipeline
```

---

#### Sub-Agent 3: Frontend Worktree

**Lancio con Task tool**:
```
- subagent_type: 'general-purpose'
- description: 'Create frontend team worktree'
- prompt: |
    Crea worktree per Frontend Team:

    ```bash
    git worktree add ../RTSTT-frontend -b feature/ui-dashboard
    ```

    Verifica:
    ```bash
    cd ../RTSTT-frontend
    git branch
    pwd
    cd -
    ```

    DELIVERABLE: Worktree ../RTSTT-frontend creato con branch feature/ui-dashboard
```

---

#### Sub-Agent 4: Integration Worktree

**Lancio con Task tool**:
```
- subagent_type: 'general-purpose'
- description: 'Create integration team worktree'
- prompt: |
    Crea worktree per Integration Team:

    ```bash
    git worktree add ../RTSTT-integration -b feature/backend-api
    ```

    Verifica:
    ```bash
    cd ../RTSTT-integration
    git branch
    pwd
    cd -
    ```

    DELIVERABLE: Worktree ../RTSTT-integration creato con branch feature/backend-api
```

---

## ⏸️ SYNC POINT 2: Verifica Completamento Ondata 3

**Esegui verifica finale**:
```bash
# Lista tutti i worktrees
git worktree list

# Output atteso:
# C:/PROJECTS/RTSTT                 <commit-hash> [feature/project-scaffold]
# C:/PROJECTS/RTSTT-audio           <commit-hash> [feature/audio-capture]
# C:/PROJECTS/RTSTT-ml              <commit-hash> [feature/ml-pipeline]
# C:/PROJECTS/RTSTT-frontend        <commit-hash> [feature/ui-dashboard]
# C:/PROJECTS/RTSTT-integration     <commit-hash> [feature/backend-api]

# Conta worktrees
git worktree list | wc -l
# Atteso: 5 (main + 4 worktrees)
```

**✅ CHECKPOINT 4**: 5 worktrees attivi

---

## ✅ VALIDAZIONE FINALE

### Checklist Completamento Foundation

Esegui questa verifica completa:

```bash
echo "=== FOUNDATION SETUP VALIDATION ==="
echo ""

echo "1. Git Repository Status:"
git log --oneline | head -5
git branch -a
echo ""

echo "2. Directory Structure:"
find src -type d | head -20
find tests -type d
echo ""

echo "3. Configuration Files:"
ls -lh pyproject.toml docker-compose.yml README.md .gitignore .env.example
echo ""

echo "4. API Contracts:"
ls -lh docs/api/
echo ""

echo "5. Worktrees:"
git worktree list
echo ""

echo "6. File Count:"
find . -type f -name "*.md" | wc -l
find . -type f -name "*.py" | wc -l
find . -type f -name "*.toml" | wc -l
echo ""

echo "=== VALIDATION COMPLETE ==="
```

### Success Criteria

- [x] Git initialized with 2 commits
- [x] Branches: main (or master), develop, feature/project-scaffold
- [x] Directory structure: 30+ folders
- [x] Configuration files: 9 files present
- [x] API contracts: 4 files in docs/api/
- [x] Worktrees: 4 active (audio, ml, frontend, integration)
- [x] No git errors
- [x] No file system errors

---

## 📊 DELIVERABLES

### Repository Structure
```
C:\PROJECTS\
├── RTSTT\                          # Main repository
│   ├── .git\
│   ├── KB\                         # Knowledge base (9 files)
│   ├── START.md
│   ├── docs\api\                   # API contracts (4 files)
│   ├── orchestration\workflows\    # Sub-plans (5 files)
│   ├── src\                        # Source structure (30+ directories)
│   ├── tests\                      # Test structure (3 directories)
│   ├── infrastructure\             # Docker, K8s, monitoring
│   ├── pyproject.toml
│   ├── docker-compose.yml
│   ├── README.md
│   └── [9 config files]
│
├── RTSTT-audio\                    # Worktree 1
│   └── [branch: feature/audio-capture]
│
├── RTSTT-ml\                       # Worktree 2
│   └── [branch: feature/ml-pipeline]
│
├── RTSTT-frontend\                 # Worktree 3
│   └── [branch: feature/ui-dashboard]
│
└── RTSTT-integration\              # Worktree 4
    └── [branch: feature/backend-api]
```

### Git Status
- **Commits**: 2 (baseline + scaffold)
- **Branches**: 5 (main, develop, feature/project-scaffold, + 4 feature branches)
- **Worktrees**: 5 (1 main + 4 parallel)

### Files Created
- **Markdown**: 15+ files
- **Config**: 9 files
- **Directories**: 30+ folders
- **Total size**: ~50KB text files

---

## 🔗 NEXT STEPS

Foundation setup è **COMPLETO**. L'utente ora può:

1. **Aprire 4 nuovi terminali** (uno per worktree)
2. **Lanciare Claude Code CLI** in ciascun worktree
3. **Eseguire sub-plan dedicati**:
   - `cd ../RTSTT-audio` → `claude` → "leggi orchestration/subt-audio.md"
   - `cd ../RTSTT-ml` → `claude` → "leggi orchestration/subt-ml.md"
   - `cd ../RTSTT-frontend` → `claude` → "leggi orchestration/subt-frontend.md"
   - `cd ../RTSTT-integration` → `claude` → "leggi orchestration/subt-integration.md"

4. **Sviluppo parallelo** inizia → 4 team × 5 sub-agenti = 20 task simultanei

---

## 📝 LOG FINALE

Scrivi un report finale:

```bash
cat > foundation-setup-report.md << 'EOF'
# Foundation Setup - Completion Report

**Data**: $(date)
**Durata**: [inserisci tempo effettivo]
**Status**: ✅ COMPLETATO

## Risultati
- Git commits: 2
- Worktrees: 4
- Directories: 30+
- Files: 30+

## Worktrees Attivi
$(git worktree list)

## Git Log
$(git log --oneline --graph --all | head -10)

## Prossimi Passi
Sviluppo parallelo pronto per avvio.
EOF

cat foundation-setup-report.md
```

---

## 🎯 REPORT A MAIN-T

**Status**: ✅ FOUNDATION COMPLETE
**Worktrees**: 4 attivi
**Branch**: feature/project-scaffold
**Commits**: 2
**Blockers**: Nessuno
**Ready for**: Parallel Development Phase

---

**FINE ISTRUZIONI FOUNDATION**
**Foundation setup completato con successo** 🎉
**I 4 team possono ora iniziare lo sviluppo parallelo**
