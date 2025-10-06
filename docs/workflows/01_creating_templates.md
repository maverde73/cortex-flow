# Guida alla Creazione di Template Workflow

## Indice

- [Struttura Base Template](#struttura-base-template)
- [Schema Completo](#schema-completo)
- [Esempi Pratici](#esempi-pratici)
- [Pattern Comuni](#pattern-comuni)
- [Best Practices](#best-practices)
- [Validazione Template](#validazione-template)

---

## Struttura Base Template

Tutti i template vanno salvati in `workflows/templates/*.json`

### Template Minimo

```json
{
  "name": "my_workflow",
  "version": "1.0",
  "description": "Breve descrizione del workflow",
  "trigger_patterns": ["regex1", "regex2"],
  "nodes": [
    {
      "id": "step1",
      "agent": "researcher",
      "instruction": "Cosa deve fare l'agente"
    }
  ]
}
```

---

## Schema Completo

```json
{
  "name": "string (required)",           // ID univoco del workflow
  "version": "string (required)",        // Versione (es. "1.0", "2.3")
  "description": "string (required)",    // Descrizione scopo workflow
  "trigger_patterns": ["array (required)"], // Regex per auto-matching

  "nodes": [                            // Lista nodi (required)
    {
      "id": "string (required)",        // ID univoco nodo
      "agent": "string (required)",     // Tipo: researcher|analyst|writer|mcp_tool
      "instruction": "string (required)", // Istruzione per l'agente

      // OPZIONALI
      "depends_on": ["array"],          // Dipendenze (altri node IDs)
      "parallel_group": "string",       // Gruppo esecuzione parallela
      "timeout": 120,                   // Timeout in secondi (default: 120)
      "tool_name": "string",            // Nome tool MCP (solo se agent="mcp_tool")
      "params": {}                      // Parametri aggiuntivi
    }
  ],

  "conditional_edges": [                // OPZIONALE: Routing condizionale
    {
      "from_node": "string (required)", // Nodo sorgente
      "conditions": [                   // Lista condizioni
        {
          "field": "string",            // Campo da valutare nello state
          "operator": "string",         // >, <, >=, <=, equals, contains, in, not_in
          "value": "any",               // Valore di confronto
          "next_node": "string"         // Nodo destinazione se condizione vera
        }
      ],
      "default": "string (required)"    // Nodo default se nessuna condizione match
    }
  ]
}
```

---

## Esempi Pratici

### Esempio 1: Email Newsletter Workflow

**Caso d'uso**: Ricerca trend → Scrivi newsletter → Invia

Vedi: [examples/newsletter_workflow.json](examples/newsletter_workflow.json)

**Caratteristiche**:
- Sequential workflow (3 nodi)
- Variable substitution: `{topic}`, `{audience}`, `{tone}`, `{length}`
- Trigger patterns: newsletter, weekly summary, email digest

**Utilizzo**:
```python
from langchain_core.messages import HumanMessage

await supervisor.ainvoke({
    "messages": [HumanMessage(content="Create weekly AI newsletter")],
    "workflow_template": "email_newsletter",
    "workflow_params": {
        "topic": "Artificial Intelligence",
        "audience": "tech professionals",
        "tone": "professional yet accessible",
        "length": "500"
    }
})
```

---

### Esempio 2: Content Repurposing Pipeline

**Caso d'uso**: Blog post → Tweet thread + LinkedIn post + Summary

Vedi: [examples/content_repurposing.json](examples/content_repurposing.json)

**Caratteristiche**:
- Parallel execution (3 writer nodes simultanei)
- Dependency resolution (tutti aspettano analyze_blog)
- Multiple output formats

**Performance**:
```
Sequential: analyze (60s) + tweet (40s) + linkedin (40s) + summary (30s) = 170s
Parallel:   analyze (60s) + max(tweet, linkedin, summary) = 100s
Risparmio: 41% tempo totale
```

---

### Esempio 3: SEO Content Optimizer

**Caso d'uso**: Analizza e ottimizza contenuto per SEO

Vedi: [examples/seo_optimizer.json](examples/seo_optimizer.json)

**Caratteristiche**:
- Research keywords → Analyze content → Optimize
- Long timeout per research (300s)
- Structured output (title, meta, H2/H3, links)

---

## Pattern Comuni

### Pattern 1: Research → Analyze → Report

```json
{
  "nodes": [
    {
      "id": "research",
      "agent": "researcher",
      "instruction": "Research {topic}"
    },
    {
      "id": "analyze",
      "agent": "analyst",
      "instruction": "Analyze:\n{research}",
      "depends_on": ["research"]
    },
    {
      "id": "report",
      "agent": "writer",
      "instruction": "Report:\n{analyze}",
      "depends_on": ["analyze"]
    }
  ]
}
```

**Quando usare**: Task che richiedono raccolta dati + insights + presentazione

---

### Pattern 2: Multiple Sources → Synthesis

```json
{
  "nodes": [
    {
      "id": "source1",
      "agent": "researcher",
      "instruction": "Research source 1",
      "parallel_group": "sources"
    },
    {
      "id": "source2",
      "agent": "researcher",
      "instruction": "Research source 2",
      "parallel_group": "sources"
    },
    {
      "id": "source3",
      "agent": "mcp_tool",
      "tool_name": "query_database",
      "parallel_group": "sources"
    },
    {
      "id": "synthesize",
      "agent": "analyst",
      "instruction": "Synthesize:\n{source1}\n{source2}\n{source3}",
      "depends_on": ["source1", "source2", "source3"]
    }
  ]
}
```

**Quando usare**: Dati da fonti multiple (web, DB, API)

---

### Pattern 3: Quality Gate (Conditional)

```json
{
  "nodes": [
    {"id": "draft", "agent": "writer", "instruction": "Draft {content_type}"},
    {
      "id": "review",
      "agent": "analyst",
      "instruction": "Review quality:\n{draft}\nProvide quality_score (0-1)"
    },
    {"id": "publish", "agent": "writer", "instruction": "Finalize:\n{draft}"},
    {
      "id": "revise",
      "agent": "writer",
      "instruction": "Improve:\n{draft}\nIssues:\n{review}"
    }
  ],

  "conditional_edges": [
    {
      "from_node": "review",
      "conditions": [
        {
          "field": "quality_score",
          "operator": ">",
          "value": 0.8,
          "next_node": "publish"
        }
      ],
      "default": "revise"
    }
  ]
}
```

**Quando usare**: Controllo qualità prima di pubblicazione

---

## Best Practices

### ✅ DO

#### 1. Nomi descrittivi

```json
// ✅ GOOD
"id": "research_competitor_pricing"

// ❌ BAD
"id": "step1"
```

#### 2. Trigger patterns specifici

```json
// ✅ GOOD
"trigger_patterns": [
  ".*competitor.*analy[sz]is.*",
  "compare .* with .*",
  ".* vs .* comparison.*"
]

// ❌ BAD (troppo generico)
"trigger_patterns": [".*analy.*"]
```

#### 3. Istruzioni chiare con contesto

```json
// ✅ GOOD
"instruction": "Analyze competitor {competitor_name} focusing on:\n1. Pricing strategy\n2. Market positioning\n3. Key differentiators\n\nProvide actionable insights."

// ❌ BAD
"instruction": "Analyze competitor"
```

#### 4. Timeout realistici

```json
// Research web → lungo
{"agent": "researcher", "timeout": 300}

// Analyze text → breve
{"agent": "analyst", "timeout": 60}

// Write long-form → medio
{"agent": "writer", "timeout": 180}
```

#### 5. Parametri documentati

```json
{
  "description": "SEO optimization workflow. Params: {topic, current_content, target_audience}",
  "nodes": [...]
}
```

---

### ❌ DON'T

#### 1. Dipendenze circolari

```json
// ❌ ERRORE: A → B → A
{"id": "A", "depends_on": ["B"]},
{"id": "B", "depends_on": ["A"]}
```

#### 2. Nodi duplicati

```json
// ❌ ERRORE: stesso ID
{"id": "analyze", ...},
{"id": "analyze", ...}
```

#### 3. Parallel group senza convergenza

```json
// ❌ WARN: parallelo senza senso se non convergono
{"id": "task1", "parallel_group": "group1"},
{"id": "task2", "parallel_group": "group1"}
// Manca nodo che dipende da entrambi!
```

#### 4. Variabili non definite

```json
// ❌ ERRORE: {undefined_var} non esiste
"instruction": "Research {undefined_var}"
// Deve esistere in workflow_params o node_outputs
```

---

## Validazione Template

### Validazione Automatica

Il sistema valida automaticamente al caricamento:

```python
from workflows.registry import WorkflowRegistry

registry = WorkflowRegistry()
registry.load_templates()

# Validazione manuale
template = registry.get("my_workflow")
errors = registry.validate_template(template)

if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Template valido")
```

### Errori Comuni

```
❌ Duplicate node IDs: ['research', 'research']
   → Fix: Rinomina uno dei due nodi

❌ Node 'analyze' depends on non-existent node 'reserch'
   → Fix: Typo in depends_on (reserch → research)

❌ Circular dependency detected: A → B → C → A
   → Fix: Rimuovi dipendenza circolare

❌ MCP node 'query' missing tool_name
   → Fix: Aggiungi "tool_name": "query_database"

❌ Conditional edge from 'review' references non-existent node 'pubilsh'
   → Fix: Typo (pubilsh → publish)
```

### Test Template

```python
# Test in isolamento
from workflows.engine import WorkflowEngine
from schemas.workflow_schemas import WorkflowTemplate

engine = WorkflowEngine()

# Carica template
import json
with open("workflows/templates/my_workflow.json") as f:
    template_data = json.load(f)
    template = WorkflowTemplate(**template_data)

# Test esecuzione (mock)
result = await engine.execute_workflow(
    template=template,
    user_input="Test input",
    params={"topic": "AI", "audience": "developers"}
)

print(f"Success: {result.success}")
print(f"Nodes executed: {len(result.node_results)}")
print(f"Output: {result.final_output[:200]}...")
```

---

## Prossimi Passi

- [Conditional Routing →](02_conditional_routing.md) - Aggiungi decision logic ai workflow
- [MCP Integration →](03_mcp_integration.md) - Integra database e API esterne
- [Examples →](examples/) - Template pronti all'uso

---

**Vedi anche**:
- `workflows/templates/` - Template esistenti
- `tests/test_workflows.py` - Test esempi
- Schema: `schemas/workflow_schemas.py`
