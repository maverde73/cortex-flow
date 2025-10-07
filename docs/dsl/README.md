# Workflow DSL - Domain-Specific Language

**Linguaggio di scripting dichiarativo per definire workflow multi-agente**

## 🎯 Overview

Il **Workflow DSL** consente di definire workflow complessi usando una sintassi YAML leggibile, anziché JSON verboso. Il sistema supporta **conversione bidirezionale** (reflection):

```
YAML DSL ←→ WorkflowTemplate (JSON) ←→ Execution
```

### Vantaggi DSL

✅ **Leggibilità**: Sintassi YAML intuitiva
✅ **Commenti**: Documentazione inline nel codice
✅ **Type safety**: Validazione con Pydantic
✅ **Reflection**: Generazione automatica da workflow esistenti
✅ **IDE support**: Syntax highlighting e autocomplete

---

## 🚀 Quick Start

### 1. Crea un workflow DSL

Crea `examples/dsl/my_workflow.yaml`:

```yaml
workflow: my_workflow
version: "1.0"
description: |
  My custom workflow description

triggers:
  - ".*my.*pattern.*"

params:
  topic: default_value

nodes:
  - research:
      agent: researcher
      instruction: |
        Research {topic} and provide insights
      timeout: 300s

  - analyze:
      agent: analyst
      depends_on: [research]
      instruction: |
        Analyze research results:
        {research}

  - write:
      agent: writer
      depends_on: [analyze]
      instruction: |
        Create report based on:
        {analyze}
```

### 2. Parse DSL → JSON

```bash
# Validate only
python scripts/parse_workflow.py examples/dsl/my_workflow.yaml --validate-only

# Parse and save to JSON
python scripts/parse_workflow.py examples/dsl/my_workflow.yaml -o workflows/templates/my_workflow.json
```

### 3. Generate DSL ← JSON

```bash
# From JSON file
python scripts/generate_dsl.py workflows/templates/report_generation.json

# From registry
python scripts/generate_dsl.py report_generation --from-registry -o examples/dsl/report.yaml
```

---

## 📖 Syntax Reference

### Basic Structure

```yaml
workflow: <name>              # Required: Workflow unique name
version: "<version>"          # Required: Version string (e.g., "1.0")
description: <text>           # Required: Description (can be multi-line with |)

triggers:                     # Optional: Regex patterns for auto-matching
  - "pattern1"
  - "pattern2"

params:                       # Optional: Default parameters
  key: value

nodes:                        # Required: List of workflow nodes
  - node_id:
      agent: <agent_type>
      instruction: <text>
      # ... optional fields

conditions:                   # Optional: Conditional routing
  - from: node_id
    rules:
      - if: {field: x, op: ">", value: 5}
        then: next_node
    default: fallback_node
```

### Node Configuration

```yaml
nodes:
  - node_id:                  # Node unique identifier
      agent: researcher       # Agent type: researcher | analyst | writer | mcp_tool
      instruction: |          # Instruction (supports variable substitution)
        Multi-line instruction
        with {variables}

      # OPTIONAL FIELDS
      depends_on:             # Dependencies (list of node IDs)
        - other_node

      parallel_group: "name"  # Parallel execution group

      timeout: 120s           # Timeout: 120s | 2m | 1h (default: 120s)

      tool_name: "tool_name"  # MCP tool name (if agent=mcp_tool)

      params:                 # Additional parameters
        key: value

      template: "template"    # Template name (for writer agent)

      use_mcp_prompt: true    # Auto-populate with MCP prompt
```

### Variable Substitution

Le istruzioni supportano la sostituzione di variabili:

```yaml
nodes:
  - research:
      agent: researcher
      instruction: "Research {topic} for {audience}"  # {topic} and {audience} from params

  - analyze:
      depends_on: [research]
      instruction: |
        Analyze results:
        {research}          # Output from 'research' node
```

**Fonti variabili** (in ordine di priorità):
1. `workflow_params` (parametri runtime)
2. `params` (parametri template)
3. `node_outputs` (output nodi precedenti)

### Conditional Routing

```yaml
conditions:
  - from: sentiment_analysis      # Source node
    rules:
      - if: {field: sentiment_score, op: ">", value: 0.7}
        then: positive_response   # Route if condition true

      - if: {field: sentiment_score, op: "<", value: 0.3}
        then: negative_response

    default: neutral_response     # Fallback if no condition matches
```

