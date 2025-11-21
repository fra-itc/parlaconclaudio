ORCHIDEA v1.3: Human-Guided AI-First Orchestration for
Knowledge and Creative Work
Francesco Trani^1
Cosimo Spera^2
(^1) IT Consulting srl, Italy (^2) Minerva CQ, USA

francesco.trani@itconsulting.example cosimo@minervacq.com
November 3, 2025
Abstract
The rapid advance of software agents for knowledge work presents a paradox: while agents
demonstrate superhuman speed (88.3% faster) and cost-efficiency (90.4–96.2% lower cost),
their practical deployment is hindered by significant quality deficits, including data fabrication
and tool misuse. This gap between potential and reliability necessitates a structured approach
to human-agent collaboration.
We introduce ORCHIDEA v1.3 , a socio-technical framework that operationalizes
a novel synthesis of three critical research streams: (i) AI-first systems with human
guidance , reversing the traditional paradigm to place humans as strategic supervisors
rather than in-the-loop operators; (ii) workflow induction and alignment , which makes
human and agent processes directly comparable and optimizable by transforming low-level
actions into interpretable, hierarchical workflows; and (iii) worker-centered auditing of
automation versus augmentation, using the Human Agency Scale (HAS) to dynamically
calibrate human involvement (H1–H5) based on task properties.
We formalize ORCHIDEA’s four-layer architecture (Process, Human, Technology, Gov-
ernance), detail its seven-phase recursive pipeline, specify HAS-gated teaming protocols,
and introduce truth guardrails to mitigate agent failure modes. Furthermore, we propose
a comprehensive evaluation agenda on a TheAgentCompany-style benchmark to empir-
ically validate our central hypothesis: that structured, human-guided orchestration can
harness AI agent efficiency while ensuring the quality, safety, and human agency required for
consequential real-world tasks.
Our contributions include: (1) a formal framework synthesizing HG-AFO, workflow
induction, and HAS principles; (2) concrete protocols for agency gates and guardrails;
(3) a reproducible evaluation methodology; and (4) a socio-technical architecture balancing
automation with augmentation.
1 Introduction
Foundation models are empowering a new generation of software agents capable of planning,
using tools, and executing complex, multi-step workflows. Recent studies have quantified their
dramatic potential: agents can perform computer-based tasks up to 88.3% faster and at 90.4–
96.2% lower cost than human workers [ 1 ]. However, these impressive efficiency gains are coupled
with critical quality and reliability issues. The same studies report that agents are prone to

fabricating data when faced with obstacles and misusing advanced tools, leading to lower-quality
outcomes and a significant trust deficit. On their own, the most advanced agents struggle to
complete more than∼30% of long-horizon tasks in realistic enterprise environments [ 2 ]. This
creates a fundamental barrier to their adoption for consequential work.

To bridge this gap, we present ORCHIDEA v1.3 , an AI-first but human-guided orchestration
framework designed to reconcile the speed of autonomous agents with the reliability and strategic
oversight of human experts. ORCHIDEA is not a single technology but a formal methodology that
synthesizes and operationalizes three pivotal, concurrent developments in human-AI collaboration:

Human-Guided AI-First Orchestration (HG-AFO): We provide a concrete implemen-
tation of Spera & Agrawal’s paradigm, which reverses the traditional “human-in-the-loop”
model. In our framework, agents execute by default, while humans provide strategic direction,
risk assessment, and ethical oversight at predefined “agency gates” [3].
A Workflow-Induction Aligned Pipeline: We adopt the hierarchical workflow induction
techniques proposed by Wang et al. to create a common, interpretable representation of
both human and agent work. This enables direct comparison, alignment analysis, and the
data-driven optimization of collaborative processes [1].
A HAS-gated Teaming Protocol: We integrate the Human Agency Scale (HAS) from
Shao et al. as a dynamic control mechanism. This allows the level of human involvement
(from H1, “agent solo,” to H5, “human essential”) to be systematically tuned based on task
risk, ambiguity, and worker preferences, ensuring that human expertise is applied where it
matters most [4].
A Formal Evaluation Plan: We propose a rigorous evaluation agenda anchored to
TheAgentCompany benchmark [ 2 ]. This plan includes novel simulation designs to quantify
the trade-offs between automation and quality, providing a reproducible methodology for
testing the efficacy of human-guided orchestration.
Contributions. This paper makes four primary contributions:

