# Workflow System - Documentazione Completa

Sistema di workflow template-based per Cortex Flow che permette di eseguire sequenze predefinite di agenti invece di lasciare che il Supervisor decida autonomamente (ReAct mode).

## 📚 Guide

### 1. [Creazione Template](01_creating_templates.md)
Impara a creare workflow personalizzati con template JSON.

**Contenuti**:
- Struttura base template
- Schema completo
- Esempi pratici (newsletter, content repurposing, SEO optimizer)
- Pattern comuni
- Best practices
- Validazione e testing

**Per chi**: Sviluppatori che vogliono creare nuovi workflow

---

### 2. [Conditional Routing](02_conditional_routing.md)
Aggiungi logica decisionale ai tuoi workflow.

**Contenuti**:
- Operatori disponibili (>, <, contains, in, etc.)
- Pattern avanzati (sentiment routing, quality gates, loops)
- Popolare metadata per routing
- Debug e testing

**Per chi**: Workflow avanzati con branching dinamico

---

### 3. [MCP Integration](03_mcp_integration.md)
Integra database, API e tool esterni nei workflow.

**Contenuti**:
- Configurazione MCP servers
- Anatomia MCP node
- Esempi pratici (database, weather, files)
- Parametri avanzati (nested, dynamic)
- Error handling e fallback
- Testing

**Per chi**: Workflow che necessitano di dati esterni

---

## 🚀 Quick Start

### 1. Configura il sistema

In `.env`:
```bash
# Abilita workflow system
WORKFLOW_ENABLE=true
WORKFLOW_MODE=hybrid  # auto-detect template o usa ReAct
WORKFLOW_AUTO_CLASSIFY=true
WORKFLOW_FALLBACK_TO_REACT=true
```

### 2. Usa un template esistente

```python
from langchain_core.messages import HumanMessage

# Modo 1: Esplicito
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Create weekly AI newsletter")],
    "workflow_template": "email_newsletter",
    "workflow_params": {
        "topic": "Artificial Intelligence",
        "audience": "tech professionals",
        "tone": "professional",
        "length": "500"
    }
})

# Modo 2: Auto-detect (trigger: ".*newsletter.*")
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Send me a newsletter on blockchain")],
    "workflow_params": {
        "topic": "blockchain",
        "audience": "investors",
        "tone": "formal",
        "length": "800"
    }
})
```

### 3. Crea il tuo template

1. Copia template esempio:
```bash
cp workflows/templates/report_generation.json workflows/templates/my_workflow.json
```

2. Modifica campi:
```json
{
  "name": "my_workflow",
  "version": "1.0",
  "description": "My custom workflow",
  "trigger_patterns": ["my.*pattern.*"],
  "nodes": [...]
}
```

3. Valida:
```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
registry.load_templates()
template = registry.get("my_workflow")
errors = registry.validate_template(template)

if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Template valid")
```

---

## 📁 Esempi Template

Nella directory [`examples/`](examples/):

| Template | Descrizione | Features |
|----------|-------------|----------|
| [`newsletter_workflow.json`](examples/newsletter_workflow.json) | Email newsletter settimanale | Sequential, web research |
| [`content_repurposing.json`](examples/content_repurposing.json) | Blog → Social media multi-platform | Parallel execution |
| [`seo_optimizer.json`](examples/seo_optimizer.json) | SEO content optimization | Research + analysis + rewrite |

Workflow esistenti in `workflows/templates/`:

| Template | Descrizione | Features |
|----------|-------------|----------|
| `report_generation.json` | Research → Analyze → Report | Sequential base pattern |
| `competitive_analysis.json` | Compare A vs B | Parallel research |
| `data_analysis_report.json` | DB query → Analysis → Report | **MCP integration** |
| `multi_source_research.json` | Web + DB parallel → Synthesize | **MCP + parallel** |
| `sentiment_routing.json` | Sentiment analysis → Route | **Conditional routing** |

---

## 🏗️ Architettura

### Componenti Principali