**Operatori supportati**:
- Numeri: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Stringhe: `contains`, `not_contains`
- Liste: `in`, `not_in`

### Parallel Execution

```yaml
nodes:
  - web_research:
      agent: researcher
      parallel_group: sources    # Same group = parallel execution
      instruction: "Web search"

  - database_query:
      agent: mcp_tool
      parallel_group: sources    # Runs in parallel with web_research
      tool_name: query_database

  - synthesize:
      depends_on: [web_research, database_query]  # Waits for both
      agent: analyst
      instruction: "Combine results"
```

### MCP Tool Integration

```yaml
nodes:
  - query_db:
      agent: mcp_tool
      tool_name: query_database         # MCP tool name
      instruction: "Query {table_name}"
      timeout: 60s
      params:
        query_payload:                  # Tool-specific parameters
          table: "{table_name}"
          method: select
          columns: ["id", "name"]
          limit: 100
```

### Timeout Formats

```yaml
nodes:
  - step1:
      timeout: 120s       # 120 seconds

  - step2:
      timeout: 2m         # 2 minutes (120 seconds)

  - step3:
      timeout: 1h         # 1 hour (3600 seconds)

  - step4:
      timeout: 300        # Plain integer (300 seconds)
```

---

## 📝 Examples

### Example 1: Sequential Workflow

```yaml
workflow: newsletter
version: "1.0"
description: Weekly newsletter generation
triggers:
  - ".*newsletter.*"

params:
  topic: AI

nodes:
  - research:
      agent: researcher
      instruction: "Research {topic} trends"
      timeout: 300s

  - analyze:
      agent: analyst
      depends_on: [research]
      instruction: "Analyze: {research}"

  - write:
      agent: writer
      depends_on: [analyze]
      instruction: "Write newsletter: {analyze}"
```

### Example 2: Parallel Workflow

```yaml
workflow: multi_source
version: "1.0"
description: Parallel web + database research

nodes:
  - web_research:
      agent: researcher
      parallel_group: sources
      instruction: "Web research"

  - db_query:
      agent: mcp_tool
      tool_name: query_database
      parallel_group: sources
      params:
        query_payload: {table: "data"}

  - synthesize:
      agent: analyst
      depends_on: [web_research, db_query]
      instruction: "Combine: {web_research} + {db_query}"
```

### Example 3: Conditional Routing

```yaml
workflow: sentiment_router
version: "1.0"
description: Route based on sentiment

nodes:
  - analyze:
      agent: analyst
      instruction: "Analyze sentiment"

  - positive:
      agent: writer
      instruction: "Positive response"

  - negative:
      agent: writer
      instruction: "Empathy response"

  - neutral:
      agent: writer
      instruction: "Neutral response"

conditions:
  - from: analyze
    rules:
      - if: {field: sentiment_score, op: ">", value: 0.7}
        then: positive
      - if: {field: sentiment_score, op: "<", value: 0.3}
        then: negative
    default: neutral
```

---

## 🔧 CLI Tools

### parse_workflow.py

Converte YAML DSL → JSON WorkflowTemplate

```bash
# Validate only
python scripts/parse_workflow.py examples/dsl/newsletter.yaml --validate-only

# Parse and print to stdout
python scripts/parse_workflow.py examples/dsl/newsletter.yaml

# Parse and save to file
python scripts/parse_workflow.py examples/dsl/newsletter.yaml -o workflows/templates/newsletter.json

# Parse multiple files
python scripts/parse_workflow.py examples/dsl/*.yaml --output-dir workflows/templates/
```

### generate_dsl.py

Converte JSON WorkflowTemplate → YAML DSL

```bash
# Generate from JSON file
python scripts/generate_dsl.py workflows/templates/report_generation.json

# Generate from registry
python scripts/generate_dsl.py report_generation --from-registry

# Save to file
python scripts/generate_dsl.py report_generation --from-registry -o examples/dsl/report.yaml

# Generate Python DSL (future)
python scripts/generate_dsl.py report_generation --from-registry -f python -o examples/dsl/report.py
```

---

## 🧪 Testing

### Round-Trip Testing

Verifica che la conversione bidirezionale preservi la semantica:

```bash
# Run all DSL tests
pytest tests/test_dsl_roundtrip.py -v

# Test specific round-trip
pytest tests/test_dsl_roundtrip.py::TestDSLRoundTrip::test_yaml_to_json_to_yaml -v

# Test all existing workflows
pytest tests/test_dsl_roundtrip.py::TestDSLRoundTrip::test_all_existing_workflows_yaml_generation -v
```

### Validation

```python
from workflows.dsl.parser import WorkflowDSLParser
from workflows.registry import WorkflowRegistry

parser = WorkflowDSLParser()
template = parser.parse_file("examples/dsl/my_workflow.yaml")

registry = WorkflowRegistry()
errors = registry.validate_template(template)

if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Valid workflow")
```

---

## 📂 File Structure

```
cortex-flow/
├── workflows/
│   ├── dsl/                           # DSL System
│   │   ├── __init__.py
│   │   ├── parser.py                  # DSL → WorkflowTemplate
│   │   ├── generator.py               # WorkflowTemplate → DSL
│   │   └── templates/                 # Jinja2 templates (future)
│   │       └── workflow.jinja2
│   │
│   ├── templates/                     # JSON workflows
│   │   ├── report_generation.json
│   │   └── ...
│   │
│   ├── engine.py                      # Workflow execution
│   └── registry.py                    # Template management
│
├── examples/
│   └── dsl/                           # YAML DSL Examples
│       ├── newsletter.yaml
│       ├── database_report.yaml
│       ├── multi_source_research.yaml
│       └── sentiment_routing.yaml
│
├── scripts/
│   ├── parse_workflow.py              # CLI: DSL → JSON
│   └── generate_dsl.py                # CLI: JSON → DSL
│
├── tests/
│   └── test_dsl_roundtrip.py          # Round-trip tests
│
└── docs/
    └── dsl/                           # DSL Documentation
        ├── README.md                  # This file
        ├── syntax_reference.md        # Complete syntax guide
        └── examples.md                # More examples
```

---

## 🎓 Advanced Features

### Custom Metadata for Routing

```yaml
nodes:
  - analyze:
      agent: analyst
      instruction: "Extract sentiment and metrics"
      # Populates: state.sentiment_score, state.content_length
      # Used by conditional routing
```

### MCP Prompt Auto-Population

```yaml
nodes:
  - query:
      agent: mcp_tool
      tool_name: query_database
      use_mcp_prompt: true      # Auto-load prompt from MCP server
      instruction: "Custom addition to MCP prompt"
```

### Nested Parameter Substitution

```yaml
nodes:
  - query:
      agent: mcp_tool
      params:
        query_payload:
          table: "{table_name}"           # Substituted from params
          filters:
            created_at: ">{start_date}"   # Nested substitution
```

---

## 🐛 Troubleshooting

### Error: "Missing required field: 'workflow'"

```yaml
# ❌ WRONG
version: "1.0"
nodes: []

# ✅ CORRECT
workflow: my_workflow
version: "1.0"
nodes: []
```

### Error: "Unknown operator: 'INVALID'"

```yaml
# ❌ WRONG
conditions:
  - from: node1
    rules:
      - if: {field: score, op: "INVALID", value: 5}

# ✅ CORRECT (use: >, <, ==, !=, contains, in)
conditions:
  - from: node1
    rules:
      - if: {field: score, op: ">", value: 5}
```

### Variable Not Substituted

```yaml
# Check:
# 1. Variable name matches exactly (case-sensitive)
# 2. Variable defined in params or previous node output
# 3. Syntax: {variable} not ${variable} or {{variable}}

params:
  topic: AI           # ✅ Correct

nodes:
  - research:
      instruction: "Research {topic}"    # ✅ Will substitute
      instruction: "Research {tpic}"     # ❌ Typo, won't substitute
```

---

## 🔗 Related Documentation

- [Workflow System Overview](../workflows/README.md)
- [Creating Templates](../workflows/01_creating_templates.md)
- [MCP Integration](../workflows/03_mcp_integration.md)
- [Conditional Routing](../workflows/02_conditional_routing.md)

---

## 🤝 Contributing

Per contribuire nuovi esempi DSL:

1. Crea YAML in `examples/dsl/`
2. Valida: `python scripts/parse_workflow.py examples/dsl/my_workflow.yaml --validate-only`
3. Testa round-trip: `pytest tests/test_dsl_roundtrip.py`
4. Documenta in `docs/dsl/examples.md`

---

**Documentazione aggiornata**: 2025-10-07