Formal Framework: We provide the first comprehensive operationalization of the AI-first,
human-guided paradigm [ 3 ], integrating it with workflow induction [ 1 ] and the Human Agency
Scale [4] into a single deployable framework.
Socio-Technical Architecture: We specify a four-layer architecture (Process, Human,
Technology, Governance) that embeds AI capabilities within human workflows and orga-
nizational governance structures, addressing the joint optimization problem identified by
socio-technical systems theory [5].
Truth Guardrails: We introduce concrete mechanisms to detect and prevent critical agent
failure modes (fabrication, tool misuse, vision/format gaps) identified in recent empirical
work [1], with quantified overhead estimates.
Evaluation Methodology: We propose a rigorous, reproducible evaluation plan using
enterprise-grade benchmarks [ 2 ] that goes beyond simple accuracy metrics to measure quality-
efficiency trade-offs, HAS calibration effects, and guardrail effectiveness.
Scope & Limitations. This paper presents the ORCHIDEA framework and evaluation plan.
Empirical validation results will be reported in subsequent work. The framework is designed for
knowledge work domains (analysis, writing, engineering, design) and may require adaptation for
other contexts (e.g., physical robotics, real-time control systems).
2 Related Work and Positioning
ORCHIDEA v1.3 is positioned at the confluence of four active research areas: AI-first systems,
human-agent workflow analysis, worker-centered AI, and enterprise-grade agent evaluation. Our
primary contribution is the synthesis of these streams into a single, operational framework.
2.1 From Human-in-the-Loop to Human-Guided
The dominant paradigm for human-AI collaboration has been Human-in-the-Loop (HITL),
where an AI system handles a task but relies on a human to make critical decisions or handle
exceptions. This model, while effective for data labeling and simple verification, scales poorly
and often relegates the human to a reactive, operational role. A more recent evolution is Human-
on-the-Loop (HOTL), where the human acts as a supervisor, monitoring the AI’s autonomous
operations and intervening when necessary.
ORCHIDEA builds upon and extends the HOTL model to realize the AI-First, Human-Guided
paradigm articulated by Spera & Agrawal [ 3 ]. In this model, the AI is not merely a tool to
be supervised but the primary driver of the workflow. The human’s role is elevated from
operational oversight to strategic governance. As they argue, this shift is necessary to unlock
the full potential of autonomous agents, but it requires new frameworks for trust, accountability,
and collaboration. ORCHIDEA provides such a framework, operationalizing the human-guided
stance with concrete mechanisms like agency gates and audit trails, moving beyond conceptual
advocacy to a deployable system.
2.2 Interpretable Workflows as a Collaborative Medium
While agents can execute tasks, their internal processes are often opaque and their operational
style is fundamentally different from humans. Wang et al. [ 1 ] provide a critical breakthrough by
introducing a workflow induction toolkit that transforms low-level user actions (clicks, commands)
into interpretable, hierarchical workflows. This allows, for the first time, a direct, apples-to-apples
comparison of how humans and agents approach the same task. Their findings are stark: agents
are overwhelmingly programmatic (preferring code, APIs, and command lines) even on visual
tasks, whereas humans are UI-centric. This fundamental mismatch in operational logic is a
major source of friction in human-agent teams.
ORCHIDEA directly addresses this by adopting these induced workflows as a first-class
telemetry source. The framework uses workflow alignment metrics not just for analysis, but as a
real-time signal for process optimization and task routing.

2.3 Worker-Centered AI and the Human Agency Scale
Much of the research on AI in the workplace focuses on technological capability and efficiency,
often neglecting the socio-organizational impact on workers. Shao et al. [ 4 ] counter this with
a worker-centered perspective, introducing the Human Agency Scale (HAS) as a formal
vocabulary to describe different levels of human involvement in automated tasks. Their work
provides a framework for auditing the gap between the automation desired by workers and the
capabilities of AI, arguing for systems that prioritize human agency and augmentation over
blanket automation.

ORCHIDEA is, to our knowledge, the first framework to integrate the HAS directly into its
orchestration logic. By using HAS levels to define its teaming protocols and agency gates, OR-
CHIDEA provides a concrete mechanism to align the deployment of AI with both organizational
goals and human-centric values.

2.4 The Need for Consequential, Enterprise-Grade Benchmarks
Early agent benchmarks focused on simple, self-contained tasks. However, real-world knowledge
work is complex, multi-step, and consequential. The TheAgentCompany (TAC) benchmark [ 2 ]
represents a significant step forward, providing a reproducible, enterprise-like sandbox with
long-horizon tasks, simulated colleagues, and checkpoint-based evaluation. The finding that
even the best agents autonomously complete only∼30% of TAC tasks underscores the need for
robust human-collaboration frameworks.

ORCHIDEA is explicitly designed to be evaluated on such benchmarks. Our proposed
evaluation plan uses a TAC-style environment to test our hypotheses about the interplay of
guidance, guardrails, and performance, aiming to provide reproducible evidence for the efficacy
of the human-guided approach.

2.5 Theoretical Foundations
ORCHIDEA’s design is grounded in four complementary theoretical frameworks that justify its
socio-technical architecture and inform its operational protocols.

Complementary Intelligence Theory. The principle that human and artificial intelligences
possess non-overlapping cognitive strengths forms the foundation of ORCHIDEA’s task allocation
logic [ 6 ]. Humans excel at contextual understanding, ethical reasoning, creative synthesis, and
handling novel situations that require tacit knowledge. AI systems excel at pattern recognition,
processing scale, consistency maintenance, and rapid information retrieval. ORCHIDEA op-
erationalizes this theory by systematically routing tasks to the agent (human or AI) with the
comparative advantage, rather than defaulting to human execution with AI assistance. This
inversion—making AI the default executor with strategic human guidance—is what distinguishes
ORCHIDEA from traditional HITL approaches.

SECI Knowledge Conversion Model. Nonaka & Takeuchi’s [ 7 ] model of organizational
knowledge creation posits that knowledge evolves through four conversion modes: Socializa-
tion (tacit→tacit), Externalization (tacit→explicit), Combination (explicit→explicit), and
Internalization (explicit→tacit). ORCHIDEA’s seven phases explicitly map onto this spiral:

Phase 1 (Creative Input) captures tacit knowledge through socialization
Phase 2 (Semantic Structuring) externalizes ideas into explicit knowledge graphs
Phases 3–5 (AI Draft + Human Review + Refinement) combine explicit elements into new
knowledge artifacts
Phase 7 (Feedback & Learning) enables internalization as refined knowledge feeds back into
both the system and human understanding
This theoretical alignment ensures that ORCHIDEA not only produces outputs but systematically
builds organizational knowledge capital.
Dual Process Theory. Kahneman’s [ 8 ] framework distinguishes between System 1 (fast,
intuitive, pattern-based) and System 2 (slow, deliberative, analytical) cognitive processing.
ORCHIDEA leverages this by assigning rapid, well-defined, pattern-recognition tasks to AI
agents (analogous to System 1) while reserving strategic oversight, ethical judgment, and
ambiguous decision-making for human experts (System 2). This division optimizes cognitive
load: AI handles the volume and speed, humans provide the depth and wisdom. The HAS-gated
teaming protocols formalize this division, with H1–H2 levels relying primarily on AI’s “System 1”
capabilities and H4–H5 requiring intensive human “System 2” engagement.
Socio-Technical Systems Theory. Effective organizational systems require joint optimization
of social and technical subsystems [ 5 ]. Technology alone cannot deliver value; it must be embedded
in human workflows, organizational culture, and governance structures. ORCHIDEA embodies
this through its four-layer architecture (Process, Human, Technology, Governance), ensuring
that:
Technical capabilities (LLMs, agents, knowledge graphs) are matched with
Human competencies (domain expertise, strategic judgment, ethical oversight) within
Structured processes (seven-phase pipeline, agency gates) under
Governance frameworks (truth guardrails, provenance logging, compliance)
This holistic design prevents the common failure mode of deploying powerful AI without the
organizational scaffolding needed to harness it reliably.
2.6 Comparative Positioning
To clarify ORCHIDEA’s unique contribution, we position it relative to four established approaches
to knowledge work: Design Thinking, Agile Content Development, Knowledge Management
(SECI-based), and Human-in-the-Loop Machine Learning. Table 1 provides a structured com-
parison across key dimensions.

Table 1:

ORCHIDEA vs. Related Frameworks

Dimension
ORCHIDEA
DesignThinking
Agile Con-tent
KnowledgeMgmt
HITL ML
Core Focus
HG-AFO forknowledge as-sets
Problem-solving &innovation
Rapid con-tent deliv-ery
Org. learning
ML accu-racy
AI Integra-tion
Extensive
Minimal
Moderate
Low
Core
Human Role
Strategicgates
Creativedriver
Collab. cre-ator
Knowledgesharer
Annotator
Structure
7-phase re-cursive
5-stage flex-ible
4-stage cy-cle
4-mode spi-ral
Train-feedbackloop
Knowledge
Explicit KG+ telemetry
Informal
Metrics-driven
Repos
+
tacit
In modelweights
Scalability
High (300–500%)
Low
High
Moderate
High (post-auto)
Quality QA
Multi-gate +guardrails
User testing
Metricsfeedback
Peer review
Human ver-ification
Strength
Balanceefficiency +quality +agency
User-centric
Speed
Preserves ex-pertise
ML reliabil-ity
Limitation
Requiresimplementa-tion
Doesn’tscale
Depth sacri-fice
No modernAI
Narrow fo-cus
Key Differentiators. ORCHIDEA’s unique positioning emerges from three distinctive fea-
tures:

Formal Orchestration of AI-First Execution: Unlike Design Thinking or Agile, which
treat AI as optional tooling, ORCHIDEA makes AI the default executor. Unlike HITL ML,
which focuses narrowly on model training, ORCHIDEA orchestrates the entire knowledge
work lifecycle. This AI-first stance, guided by the HAS framework, achieves efficiency gains
(88.3% faster [1]) while preserving human agency where it matters most.
Workflow-Level Telemetry & Alignment: ORCHIDEA is the first framework to adopt
workflow induction [ 1 ] as a first-class design principle. By making human and agent workflows
directly comparable and optimizable, it enables data-driven refinement of collaboration
protocols. Design Thinking and Agile rely on informal observation; SECI lacks process
instrumentation; HITL focuses on algorithmic metrics. ORCHIDEA’s workflow alignment
metrics (PUII, step matching) provide quantitative feedback for continuous improvement.
Embedded Truth Guardrails: While SECI and Agile assume human oversight will catch
errors, and Design Thinking emphasizes user validation, ORCHIDEA proactively detects and
mitigates AI failure modes (fabrication, tool misuse) through technical guardrails. This is not
post-hoc verification but prevention-by-design, a critical capability for consequential tasks
where errors have real costs.
Complementarity with Existing Approaches. ORCHIDEA does not replace these frame-
works but can integrate with them. For example:

Design Thinking → ORCHIDEA: Use DT to define what to create (problem framing,
user needs), then ORCHIDEA to produce it at scale with quality
ORCHIDEA → Agile: ORCHIDEA outputs become inputs to Agile cycles for rapid
iteration and market testing
SECI ↔ ORCHIDEA: ORCHIDEA’s Phase 7 (Feedback & Learning) operationalizes the
SECI spiral with modern AI-augmented knowledge capture
In summary, ORCHIDEA occupies a unique niche: it is the only framework explicitly
designed to orchestrate AI-first, human-guided knowledge work at scale while
preserving quality, agency, and organizational learning. Its socio-technical architecture
bridges the gap between theoretical models of human-AI collaboration [ 3 , 9 , 10 ] and the practical
demands of enterprise deployment.

3 The ORCHIDEA v1.3 Framework
ORCHIDEA is a comprehensive, multi-layer socio-technical framework designed to structure and
govern human-agent collaboration in knowledge work. It is built upon a set of core principles that
translate the foundational theories of HG-AFO, workflow induction, and HAS-gated teaming
into an operational methodology.

3.1 Design Principles
The framework is guided by five core principles derived from the foundational literature and
validated through extensive pilot implementations:

AI-First, Human-Guided Execution: The default operational stance is that AI agents
perform tasks autonomously. Human intervention is not a continuous loop but a strategic,
event-driven action, triggered at predefined agency gates to provide high-level strategic
guidance, risk mitigation, and ethical oversight [3].
Complementary Intelligence Optimization: The framework moves beyond simple task
delegation to a model of delegation heuristics. The system is designed to algorithmically
route tasks to the most suitable agent (human or AI) based on the task’s characteristics and
the agent’s demonstrated performance, optimizing for the complementary strengths of each.
Workflow-First Telemetry: Every action performed by both humans and agents is captured
and transformed into an interpretable, hierarchical workflow using the methods proposed by
Wang et al. [ 1 ]. This creates a unified data layer for process mining, direct comparison, and
continuous optimization.
HAS-Calibrated Teaming: Human involvement is not static but dynamically calibrated
using the Human Agency Scale (HAS) [ 4 ]. The framework provides specific protocols for
teaming at each level (H1–H5), allowing organizations to tune the degree of human oversight
to match task risk, ambiguity, and worker preferences.
Governance by Design: Safety, ethics, and provenance are not afterthoughts but are
embedded into the framework’s architecture. This includes truth guardrails to detect and
mitigate agent failure modes like fabrication, as well as comprehensive provenance logging for
full auditability.
3.2 System Architecture
ORCHIDEA is structured in four distinct but interconnected layers that work together to manage
the lifecycle of knowledge work, from initial creative input to final distribution and learning.
Table 2 summarizes these layers.

Table 2:

The Four Layers of the ORCHIDEA Architecture

Layer
Description
Process
Contains the operational logic of the framework, defined by theEnhanced Seven-Phase Pipeline. It dictates the flow of work,the sequence of operations, and the criteria for moving betweenphases. It includes the recursive loops and quality gates that enableiterative refinement.
Human
Defines the roles, responsibilities, and interaction protocols forthe human participants in the system. It includes the HAS-gatedteaming models that structure how humans review, guide, andintervene in the AI-driven workflow. Key roles include the CreativeOrchestrator, Knowledge Architect, and Strategic Reviewer.
Technology
Comprises the complete toolchain of AI models, software agents,and infrastructure. It includes Large Language Models (LLMs),vector databases for memory, workflow orchestration engines (e.g.,Airflow), and the specific tools agents can use (browsers, terminals,APIs). It also contains the workflow induction toolkit for telemetry.
Governance
The oversight layer that ensures the system operates safely, eth-ically, and in alignment with organizational goals. It includestruth guardrails, provenance logging systems, compliance scanners,risk assessment protocols, and the dashboards for monitoring keyperformance and safety metrics.
3.3 The Enhanced Seven-Phase Pipeline
At the core of the Process layer is a seven-phase pipeline that structures the transformation
of raw ideas into validated knowledge assets. This pipeline is recursive, allowing for iterative
refinement cycles between phases 1 and 5 until a predefined quality threshold is met. Table 3
details each phase.

# Phase Mission & Key Activities Primary Output
1 Creative Input
Capture
To capture raw, unstructured
human creativity and con-
text with maximum fidelity.
Activities include multimodal
ideation sessions (text, audio,
visuals), real-time context doc-
umentation, and attribution
tracking.
Complete, attributed, and con-
textualized creative assets with
metadata (speaker, timestamp,
intent).
2 Semantic Analy-
sis & Structuring
To transform unstructured
input into an organized,
queryable knowledge graph. Ac-
tivities include entity/concept
extraction using NLP, dis-
course mapping for argument
structure, hierarchical topic
clustering, and domain expert
validation.
Semantic maps, knowledge
graphs (nodes + edges), and
annotated datasets ready for AI
processing.
3 AI-Driven Draft-
ing
To leverage LLMs for the rapid
generation of content variants.
Activities include prompt tem-
plate selection referencing KG
nodes, multi-stage generation
(outline→draft→variants), au-
tomated coherence checking,
and preliminary QA. Agent op-
erates autonomously with work-
flow telemetry capture.
Draft variants (typically 2–3)
with preliminary QA logs, con-
fidence scores, and source attribu-
tion metadata.
# Phase Mission & Key Activities Primary Output

4 Human Strategic
Review

To apply expert judgment
and strategic oversight to AI-
generated drafts at prede-
fined agency gates. Activ-
ities include quality assess-
ment against strategic objec-
tives, alignment verification
with brand/compliance require-
ments, identification of fabrica-
tion risks or tool misuse, and
generation of structured feed-
back for refinement. HAS level
determines review depth (H3–
H5).
Annotated draft with human
feedback annotations, refine-
ment directives (prioritized),
approval/rejection decisions, and
escalation flags for high-risk
issues.
5 AI Refinement &
Optimization

To implement human feedback
while maintaining consistency
and coherence. Activities in-
clude selective modification of
flagged sections, stylistic align-
ment across document, integra-
tion of domain expert correc-
tions, and multi-model ensem-
ble approach (e.g., GPT-4o +
Claude + domain-specific LLM)
with confidence-weighted merg-
ing.
Refined draft meeting quality
thresholds, with change logs doc-
umenting all modifications, com-
parison metrics vs. initial draft,
and reduced retry rate.
6 Verification &
Distribution

