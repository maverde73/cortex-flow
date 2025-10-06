# Guida all'Integrazione MCP nei Workflow

## Indice

- [Prerequisiti](#prerequisiti)
- [Anatomia MCP Node](#anatomia-mcp-node)
- [MCP Prompts](#mcp-prompts)
- [Esempi Pratici](#esempi-pratici)
- [Parametri Avanzati](#parametri-mcp-avanzati)
- [Error Handling](#error-handling-mcp-tools)
- [Best Practices](#best-practices-mcp-integration)
- [Testing](#testing-mcp-workflows)

---

## Prerequisiti

### Configurazione MCP Server

In `.env`:

```bash
# Abilita MCP system
MCP_ENABLE=true

# Corporate Server (database queries)
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_API_KEY=your_api_key_here

# Weather Server (esempio)
MCP_SERVER_WEATHER_TYPE=remote
MCP_SERVER_WEATHER_TRANSPORT=streamable_http
MCP_SERVER_WEATHER_URL=http://localhost:8006/mcp
MCP_SERVER_WEATHER_ENABLED=true

# File Server (locale)
MCP_SERVER_FILES_TYPE=local
MCP_SERVER_FILES_TRANSPORT=stdio
MCP_SERVER_FILES_COMMAND=python
MCP_SERVER_FILES_ARGS=["-m", "mcp_servers.file_server"]
MCP_SERVER_FILES_ENABLED=true
```

### Verifica MCP Tools Disponibili

```python
from utils.mcp_registry import get_mcp_registry

registry = get_mcp_registry()
await registry.discover_all_servers()

# Lista tools
tools = await registry.list_tools()
for tool in tools:
    print(f"- {tool.name} ({tool.server_name})")
    print(f"  {tool.description}")
```

**Output esempio**:
```
- query_database (corporate)
  Query corporate database using SQL
- get_weather (weather)
  Get current weather for a city
- read_file (files)
  Read file contents from local filesystem
- write_file (files)
  Write content to file
```

---

## Anatomia MCP Node

### Struttura Base

```json
{
  "id": "unique_node_id",
  "agent": "mcp_tool",              // ← OBBLIGATORIO per MCP
  "tool_name": "tool_name_here",    // ← Nome tool MCP
  "instruction": "Human-readable description of what this does",

  "params": {                       // ← Parametri tool
    "param1": "value",
    "param2": "{variable}",
    "nested": {
      "key": "{another_var}"
    }
  },

  "timeout": 60                     // Opzionale (default: 120s)
}
```

### Esempio Completo

```json
{
  "id": "fetch_weather",
  "agent": "mcp_tool",
  "tool_name": "get_weather",
  "instruction": "Fetch current weather for {city}",

  "params": {
    "city": "{city_name}",
    "units": "metric",
    "include_forecast": true
  },

  "timeout": 30
}
```

**Esecuzione workflow engine**:

```python
# 1. Sostituisce variabili
params_resolved = {
    "city": "Milan",  # Da workflow_params["city_name"]
    "units": "metric",
    "include_forecast": True
}

# 2. Chiama MCP client
from utils.mcp_client import MCPClient
client = MCPClient()

result = await client.call_tool(
    tool_name="get_weather",
    arguments=params_resolved
)

# 3. Salva output
state.node_outputs["fetch_weather"] = result
```

---

## MCP Prompts

### Panoramica

Gli **MCP Prompts** sono istruzioni fornite dai server MCP che guidano gli agenti LLM sull'utilizzo corretto dei tool. Il protocollo MCP supporta l'endpoint `prompts/list` che restituisce una lista di prompt associati ai tool.

**Benefici**:
- ✅ **Migliore accuratezza**: Gli agenti ReAct ricevono istruzioni precise su come usare i tool
- ✅ **Meno errori**: Riduce chiamate malformate o parametri mancanti
- ✅ **Auto-documentazione**: I workflow si auto-documentano con le istruzioni del server
- ✅ **Manutenzione centralizzata**: Le istruzioni sono gestite dal server MCP, non duplicate nei template

### Architettura MCP Prompts

Il sistema implementa 3 livelli di integrazione:

#### Livello 1: Prompt Discovery (Registry)

Il `MCPRegistry` scopre automaticamente i prompts durante la registrazione del server:

```python
from utils.mcp_registry import get_mcp_registry

registry = get_mcp_registry()

# Registrazione server → Automatic prompt discovery
await registry.register_server(server_config)

# Recupera un prompt specifico
prompt = await registry.get_prompt("database_query_guide")

# Lista tutti i prompts disponibili
prompts = await registry.get_available_prompts()
for p in prompts:
    print(f"- {p.name}: {p.description}")
```

**Struttura MCPPrompt**:
```python
@dataclass
class MCPPrompt:
    name: str                                    # Nome prompt
    description: str                             # Istruzioni testuali
    arguments: List[MCPPromptArgument]           # Parametri richiesti
    server_name: str                             # Server di provenienza
    content: Optional[str] = None                # Contenuto esteso (opzionale)
```

#### Livello 2: Prompt Injection (LangChain Tools)

I tool LangChain vengono automaticamente arricchiti con i prompt MCP:

```python
from utils.mcp_client import get_mcp_langchain_tools

# Crea LangChain tools con prompt injection
tools = await get_mcp_langchain_tools()

for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    # Description include MCP prompt se disponibile:
    # "Query corporate database using SQL
    #
    # ## Usage Guide
    # [MCP Prompt instructions here...]"
```

**Come funziona**:
1. `get_mcp_langchain_tools()` recupera tutti i tool MCP disponibili
2. Per ogni tool, cerca un prompt associato (via `associated_prompt` o nome uguale)
3. Se trovato, aggiunge il prompt alla `description` del tool
4. Gli agenti ReAct vedono le istruzioni estese quando selezionano il tool

**Vantaggi per ReAct**:
- Il supervisor ReAct riceve guidance esplicita nella descrizione del tool
- Migliora tool selection durante il reasoning step
- Riduce tentativi ed errori nell'utilizzo dei tool

#### Livello 3: Auto-Population (Workflow Templates)

I workflow possono auto-popolare le istruzioni dei nodi MCP:

```json
{
  "id": "query_corporate_db",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": true,          // ← Abilita auto-population
  "instruction": "Query sales data", // ← Verrà arricchita con MCP prompt

  "params": {
    "query_payload": {
      "database": "sales_db",
      "table": "transactions",
      "method": "select"
    }
  }
}
```

**Comportamento**:
- Se `use_mcp_prompt: true`, il workflow engine cerca il prompt associato al tool
- Se trovato, **arricchisce** l'instruction esistente con il prompt
- Se instruction è generica ("Execute MCP tool"), la **sostituisce** completamente
- Se il prompt non è disponibile, usa l'instruction originale

**Esempio concreto**:

Template originale:
```json
{
  "instruction": "Query sales data",
  "use_mcp_prompt": true
}
```

Dopo auto-population (runtime):
```json
{
  "instruction": "Query sales data\n\n## MCP Tool Guidance\n\n**Database Query Tool Instructions**\n\nThis tool requires a structured query_payload object with:\n- database: Target database name\n- table: Table to query\n- method: 'select', 'insert', 'update', or 'delete'\n- columns: Array of column names\n- filters: Object with filter conditions\n\nExample:\n{\n  \"database\": \"sales_db\",\n  \"table\": \"orders\",\n  \"method\": \"select\",\n  \"columns\": [\"id\", \"amount\", \"date\"],\n  \"filters\": {\"status\": \"completed\"}\n}\n\nIMPORTANT:\n- Always specify required fields\n- Use proper data types\n- Avoid SQL injection in filters"
}
```

### Esempi Pratici MCP Prompts

#### Esempio 1: Tool con Prompt Associato

**Server MCP** (corporate_server) espone:

```json
// GET http://localhost:8005/mcp → prompts/list
{
  "result": {
    "prompts": [
      {
        "name": "database_query_guide",
        "description": "Instructions for safely querying corporate databases...",
        "arguments": [
          {"name": "database", "description": "Target database", "required": true},
          {"name": "query_type", "description": "Type of query", "required": false}
        ]
      }
    ]
  }
}
```

**Tool MCP**:
```python
# Tool registrato con associated_prompt
tool = MCPTool(
    name="query_database",
    description="Query corporate database",
    associated_prompt="database_query_guide",  // ← Link al prompt
    server_name="corporate"
)
```

**Nel workflow**:
```json
{
  "id": "fetch_sales",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": true,  // ← Usa il prompt associato

  "params": {
    "query_payload": {
      "database": "sales_db",
      "table": "orders",
      "method": "select"
    }
  }
}
```

#### Esempio 2: Workflow con e senza MCP Prompt

**Senza MCP Prompt** (instruction manuale):
```json
{
  "id": "custom_query",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": false,  // ← Usa solo instruction manuale

  "instruction": "Execute a simple select query on the users table to retrieve active users only. Use filters carefully.",

  "params": {...}
}
```

**Con MCP Prompt** (auto-population):
```json
{
  "id": "guided_query",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": true,  // ← Arricchisce con prompt MCP

  "instruction": "Retrieve active users",  // Verrà espanso

  "params": {...}
}
```

Risultato runtime per `guided_query`:
```
Instruction finale:
"Retrieve active users

## MCP Tool Guidance

[Full database query guide from MCP server, including:
- Required parameters
- Data types
- Security considerations
- Examples
- Common pitfalls]"
```

#### Esempio 3: ReAct Agent con MCP Tools Enhanced

**Scenario**: Supervisor ReAct agent deve scegliere tra più tool MCP.

**Tool descriptions (senza prompt)**:
```
1. query_database - Query corporate database
2. get_weather - Get weather data
3. send_email - Send email via SMTP
```

**Tool descriptions (con prompt injection)**:
```
1. query_database - Query corporate database

   ## Usage Guide

   This tool accepts a query_payload with database, table, method,
   columns, and filters. Always validate database name against
   allowed list. Use parameterized queries to prevent SQL injection.

   Example:
   {"database": "sales_db", "table": "orders", "method": "select", ...}

2. get_weather - Get weather data

   ## Usage Guide

   Requires city name and optional units (metric/imperial).
   Returns current conditions and 7-day forecast. Rate limited
   to 100 requests/hour.

3. send_email - Send email via SMTP

   ## Usage Guide

   Requires recipient, subject, body. Optional: cc, bcc, attachments.
   Validates email format. Max 10 recipients per call. Attachments
   limited to 10MB total.
```

**Risultato**: L'agente ReAct ha informazioni dettagliate per:
- Selezionare il tool giusto
- Costruire i parametri corretti
- Evitare errori comuni

### Configurazione MCP Prompts

#### Associare Prompts ai Tool

**Opzione 1: Nome uguale** (convenzione)
```python
# Tool: query_database
# Prompt: query_database  ← Stesso nome, auto-associato
```

**Opzione 2: Campo associated_prompt**
```python
tool = MCPTool(
    name="db_query",
    description="...",
    associated_prompt="database_query_guide"  // ← Explicit link
)
```

#### Verificare Prompts Disponibili

```python
from utils.mcp_registry import get_mcp_registry

registry = get_mcp_registry()

# Lista prompts
prompts = await registry.get_available_prompts()

for prompt in prompts:
    print(f"\nPrompt: {prompt.name}")
    print(f"Server: {prompt.server_name}")
    print(f"Description: {prompt.description[:100]}...")
    print(f"Arguments: {[arg.name for arg in prompt.arguments]}")
```

Output esempio:
```
Prompt: database_query_guide
Server: corporate
Description: Comprehensive guide for querying corporate databases safely. This tool requires structured...
Arguments: ['database', 'query_type']

Prompt: email_sending_guide
Server: communication
Description: Instructions for sending emails through the corporate SMTP server...
Arguments: ['recipient_type', 'template_id']
```

### Best Practices MCP Prompts

#### ✅ DO

**1. Usa `use_mcp_prompt: true` quando disponibile**
```json
// ✅ GOOD: Sfrutta guidance del server
{
  "agent": "mcp_tool",
  "tool_name": "complex_api",
  "use_mcp_prompt": true,
  "instruction": "Call API for user data"  // Verrà arricchito
}
```

**2. Override selettivo quando necessario**
```json
// ✅ GOOD: Prompt MCP + custom instruction
{
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": true,
  "instruction": "IMPORTANT: Query read-replica only. Standard query for active users."
  // → Instruction custom + MCP guidance appended
}
```

**3. Documenta quando NON usi MCP prompt**
```json
// ✅ GOOD: Spiega perché skip MCP prompt
{
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": false,  // Skip: istruzioni specifiche per questo workflow
  "instruction": "Execute pre-validated query from template X. Skip normal validation."
}
```

**4. Verifica prompt availability prima del deploy**
```python
# ✅ GOOD: Pre-flight check
registry = get_mcp_registry()
prompt = await registry.get_prompt("critical_tool_guide")

if not prompt:
    logger.warning("MCP prompt 'critical_tool_guide' not available. Workflow may have reduced accuracy.")
```

#### ❌ DON'T

**1. Non duplicare istruzioni MCP nei template**
```json
// ❌ BAD: Duplicate MCP prompt content
{
  "use_mcp_prompt": true,
  "instruction": "This tool requires query_payload with database, table, method... [entire MCP prompt duplicated]"
  // → Ridondante, il prompt verrà aggiunto automaticamente
}

// ✅ GOOD: Breve instruction + auto-inject
{
  "use_mcp_prompt": true,
  "instruction": "Query sales data for Q1"
}
```

**2. Non assumere che i prompts siano sempre disponibili**
```json
// ❌ BAD: Assume prompt exists
{
  "use_mcp_prompt": true,
  "instruction": ""  // Vuota! Se prompt non c'è, nessuna guidance
}

// ✅ GOOD: Fallback instruction
{
  "use_mcp_prompt": true,
  "instruction": "Query database for sales data. Use query_payload format."
}
```

**3. Non hardcodare prompt nei workflow**
```json
// ❌ BAD: Hardcoded prompt (diventa stale)
{
  "use_mcp_prompt": false,
  "instruction": "Tool guide v1.2: Use format X, avoid Y..."
  // → Se server aggiorna prompt, questo è obsoleto
}

// ✅ GOOD: Usa MCP prompt dinamico
{
  "use_mcp_prompt": true,
  "instruction": "Query sales data"
}
```

### Troubleshooting MCP Prompts

#### Problema: Prompt non trovato

**Sintomo**: Log message
```
📋 Auto-populated instruction for 'node_id' with MCP prompt
[Non appare]
```

**Soluzioni**:

1. Verifica che il server MCP supporti prompts:
```bash
curl -X POST http://localhost:8005/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "prompts/list"
  }'
```

2. Controlla registry:
```python
prompts = await registry.get_available_prompts()
print([p.name for p in prompts])
```

3. Controlla tool association:
```python
tool = await registry.get_tool("query_database")
print(f"Associated prompt: {tool.associated_prompt}")
```

#### Problema: Prompt non aggiunto a tool description

**Sintomo**: ReAct agent non vede guidance nei tool

**Soluzioni**:

1. Verifica che `get_mcp_langchain_tools()` sia chiamato dopo discovery:
```python
# ✅ CORRECT ORDER
await registry.discover_all_servers()  # ← Prima
tools = await get_mcp_langchain_tools()  # ← Poi
```

2. Check tool description:
```python
tools = await get_mcp_langchain_tools()
for tool in tools:
    if "Usage Guide" in tool.description:
        print(f"✓ {tool.name} has prompt")
    else:
        print(f"✗ {tool.name} missing prompt")
```

---

## Esempi Pratici

### Esempio 1: Database Query + Analysis

**File**: `examples/sales_analysis_workflow.json`

```json
{
  "name": "sales_analysis",
  "version": "1.0",
  "description": "Query sales DB and generate insights. Params: {time_period}",
  "trigger_patterns": [".*sales.*report.*", ".*revenue.*analysis.*"],

  "nodes": [
    {
      "id": "query_sales_data",
      "agent": "mcp_tool",
      "tool_name": "query_database",
      "instruction": "Query sales data for {time_period}",

      "params": {
        "query_payload": {
          "database": "sales_db",
          "table": "transactions",
          "method": "select",
          "columns": ["date", "product", "amount", "customer_id"],
          "filters": {
            "date_range": "{time_period}"
          },
          "limit": 1000
        }
      },

      "timeout": 60
    },
    {
      "id": "analyze_trends",
      "agent": "analyst",
      "instruction": "Analyze sales trends from this data:\n\n{query_sales_data}\n\nProvide:\n- Top products\n- Growth trends\n- Customer segments\n- Anomalies",
      "depends_on": ["query_sales_data"]
    },
    {
      "id": "create_report",
      "agent": "writer",
      "instruction": "Create executive sales report:\n\n{analyze_trends}\n\nFormat: Professional business report with chart suggestions",
      "depends_on": ["analyze_trends"]
    }
  ]
}
```

**Utilizzo**:
```python
from langchain_core.messages import HumanMessage

await supervisor.ainvoke({
    "messages": [HumanMessage(content="Generate sales report")],
    "workflow_template": "sales_analysis",
    "workflow_params": {
        "time_period": "2024-Q1"
    }
})
```

**Output query_sales_data** (esempio):
```json
[
  {"date": "2024-01-15", "product": "Widget A", "amount": 1250.0, "customer_id": 101},
  {"date": "2024-01-16", "product": "Widget B", "amount": 890.5, "customer_id": 102},
  ...
]
```

---

### Esempio 2: Multi-Source Weather + Travel

**File**: `examples/travel_planner_workflow.json`

```json
{
  "name": "travel_planner",
  "version": "1.0",
  "description": "Plan trip using weather + flight data. Params: {destination_city, departure_city, travel_date, num_passengers, user_preferences}",
  "trigger_patterns": [".*plan.*trip.*", ".*travel.*to.*"],

  "nodes": [
    {
      "id": "get_destination_weather",
      "agent": "mcp_tool",
      "tool_name": "get_weather",
      "instruction": "Get weather forecast for {destination_city}",

      "params": {
        "city": "{destination_city}",
        "days": 7,
        "units": "metric"
      },

      "parallel_group": "external_data"
    },
    {
      "id": "search_flights",
      "agent": "mcp_tool",
      "tool_name": "search_flights",
      "instruction": "Find flights to {destination_city}",

      "params": {
        "origin": "{departure_city}",
        "destination": "{destination_city}",
        "date": "{travel_date}",
        "passengers": "{num_passengers}"
      },

      "parallel_group": "external_data"
    },
    {
      "id": "research_attractions",
      "agent": "researcher",
      "instruction": "Research top attractions in {destination_city}",
      "parallel_group": "external_data"
    },
    {
      "id": "create_itinerary",
      "agent": "writer",
      "instruction": "Create travel itinerary combining:\n\nWeather:\n{get_destination_weather}\n\nFlights:\n{search_flights}\n\nAttractions:\n{research_attractions}\n\nPreferences: {user_preferences}",

      "depends_on": ["get_destination_weather", "search_flights", "research_attractions"]
    }
  ]
}
```

**Note**:
- 3 fonti in parallelo: Weather MCP + Flights MCP + Web Research
- `parallel_group: "external_data"` → Esecuzione simultanea
- `depends_on` tutti e 3 → Aspetta completamento prima di creare itinerario

**Performance**:
```
Sequential: weather (10s) + flights (15s) + research (60s) = 85s
Parallel:   max(weather, flights, research) = 60s
Risparmio: 29% tempo totale
```

---

### Esempio 3: File Operations Workflow

**File**: `examples/document_processor_workflow.json`

```json
{
  "name": "document_processor",
  "version": "1.0",
  "description": "Read file, process, save result. Params: {input_file, output_file, query_topic}",
  "trigger_patterns": [".*process.*document.*", ".*analyze.*file.*"],

  "nodes": [
    {
      "id": "read_input_file",
      "agent": "mcp_tool",
      "tool_name": "read_file",
      "instruction": "Read input document from {input_file}",

      "params": {
        "file_path": "{input_file}",
        "encoding": "utf-8"
      }
    },
    {
      "id": "analyze_content",
      "agent": "analyst",
      "instruction": "Analyze document:\n{read_input_file}\n\nExtract:\n- Key topics\n- Action items\n- Sentiment",
      "depends_on": ["read_input_file"]
    },
    {
      "id": "generate_summary",
      "agent": "writer",
      "instruction": "Generate executive summary:\n{analyze_content}",
      "depends_on": ["analyze_content"]
    },
    {
      "id": "save_output",
      "agent": "mcp_tool",
      "tool_name": "write_file",
      "instruction": "Save summary to {output_file}",

      "params": {
        "file_path": "{output_file}",
        "content": "{generate_summary}",
        "encoding": "utf-8"
      },

      "depends_on": ["generate_summary"]
    }
  ]
}
```

**Utilizzo**:
```python
await supervisor.ainvoke({
    "messages": [HumanMessage(content="Process quarterly report")],
    "workflow_template": "document_processor",
    "workflow_params": {
        "input_file": "/data/reports/Q1_2024.txt",
        "output_file": "/data/summaries/Q1_2024_summary.txt"
    }
})
```

---

## Parametri MCP Avanzati

### Nested Parameter Substitution

```json
{
  "id": "complex_query",
  "agent": "mcp_tool",
  "tool_name": "advanced_search",

  "params": {
    "query": {
      "filters": {
        "category": "{product_category}",
        "price_range": {
          "min": "{min_price}",
          "max": "{max_price}"
        },
        "tags": "{search_tags}"  // ← Può essere array JSON string
      },
      "sort": {
        "field": "relevance",
        "order": "desc"
      },
      "pagination": {
        "page": 1,
        "per_page": 50
      }
    },
    "options": {
      "include_metadata": true,
      "highlight": "{search_term}"
    }
  }
}
```

**Engine resolution**:

```python
# Input workflow_params
workflow_params = {
    "product_category": "electronics",
    "min_price": 100,
    "max_price": 500,
    "search_tags": '["laptop", "portable"]',  # JSON string
    "search_term": "gaming laptop"
}

# Dopo sostituzione (engine)
{
    "query": {
        "filters": {
            "category": "electronics",
            "price_range": {"min": 100, "max": 500},
            "tags": ["laptop", "portable"]  # ← Parsed da JSON
        },
        "sort": {"field": "relevance", "order": "desc"},
        "pagination": {"page": 1, "per_page": 50}
    },
    "options": {
        "include_metadata": True,
        "highlight": "gaming laptop"
    }
}
```

---

### Dynamic Parameter Building

Parametri che dipendono da output precedenti:

```json
{
  "nodes": [
    {
      "id": "extract_entities",
      "agent": "analyst",
      "instruction": "Extract entities from:\n{user_query}\n\nProvide JSON:\n{\"location\": \"...\", \"date\": \"...\", \"category\": \"...\"}"
    },
    {
      "id": "search_with_entities",
      "agent": "mcp_tool",
      "tool_name": "semantic_search",

      "params": {
        "location": "{extract_entities.location}",     // ← Da JSON output
        "date_filter": "{extract_entities.date}",
        "category": "{extract_entities.category}",
        "query_text": "{user_query}"
      },

      "depends_on": ["extract_entities"]
    }
  ]
}
```

**Come funziona**:

1. `extract_entities` output:
```json
{
  "location": "Milan",
  "date": "2024-03-15",
  "category": "restaurants"
}
```

2. Engine parsea JSON e accede con dot notation:
```python
params["location"] = state.node_outputs["extract_entities"]["location"]
# → "Milan"
```

3. MCP tool riceve:
```json
{
  "location": "Milan",
  "date_filter": "2024-03-15",
  "category": "restaurants",
  "query_text": "best pizza places"
}
```

---

## Error Handling MCP Tools

### Timeout Configuration

```json
{
  "id": "slow_api_call",
  "agent": "mcp_tool",
  "tool_name": "external_api",

  "params": {...},

  "timeout": 180  // ← 3 minuti (default: 120s)
}
```

**Timeout per tipo di operazione**:
```
Database query:          30-60s
External API call:       60-90s
File read/write:         10-30s
Heavy processing (ML):   180-300s
```

---

### Retry Logic (MCP Client)

Configurazione globale in `.env`:

```bash
MCP_CLIENT_RETRY_ATTEMPTS=3
MCP_CLIENT_TIMEOUT=30.0
MCP_TOOLS_TIMEOUT_MULTIPLIER=1.5  # Moltiplicatore per MCP tools
```

**MCP Client retry automaticamente su**:
- Connection errors (ConnectionError, TimeoutError)
- HTTP 5xx errors (server unavailable)
- Network errors

**NON retry su**:
- HTTP 4xx (bad request, unauthorized, forbidden)
- Validation errors
- Tool not found

**Retry strategy**:
```python
# In utils/mcp_client.py
for attempt in range(retry_attempts):
    try:
        return await call_tool(...)
    except (ConnectionError, TimeoutError) as e:
        if attempt < retry_attempts - 1:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        else:
            raise RuntimeError(f"Tool failed after {retry_attempts} attempts")
```

---

### Fallback Strategy

Template con fallback a web research:

```json
{
  "name": "resilient_search",
  "version": "1.0",
  "description": "Search with MCP API fallback to web",

  "nodes": [
    {
      "id": "primary_search",
      "agent": "mcp_tool",
      "tool_name": "premium_search_api",
      "params": {
        "query": "{query}",
        "max_results": 10
      },
      "timeout": 30
    },
    {
      "id": "check_results",
      "agent": "analyst",
      "instruction": "Check if search returned results:\n{primary_search}\n\nProvide has_results: true/false"
    },
    {
      "id": "use_results",
      "agent": "writer",
      "instruction": "Process results:\n{primary_search}"
    },
    {
      "id": "fallback_search",
      "agent": "researcher",
      "instruction": "Perform web research as fallback for: {query}"
    }
  ],

  "conditional_edges": [
    {
      "from_node": "check_results",
      "conditions": [
        {
          "field": "custom_metadata.has_results",
          "operator": "equals",
          "value": true,
          "next_node": "use_results"
        }
      ],
      "default": "fallback_search"
    }
  ]
}
```

**Flow**:
```
primary_search → check_results → [has_results?]
                                    ├─ YES → use_results
                                    └─ NO → fallback_search
```

---

## Best Practices MCP Integration

### ✅ DO

#### 1. Validate tool availability

```python
# Prima di usare template con MCP
from utils.mcp_registry import get_mcp_registry

registry = get_mcp_registry()
tool = await registry.get_tool("query_database")

if not tool:
    raise ValueError("Tool 'query_database' not available. Start corporate_server.")
```

#### 2. Set realistic timeouts

```json
// Database query → breve
{"tool_name": "query_database", "timeout": 30}

// External API → medio
{"tool_name": "weather_api", "timeout": 60}

// Heavy processing → lungo
{"tool_name": "video_transcription", "timeout": 300}
```

#### 3. Handle empty results

```json
{
  "id": "validate_output",
  "agent": "analyst",
  "instruction": "Check if MCP tool returned data:\n{mcp_node}\n\nIf empty, set error_flag: true"
}
```

Con conditional routing:
```json
{
  "from_node": "validate_output",
  "conditions": [
    {
      "field": "custom_metadata.error_flag",
      "operator": "equals",
      "value": true,
      "next_node": "error_handler"
    }
  ],
  "default": "success_handler"
}
```

#### 4. Use parallel when independent

```json
// ✅ GOOD: 3 MCP calls in parallelo
{
  "nodes": [
    {
      "id": "db_users",
      "agent": "mcp_tool",
      "tool_name": "query_database",
      "parallel_group": "data"
    },
    {
      "id": "db_orders",
      "agent": "mcp_tool",
      "tool_name": "query_database",
      "parallel_group": "data"
    },
    {
      "id": "api_pricing",
      "agent": "mcp_tool",
      "tool_name": "get_pricing",
      "parallel_group": "data"
    },
    {
      "id": "combine",
      "agent": "analyst",
      "instruction": "Combine:\n{db_users}\n{db_orders}\n{api_pricing}",
      "depends_on": ["db_users", "db_orders", "api_pricing"]
    }
  ]
}
```

**Performance**: 3 chiamate simultanee invece di sequenziali.

#### 5. Document MCP dependencies

```json
{
  "name": "sales_report",
  "description": "Sales report workflow.\n\nREQUIRES:\n- corporate_server on port 8005\n- Tool: query_database\n- Database: sales_db\n\nParams: {time_period}",
  "nodes": [...]
}
```

---

### ❌ DON'T

#### 1. Sequential MCP calls quando possibile parallelo

```json
// ❌ BAD: 3 chiamate sequenziali (lente)
{"id": "db1", "depends_on": []},
{"id": "db2", "depends_on": ["db1"]},  // Non serve dipendenza!
{"id": "db3", "depends_on": ["db2"]}   // Non serve dipendenza!

// ✅ GOOD: Parallelo
{"id": "db1", "parallel_group": "queries"},
{"id": "db2", "parallel_group": "queries"},
{"id": "db3", "parallel_group": "queries"}
```

#### 2. Hardcode credentials in template

```json
// ❌ NEVER
{
  "params": {
    "api_key": "sk-1234567890abcdef"  // ← MAI!
  }
}

// ✅ GOOD: Credentials in MCP server config (.env)
MCP_SERVER_MYAPI_API_KEY=sk-1234567890abcdef
```

#### 3. Assume MCP tool schema

```json
// ❌ BAD: Assumes unknown fields
{
  "params": {
    "query": "...",
    "unknown_field": "..."  // ← Può causare errore
  }
}

// ✅ GOOD: Check tool input_schema
```

Check schema:
```python
tool = await registry.get_tool("query_database")
print(tool.input_schema)
# {"type": "object", "properties": {"query_payload": {...}}, "required": ["query_payload"]}
```

#### 4. Ignore timeout errors

```json
// ❌ BAD: Timeout troppo breve per operazione pesante
{
  "tool_name": "process_large_dataset",
  "timeout": 30  // ← Troppo breve!
}

// ✅ GOOD: Timeout adeguato
{
  "tool_name": "process_large_dataset",
  "timeout": 300
}
```

---

## Testing MCP Workflows

### Unit Test (Mock MCP)

```python
import pytest
from unittest.mock import AsyncMock, patch
from workflows.engine import WorkflowEngine
from workflows.registry import WorkflowRegistry

@pytest.mark.asyncio
async def test_mcp_workflow_mock():
    """Test workflow with mocked MCP client"""

    # Mock MCP client
    mock_client = AsyncMock()
    mock_client.call_tool.return_value = '{"temperature": 22, "condition": "sunny"}'

    with patch('workflows.engine.MCPClient', return_value=mock_client):
        engine = WorkflowEngine()
        registry = WorkflowRegistry()
        registry.load_templates()

        template = registry.get("weather_workflow")

        result = await engine.execute_workflow(
            template=template,
            user_input="Get weather",
            params={"city_name": "Milan"}
        )

        # Assertions
        assert result.success
        assert "22" in result.final_output
        assert "sunny" in result.final_output.lower()

        # Verify MCP call
        mock_client.call_tool.assert_called_once_with(
            tool_name="get_weather",
            arguments={"city": "Milan", "units": "metric", "include_forecast": True}
        )
```

---

### Integration Test (Real MCP Server)

```python
@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.skip(reason="Requires corporate_server on port 8005")
async def test_real_mcp_workflow():
    """
    Test with real MCP server.

    PREREQUISITI:
    - Corporate server: python -m servers.corporate_server --port 8005
    - MCP_SERVER_CORPORATE_ENABLED=true in .env
    - Database: sales_db accessible
    """
    engine = WorkflowEngine()
    registry = WorkflowRegistry()
    registry.load_templates()

    template = registry.get("sales_analysis")

    result = await engine.execute_workflow(
        template=template,
        user_input="Generate Q1 sales report",
        params={"time_period": "2024-Q1"}
    )

    # Assertions
    assert result.success
    assert len(result.node_results) == 3  # query + analyze + report

    # Check MCP node
    mcp_result = result.node_results[0]
    assert mcp_result.agent == "mcp_tool"
    assert mcp_result.success
    assert len(mcp_result.output) > 0

    # Verify data structure
    import json
    data = json.loads(mcp_result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "date" in data[0]
    assert "amount" in data[0]
```

Vedi: `tests/test_workflow_mcp.py` per più esempi.

---

## Troubleshooting

### Problema: MCP tool not found

**Errore**:
```
ValueError: MCP tool 'query_database' not found
```

**Soluzioni**:

1. Check server status:
```python
registry = get_mcp_registry()
servers = await registry.list_servers()
for server in servers:
    print(f"{server.name}: {server.status}")
```

2. Check tool availability:
```python
tools = await registry.list_tools()
print([t.name for t in tools])
```

3. Restart MCP server:
```bash
# Stop
pkill -f corporate_server

# Start
python -m servers.corporate_server --port 8005
```

---

### Problema: Timeout errors

**Errore**:
```
RuntimeError: MCP tool 'slow_api' timed out after 30s
```

**Soluzioni**:

1. Aumenta timeout nel template:
```json
{"timeout": 120}
```

2. Aumenta global timeout:
```bash
# .env
MCP_CLIENT_TIMEOUT=60.0
```

3. Optimize tool performance (server-side)

---

### Problema: Parameter substitution failed

**Errore**:
```
KeyError: 'table_name' not found in workflow_params
```

**Soluzioni**:

1. Verifica parametri richiesti:
```python
# In template description
"description": "Params: {time_period, table_name}"
```

2. Fornisci tutti i parametri:
```python
await supervisor.ainvoke({
    ...,
    "workflow_params": {
        "time_period": "2024-Q1",
        "table_name": "sales"  # ← Mancava!
    }
})
```

---

## Prossimi Passi

- [Creating Templates ←](01_creating_templates.md) - Crea template base
- [Conditional Routing ←](02_conditional_routing.md) - Combina MCP con routing
- [Examples →](examples/) - Template MCP pronti all'uso

---

**Vedi anche**:
- `workflows/templates/data_analysis_report.json` - MCP database example
- `workflows/templates/multi_source_research.json` - Parallel MCP + web
- `utils/mcp_client.py` - MCP client implementation
- `utils/mcp_registry.py` - MCP registry implementation
- `tests/test_workflow_mcp.py` - MCP integration tests
