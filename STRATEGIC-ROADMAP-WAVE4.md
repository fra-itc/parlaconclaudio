# Strategic Roadmap: Wave 4 and Beyond

**Date:** November 23, 2025
**Author:** Claude Code
**Context:** Post-Wave 3 Cross-Platform POC Completion

## Executive Summary

Wave 3 successfully delivered cross-platform support (WSL2, Linux, Windows), complete STT→NLP→Summary pipeline, and WebSocket audio bridge infrastructure. The POC demonstrates:

- **253-312ms end-to-end latency** (48% under 500ms target)
- **100% success rate** in audio pipeline tests
- **Cross-platform audio abstraction** with multiple driver support
- **Production-ready deployment scripts** for WSL2/Linux

This roadmap presents **7 strategic development tracks** with priority rankings, effort estimates, and dependency analysis to guide Wave 4 planning.

---

## Current State Assessment

### ✅ Completed (Wave 3)
- Cross-platform audio capture (PulseAudio, PortAudio, Mock)
- WebSocket audio bridge for WSL2
- STT→NLP→Summary pipeline integration
- Keyword extraction and summarization POC
- Automated deployment scripts
- Comprehensive documentation

### ⚠️ In Progress
- Material-UI frontend components (partial)
- gRPC health checks (implemented but not fully integrated)
- Secrets management infrastructure (templates created)

### ❌ Not Started
- WASAPI native driver (Windows)
- Production ML services via gRPC
- Redis streams for service communication
- Observability stack (Prometheus/Grafana)
- Mobile applications
- CI/CD automation

---

## Development Tracks Overview

| Track | Priority | Effort | Business Value | Technical Risk |
|-------|----------|--------|----------------|----------------|
| **1. WASAPI Native Driver** | HIGH | Medium | High | Medium |
| **2. Production ML Services** | CRITICAL | High | Critical | Low |
| **3. Frontend Enhancement** | HIGH | Medium | High | Low |
| **4. Observability Stack** | MEDIUM | Medium | Medium | Low |
| **5. Mobile Applications** | LOW | High | Medium | High |
| **6. Multi-Language Support** | MEDIUM | Medium | High | Medium |
| **7. Testing & CI/CD** | HIGH | Medium | High | Low |

---

## Track 1: WASAPI Native Driver (Windows)

### Objective
Replace PyAudio dependency on Windows with native WASAPI implementation for production-grade audio capture.

### Motivation
- **Current:** PortAudio driver works but adds dependency layer
- **Target:** Direct Windows Audio Session API (WASAPI) integration
- **Benefit:** Lower latency, better device control, professional audio support

### Scope
1. **Phase 1: Core WASAPI Wrapper**
   - COM interface initialization (`IMMDeviceEnumerator`, `IAudioClient`)
   - Loopback and endpoint capture modes
   - Device enumeration and selection

2. **Phase 2: Integration**
   - Implement `AudioCaptureBase` interface
   - Add to driver factory with auto-detection
   - Update `requirements-audio-windows.txt`

3. **Phase 3: Advanced Features**
   - WASAPI exclusive mode for lowest latency
   - Automatic format negotiation
   - Device hot-plug detection

### Deliverables
- `src/core/audio_capture/drivers/wasapi_driver.py` (~600 lines)
- `src/core/audio_capture/drivers/wasapi_com.py` (COM helpers, ~400 lines)
- Unit tests and manual microphone tests
- Documentation update

### Dependencies
- **Requires:** `comtypes>=1.2.0`, Windows SDK headers
- **Blocks:** None (optional enhancement)

### Effort Estimate
- **Development:** 3-5 days
- **Testing:** 2 days
- **Documentation:** 1 day
- **Total:** ~1 week

### Success Criteria
- [ ] Enumerate all Windows audio devices
- [ ] Capture audio at 16kHz mono with <10ms added latency
- [ ] Pass all existing audio pipeline tests
- [ ] Fallback to PortAudio if WASAPI fails

---

## Track 2: Production ML Services Integration

### Objective
Replace POC keyword extraction with production-ready NLP and summarization services using gRPC and Redis streams.