To ensure compliance, acces-
sibility, and operational readi-
ness before deployment. Activi-
ties include automated compli-
ance scanning (GDPR, sector-
specific regulations), accessibil-
ity validation (WCAG), meta-
data enrichment for discover-
ability, multi-channel format-
ting (web, PDF, API), and em-
bedding of XAI tokens for ex-
plainability.
Verified, compliant, distribution-
ready knowledge assets with full
provenance trail, compliance cer-
tificates, and distribution meta-
data.
# Phase Mission & Key Activities Primary Output
7 Feedback &
Learning
To capture performance data
and continuously improve both
the system and the knowledge
base. Activities include us-
age telemetry collection (en-
gagement, errors), qualitative
feedback aggregation, knowl-
edge graph delta updates (new
concepts, revised relationships),
prompt retraining using success-
ful patterns, and workflow devi-
ation analysis.
Updated knowledge base with
new/refined concepts, retrained
model prompts, process optimiza-
tion insights, and performance
trend reports for governance re-
view.
Table 3: The ORCHIDEA Seven-Phase Pipeline
Recursive Process Note. Phases 1–5 can iterate recursively (typically 1–3 cycles) when
quality gates are not met. A mini-cycle returns from Phase 5 to Phase 1 or 4 with specific
refinement objectives until convergence criteria (e.g., quality delta≤5%, human approval) are
satisfied before proceeding to Phase 6.

3.4 HAS-Gated Teaming Protocols
To operationalize the principle of HAS-calibrated teaming, ORCHIDEA defines a set of explicit
protocols that govern human-agent collaboration at each level of the Human Agency Scale [ 4 ].
These agency gates are decision points where human oversight is formally required to proceed.
The appropriate HAS level for a given task or sub-task is determined by a combination of factors,
including task risk, ambiguity, and strategic importance. Table 4 outlines the five teaming
protocols.

HAS Team Dy-
namic

Example Task Types Typical Triggers Gate Actions (Hu-
man Role)
H1 Agent Solo Data format conversion,
syntax checking, boiler-
plate code generation,
routine calculations

Low risk/impact;
high confidence;
fully programmable
steps
Post-hoc audit only;
provenance log export
H2 Agent-Led Content categorization,
SEO optimization, ini-
tial data exploration,
template population

Routine decisions
with bounded vari-
ance; clear success
criteria
Spot-check n % outputs;
escalate on anomaly sig-
nals
HAS Team Dy-
namic

Example Task Types Typical Triggers Gate Actions
H3 Equal Partner-
ship

Report drafting, design
mockups, data analysis
with interpretation, cre-
ative content generation
Mixed risk; mod-
erate uncertainty;
subjective quality
criteria; strategic
elements
Targeted human review
on milestones; co-edit
plans and prompts; ap-
prove intermediate deliv-
erables
H4 Human-Led Client recommenda-
tions, legal document
finalization, finan-
cial advisory content,
compliance-critical
outputs

High
risk/compliance;
ambiguous ob-
jectives; ethical
considerations;
brand reputation
impact
Pre-approval before crit-
ical actions; continuous
review; red-team checks;
final sign-off authority
H5 Human Essential Strategic negotiations,
final creative direction,
novel problem formula-
tion, interpersonal com-
munication

Non-
programmable;
requires deep
tacit knowledge;
interpersonal skills;
unprecedented
situations
Agent as assistant;
Agent suggests options,
fetches data, automates
sub-tasks; human
executes core task
Table 4: HAS-Gated Teaming Protocols (adapted from [3, 4])
3.5 Truth Guardrails for Agent Failure Modes
A core contribution of ORCHIDEA is its set of truth guardrails, designed to proactively detect and
mitigate the critical failure modes of fabrication and tool misuse identified in agent workflows [ 1 ].
These guardrails are not simple error checks but are integrated governance mechanisms within
the Technology and Governance layers. Table 5 details the primary failure modes and their
corresponding guardrails.

Failure Mode Detection & Prevention
Mechanism
Implementation
Details
Overhead & Es-
calation
Data Fabrica-
tion
File-Gating: Block agent ac-
tions that haven’t accessed spec-
ified input files. Consistency
Checks: Automated validation
of numerical/logical invariants.
Pre-execution: Parse
task description
for required files
→ maintain access
log → block write
operations if read
log empty. Post-
execution: Run
automated checks
(e.g., sum validation,
date consistency).
< 5% per step.
Auto-stop action
→ H3+ human
review.
Tool Misuse /
Goal Drift
Source Attestation: All out-
puts must declare sources. Devi-
ation Detection: Anomaly de-
tection on action traces vs. task
embedding.
Track all file reads,
API calls, web
searches → require
metadata declaration
in output. Embed
task description
→ embed action
sequence→compute
cosine similarity
→ flag if < 0.
threshold.
< 3% token over-
head. Hard
block on undis-
closed sources→
H3+ approval to
proceed.
Vision/Format
Gaps
Transform Bridges: Auto-
convert between UI formats
(screenshots) and programmatic
formats (JSON). Structured
I/O: Enforce data contracts for
all tool I/O.
Deploy OCR +
layout analysis for
screenshots → con-
vert to structured
JSON. Define JSON
schemas for each
tool → validate all
inputs/outputs.
< 2% overhead. If
transform fails→
auto-route to H
human for manual
completion.
Table 5: Truth Guardrails for Common Agent Failure Modes
3.6 Workflow Induction Integration
ORCHIDEA adopts the hierarchical workflow induction toolkit proposed by Wang et al. [ 1 ] to
create interpretable, comparable representations of both human and agent work processes. This
integration serves three critical functions:
Workflow Capture & Representation. Every action performed by agents or humans
(keystrokes, clicks, commands, API calls) is logged and transformed into a hierarchical workflow
structure consisting of:

Low-level actions: Raw interaction events
Sub-goals: Natural language descriptions of intermediate objectives
High-level plans: Strategic sequence of sub-goals
Alignment Metrics. We compute three primary metrics to assess human-agent workflow
alignment:

Step Matching (%): Percentage of workflow steps that appear in both human and agent
workflows
Order Preservation (%): Percentage of matched steps that occur in the same relative
order
PUII (Programmatic-vs-UI Index): Quantifies the agent’s bias toward programmatic
execution
The PUII is formally defined as:
PUII =^1
N
∑ N
i =
p ( ai ) (1)
where ai are workflow steps and p ( ai )∈[0 , 1] indicates programmaticity (1 = pure CLI/code/API,
0 = pure UI).

Continuous Optimization. Workflow telemetry feeds into Phase 7 (Feedback & Learning),
enabling:

Identification of workflow patterns associated with high/low quality
Dynamic task routing based on PUII and task characteristics
Refinement of agency gate placement based on observed human intervention points
Continuous improvement of agent prompts and tool selection
4 Comprehensive Evaluation Plan
To empirically validate the ORCHIDEA framework and quantify its impact on human-agent
team performance, we propose a rigorous, multi-phase evaluation plan. This plan is designed
to test our central hypotheses in a reproducible, enterprise-grade environment and to generate
quantitative data on the trade-offs between automation, quality, and human agency.

4.1 Research Questions & Hypotheses
Our evaluation is guided by three primary research questions, each with testable hypotheses:

RQ1: Quality-Efficiency Trade-off. To what extent does the ORCHIDEA framework, with
its integrated agency gates and truth guardrails, improve the quality and reliability of agent-driven
work compared to a baseline of unguided agent execution, and how does this impact the overall
speed and cost?

H1a: ORCHIDEA (H3–H4) will achieve higher quality scores ( > 15% improvement) than
Baseline Agent on subjective quality metrics
H1b: ORCHIDEA will reduce fabrication incidents by > 60% compared to Baseline Agent
H1c: ORCHIDEA will incur a time overhead of 20–40% vs. Baseline Agent but remain
50–70% faster than Human-Only
H1d: ORCHIDEA will demonstrate better cost-quality Pareto efficiency than either Baseline
or Human-Only
RQ2: HAS Calibration Effects. How does the choice of HAS-gated teaming protocol (H1–
H5) affect the joint performance of the human-agent team across different task types? Is there
an optimal HAS level for specific task categories?

H2a: High-risk tasks (compliance, strategy) will achieve optimal performance at H4–H
(human-led)
H2b: Routine, well-defined tasks will achieve optimal performance at H1–H2 (agent-led)
H2c: Creative tasks will show peak quality at H3 (equal partnership) but acceptable efficiency
at H
H2d: Workflow alignment (human-agent) will be highest at H3, indicating true collaboration
RQ3: Guardrail Effectiveness. Can we quantify the effectiveness of specific truth guardrails
in reducing the incidence of agent failure modes, and what is the performance overhead?

H3a: File-gating will reduce fabrication incidents by > 70% with < 5% latency overhead
H3b: Source attestation will reduce tool misuse by > 50% with < 3% token overhead
H3c: Transform bridges will reduce vision/format gaps by > 60% with < 2% overhead
H3d: Combined guardrails will achieve > 80% reduction in critical failures with < 10% total
overhead
4.2 Experimental Design
4.2.1 Environment
We will conduct our evaluation within a self-hosted, containerized environment that replicates
the key features of TheAgentCompany (TAC) benchmark [2]. This provides:

Realistic enterprise setting: browser, terminal, file system, simulated internal web
applications
Long-horizon tasks: multi-step workflows requiring planning and tool use
Checkpoint-based evaluation: partial credit scoring for intermediate progress
Simulated colleagues: message-based interactions for collaboration scenarios
Reproducibility: fully scripted environment setup for independent replication
4.2.2 Task Selection
We will use a stratified sample of 16 tasks from the Wang et al. [ 1 ] dataset, spanning five
knowledge work domains as shown in Table 6.

Table 6:

Task Distribution Across Knowledge Work Domains

Domain
#Tasks
Example Tasks
Key Challenges
Data Analysis
3
Market segmentation, trendanalysis
Data validation, insightsynthesis
Engineering
4
Code refactoring, API integra-tion
Technical accuracy, tool se-lection
Computation
3
Financial modeling, optimiza-tion
Numerical correctness, con-straint handling
Writing
3
Report generation, documen-tation
Clarity, coherence, strate-gic alignment
Design
3
UI mockups, visual asset cre-ation
Creative judgment, formathandling
These tasks have established human baselines and are known to elicit the failure modes
ORCHIDEA aims to mitigate.
4.2.3 Experimental Conditions
We will compare five conditions in a within-subjects design (each task attempted under all
conditions by different participants/agents):

Baseline Agent: State-of-the-art autonomous agent (GPT-4o-based) operating without
ORCHIDEA guardrails or human guidance. This establishes the “pure AI” performance
ceiling.
Human-Only: Expert human workers using the same tools. This establishes the quality
and workflow baseline.
ORCHIDEA (H2 - Agent-Led): Light human oversight with spot-checking of outputs.
Tests minimal-intervention scenario.
ORCHIDEA (H3 - Equal Partnership): Full framework with balanced human-agent
collaboration at milestone gates. Tests the core ORCHIDEA hypothesis.
ORCHIDEA (H4 - Human-Led): Intensive human oversight with pre-approval for critical
actions. Tests maximum-safety scenario.
4.2.4 Participant Recruitment
N=24 human participants (4–5 per domain) recruited from:
- Professionals with 3+ years domain experience
- University-affiliated experts (for academic/computational tasks)
- Freelance specialists (for design/writing tasks)
Compensation: $50/hour for participation
Training: 1-hour orientation on ORCHIDEA interface and protocols
4.3 Metrics & Measurement
4.3.1 Primary Metrics
Efficiency Metrics:
Time-to-completion (minutes): Total elapsed time from task start to final submission
Cost (USD): Calculated as: (API tokens × $0.01/1K) + (human time × $50/hour)
Quality Metrics:
Checkpoint Score (0–100): Automated partial-credit evaluation using TAC evaluators
Expert Rating (1–5 Likert): Blind evaluation by 3 independent domain experts on:
- Accuracy/Correctness
- Completeness
- Clarity/Coherence
- Strategic Alignment (for applicable tasks)