```
┌─────────────────────────────────────────────────┐
│         Workflow Supervisor (Dual-Mode)         │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │ Router: workflow vs ReAct?               │  │
│  └────┬─────────────────────────────┬───────┘  │
│       │                              │          │
│   ┌───▼──────┐              ┌────────▼─────┐   │
│   │ Workflow │              │ ReAct Agent  │   │
│   │ Executor │              │ (Autonomous) │   │
│   └───┬──────┘              └──────────────┘   │
│       │                                         │
│  ┌────▼────────────────────────────────────┐   │
│  │        Workflow Engine                  │   │
│  │ - Build execution plan (DAG)            │   │
│  │ - Parallel execution (asyncio.gather)   │   │
│  │ - Conditional routing evaluation        │   │
│  │ - Variable substitution                 │   │
│  │ - MCP tool integration                  │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    ↓
Supervisor Router
    ↓
Auto-match template? (regex on trigger_patterns)
    ↓
    ├─ YES → Workflow Executor
    │           ↓
    │        Load Template (JSON)
    │           ↓
    │        Build Execution Plan (resolve dependencies)
    │           ↓
    │        Execute Nodes (sequential/parallel)
    │           ↓
    │        [Conditional Routing?]
    │           ↓
    │        Return Final Output
    │
    └─ NO → ReAct Agent (autonomous decision-making)
```

---

## 🔧 Configurazione

### Workflow Mode

```bash
# .env
WORKFLOW_MODE=hybrid  # Opzioni: react | template | hybrid
```

**Modi disponibili**:

| Mode | Comportamento |
|------|---------------|
| `react` | Solo ReAct autonomo (nessun template) |
| `template` | Solo template espliciti (errore se non specificato) |
| `hybrid` | Auto-detect template → fallback ReAct ✅ **CONSIGLIATO** |

### Auto-Classification

```bash
WORKFLOW_AUTO_CLASSIFY=true  # Match template via trigger_patterns
```

Quando `true`, il sistema:
1. Prende user input
2. Cerca match con `trigger_patterns` di ogni template (regex)
3. Se match → usa template
4. Se no match → usa ReAct

**Esempio**:
```
User: "Create a report on AI trends"
       ↓
Regex match: ".*report.*" → template "report_generation"
       ↓
Esegue: research → analyze → write
```

### Fallback Strategy

```bash
WORKFLOW_FALLBACK_TO_REACT=true  # Use ReAct if workflow fails
```

Se workflow fallisce (errore, timeout, validation):
- `true` → Tenta con ReAct mode
- `false` → Ritorna errore

---

## 📊 Performance

### Sequential vs Parallel

**Sequential workflow**:
```json
{"id": "step1", "depends_on": []},
{"id": "step2", "depends_on": ["step1"]},
{"id": "step3", "depends_on": ["step2"]}
```
Tempo: `t1 + t2 + t3`

**Parallel workflow**:
```json
{"id": "step1", "parallel_group": "group1"},
{"id": "step2", "parallel_group": "group1"},
{"id": "step3", "parallel_group": "group1"}
```
Tempo: `max(t1, t2, t3)`

**Esempio reale** (content repurposing):
- Sequential: 40s + 40s + 30s = 110s
- Parallel: max(40s, 40s, 30s) = 40s
- **Risparmio: 64%**

---

## 🧪 Testing

### Validazione Template

```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
count = registry.load_templates()
print(f"Loaded {count} templates")

# Validate all
templates = registry.list_templates()
for name in templates:
    template = registry.get(name)
    errors = registry.validate_template(template)
    if errors:
        print(f"❌ {name}: {errors}")
    else:
        print(f"✅ {name}: valid")
```

### Unit Tests

```bash
# Test workflow system
pytest tests/test_workflows.py -v

# Test MCP integration
pytest tests/test_workflow_mcp.py -v

# Test specifico
pytest tests/test_workflows.py::TestConditionalRouting::test_sentiment_routing -v
```

### Integration Tests

```bash
# Requires running servers
pytest tests/test_workflow_mcp.py::TestWorkflowMCPIntegration::test_execute_mcp_workflow -v

# Mark integration tests
pytest -m integration -v
```

---

## 🐛 Troubleshooting

### Template non caricato

**Problema**: Template non appare in `registry.list_templates()`

