# WORKFLOW ORCHESTRATION - Guida Master
## Orchestrazione Ricorsiva Multi-Livello per POC RTSTT

**Versione**: 1.0
**Data**: 2025-11-21
**Framework**: ORCHIDEA v1.3

---

## 🎯 ARCHITETTURA ORCHESTRAZIONE

```
LIVELLO 1: MAIN-T (Questo terminale)
    ├── Genera 6 file di istruzione
    └── Coordina 5 terminali
         │
LIVELLO 2: 5 TERMINALI CLAUDE CODE CLI
    ├── Terminal 1: Foundation (setup iniziale)
    ├── Terminal 2: Audio Team
    ├── Terminal 3: ML Team
    ├── Terminal 4: Frontend Team
    └── Terminal 5: Integration Team
         │
LIVELLO 3: SUB-AGENTI (Max 5 per terminal)
    └── Ogni terminal lancia Task tool per parallelizzare
```

**Parallelismo Totale**: 5 terminali × 5 sub-agenti = **25 task simultanei**

---

## 📋 WORKFLOW COMPLETO

### STEP 1: Foundation Setup (Terminal 1)

**Directory**: `C:\PROJECTS\RTSTT`

**Comando**:
```bash
cd C:\PROJECTS\RTSTT
claude
```

**Prompt da dare a Claude Code CLI**:
```
leggi orchestration/subt-foundation.md e segui tutte le sue istruzioni parallelizzando con sub-agenti dove possibile
```

**Durata attesa**: 10-15 minuti

**Output**:
- Git repository con 2 commit
- 30+ directory create
- 4 worktrees attivi (audio, ml, frontend, integration)

**Verifica completamento**:
```bash
git worktree list
# Dovresti vedere 5 worktrees (main + 4)
```

**✅ CHECKPOINT 1**: Worktrees creati → Procedi a Step 2

---

### STEP 2: Sviluppo Parallelo (4 Terminali simultanei)

**Apri 4 terminali separati contemporaneamente**

#### Terminal 2 - Audio Team

**Directory**: `C:\PROJECTS\RTSTT-audio`

**Comando**:
```bash
cd C:\PROJECTS\RTSTT-audio
claude
```

**Prompt**:
```
leggi orchestration/subt-audio.md e segui tutte le sue istruzioni parallelizzando con sub-agenti
```

**Durata attesa**: 4-6 ore
**Sub-agenti**: 5 (2 ondate)
**Output**: Audio capture completo

---

#### Terminal 3 - ML Team

**Directory**: `C:\PROJECTS\RTSTT-ml`

**Comando**:
```bash
cd C:\PROJECTS\RTSTT-ml
claude
```

**Prompt**:
```
leggi orchestration/subt-ml.md e segui tutte le sue istruzioni parallelizzando con sub-agenti
```

**Durata attesa**: 4-6 ore
**Sub-agenti**: 5 (2 ondate)
**Output**: STT + NLP + Summary completi

---

#### Terminal 4 - Frontend Team

**Directory**: `C:\PROJECTS\RTSTT-frontend`

**Comando**:
```bash
cd C:\PROJECTS\RTSTT-frontend
claude
```

**Prompt**:
```
leggi orchestration/subt-frontend.md e segui tutte le sue istruzioni parallelizzando con sub-agenti
```

**Durata attesa**: 4-6 ore
**Sub-agenti**: 5 (2 ondate)
**Output**: Electron app completa

---

#### Terminal 5 - Integration Team

**Directory**: `C:\PROJECTS\RTSTT-integration`

**Comando**:
```bash
cd C:\PROJECTS\RTSTT-integration
claude
```

**Prompt**:
```
leggi orchestration/subt-integration.md e segui tutte le sue istruzioni parallelizzando con sub-agenti
```

**Durata attesa**: 4-6 ore
**Sub-agenti**: 5 (2 ondate)
**Output**: Backend + Docker completo

---

## ⏰ TIMELINE