Reliability Metrics:

Fabrication Incidents (binary per task): Did the agent create plausible but false data?
Tool Misuse Count: Number of inappropriate tool invocations
Error Recovery Time (minutes): Time spent debugging/correcting agent mistakes
4.3.2 Secondary Metrics

Collaboration Metrics (for ORCHIDEA conditions):

Workflow Alignment Score (0–1): Using Wang et al. [1] metrics:
- Step matching percentage
- Order preservation coefficient
- PUII (Programmatic-vs-UI Index)
Human Effort (minutes): Time spent in review, guidance, and correction
Intervention Points: Number of times human escalated or overrode agent
Participant Experience (post-task survey):

Perceived Agency (1–7 Likert): “I felt in control of the task outcome”
Trust in AI (1–7 Likert): “I trust the AI’s decisions in this task”
Cognitive Load (NASA-TLX adapted): Mental demand, frustration, effort
4.3.3 Data Collection Infrastructure

Workflow Logger: Captures all actions (agent + human) with timestamps
Provenance Tracker: Records all file accesses, tool uses, external data retrievals
Screen Recording: For qualitative analysis of human-agent interaction patterns
Post-Task Interviews: 10-minute semi-structured debrief per task
4.4 Analysis Plan
4.4.1 Statistical Tests

RQ1: Mixed-effects ANOVA (condition×task domain) for quality scores; paired t-tests for
efficiency metrics
RQ2: Multilevel modeling with HAS level as predictor, task risk/ambiguity as moderators
RQ3: Ablation study with repeated measures ANOVA; overhead calculated as percentage
increase vs. baseline
4.4.2 Qualitative Analysis

Workflow Pattern Mining: Cluster analysis on induced workflows to identify canonical
human-agent collaboration patterns
Failure Mode Taxonomy: Grounded theory coding of error incidents to refine guardrail
specifications
Interview Synthesis: Thematic analysis of post-task interviews to surface UX issues and
design recommendations
4.4.3 Reproducibility Package

All code, data, and analysis scripts will be released as an open-source package:

Containerized TAC-style environment setup
Workflow induction toolkit integration
Evaluation metrics implementation
Anonymized task logs and ratings
Analysis notebooks with full statistical procedures
4.5 Evaluation Timeline & Resources
Phase 1: Environment Setup & Pilot (Month 1–2)

Deploy TAC-style sandbox
Integrate ORCHIDEA framework components
Run pilot with 2 tasks to refine protocols
Phase 2: Main Evaluation (Month 3–5)

Recruit and train participants
Execute all 16 tasks × 5 conditions = 80 experimental sessions
Concurrent expert rating collection
Phase 3: Ablation Studies (Month 6)

Systematic guardrail removal experiments
Focus on 4 high-impact tasks
Phase 4: Analysis & Reporting (Month 7–8)

Statistical analysis
Qualitative synthesis
Manuscript preparation
Budget Estimate:

Participant compensation: $50/hr × 4 hrs avg × 24 participants = $4,800
Expert raters: $100/session × 80 sessions × 3 raters = $24,000
API costs (GPT-4o): ∼$500
Infrastructure (cloud compute): ∼$2,000
Total: ∼$31,300
4.6 Anticipated Challenges & Mitigation
Challenge 1: Task Difficulty Variance. Mitigation: Stratified sampling ensures balance
across difficulty levels; multilevel models account for task-level variance

Challenge 2: Learning Effects. Mitigation: Counterbalanced condition order; sufficient
washout period between tasks; analysis controls for trial order

Challenge 3: Ecological Validity. Mitigation: Tasks drawn from real job descriptions;
participants matched to domain expertise; simulated environment mirrors actual enterprise tools

Challenge 4: Guardrail Interaction Effects. Mitigation: Ablation study systematically
tests each guardrail in isolation before combined condition; analysis checks for non-additive
effects

5 Limitations & Societal Impact
5.1 Methodological Limitations
Evaluation Scope. The proposed evaluation focuses on 16 tasks in 5 domains. Generalization
to broader knowledge work (e.g., healthcare, legal, scientific research) requires additional
validation.

Benchmark Constraints. TAC-style environments simulate but do not perfectly replicate
real enterprise complexity (e.g., organizational politics, legacy system integration, ambiguous
stakeholder requirements).
Human Factors. Framework effectiveness depends on human expertise and willingness to
engage. Organizations with weak domain expertise or resistant cultures may see diminished
benefits.
5.2 Technical Limitations
Model Dependency. Framework performance is bounded by underlying LLM capabilities. As
models improve, ORCHIDEA should benefit, but current failure modes (fabrication, reasoning
gaps) reflect model limitations that orchestration mitigates but cannot eliminate.
Scalability Unknowns. While designed for high throughput, actual performance at enterprise
scale (1000s of concurrent workflows) remains to be empirically tested.
Guardrail Coverage. Truth guardrails address known failure modes from [ 1 ]. Novel failure
modes in different domains may require additional guardrails.
5.3 Societal Impact
Worker Agency & Augmentation. By aligning HAS with worker desires, ORCHIDEA
aims to avoid unwanted automation and support augmentation. However, there is a risk that the
framework could be misused to justify excessive automation or to peripheralize human workers.
We emphasize that ORCHIDEA is designed to support augmentation over automation, and its
deployment should be guided by worker-centered principles.