**Soluzioni**:
1. Verifica posizione: `workflows/templates/*.json`
2. Verifica sintassi JSON (usa JSON validator)
3. Check logs: `registry.load_templates()` stampa errori

### Auto-match non funziona

**Problema**: Template non auto-selezionato

**Soluzioni**:
1. Verifica trigger_patterns regex:
```python
import re
pattern = ".*report.*"
user_input = "Create a report"
print(bool(re.search(pattern, user_input.lower())))  # Should be True
```

2. Abilita logging:
```bash
REACT_ENABLE_VERBOSE_LOGGING=true
```

3. Check workflow_mode:
```bash
WORKFLOW_MODE=hybrid  # Not "react"
WORKFLOW_AUTO_CLASSIFY=true
```

### Variabile non sostituita

**Problema**: `{variable}` appare letteralmente nell'output

**Soluzioni**:
1. Verifica nome variabile in workflow_params
2. Check typos: `{topic}` vs `{tpic}`
3. Nested access: `{node_id.field}` richiede JSON output dal nodo

### MCP tool not found

**Problema**: `ValueError: MCP tool 'query_database' not found`

**Soluzioni**:
1. Check server running:
```bash
curl http://localhost:8005/mcp
```

2. Verifica .env:
```bash
MCP_ENABLE=true
MCP_SERVER_CORPORATE_ENABLED=true
```

3. Restart server:
```bash
python -m servers.corporate_server --port 8005
```

---

## 📖 Reference

### File Structure

```
cortex-flow/
├── workflows/
│   ├── __init__.py
│   ├── engine.py          # Core execution engine
│   ├── registry.py        # Template management
│   ├── conditions.py      # Conditional routing logic
│   └── templates/         # JSON templates
│       ├── report_generation.json
│       ├── competitive_analysis.json
│       ├── data_analysis_report.json  # MCP example
│       ├── multi_source_research.json
│       └── sentiment_routing.json
│
├── schemas/
│   └── workflow_schemas.py  # Pydantic models
│
├── agents/
│   └── workflow_supervisor.py  # Dual-mode supervisor
│
├── tests/
│   ├── test_workflows.py       # Unit tests
│   └── test_workflow_mcp.py    # MCP integration tests
│
└── docs/
    └── workflows/              # This directory
        ├── README.md
        ├── 01_creating_templates.md
        ├── 02_conditional_routing.md
        ├── 03_mcp_integration.md
        └── examples/
            ├── newsletter_workflow.json
            ├── content_repurposing.json
            └── seo_optimizer.json
```

### API Reference

#### WorkflowRegistry

```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry(templates_dir="workflows/templates")

# Load all templates
count = registry.load_templates()

# Get template
template = registry.get("template_name")

# List all
templates = registry.list_templates()

# Auto-match
template = await registry.match_template("user input text")

# Validate
errors = registry.validate_template(template)
```

#### WorkflowEngine

```python
from workflows.engine import WorkflowEngine

engine = WorkflowEngine()

result = await engine.execute_workflow(
    template=template,
    user_input="User request",
    params={"param1": "value1", "param2": "value2"}
)

# Result structure
result.success          # bool
result.workflow_name    # str
result.final_output     # str (last node output)
result.node_results     # List[NodeExecutionResult]
result.total_execution_time  # float (seconds)
result.error           # Optional[str]
```

#### ConditionEvaluator

```python
from workflows.conditions import ConditionEvaluator

evaluator = ConditionEvaluator()

next_node = evaluator.evaluate_edge(
    conditional_edge=edge,
    state=workflow_state
)
```

---

## 🤝 Contributing

Vuoi contribuire nuovi template o miglioramenti?

1. Crea template in `workflows/templates/`
2. Aggiungi test in `tests/test_workflows.py`
3. Documenta in `docs/workflows/examples/`
4. Valida con `registry.validate_template()`

---

## 📚 Risorse

- **Codebase**: `workflows/`, `schemas/workflow_schemas.py`
- **Tests**: `tests/test_workflows.py`, `tests/test_workflow_mcp.py`
- **Esempi**: `workflows/templates/`, `docs/workflows/examples/`
- **Config**: `.env.example` (workflow section)

---

**Documentazione aggiornata**: 2025-01-06