### Motivation
- **Current:** Keyword extraction runs in orchestrator (not scalable)
- **Target:** Dedicated ML services with horizontal scaling
- **Benefit:** True microservices architecture, independent scaling, GPU optimization

### Scope
1. **Phase 1: gRPC Service Architecture**
   - Complete gRPC proto definitions for NLP and Summary
   - Implement gRPC servers in `src/core/nlp_insights/server.py`
   - Implement gRPC servers in `src/core/summary_generator/server.py`

2. **Phase 2: Redis Streams Integration**
   - Replace WebSocket push with Redis pub/sub
   - Implement stream consumers in orchestrator
   - Add backpressure handling

3. **Phase 3: ML Service Deployment**
   - Dockerfiles with GPU support (already in place)
   - Health checks and readiness probes
   - Horizontal Pod Autoscaling (HPA) configurations

4. **Phase 4: Load Balancing**
   - gRPC load balancing strategies
   - Service mesh evaluation (Istio/Linkerd)
   - Circuit breakers and retries

### Deliverables
- gRPC service implementations (~800 lines total)
- Redis stream consumers in orchestrator (~500 lines)
- Updated `docker-compose.yml` with Redis configuration
- Performance benchmarks (target: 1000 req/s per service)

### Dependencies
- **Requires:** Redis 7.0+, gRPC Python libraries
- **Blocks:** Multi-user support, horizontal scaling

### Effort Estimate
- **Phase 1:** 3-4 days
- **Phase 2:** 3-4 days
- **Phase 3:** 2-3 days
- **Phase 4:** 3-5 days
- **Total:** ~2-3 weeks

### Success Criteria
- [ ] NLP service responds to gRPC calls with <50ms latency
- [ ] Summary service handles 100+ concurrent requests
- [ ] Redis streams deliver messages with <10ms overhead
- [ ] Services auto-scale based on CPU/memory thresholds
- [ ] End-to-end pipeline latency remains <500ms

---

## Track 3: Frontend Enhancement

### Objective
Complete Material-UI integration, add real-time audio visualization, and implement advanced user controls.

### Motivation
- **Current:** Basic transcription/insights/summary panels
- **Target:** Professional, polished UI with rich features
- **Benefit:** Better UX, competitive product appearance, demo-ready

### Scope
1. **Phase 1: Material-UI Completion**
   - Finish `AppLayout.tsx` and `StatusBar.tsx` integration
   - Apply consistent theming across all panels
   - Add dark mode toggle

2. **Phase 2: Audio Visualization**
   - Implement `AudioVisualizer.tsx` with real-time waveform
   - Add volume meter and clipping indicator
   - Integrate with WebSocket audio stream

3. **Phase 3: Advanced Controls**
   - Multi-session management (start/stop/pause)
   - Audio device selection dropdown
   - Configuration panel (sample rate, buffer size, etc.)
   - Export transcriptions (TXT, JSON, SRT)

4. **Phase 4: Dashboard**
   - Real-time metrics dashboard (`MetricsDashboard.tsx`)
   - Latency charts (STT, NLP, Summary)
   - Error rate and uptime displays

### Deliverables
- Completed Material-UI components (~1,200 lines)
- Audio visualizer with WebAudio API integration
- Configuration persistence (localStorage + backend)
- User guide documentation

### Dependencies
- **Requires:** Material-UI v5, D3.js or Chart.js
- **Blocks:** None (UI-only enhancements)

### Effort Estimate
- **Phase 1:** 2-3 days
- **Phase 2:** 3-4 days
- **Phase 3:** 3-4 days
- **Phase 4:** 2-3 days
- **Total:** ~2 weeks

### Success Criteria
- [ ] All panels use Material-UI components
- [ ] Audio visualizer displays real-time waveform at 60fps
- [ ] Device selection works on all platforms
- [ ] Dashboard updates metrics every 1s
- [ ] Export feature generates valid SRT subtitles

---

## Track 4: Observability Stack

### Objective
Deploy Prometheus, Grafana, and distributed tracing for production monitoring and debugging.

### Motivation
- **Current:** Log-based debugging only
- **Target:** Metrics, traces, and alerts
- **Benefit:** Proactive issue detection, performance insights, SLA monitoring

