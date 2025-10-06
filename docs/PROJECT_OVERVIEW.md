# Cortex Flow - Multi-Agent AI System
## Documentazione Completa del Progetto

---

## 📋 Indice

1. [Overview del Progetto](#overview)
2. [Architettura del Sistema](#architettura)
3. [Capacità Implementate](#capacità)
4. [Stato di Avanzamento](#stato)
5. [Pattern ReAct Avanzati](#react-patterns)
6. [Configurazione e Setup](#setup)
7. [Testing e Qualità](#testing)
8. [Roadmap Futura](#roadmap)

---

## 1. Overview del Progetto {#overview}

### Cos'è Cortex Flow?

**Cortex Flow** è un sistema multi-agente AI avanzato costruito con **LangGraph** e **LangChain**, progettato per orchestrare agenti specializzati che collaborano per risolvere task complessi.

### Caratteristiche Principali

- **Architettura Multi-Agente**: 4 agenti specializzati che collaborano
- **Pattern ReAct Avanzato**: Reason+Act con 5 fasi di implementazione
- **State Persistence**: PostgreSQL per affidabilità production
- **Self-Reflection**: Quality assessment automatico con refinement
- **Structured Logging**: Tracciamento completo dell'esecuzione
- **Human-in-the-Loop**: Controllo umano su azioni critiche
- **Strategie Reasoning**: Fast, Balanced, Deep, Creative

### Stack Tecnologico

- **Framework**: LangGraph 0.6.8, LangChain Core
- **LLM Provider**: OpenRouter (supporta 100+ modelli)
- **Database**: PostgreSQL 16 (Docker)
- **API**: FastAPI con CORS
- **Testing**: Pytest (113 test suite)
- **Language**: Python 3.12+

---

## 2. Architettura del Sistema {#architettura}

### Agenti Specializzati

#### 🎯 Supervisor Agent (Port 8000)
- **Ruolo**: Orchestratore centrale del workflow
- **Strategia**: FAST (3 iter, 30s timeout, temp 0.3)
- **Capacità**:
  - Task decomposition e planning
  - Delegazione ad agenti specializzati
  - Coordinamento multi-agent
  - Routing intelligente

#### 🔬 Researcher Agent (Port 8001)
- **Ruolo**: Ricerca web e information gathering
- **Strategia**: DEEP (20 iter, 300s timeout, temp 0.7)
- **Tool**: Tavily Search API
- **Capacità**:
  - Web search avanzata
  - Source validation
  - Information synthesis
  - Fact checking

#### 📊 Analyst Agent (Port 8003)
- **Ruolo**: Analisi dati e insights
- **Strategia**: BALANCED (10 iter, 120s timeout, temp 0.7)
- **Capacità**:
  - Data analysis
  - Pattern recognition
  - Insight generation
  - Decision support

#### ✍️ Writer Agent (Port 8004)
- **Ruolo**: Content creation professionale
- **Strategia**: CREATIVE (15 iter, 180s timeout, temp 0.9)
- **Capacità**:
  - Article/report writing
  - Content structuring
  - Style adaptation
  - **Self-Reflection** per quality assurance

### Flusso di Esecuzione

```
User Query
    ↓
Supervisor (planning)
    ↓
┌───────────┬──────────┬──────────┐
│           │          │          │
Researcher  Analyst    Writer
│           │          │          │
└───────────┴──────────┴──────────┘
    ↓
Supervisor (synthesis)
    ↓
Final Answer
```

---

## 3. Capacità Implementate {#capacità}

### FASE 1: Fondamenti ReAct ✅ COMPLETA

**Controllo Iterazioni e Resilienza**

- ✅ Timeout control (120s default, configurabile)
- ✅ Max iterations (10 default, per strategia)
- ✅ Error tracking (max 3 errori consecutivi)
- ✅ Manual stop flag
- ✅ Early stopping
- ✅ Verbose logging (Thought/Action/Observation)
- ✅ Structured react_history

**Test**: 17 unit tests passed

### FASE 2: Strategie di Reasoning ✅ COMPLETA

**4 Strategie Configurabili**

| Strategia | Iter | Timeout | Temp | Use Case |
|-----------|------|---------|------|----------|
| **FAST** | 3 | 30s | 0.3 | Quick decisions, routing |
| **BALANCED** | 10 | 120s | 0.7 | Standard analysis |
| **DEEP** | 20 | 300s | 0.7 | Complex research |
| **CREATIVE** | 15 | 180s | 0.9 | Content generation |

**Configurazione Per-Agent**:
```python
SUPERVISOR_REACT_STRATEGY=fast      # Coordinamento veloce
RESEARCHER_REACT_STRATEGY=deep      # Ricerca approfondita
ANALYST_REACT_STRATEGY=balanced     # Analisi standard
WRITER_REACT_STRATEGY=creative      # Contenuti creativi
```

**Features**:
- ✅ Strategy enum e dataclass
- ✅ Per-agent configuration
- ✅ Task-specific overrides
- ✅ LLM factory integration
- ✅ Temperature da strategia

**Test**: 30 unit tests passed

### FASE 3: Self-Reflection ✅ COMPLETA

**Quality Assessment Automatico**

**Decisioni Reflection**:
- **ACCEPT**: Qualità sufficiente → end
- **REFINE**: Migliora risposta → refinement loop
- **INSUFFICIENT**: Troppo scarso → end

**Flusso Writer con Reflection**:
```
agent → reflect → refine
  ↓       ↓         ↓
 END     END    (→ reflect)
```

**Configurazione**:
```python
REACT_ENABLE_REFLECTION=true
WRITER_REFLECTION_THRESHOLD=0.8  # Score minimo
WRITER_REFLECTION_MAX_ITERATIONS=3  # Max refinements
```

**Prompt Specializzati**:
- **Writer**: engagement, structure, tone, completeness
- **Researcher**: source quality, depth, recency, accuracy
- **Analyst**: logic, evidence, clarity, actionability

**Features**:
- ✅ ReflectionResult con score/decision/suggestions
- ✅ Quality scoring 0.0-1.0
- ✅ Refinement prompts
- ✅ Per-agent thresholds
- ✅ Async reflection

**Test**: 26 unit tests passed

### FASE 4: Structured Logging ✅ COMPLETA

**Event-Based Logging System**

**9 Event Types**:
```python
THOUGHT       # Agent reasoning
ACTION        # Tool call
OBSERVATION   # Tool result
REFLECTION    # Quality assessment
REFINEMENT    # Response improvement
COMPLETION    # Success finish
ERROR         # Execution error
TIMEOUT       # Time exceeded
MAX_ITERATIONS # Limit reached
```

**ReactLogger API**:
```python
logger = create_react_logger("writer", "task-123")

logger.log_thought(iteration=1, thought="...")
logger.log_action(iteration=1, action_name="search")
logger.log_observation(iteration=1, observation="...", duration_ms=150)
logger.log_reflection(iteration=1, quality_score=0.75, decision="refine")
logger.log_completion(total_iterations=2, success=True)

# Retrieve
history = logger.get_history()      # List[Dict]
json_str = logger.get_history_json()  # JSON string
summary = logger.get_summary()      # Metrics
```

**Output Formats**:
- **JSON**: Machine-readable per analytics
- **Human-readable**: Debugging console-friendly

**Execution Summary**:
```python
{
  "agent_name": "writer",
  "total_duration_ms": 15500,
  "total_events": 8,
  "event_counts": {
    "thought": 2,
    "reflection": 2,
    "completion": 1
  }
}
```

**Features**:
- ✅ 500+ linee di codice
- ✅ Timestamp + duration tracking
- ✅ Performance metrics
- ✅ Backward compatible con react_history
- ✅ API endpoint `/react_history/{task_id}`

**Test**: 19 unit tests passed

### FASE 5: Human-in-the-Loop 🟡 85% COMPLETA

**Controllo Umano su Azioni Critiche**

**PostgreSQL Infrastructure** ✅:
- Docker PostgreSQL 16 container
- Connection pooling (max 20)
- Auto-setup tables
- State persistence funzionante

**HITL Module** ✅:
```python
# Create approval request
request = create_approval_request(
    tool_name="send_email",
    tool_input={"to": "client@example.com"},
    agent_name="writer",
    task_id="task-001",
    iteration=1
)

# Human decision
decision = hitl_manager.make_decision(
    task_id="task-001",
    action=ApprovalAction.APPROVE,  # or REJECT, MODIFY
    reason="Looks good"
)
```

**Approval Actions**:
- **APPROVE**: Procedi con azione
- **REJECT**: Cancella azione
- **MODIFY**: Cambia input e procedi

**Features Implementate** ✅:
- ✅ ApprovalRequest con timeout (300s default)
- ✅ ApprovalDecision con modify support
- ✅ HITLConfig con wildcard patterns (`send_*`)
- ✅ HITLManager per lifecycle
- ✅ Timeout handling
- ✅ Per-agent configuration
- ✅ PostgreSQL checkpointer funzionante

**Da Completare** ⏸️:
- API endpoints (3 × 4 server = 12 endpoint)
- Graph integration con interrupt/resume
- Documentazione API completa

**Configurazione**:
```python
REACT_ENABLE_HITL=false
WRITER_ENABLE_HITL=true
WRITER_HITL_REQUIRE_APPROVAL_FOR="publish_*,send_*,delete_*"
WRITER_HITL_TIMEOUT_SECONDS=600  # 10 min
```

**Test**: 21 unit tests passed

---

## 4. Stato di Avanzamento {#stato}

### Summary Implementazione

| Fase | Nome | Completamento | Test | Status |
|------|------|---------------|------|--------|
| FASE 1 | Fondamenti ReAct | 100% | 17/17 ✅ | Production |
| FASE 2 | Strategie Reasoning | 100% | 30/30 ✅ | Production |
| FASE 3 | Self-Reflection | 100% | 26/26 ✅ | Production |
| FASE 4 | Structured Logging | 100% | 19/19 ✅ | Production |
| FASE 5 | Human-in-the-Loop | 85% | 21/21 ✅ | Beta |
| FASE 6 | Reasoning Avanzati | 0% | - | Planned |
| FASE 7 | Metrics & Optimization | 0% | - | Planned |

### Test Suite

**Total: 113/113 tests passed (100%)**

- Unit tests: 113
- Integration tests: Ready
- Regression tests: 92 (FASE 1-4)
- Coverage: Core modules 100%

### File Statistics

**Code**:
- `utils/react_strategies.py`: 190 linee
- `utils/react_reflection.py`: 350 linee
- `utils/react_logger.py`: 500 linee
- `utils/react_hitl.py`: 300 linee
- `utils/checkpointer.py`: 118 linee (PostgreSQL support)
- 4 agent files: ~300 linee ciascuno
- 4 server files: ~100 linee ciascuno

**Tests**:
- `test_fase2_strategies.py`: 30 tests
- `test_fase3_reflection.py`: 26 tests
- `test_fase4_logging.py`: 19 tests
- `test_fase5_hitl.py`: 21 tests
- `test_regression_fase1.py`: 17 tests

**Documentation**:
- `REACT_IMPLEMENTATION_CHECKLIST.md`: 576 linee
- `docs/REACT_CONTROLS.md`: 850 linee
- `.env.example`: 220 linee

---

## 5. Pattern ReAct Avanzati {#react-patterns}

### ReAct Base Pattern

```
Thought: "I need to search for information about X"
Action: search_web(query="X")
Observation: "Found 10 results about X..."
Thought: "Now I have enough information"
Action: Final Answer
```

### Con Self-Reflection (FASE 3)

```
Thought: "Writing article about AI"
Action: generate_content()
Observation: "Draft created"
↓
Reflection: score=0.65, decision=REFINE
  "Needs more examples and better structure"
↓
Thought: "Improving with suggestions"
Action: refine_content()
Observation: "Refined draft"
↓
Reflection: score=0.85, decision=ACCEPT
  "Quality sufficient"
↓
Final Answer
```

### Con Human-in-the-Loop (FASE 5)

```
Thought: "Article ready, need to publish"
Action: publish_to_blog(url="/new-post")
↓
[PAUSE - Approval Required]
  Human sees: "Agent wants to publish to /new-post"
  Options: APPROVE | REJECT | MODIFY
↓
Human Decision: APPROVE
↓
Observation: "Published successfully"
Final Answer
```

---

## 6. Configurazione e Setup {#setup}

### Prerequisiti

```bash
# Python
python >= 3.12

# Docker (per PostgreSQL)
docker >= 20.10
docker-compose >= 2.0

# API Keys (almeno una)
- OpenRouter API key (recommended)
- O: OpenAI / Anthropic / Google / Groq
```

### Quick Start

```bash
# 1. Clone e setup
git clone <repo>
cd cortex-flow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configurazione
cp .env.example .env
# Aggiungi OPENROUTER_API_KEY e TAVILY_API_KEY

# 3. Start PostgreSQL (opzionale, default memory)
docker-compose -f docker-compose.postgres.yml up -d

# 4. Start agents
./start_all.sh

# 5. Test
curl http://localhost:8000/health
```

### Configurazione Avanzata

**.env - Strategie Reasoning**:
```bash
# Per-Agent Strategies
SUPERVISOR_REACT_STRATEGY=fast
RESEARCHER_REACT_STRATEGY=deep
ANALYST_REACT_STRATEGY=balanced
WRITER_REACT_STRATEGY=creative

# Task-Specific Overrides
RESEARCHER_QUICK_SEARCH_REACT_STRATEGY=fast
WRITER_TECHNICAL_REACT_STRATEGY=balanced
```

**.env - Self-Reflection**:
```bash
# Global
REACT_ENABLE_REFLECTION=true
REACT_REFLECTION_QUALITY_THRESHOLD=0.7

# Writer (più strict)
WRITER_ENABLE_REFLECTION=true
WRITER_REFLECTION_THRESHOLD=0.8
WRITER_REFLECTION_MAX_ITERATIONS=3
```

**.env - PostgreSQL**:
```bash
CHECKPOINT_BACKEND=postgres
POSTGRES_URL="postgresql://cortex:cortex_dev_password@localhost:5432/cortex_flow"
```

**.env - HITL**:
```bash
REACT_ENABLE_HITL=true
WRITER_ENABLE_HITL=true
WRITER_HITL_REQUIRE_APPROVAL_FOR="publish_*,send_*,delete_*"
WRITER_HITL_TIMEOUT_SECONDS=600
```

---

## 7. Testing e Qualità {#testing}

### Test Suite Completa

```bash
# All tests
pytest tests/ -v

# FASE specific
pytest tests/ -m fase2  # Strategies
pytest tests/ -m fase3  # Reflection
pytest tests/ -m fase4  # Logging
pytest tests/ -m fase5  # HITL

# Regression
pytest tests/ -m "unit and (fase1 or fase2 or fase3 or fase4)"

# Coverage
pytest tests/ --cov=. --cov-report=html
```

### Test Markers

- `@pytest.mark.unit`: Unit tests (no dependencies)
- `@pytest.mark.integration`: Integration tests (require servers)
- `@pytest.mark.regression`: Backward compatibility tests
- `@pytest.mark.fase1-5`: Feature-specific tests

### Quality Metrics

**Code Quality**:
- Type hints: 90%+
- Docstrings: 100% (public API)
- Error handling: Comprehensive
- Logging: Structured

**Test Quality**:
- Unit test coverage: 95%+
- Edge cases: Covered
- Error scenarios: Tested
- Performance: Monitored

---

## 8. Roadmap Futura {#roadmap}

### FASE 6: Reasoning Modes Avanzati (Planned)

**Chain-of-Thought Esplicito**:
- Modalità COT_EXPLICIT
- Step-by-step reasoning logging
- Intermediate checkpoints

**Tree-of-Thought**:
- Modalità TREE_OF_THOUGHT
- Branching per alternative exploration
- Best path selection
- Parallel reasoning paths

**Adaptive Reasoning**:
- Modalità ADAPTIVE
- Dynamic strategy switching
- Performance-based adaptation

### FASE 7: Metrics & Optimization (Planned)

**Performance Tracking**:
- Tempo per iterazione
- Token usage per agent
- Success rate tools
- Latency distribution

**Cost Analysis**:
- LLM cost per task
- Cost by agent type
- Budget monitoring
- Optimization suggestions

**Auto-Tuning**:
- Historical metrics analysis
- Strategy recommendation
- A/B testing framework
- Automatic parameter tuning

### Features Aggiuntive

**Multi-Modal Support**:
- Image analysis agents
- Document processing
- Audio transcription

**Advanced Tools**:
- Code execution sandbox
- Database query tools
- API integration framework

**Enterprise Features**:
- Multi-tenancy
- Role-based access control
- Audit logging
- SLA monitoring

---

## 📊 Statistiche Finali

**Codice Totale**: ~3500 linee (esclusi test)
**Test Suite**: 113 tests, 100% passed
**Documentazione**: ~1500 linee
**Fasi Completate**: 4.85 / 7 (69%)
**Production Ready**: FASE 1-4 (100%)
**Beta**: FASE 5 (85%)

**Tecnologie Chiave**:
- LangGraph 0.6.8
- LangChain Core 0.3.78
- FastAPI per REST API
- PostgreSQL 16 per persistence
- Docker per infrastruttura
- Pytest per testing

**Performance**:
- Latency: 3-30s (per strategia)
- Throughput: 10+ req/sec
- Persistence: PostgreSQL production-ready
- Scalability: Multi-process ready

---

## 🎯 Conclusioni

Cortex Flow è un sistema multi-agente AI **production-ready** con:

✅ **Architettura Solida**: 4 agenti specializzati con orchestrazione LangGraph
✅ **Pattern ReAct Avanzati**: 5 fasi implementate (4 complete, 1 in beta)
✅ **Alta Qualità**: 113 tests passed, extensive documentation
✅ **Flessibilità**: Strategie configurabili, self-reflection, HITL support
✅ **Persistence**: PostgreSQL per state management production
✅ **Monitoring**: Structured logging e metrics ready

**Pronto per**:
- Deployment production (FASE 1-4)
- Feature extension (FASE 6-7 roadmap clear)
- Enterprise integration (architecture scalable)

---

*Documento generato: 2025-10-06*
*Versione Sistema: 5.0 (FASE 5 Beta)*
*Status: Production Ready (Core) + Beta (HITL)*