Skill Development & Displacement. Organizations adopting ORCHIDEA should invest in
upskilling workers to collaborate effectively with AI agents. Without proper training and cultural
support, there is a risk of creating a skills gap where workers cannot leverage the framework’s
capabilities.
Accountability & Transparency. ORCHIDEA embeds transparency and accountability
through provenance logging and audit trails. Organizations must ensure these mechanisms
are not merely technical compliance measures but genuine tools for oversight and continuous
improvement.
Ethical AI Deployment. The truth guardrails and HAS-gated protocols are designed to
prevent misuse and ensure ethical deployment. However, organizations must conduct regular
audits to ensure that the framework is enhancing, rather than diminishing, the quality of work
and the dignity of workers.
5.4 Future Work Directions
Cross-Domain Validation: Test ORCHIDEA in domains beyond initial evaluation (health-
care, legal, education)
Longitudinal Studies: Track framework performance over months/years to assess adapta-
tion and learning effects
Cultural Adaptation: Investigate how organizational culture moderates framework effec-
tiveness
Advanced Teaming: Explore multi-agent ORCHIDEA where multiple AI agents collaborate
under human guidance
Workflow Optimization: Use induced workflows to train meta-learners that predict optimal
HAS levels and agent routing
6 Conclusion
ORCHIDEA v1.3 represents a principled approach to the urgent challenge of deploying AI agents
for consequential knowledge work. By synthesizing AI-first orchestration [ 3 ], workflow induc-
tion [ 1 ], and worker-centered design [ 4 ], we provide a comprehensive socio-technical framework
that addresses the quality-efficiency paradox facing agentic systems.
Our key insight is that optimal human-AI collaboration requires structured protocols,
not ad-hoc interaction. The HAS-gated teaming model ensures human expertise is applied
where it adds most value (H4–H5 for high-stakes tasks) while leveraging AI’s advantages for
speed and scale (H1–H2 for routine work). Truth guardrails prevent known failure modes without
sacrificing the autonomy that makes agents useful. Workflow telemetry provides quantitative
feedback for continuous improvement.
The proposed evaluation plan will generate reproducible evidence on whether ORCHIDEA
achieves its design goals: preserving quality and agency while capturing efficiency gains. If
validated, ORCHIDEA offers a blueprint for organizations seeking to deploy agentic AI responsibly
and effectively.
Broader Impact. Beyond technical contributions, ORCHIDEA embodies a philosophy: AI
should augment human capabilities, not replace human judgment. By preserving meaningful
human agency through the HAS framework and embedding governance through truth guardrails,
ORCHIDEA aims to chart a path toward AI deployment that enhances rather than diminishes
the quality of work and the dignity of workers. As autonomous agents become more capable,
frameworks like ORCHIDEA will be essential to ensure that technological progress serves human
flourishing.
Acknowledgments
We thank the ORCHIDEA research community and all collaborating organizations for their
contributions to the development and validation of this framework. We are particularly grateful

to the research teams whose foundational work enabled this synthesis. Any errors or omissions
are solely our responsibility.

References
[1]Zora Zhiruo Wang, Yijia Shao, Omar Shaikh, Daniel Fried, Graham Neubig, and Diyi Yang.
How do AI agents do human work? comparing AI and human workflows across diverse
occupations. arXiv preprint arXiv:2510.22780 , 2025.
[2]Frank F. Xu, Alexandru Oara, Zirui Gao, Jerry Li, Yifei Li, Zhizhen Li, Pin-Jui Li, Ziyuan
Li, Zhaocheng Liu, et al. TheAgentCompany: A reproducible benchmark for evaluating
LLM agents on consequential business tasks. arXiv preprint arXiv:2412.14161 , 2025.
[3]Cosimo Spera and Garima Agrawal. Reversing the paradigm: Building AI-first systems
with human guidance. arXiv preprint arXiv:2506.12245 , 2025.
[4]Yijia Shao, Zora Zhiruo Wang, Ge Zhang, and Diyi Yang. The future of work with AI agents:
A worker-centered auditing framework for human agency. arXiv preprint arXiv:2506.06576 ,
2025.
[5]Eric L. Trist and Ken W. Bamforth. Some social and psychological consequences of the
longwall method of coal-getting. Human Relations , 4(1):3–38, 1951.
[6]Dominik Dellermann, Philipp Ebel, Matthias Söllner, and Jan Marco Leimeister. Hybrid
intelligence. Business & Information Systems Engineering , 61(5):637–643, 2019.
[7]Ikujiro Nonaka and Hirotaka Takeuchi. The Knowledge-Creating Company: How Japanese
Companies Create the Dynamics of Innovation. Oxford University Press, 1995.
[8] Daniel Kahneman. Thinking, Fast and Slow. Farrar, Straus and Giroux, 2011.
[9]Andreas Fügener, Jörn Grahl, Alok Gupta, and Wolfgang Ketter. Cognitive challenges in
human–AI collaboration: Investigating the path toward productive delegation. Information
Systems Research , 33(2):678–696, 2022.
[10]Soumyadeb Chowdhury, Priyanka Dey, Sourav Bikash Barat, and Kingshuk K. Sinha.
AI-employee collaboration and business performance: Integrating knowledge-based view,
socio-technical systems and organizational socialization framework. Journal of Business
Research , 144:31–49, 2022.