### Scope
1. **Phase 1: Metrics Collection**
   - Instrument FastAPI with `prometheus-fastapi-instrumentator`
   - Add custom metrics (transcription latency, queue depth, errors)
   - Deploy Prometheus in docker-compose

2. **Phase 2: Visualization**
   - Grafana dashboards for system health
   - Latency percentile charts (p50, p95, p99)
   - Service dependency graphs

3. **Phase 3: Distributed Tracing**
   - OpenTelemetry integration
   - Jaeger or Tempo backend
   - Trace context propagation across services

4. **Phase 4: Alerting**
   - Alertmanager configuration
   - Slack/email notifications
   - On-call rotation setup (PagerDuty/Opsgenie)

### Deliverables
- `docker-compose.observability.yml` with Prometheus/Grafana/Jaeger
- 5+ Grafana dashboards (overview, STT, NLP, summary, errors)
- Alerting rules for critical metrics (>500ms latency, >5% error rate)
- Runbook for common incidents

### Dependencies
- **Requires:** Prometheus, Grafana, OpenTelemetry
- **Blocks:** Production deployment, SLA guarantees

### Effort Estimate
- **Phase 1:** 2-3 days
- **Phase 2:** 2-3 days
- **Phase 3:** 3-4 days
- **Phase 4:** 2-3 days
- **Total:** ~2 weeks

### Success Criteria
- [ ] Metrics scraped every 15s from all services
- [ ] Grafana displays real-time latency with <1s delay
- [ ] Traces span from WebSocket ingestion to final response
- [ ] Alerts fire within 1 minute of threshold breach
- [ ] Zero instrumentation overhead (<1% CPU/memory)

---

## Track 5: Mobile Applications

### Objective
Build iOS and Android apps with WebSocket streaming and push notifications.

### Motivation
- **Current:** Desktop-only application
- **Target:** Mobile-first transcription on the go
- **Benefit:** Accessibility, meetings, interviews, accessibility features

### Scope
1. **Phase 1: React Native Setup**
   - Initialize React Native project with TypeScript
   - Share WebSocket client code from desktop app
   - Audio recording permissions (iOS AVFoundation, Android MediaRecorder)

2. **Phase 2: Core Features**
   - Real-time audio capture from microphone
   - WebSocket streaming to backend
   - Display live transcriptions
   - Background recording support

3. **Phase 3: Platform-Specific**
   - iOS: CallKit integration for call transcription
   - Android: Foreground service for persistent recording
   - Push notifications for completed summaries

4. **Phase 4: App Store Submission**
   - Privacy policy and terms of service
   - App Store screenshots and descriptions
   - Beta testing via TestFlight/Google Play Beta

### Deliverables
- React Native app (~5,000 lines)
- iOS and Android builds
- App Store listings (screenshots, descriptions)
- Mobile-specific backend endpoints (if needed)

### Dependencies
- **Requires:** React Native, Expo (optional), backend HTTPS
- **Blocks:** None (standalone feature)

### Effort Estimate
- **Phase 1:** 1 week
- **Phase 2:** 2-3 weeks
- **Phase 3:** 1-2 weeks
- **Phase 4:** 1 week (+ app review time)
- **Total:** ~1.5-2 months

### Success Criteria
- [ ] Record audio on iOS and Android
- [ ] Stream to backend with <500ms latency
- [ ] Display transcriptions in real-time
- [ ] Background recording works for 1+ hour
- [ ] Push notifications delivered within 5s
- [ ] App approved on both stores

---

## Track 6: Multi-Language Support

### Objective
Add language detection, multi-language Whisper models, and optional translation.

### Motivation
- **Current:** English-only transcription
- **Target:** Support 50+ languages
- **Benefit:** Global market, international users, translation services

### Scope
1. **Phase 1: Language Detection**
   - Integrate `langdetect` or Whisper's language detection
   - Auto-select Whisper model variant
   - UI language selector

2. **Phase 2: Multi-Language Models**
   - Deploy Whisper multilingual models (medium, large)
   - Model switching based on detected language
   - Fallback to English if confidence low

