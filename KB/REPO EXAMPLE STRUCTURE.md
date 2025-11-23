realtime-stt-orchestrator/
├── .github/
│   ├── workflows/
│   │   ├── ci-pipeline.yml
│   │   └── agent-orchestration.yml
│   └── CODEOWNERS
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AGENT_SPECIFICATION.md
│   ├── ORCHIDEA_INTEGRATION.md
│   └── api/
│
├── specs/
│   ├── technical/
│   │   ├── audio-capture.spec.md
│   │   ├── stt-pipeline.spec.md
│   │   ├── nlp-insights.spec.md
│   │   └── summary-engine.spec.md
│   ├── agents/
│   │   ├── orchestrator.agent.md
│   │   ├── audio-team.agents.md
│   │   ├── ml-team.agents.md
│   │   └── frontend-team.agents.md
│   └── workflows/
│       └── development-cycles.md
│
├── src/
│   ├── core/
│   │   ├── audio_capture/
│   │   ├── stt_engine/
│   │   ├── nlp_insights/
│   │   └── summary_generator/
│   ├── agents/
│   │   ├── orchestrator/
│   │   ├── teams/
│   │   └── metrics/
│   ├── ui/
│   │   ├── desktop/
│   │   └── web/
│   └── shared/
│       └── protocols/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── orchestration/
│   ├── agent_configs/
│   ├── workflows/
│   └── metrics/
│
├── infrastructure/
│   ├── docker/
│   ├── k8s/
│   └── monitoring/
│
├── .env.example
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── audio.txt
│   ├── ml.txt
│   └── dev.txt
└── README.md