| Fase | Durata | Terminali | Output |
|------|--------|-----------|--------|
| Foundation | 15 min | 1 | Worktrees ready |
| Parallel Dev | 6 ore | 4 simultanei | 4 branch completi |
| Integration | 2 ore | MAIN-T | Merge + tests |
| **TOTALE** | **~8 ore** | **5** | **POC completo** |

---

## 🔍 MONITORING PROGRESS

### Per Ogni Terminal

**Check commit progress**:
```bash
git log --oneline | grep "SUB-"
# Conta quanti sub-agenti hanno completato
```

**Check files created**:
```bash
git status
git diff --stat
```

**Check tests**:
```bash
pytest tests/ -v --cov=src
```

---

## ⚠️ TROUBLESHOOTING

### Se un terminal si blocca:
1. Verifica log errori
2. Riavvia il sub-agent problematico
3. Continua con altri sub-agent

### Se conflitti git:
1. Ogni terminal lavora su branch diverso → No conflitti
2. Se succede: stash, merge manualmente, riprendi

### Se modelli non scaricano:
1. Verifica connessione internet
2. Usa cache HuggingFace se disponibile
3. Download manuale e copia in `models/`

---

## ✅ VALIDAZIONE FINALE

Dopo completamento di tutti i 4 team:

```bash
# In C:\PROJECTS\RTSTT (terminal main)

# Verifica tutti i branch
git branch -a

# Verifica commit per team
for branch in feature/audio-capture feature/ml-pipeline feature/ui-dashboard feature/backend-api; do
  echo "=== $branch ==="
  git log origin/$branch --oneline | head -5
done

# Count files
find . -name "*.py" | wc -l
find . -name "*.ts" | wc -l
find . -name "*.tsx" | wc -l
```

**Success Criteria**:
- ✅ 4 branch con 20+ commit totali
- ✅ 50+ file Python creati
- ✅ 20+ file TypeScript/React creati
- ✅ Tests passing in ogni worktree
- ✅ Docker-compose funzionante

---

## 🎬 NEXT STEP: FASE 2 (Merge & Integration)

Quando tutti i 4 team completano, **MAIN-T** coordina:

1. **Code Review** (ogni branch)
2. **Merge sequenziale** (audio → ml → backend → frontend)
3. **Integration Testing** (end-to-end pipeline)
4. **Quality Gates ORCHIDEA** (99% validation)
5. **Final Commit** su `develop` branch

---

## 📊 METRICHE FINALI ATTESE

**Codice**:
- Python: ~15,000 righe
- TypeScript/React: ~3,000 righe
- Config/Docker: ~1,000 righe

**Tests**:
- Unit tests: 150+
- Integration tests: 50+
- E2E tests: 10+
- Coverage: >95%

**Performance**:
- Latency: <100ms end-to-end
- WER: <5%
- GPU memory: <14GB
- CPU audio: <5%

---

## 🎯 COMANDI RAPIDI

**Avvia Foundation**:
```bash
cd C:\PROJECTS\RTSTT && claude
> leggi orchestration/subt-foundation.md e segui le istruzioni
```

**Avvia tutti i 4 team** (dopo foundation):
```bash
# Terminal 2
cd C:\PROJECTS\RTSTT-audio && claude
> leggi orchestration/subt-audio.md e segui le istruzioni

# Terminal 3
cd C:\PROJECTS\RTSTT-ml && claude
> leggi orchestration/subt-ml.md e segui le istruzioni

# Terminal 4
cd C:\PROJECTS\RTSTT-frontend && claude
> leggi orchestration/subt-frontend.md e segui le istruzioni

# Terminal 5
cd C:\PROJECTS\RTSTT-integration && claude
> leggi orchestration/subt-integration.md e segui le istruzioni
```

---

## 🎉 RISULTATO FINALE

**POC RTSTT Windows 11 completo in ~8 ore** attraverso orchestrazione ricorsiva a 3 livelli con parallelismo massimo (25 task simultanei).

**Powered by ORCHIDEA Framework v1.3** 🚀

---

**FINE GUIDA ORCHESTRAZIONE**