3. **Phase 3: Translation**
   - Optional translation to English (or target language)
   - Use MarianMT or NLLB models
   - Display original + translated transcriptions side-by-side

4. **Phase 4: Localization**
   - UI strings in multiple languages (i18n)
   - React Intl or similar library
   - RTL layout support (Arabic, Hebrew)

### Deliverables
- Language detection service (~300 lines)
- Multi-language Whisper deployment
- Translation service integration (~500 lines)
- Localized UI (5+ languages)

### Dependencies
- **Requires:** Whisper multilingual, translation models
- **Blocks:** None (optional feature)

### Effort Estimate
- **Phase 1:** 3-4 days
- **Phase 2:** 1 week
- **Phase 3:** 1-2 weeks
- **Phase 4:** 1 week
- **Total:** ~1 month

### Success Criteria
- [ ] Detect language with >95% accuracy
- [ ] Transcribe 50+ languages with <10% WER
- [ ] Translate to English with acceptable quality (BLEU >30)
- [ ] UI supports 5+ languages (EN, ES, FR, DE, ZH)
- [ ] RTL layouts render correctly

---

## Track 7: Testing & CI/CD

### Objective
Implement comprehensive automated testing and continuous integration/deployment pipelines.

### Motivation
- **Current:** Manual testing only
- **Target:** Automated E2E, performance, and regression tests
- **Benefit:** Faster releases, fewer bugs, confidence in deployments

### Scope
1. **Phase 1: Unit Test Coverage**
   - Achieve 80%+ coverage for core modules
   - Mock ML services for fast tests
   - Use `pytest` with fixtures

2. **Phase 2: Integration Tests**
   - E2E audio pipeline tests (already started)
   - WebSocket streaming tests
   - gRPC service tests

3. **Phase 3: Performance Tests**
   - Latency benchmarks with pass/fail thresholds
   - Throughput tests (concurrent users)
   - Memory leak detection

4. **Phase 4: CI/CD Pipeline**
   - GitHub Actions workflows for test/build/deploy
   - Docker image builds and pushes
   - Automated deployment to staging environment
   - Rollback mechanisms

### Deliverables
- 80%+ unit test coverage
- E2E test suite with 50+ scenarios
- GitHub Actions workflows (`.github/workflows/`)
- Deployment playbooks (Ansible or Terraform)

### Dependencies
- **Requires:** pytest, pytest-asyncio, GitHub Actions
- **Blocks:** Production deployment

### Effort Estimate
- **Phase 1:** 1 week
- **Phase 2:** 1 week
- **Phase 3:** 3-4 days
- **Phase 4:** 1 week
- **Total:** ~3 weeks

### Success Criteria
- [ ] All tests run in <5 minutes
- [ ] CI pipeline triggers on every PR
- [ ] Failed tests block merges
- [ ] Automated deployments to staging after merge
- [ ] Zero downtime deployments with health checks

---

## Priority Matrix

### Critical Path (Must-Have for Production)
1. **Track 2: Production ML Services** - Core architecture
2. **Track 7: Testing & CI/CD** - Deployment reliability
3. **Track 4: Observability Stack** - Production monitoring

### High Priority (Major Value/Quick Wins)
4. **Track 1: WASAPI Native Driver** - Windows production quality
5. **Track 3: Frontend Enhancement** - User experience

### Medium Priority (Competitive Differentiation)
6. **Track 6: Multi-Language Support** - Global reach
7. **Track 4: Observability Stack (Advanced)** - Tracing and alerting

### Low Priority (Future Expansion)
8. **Track 5: Mobile Applications** - New platform

---

## Recommended Execution Sequence

### Wave 4A: Production Readiness (6-8 weeks)
**Focus:** Stability, scalability, observability

1. **Weeks 1-2:** Track 2 Phase 1-2 (gRPC + Redis)
2. **Weeks 3-4:** Track 7 Phase 1-3 (Testing)
3. **Weeks 5-6:** Track 4 Phase 1-2 (Metrics + Grafana)
4. **Weeks 7-8:** Track 2 Phase 3-4 (ML service deployment + load balancing)

**Deliverable:** Production-ready backend with monitoring

### Wave 4B: Enhanced User Experience (4-6 weeks)
**Focus:** UI polish, Windows native, features

1. **Weeks 1-2:** Track 3 Phase 1-2 (MUI + audio viz)
2. **Weeks 3-4:** Track 1 (WASAPI driver)
3. **Weeks 5-6:** Track 3 Phase 3-4 (advanced controls + dashboard)

**Deliverable:** Professional UI with native Windows audio

### Wave 4C: Global Expansion (4-6 weeks)
**Focus:** Multi-language, mobile, scale

1. **Weeks 1-2:** Track 6 Phase 1-2 (language detection + models)
2. **Weeks 3-6:** Track 5 Phase 1-3 (mobile app)

**Deliverable:** Multi-language support and mobile apps

---

## Alternative Approaches

### Approach A: Vertical Slice
**Strategy:** Complete one full feature end-to-end before starting another

**Example:** Finish Track 3 (frontend) entirely, then Track 2 (backend), then Track 4 (observability)

**Pros:** Clear milestones, demo-ready increments
**Cons:** Backend bottlenecks remain unaddressed longer

### Approach B: Horizontal Layers
**Strategy:** Work on all backend improvements first, then all frontend

**Example:** Tracks 2, 4, 7 together → Tracks 1, 3 together → Track 5, 6

**Pros:** Solid foundation before adding features
**Cons:** No visible progress for weeks

### Approach C: Parallel Teams (Recommended)
**Strategy:** Split into 2-3 concurrent tracks based on team size

**Example:**
- **Team 1 (Backend):** Track 2 + 7
- **Team 2 (Frontend):** Track 3 + 1
- **Team 3 (DevOps):** Track 4

**Pros:** Fastest overall progress, specialization
**Cons:** Requires coordination, merge conflicts

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| WASAPI COM complexity | Medium | Medium | Start with PortAudio fallback working |
| gRPC latency overhead | Low | High | Benchmark early, optimize proto |
| Mobile app store rejection | Medium | Medium | Review guidelines, privacy policy |
| Translation model quality | Medium | Medium | Use established models (NLLB) |
| Observability overhead | Low | Medium | Profile before/after instrumentation |
| Multi-team coordination | High | Medium | Daily standups, clear interfaces |

---

## Success Metrics (Wave 4)

### Performance
- **Latency:** Maintain <500ms end-to-end (95th percentile)
- **Throughput:** Support 100+ concurrent users per backend instance
- **Uptime:** Achieve 99.9% availability

### Quality
- **Test Coverage:** 80%+ for core modules
- **Bug Density:** <0.5 critical bugs per 1,000 lines of code
- **Code Review:** 100% of changes reviewed before merge

### User Satisfaction
- **UI Responsiveness:** <100ms click-to-action
- **Error Rate:** <1% failed transcriptions
- **Feature Adoption:** 80%+ of users enable audio visualization

---

## Next Steps

1. **Review this roadmap** with stakeholders and prioritize tracks
2. **Assign teams/individuals** to tracks based on skills
3. **Create GitHub Projects** for each track with milestones
4. **Schedule kickoff meetings** for Wave 4A
5. **Set up weekly sync meetings** for coordination

---

## Appendix: Resource Estimates

### Team Size Recommendations

**Minimum Viable Team (1-2 developers):**
- Focus on Track 2 + 7 only
- Timeline: 12-16 weeks for production-ready

**Optimal Team (3-4 developers):**
- Parallel tracks: 2 + 7, 1 + 3, 4
- Timeline: 8-10 weeks for Wave 4A+4B

**Full Team (5+ developers):**
- All tracks in parallel
- Timeline: 6-8 weeks for Wave 4A+4B+4C

### Infrastructure Costs (Monthly)

- **Development:** $200-500 (cloud VMs, GPU instances)
- **Staging:** $500-1,000 (persistent environment)
- **Production:** $2,000-5,000 (multi-region, HA, backups)
- **Observability:** $100-300 (Grafana Cloud, Datadog)

---

**Document Version:** 1.0
**Last Updated:** November 23, 2025
**Next Review:** Start of Wave 4 planning
