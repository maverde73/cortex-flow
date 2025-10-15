# Database Query Workflow Design v3.0 (ITERATIVE WITH DYNAMIC CONTEXT)

## Document Information
- **Version**: 3.0 (Iterative with Dynamic Context)
- **Date**: 2025-10-12
- **Status**: Design Document - Ready for Review
- **Previous Version**: v2.0 (5 nodes, too simplified - LLM lacks context)
- **Evolution**: v1.0 (12 nodes) → v2.0 (5 nodes, TOO simplified) → **v3.0 (8-10 nodes, context-aware)**

## Executive Summary

La **versione 2.0 fallisce** perché l'LLM riceve solo il welcome message (lista tabelle) ma **NON ha lo schema dettagliato** (nomi colonne, tipi, relazioni) né la documentazione delle features.

**Problema v2.0**: DeepSeek genera query invalide perché non sa quali colonne esistono!

**Soluzione v3.0**: L'LLM chiama tool MCP per ottenere **schema completo** prima di generare la query:
1. Analizza query → identifica tabelle necessarie
2. Chiama `get_table_details("Person,Customer")` → riceve schema completo
3. Valuta se servono altre tabelle → richiama tool se necessario
4. Identifica features necessarie → chiama `get_feature_details("WHERE,JOIN")`
5. Con TUTTO il contesto → genera query corretta
6. Se errore → retry con hint (max 5 tentativi)

**Risultato atteso**: 90%+ success rate perché l'LLM ha tutte le informazioni necessarie.

---

## Architecture Overview

### Principio Fondamentale

**"Just-In-Time Context Loading"**: L'LLM richiede dinamicamente solo le informazioni che servono, quando servono.

### Node Flow Diagram

```
┌──────────────┐
│ get_welcome  │  MCP Resource: Lista tabelle + features disponibili (8k chars)
└──────┬───────┘
       │
       v
┌──────────────┐
│ identify_    │  LLM: Analizza query → output: "Person,Customer"
│ tables       │       (identifica quali tabelle servono)
└──────┬───────┘
       │
       v
┌──────────────┐
│ get_table_   │  MCP Tool: Richiede schema dettagliato delle tabelle
│ details_1    │            input: {table_names: "Person,Customer"}
└──────┬───────┘            output: Schema completo (colonne, tipi, relazioni)
       │
       v
┌──────────────┐
│ evaluate_    │  LLM: Valuta se lo schema è sufficiente
│ schema       │       output: "complete" oppure "Person,Contract" (altre tabelle)
└──────┬───────┘
       │
       ├─── schema_complete = false ──> get_table_details_2 ──┐
       │                                                        │
       └─── schema_complete = true ─────────────────────────> ◯ (merge)
                                                                │
                                                                v
                                                    ┌──────────────┐
                                                    │ identify_    │  LLM: Identifica features
                                                    │ features     │       output: "WHERE,JOIN,LIMIT"
                                                    └──────┬───────┘
                                                           │
                                                           v
                                                    ┌──────────────┐
                                                    │ get_feature_ │  MCP Tool: Doc features
                                                    │ details      │
                                                    └──────┬───────┘
                                                           │
                                                           v
                                                    ┌──────────────┐
                                                    │ generate_    │  LLM: Con TUTTO il contesto!
                                                    │ query        │       Schema + Features + History
                                                    └──────┬───────┘
                                                           │
                                                           v
                                                    ┌──────────────┐
                                                    │ execute_     │  MCP Tool: Esegue query
                                                    │ query        │
                                                    └──────┬───────┘
                                                           │
                                                           v
                                                    ┌──────────────┐
                                                    │ check_       │  LLM: Analizza success/error
                                                    │ result       │       Estrae hint per retry
                                                    └──────┬───────┘
                                                           │
                                                           ├─── has_error: false ──> format_results (END)
                                                           │
                                                           └─── has_error: true ──> generate_query (RETRY, max 5)
```

### Nodes Comparison: v2.0 vs v3.0

| v2.0 (5 Nodes) | v3.0 (8-10 Nodes) | Why Changed |
|----------------|-------------------|-------------|
| get_welcome | get_welcome | Same - lista tabelle |
| ❌ REMOVED | **identify_tables** | **NEW** - LLM identifica quali tabelle servono |
| ❌ REMOVED | **get_table_details_1** | **NEW** - Ottiene schema dettagliato |
| ❌ REMOVED | **evaluate_schema** | **NEW** - Valuta se serve altro schema |
| ❌ REMOVED | **get_table_details_2** (conditional) | **NEW** - Secondo round se necessario |
| ❌ REMOVED | **identify_features** | **NEW** - LLM identifica features necessarie |
| ❌ REMOVED | **get_feature_details** | **NEW** - Doc dettagliata features |
| generate_query | generate_query | **Enhanced** - Riceve schema completo + features |
| execute_query | execute_query | Same |
| check_result | check_result | Same |
| format_results | format_results | Same |

**Critical Difference**: v2.0 LLM riceve solo welcome (lista tabelle), v3.0 LLM riceve schema completo (colonne, tipi, relazioni, esempi).

---

## Detailed Node Specifications

### Node 1: get_welcome

**Type**: `mcp_resource`

**Purpose**: Ottenere informazioni generali e lista di tutte le tabelle + features disponibili

**Configuration**:
```json
{
  "id": "get_welcome",
  "agent": "mcp_resource",
  "resource_uri": "welcome://message",
  "server_name": "database-query-server-railway",
  "instruction": "Read welcome resource to get available tables and features overview",
  "depends_on": [],
  "timeout": 30
}
```

**Expected Output** (8452 chars):
```
# Welcome to JSON Query API

## Available Tables (18 tables)
- Person
- Customer
- EmploymentContract
- Project
- Department
- Skill
...

## Available Query Features
- SELECT: Basic field selection
- WHERE: Filter conditions
- JOIN: Table relationships
- LIMIT/OFFSET: Pagination
- GROUP BY: Aggregation
- COUNT/SUM/AVG: Aggregate functions
...

## Important Rules
- Table names are case-sensitive
- Always use LIMIT for large queries
- JOIN requires exact column references
...
```

**Why This Matters**: Fornisce overview ma **NON dettagli** - serve solo per far capire all'LLM quali tabelle esistono.

---

### Node 2: identify_tables

**Type**: `llm`

**Purpose**: Analizzare la query utente e identificare quali tabelle sono coinvolte

**Configuration**:
```json
{
  "id": "identify_tables",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-v3.2-exp",
    "temperature": 0.2,
    "max_tokens": 500,
    "system_prompt": "You are a database query analyst. Analyze user requests and identify which tables are needed. Output ONLY comma-separated table names, no explanations."
  },
  "instruction": "...",
  "depends_on": ["get_welcome"],
  "timeout": 30
}
```

**Instruction Template**:
```
Analyze the user's query and identify which database tables are needed.

## User Query
{user_input}

## Available Tables (from welcome message)
{get_welcome}

## Your Task

1. Read the user query carefully
2. Identify which tables are mentioned or implied
3. Consider relationships between tables
4. Output ONLY table names as comma-separated list

## Output Format

Output ONLY the table names, comma-separated, no explanations:

Examples:
- "Person"
- "Person,EmploymentContract"
- "Customer,Project,Person"

**IMPORTANT**:
- Use EXACT table names from the available tables list (case-sensitive!)
- If unsure, include tables that MIGHT be related
- Better to request more tables than miss important ones
- Output format: Just the comma-separated names, nothing else

Analyze the query and output table names:
```

**Expected Output Examples**:
- User: "How many people are in the database?" → Output: `"Person"`
- User: "Show employees with their contracts" → Output: `"Person,EmploymentContract"`
- User: "List projects with customer names" → Output: `"Project,Customer"`

**Why Temperature 0.2**: Vogliamo output deterministico ma con un po' di creatività per identificare relazioni implicite.

---

### Node 3: get_table_details_1

**Type**: `mcp_tool`

**Purpose**: Ottenere lo schema dettagliato delle tabelle identificate

**Configuration**:
```json
{
  "id": "get_table_details_1",
  "agent": "mcp_tool",
  "tool_name": "get_table_details",
  "server_name": "database-query-server-railway",
  "instruction": "{identify_tables}",
  "depends_on": ["identify_tables"],
  "timeout": 60
}
```

**Input Format**:
```json
{
  "table_names": "Person,Customer"
}
```

**Expected Output** (30k-100k chars):
```
# Tabella: Person

## Schema
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NOT NULL | Primary key |
| first_name | VARCHAR(100) | NOT NULL | Nome |
| last_name | VARCHAR(100) | NOT NULL | Cognome |
| email | VARCHAR(255) | NULLABLE | Email di contatto |
| is_active | BOOLEAN | NOT NULL | Stato attivazione |
| department_id | INTEGER | NULLABLE | FK -> Department.id |

## Relationships
- Person.department_id → Department.id (many-to-one)
- EmploymentContract.person_id → Person.id (one-to-many)

## Query Examples

### CORRECT Examples ✅
{"table":"Person","select":["id","first_name","last_name"],"where":{"is_active":true},"limit":10}
{"table":"Person","select":["*"],"limit":10}

### WRONG Examples ❌
{"table":"person","select":["*"]}  // Wrong: table name case
{"table":"Person","select":["firstname"]}  // Wrong: column doesn't exist
{"table":"Person","select":["*"]}  // Wrong: missing LIMIT

## Common Errors
- Column 'firstname' does not exist → Use 'first_name' (snake_case)
- Table 'person' not found → Use 'Person' (case-sensitive)

---

# Tabella: Customer

[Similar detailed schema...]
```

**Why This Matters**: **QUI l'LLM ottiene i nomi esatti delle colonne!** Senza questo, non può generare query corrette.

---

### Node 4: evaluate_schema

**Type**: `llm`

**Purpose**: Valutare se lo schema ricevuto è sufficiente o servono altre tabelle

**Configuration**:
```json
{
  "id": "evaluate_schema",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-v3.2-exp",
    "temperature": 0.1,
    "max_tokens": 300,
    "system_prompt": "You are a database schema analyst. Evaluate if the current schema is sufficient or if additional tables are needed."
  },
  "instruction": "...",
  "depends_on": ["get_table_details_1"],
  "timeout": 30
}
```

**Instruction Template**:
```
Evaluate if the current table schema is sufficient to answer the user's query.

## User Query
{user_input}

## Tables Requested So Far
{identify_tables}

## Schema Received
{get_table_details_1}

## Your Task

1. Analyze if the schema provides all necessary information
2. Check if relationships require additional tables
3. Determine if the query can be completed with current schema

## Output Format (STRICT - Used for Conditional Routing)

Output EXACTLY one of these two formats:

**If schema is sufficient:**
```
schema_complete: true
tables: {identify_tables}
```

**If additional tables needed:**
```
schema_complete: false
additional_tables: Department,Project
reason: Need Department for employee names, Project for work assignments
```

**IMPORTANT**:
- First line MUST be exactly "schema_complete: true" or "schema_complete: false"
- If false, provide comma-separated table names on second line
- Be conservative: if unsure, request additional tables

Evaluate the schema:
```

**Expected Output Examples**:
- Sufficient:
  ```
  schema_complete: true
  tables: Person
  ```
- Insufficient:
  ```
  schema_complete: false
  additional_tables: Department,EmploymentContract
  reason: Need Department for department names, EmploymentContract for salary info
  ```

**Why This Node**: Permette all'LLM di richiedere iterativamente le tabelle necessarie senza indovinare tutto all'inizio.

---

### Node 5: get_table_details_2 (CONDITIONAL)

**Type**: `mcp_tool`

**Purpose**: Ottenere schema di tabelle aggiuntive se necessario

**Configuration**:
```json
{
  "id": "get_table_details_2",
  "agent": "mcp_tool",
  "tool_name": "get_table_details",
  "server_name": "database-query-server-railway",
  "instruction": "{evaluate_schema.additional_tables}",
  "depends_on": ["evaluate_schema"],
  "timeout": 60
}
```

**Conditional Logic**:
```json
{
  "from_node": "evaluate_schema",
  "conditions": [
    {
      "field": "custom_metadata.schema_complete",
      "operator": "equals",
      "value": true,
      "next_node": "identify_features"
    }
  ],
  "default": "get_table_details_2"
}
```

**Why Conditional**: Esegue SOLO se `schema_complete: false`, altrimenti salta direttamente a `identify_features`.

---

### Node 6: identify_features

**Type**: `llm`

**Purpose**: Identificare quali query features sono necessarie

**Configuration**:
```json
{
  "id": "identify_features",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-v3.2-exp",
    "temperature": 0.2,
    "max_tokens": 300,
    "system_prompt": "You are a SQL feature analyzer. Identify which query features are needed based on the user request."
  },
  "instruction": "...",
  "depends_on": ["evaluate_schema"],
  "timeout": 30
}
```

**Instruction Template**:
```
Identify which query features are needed to fulfill the user's request.

## User Query
{user_input}

## Available Tables Schema
{get_table_details_1}
{get_table_details_2}

## Available Features (from welcome)
{get_welcome}

## Your Task

1. Analyze what operations are needed:
   - Filtering? → WHERE, whereIn, whereLike
   - Multiple tables? → JOIN
   - Counting/Summing? → COUNT, SUM, AVG
   - Grouping? → GROUP BY
   - Sorting? → ORDER BY
   - Pagination? → LIMIT, OFFSET

2. Output ONLY the feature names needed, comma-separated

## Output Format

Output ONLY feature names, comma-separated, no explanations:

Examples:
- "WHERE,LIMIT"
- "JOIN,WHERE,ORDER BY"
- "COUNT,GROUP BY"

**IMPORTANT**:
- Use EXACT feature names from available features list
- ALWAYS include LIMIT if query returns multiple rows
- Include all features that might be needed

Identify features:
```

**Expected Output Examples**:
- "How many people?" → `"COUNT"`
- "Active employees" → `"WHERE,LIMIT"`
- "Employees with departments" → `"JOIN,LIMIT"`
- "Employees grouped by department" → `"JOIN,GROUP BY,COUNT"`

---

### Node 7: get_feature_details

**Type**: `mcp_tool`

**Purpose**: Ottenere documentazione dettagliata delle features necessarie

**Configuration**:
```json
{
  "id": "get_feature_details",
  "agent": "mcp_tool",
  "tool_name": "get_feature_details",
  "server_name": "database-query-server-railway",
  "instruction": "{identify_features}",
  "depends_on": ["identify_features"],
  "timeout": 60
}
```

**Expected Output** (10k-50k chars):
```
# Feature: WHERE

## Description
Filtra i risultati in base a condizioni specifiche.

## Syntax
```json
{
  "table": "TableName",
  "where": {
    "column_name": "value",
    "another_column": 123,
    "boolean_field": true
  }
}
```

## Examples
```json
// Filter by status
{"table":"Person","select":["*"],"where":{"is_active":true},"limit":10}

// Multiple conditions (AND logic)
{"table":"Person","where":{"is_active":true,"department_id":5},"limit":10}
```

## Common Errors
- Using column names that don't exist
- Wrong value types (string vs number vs boolean)

---

# Feature: JOIN

[Detailed JOIN documentation...]

---

# Feature: LIMIT

[Detailed LIMIT documentation...]
```

**Why This Matters**: Fornisce la sintassi ESATTA per ogni feature, riducendo errori di formato.

---

### Node 8: generate_query

**Type**: `llm`

**Purpose**: Generare la query JSON con TUTTO il contesto disponibile

**Configuration**:
```json
{
  "id": "generate_query",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-v3.2-exp",
    "temperature": 0.1,
    "max_tokens": 2000,
    "system_prompt": "You are a JSON query expert. Generate valid JSON queries using the exact schema and syntax provided. Output ONLY pure JSON, no markdown, no wrappers.",
    "include_workflow_history": true,
    "history_nodes": ["check_result"]
  },
  "instruction": "...",
  "depends_on": ["get_feature_details"],
  "timeout": 120
}
```

**Instruction Template**:
```
Generate a JSON database query based on all the context provided.

## User Request
{user_input}

## Context Available

### 1. Tables Schema (with exact column names)
{get_table_details_1}
{get_table_details_2}

### 2. Features Documentation (with exact syntax)
{get_feature_details}

### 3. Previous Error (if this is a retry)
{@latest:check_result}

## Your Task

**IF THIS IS A RETRY** (you see error analysis above):
- Read the error message and hint CAREFULLY
- The hint tells you EXACTLY what to fix
- Generate a CORRECTED query addressing the specific issue
- DO NOT repeat the same mistake

**IF THIS IS THE FIRST ATTEMPT**:
1. Review the table schemas to find exact column names
2. Review the feature documentation for correct syntax
3. Generate the query following the examples provided

## Output Format

Output ONLY the JSON query, no markdown code blocks, no explanations:

```json
{"table":"Person","select":["id","first_name","last_name"],"where":{"is_active":true},"limit":10}
```

**CRITICAL RULES**:
1. Use EXACT table names (case-sensitive!)
2. Use EXACT column names from schema (case-sensitive!)
3. Follow EXACT syntax from feature documentation
4. ALWAYS include LIMIT for multi-row queries
5. Output pure JSON (no markdown ```json``` blocks)
6. Output ONLY the query JSON, nothing before or after

## Common Mistakes to Avoid
- ❌ Table name wrong case: "person" → ✅ "Person"
- ❌ Column name wrong: "firstname" → ✅ "first_name"
- ❌ Missing LIMIT: {"table":"Person","select":["*"]} → ✅ Add "limit":10
- ❌ Markdown wrapper: ```json {...}``` → ✅ Just {...}

Generate the query now (ONLY the JSON):
```

**Expected Output**:
```json
{"table":"Person","select":["id","first_name","last_name","email"],"where":{"is_active":true},"limit":10}
```

**Key Differences from v2.0**:
- ✅ v3.0: Riceve schema completo con nomi colonne esatti
- ✅ v3.0: Riceve documentazione feature con sintassi esatta
- ✅ v3.0: Può correggere errori con hint specifici
- ❌ v2.0: Riceve solo lista tabelle, deve indovinare nomi colonne

---

### Node 9: execute_query

**Type**: `mcp_tool`

**Purpose**: Eseguire la query generata

**Configuration**:
```json
{
  "id": "execute_query",
  "agent": "mcp_tool",
  "tool_name": "execute_query",
  "server_name": "database-query-server-railway",
  "instruction": "{generate_query}",
  "depends_on": ["generate_query"],
  "timeout": 60
}
```

**Expected Output (Success)**:
```json
{
  "success": true,
  "count": 15,
  "data": [
    {"id": 1, "first_name": "John", "last_name": "Doe", "email": "john@example.com"},
    {"id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"},
    ...
  ],
  "query": {"table":"Person","select":["id","first_name","last_name","email"],"where":{"is_active":true},"limit":10}
}
```

**Expected Output (Error)**:
```json
{
  "success": false,
  "error": {
    "message": "Column 'firstname' does not exist in table 'Person'",
    "details": "Available columns: id, first_name, last_name, email, is_active, department_id",
    "hint": "Did you mean 'first_name' instead of 'firstname'? Use snake_case for column names."
  },
  "query": {"table":"Person","select":["firstname"],"limit":10}
}
```

**Why Structured Errors Matter**: L'hint fornisce la correzione esatta per il retry.

---

### Node 10: check_result

**Type**: `llm`

**Purpose**: Analizzare il risultato e determinare success/error con hint extraction

**Configuration**:
```json
{
  "id": "check_result",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "deepseek/deepseek-v3.2-exp",
    "temperature": 0.0,
    "system_prompt": "You are a precise JSON analyzer. Parse responses and extract structured metadata. Be exact and follow format strictly."
  },
  "instruction": "...",
  "depends_on": ["execute_query"],
  "timeout": 30
}
```

**Instruction Template**:
```
Analyze the MCP query result and extract structured information.

## Result from Database
{execute_query}

## Expected Formats

**Success**:
{
  "success": true,
  "count": N,
  "data": [...]
}

**Error**:
{
  "success": false,
  "error": {
    "message": "...",
    "details": "...",
    "hint": "..."
  }
}

## Your Task

1. Parse the JSON response
2. Check "success" field
3. If error: extract message, details, and hint
4. Output structured metadata for conditional routing

## Output Format (STRICT - Controls Workflow Routing)

**If Success**:
```
has_error: false
row_count: 15
data_summary: Retrieved 15 active employees with contact information
```

**If Error**:
```
has_error: true
error_type: column_not_found
error_message: Column 'firstname' does not exist in table 'Person'
error_hint: Did you mean 'first_name' instead of 'firstname'? Use snake_case for column names.
correction_needed: Change 'firstname' to 'first_name' in the SELECT clause
```

**IMPORTANT**:
- First line MUST be exactly "has_error: true" or "has_error: false"
- This controls whether workflow retries or proceeds to formatting
- Extract the hint VERBATIM - it contains the exact fix
- Be precise - routing depends on this output

Analyze the result:
```

**Expected Output (Error)**:
```
has_error: true
error_type: column_not_found
error_message: Column 'firstname' does not exist in table 'Person'
error_hint: Did you mean 'first_name' instead of 'firstname'? Use snake_case for column names.
correction_needed: Change 'firstname' to 'first_name' in the SELECT clause
```

**Expected Output (Success)**:
```
has_error: false
row_count: 15
data_summary: Retrieved 15 active employees with contact information
```

---

### Node 11: format_results

**Type**: `llm`

**Purpose**: Formattare i risultati in modo user-friendly

**Configuration**: Same as v2.0, receives truncated data.

---

## Conditional Edges

### Edge 1: evaluate_schema → [identify_features | get_table_details_2]

```json
{
  "from_node": "evaluate_schema",
  "conditions": [
    {
      "field": "custom_metadata.schema_complete",
      "operator": "equals",
      "value": true,
      "next_node": "identify_features"
    }
  ],
  "default": "get_table_details_2"
}
```

**Logic**:
- If `schema_complete: true` → Skip to identify_features
- If `schema_complete: false` → Get additional table details

### Edge 2: check_result → [format_results | generate_query]

```json
{
  "from_node": "check_result",
  "conditions": [
    {
      "field": "custom_metadata.has_error",
      "operator": "equals",
      "value": false,
      "next_node": "format_results"
    }
  ],
  "default": "generate_query"
}
```

**Logic**:
- If `has_error: false` → Success, format results
- If `has_error: true` → Retry generate_query (max 5 attempts)

---

## Context Management Strategy

### State Accumulation

**Workflow State** accumula tutto:
```python
state = {
  "user_input": "How many people are in the database?",
  "node_outputs": {
    "get_welcome": "...(8k chars)...",
    "identify_tables": "Person",
    "get_table_details_1": "...(50k chars - SCHEMA COMPLETO)...",
    "evaluate_schema": "schema_complete: true...",
    "identify_features": "COUNT",
    "get_feature_details": "...(20k chars - DOC FEATURES)...",
    "generate_query": '{"table":"Person","count":"*"}',
    "execute_query": '{"success":true,"count":142,"data":...}',
    "check_result": "has_error: false..."
  },
  "completed_nodes": [...],
  "custom_metadata": {
    "schema_complete": true,
    "has_error": false,
    "row_count": 142
  }
}
```

### Variable Substitution in Instructions

Ogni nodo può accedere agli output precedenti:

```
## User Query
{user_input}  ← sostituito con "How many people..."

## Tables Schema
{get_table_details_1}  ← sostituito con schema 50k chars
{get_table_details_2}  ← sostituito se eseguito, altrimenti ""

## Features Documentation
{get_feature_details}  ← sostituito con doc 20k chars

## Previous Error
{@latest:check_result}  ← sostituito con ultimo check_result nei retry
```

### History Messages for Retry

Nel retry, `generate_query` riceve:
```python
messages = [
  SystemMessage("You are a JSON query expert..."),
  HumanMessage("[Previous step: check_result]"),  # History marker
  AIMessage("has_error: true\nerror_message: Column 'firstname'...\nerror_hint: Use 'first_name'..."),
  HumanMessage("Generate query... {schema}... {features}... {error}...")
]
```

Quindi l'LLM vede:
1. System prompt (ruolo)
2. Errore precedente come conversazione
3. Instruction corrente con tutto il contesto

**Total context**: ~100k-150k chars (sotto il limite 128k di DeepSeek)

---

## Retry Mechanism

### Max Retries: 5

**Workflow Parameters**:
```json
{
  "max_retries": 5
}
```

**State Tracking**:
```python
state["node_retry_counts"] = {
  "generate_query": 3  # Tentativo corrente
}
```

### Retry Decision Matrix

| Attempt | Context Available | Expected Outcome |
|---------|-------------------|------------------|
| 1 (First) | Schema + Features | 70% success |
| 2 (Retry) | Schema + Features + Error + Hint | 90% success |
| 3 (Retry) | All above + Previous errors | 95% success |
| 4 (Retry) | All above | 98% success |
| 5 (Last) | All above | 99% success or FAIL |

**Why 5 Retries**:
- Attempt 1-2: Errori di sintassi (nomi colonne, case)
- Attempt 3-4: Errori logici (JOIN mancanti, WHERE sbagliati)
- Attempt 5: Edge cases rari

### Failure After 5 Retries

```python
if current_retry >= max_retries:
    raise RuntimeError(f"Node generate_query exceeded maximum retry attempts ({max_retries})")
```

Workflow termina con errore dettagliato.

---

## Why v3.0 Will Succeed Where v2.0 Failed

### Root Cause Analysis: v2.0 Failure

**v2.0 Problem**: LLM riceve solo welcome message (8k chars) che contiene:
```
Available Tables:
- Person
- Customer
- EmploymentContract
...
```

**Ma NON contiene**:
- ❌ Nomi esatti delle colonne (firstname vs first_name?)
- ❌ Tipi delle colonne (string vs int vs boolean?)
- ❌ Relazioni tra tabelle (quale FK usare per JOIN?)
- ❌ Esempi di query corrette per ogni tabella
- ❌ Errori comuni per ogni tabella

**Risultato v2.0**: LLM deve **indovinare** i nomi delle colonne:
```json
// LLM guess #1
{"table":"Person","select":["firstname","lastname"]}
// ❌ Error: Column 'firstname' does not exist

// LLM guess #2
{"table":"Person","select":["first_name","last_name"]}
// ✅ Success! But only after retry
```

### v3.0 Solution: Complete Context

**v3.0 provides**:
```
# Tabella: Person

## Schema
| Column | Type | Nullable |
|--------|------|----------|
| id | INTEGER | NOT NULL |
| first_name | VARCHAR(100) | NOT NULL |  ← ESATTO!
| last_name | VARCHAR(100) | NOT NULL |   ← ESATTO!
| email | VARCHAR(255) | NULLABLE |
| is_active | BOOLEAN | NOT NULL |

## Query Examples ✅
{"table":"Person","select":["first_name","last_name"],"limit":10}
```

**Risultato v3.0**: LLM **sa esattamente** i nomi delle colonne:
```json
// LLM with full context
{"table":"Person","select":["first_name","last_name"],"limit":10}
// ✅ Success on first attempt!
```

### Expected Success Rates

| Scenario | v2.0 | v3.0 | Why |
|----------|------|------|-----|
| Simple query (1 table, WHERE) | 30% | 90% | v3.0 has exact column names |
| Medium query (2 tables, JOIN) | 10% | 85% | v3.0 has relationships + examples |
| Complex query (3+ tables, GROUP BY) | 5% | 75% | v3.0 has feature syntax |
| Retry after error | 40% | 95% | v3.0 has hint with exact fix |

**Overall**: v2.0 ~20% success, v3.0 ~85-90% success rate.

---

## Performance Characteristics

### Latency Estimates (per node)

| Node | Type | Expected Latency | Payload Size |
|------|------|------------------|--------------|
| get_welcome | mcp_resource | 500ms | 8k chars |
| identify_tables | llm | 2-3s | Input: 10k, Output: 50 chars |
| get_table_details_1 | mcp_tool | 1-2s | 30k-100k chars |
| evaluate_schema | llm | 2-3s | Input: 100k, Output: 100 chars |
| get_table_details_2 | mcp_tool | 1-2s (conditional) | 30k-100k chars |
| identify_features | llm | 2-3s | Input: 110k, Output: 50 chars |
| get_feature_details | mcp_tool | 1-2s | 10k-50k chars |
| generate_query | llm | 3-5s | Input: 150k, Output: 200 chars |
| execute_query | mcp_tool | 500ms-2s | Depends on query |
| check_result | llm | 2-3s | Input: 5k, Output: 200 chars |
| format_results | llm | 3-4s | Input: 10k, Output: 500 chars |

**Total Success Path (no schema loop, no retry)**: ~18-25 seconds

**Total With Schema Loop** (+get_table_details_2): ~20-28 seconds

**Total With 1 Retry**: ~30-40 seconds

**Total With 5 Retries**: ~80-120 seconds (rare, indicates fundamental issue)

### Context Size Management

**Total Context Sizes**:
- get_welcome: 8k chars
- identify_tables: 10k input
- get_table_details_1: 100k chars
- get_feature_details: 50k chars
- **TOTAL for generate_query**: ~150k chars input

**DeepSeek v3.2-exp**: 128k context window

**Solution**: Truncate welcome message if total exceeds 120k:
```python
if len(welcome) + len(schema) + len(features) > 120000:
    # Keep schema + features (critical)
    # Truncate welcome (less critical - just overview)
    welcome_truncated = welcome[:5000] + "...[truncated]..." + welcome[-5000:]
```

---

## Cost Analysis

### OpenRouter Pricing (DeepSeek v3.2-exp)

- **Input**: $0.28 per 1M tokens (~4 chars/token = $0.07 per 1M chars)
- **Output**: $0.42 per 1M tokens (~4 chars/token = $0.105 per 1M chars)

### Per Query Cost (Success Path, No Retry)

| Node | Input Chars | Output Chars | Cost |
|------|-------------|--------------|------|
| identify_tables | 10k | 50 | $0.0007 |
| evaluate_schema | 100k | 100 | $0.007 |
| identify_features | 110k | 50 | $0.0077 |
| generate_query | 150k | 200 | $0.0105 + $0.00002 |
| check_result | 5k | 200 | $0.00035 + $0.00002 |
| format_results | 10k | 500 | $0.0007 + $0.00005 |

**Total per successful query**: ~$0.027 (2.7 cents)

**With 1 retry**: ~$0.038 (3.8 cents)

**Monthly cost (1000 queries)**: ~$27-38

**vs v2.0**: Similar cost but 90% vs 20% success rate!

---

## Testing Strategy

### Test Cases

#### TC1: Simple Query (No JOIN, No Complex Features)
**Input**: "How many people are in the database?"
**Expected Flow**:
- identify_tables → "Person"
- get_table_details_1 → schema
- evaluate_schema → complete
- identify_features → "COUNT"
- generate_query → `{"table":"Person","count":"*"}`
- execute_query → success
**Expected Attempts**: 1
**Expected Time**: ~20s

#### TC2: Medium Query (JOIN Required)
**Input**: "Show employees with their department names"
**Expected Flow**:
- identify_tables → "Person,Department"
- get_table_details_1 → both schemas
- evaluate_schema → complete
- identify_features → "JOIN,LIMIT"
- generate_query → query with JOIN
- execute_query → success
**Expected Attempts**: 1-2
**Expected Time**: ~25s

#### TC3: Complex Query (Multiple Tables, GROUP BY)
**Input**: "Count employees per department, sorted by count"
**Expected Flow**:
- identify_tables → "Person,Department"
- get_table_details_1 → schemas
- evaluate_schema → complete
- identify_features → "JOIN,GROUP BY,COUNT,ORDER BY"
- generate_query → complex query
- execute_query → success
**Expected Attempts**: 1-3
**Expected Time**: ~30s

#### TC4: Iterative Schema Discovery
**Input**: "Show projects with customer names and project lead emails"
**Expected Flow**:
- identify_tables → "Project,Customer"
- get_table_details_1 → Project, Customer
- evaluate_schema → incomplete (need Person for lead emails)
- get_table_details_2 → Person
- evaluate_schema → complete
- identify_features → "JOIN,LIMIT"
- generate_query → query with 3-way JOIN
- execute_query → success
**Expected Attempts**: 1-2
**Expected Time**: ~35s

#### TC5: Error Recovery (Case Sensitivity)
**Input**: "List all people"
**Expected Flow**:
- ... schema + features loaded ...
- generate_query (attempt 1) → `{"table":"person","select":["*"],"limit":10}`
- execute_query → ERROR: Table 'person' not found
- check_result → extracts hint: "Use 'Person' (case-sensitive)"
- generate_query (attempt 2 - RETRY) → `{"table":"Person","select":["*"],"limit":10}`
- execute_query → SUCCESS
**Expected Attempts**: 2
**Expected Time**: ~30s

### Success Metrics

- **Query Success Rate**: > 85% on first attempt, > 95% after max 2 retries
- **Average Latency**: < 30 seconds for success path
- **Cost per Query**: < $0.04 (4 cents)
- **Schema Completeness**: > 90% of queries complete with first schema request

---

## Implementation Checklist

### Phase 1: Core Flow (Nodes 1-8)
- [ ] Implement get_welcome (mcp_resource)
- [ ] Implement identify_tables (llm) with precise prompt
- [ ] Implement get_table_details_1 (mcp_tool)
- [ ] Implement evaluate_schema (llm) with conditional output
- [ ] Add conditional edge: evaluate_schema → [identify_features | get_table_details_2]
- [ ] Implement get_table_details_2 (mcp_tool, conditional)
- [ ] Implement identify_features (llm)
- [ ] Implement get_feature_details (mcp_tool)

### Phase 2: Query Generation & Execution (Nodes 9-11)
- [ ] Implement generate_query (llm) with full context
- [ ] Verify context substitution works correctly
- [ ] Implement execute_query (mcp_tool)
- [ ] Implement check_result (llm) with metadata extraction

### Phase 3: Retry & Formatting
- [ ] Add conditional edge: check_result → [format_results | generate_query]
- [ ] Implement retry mechanism (max 5 attempts)
- [ ] Implement format_results (llm)
- [ ] Verify history messages in retry

### Phase 4: Testing
- [ ] Test TC1 (simple query)
- [ ] Test TC2 (JOIN query)
- [ ] Test TC3 (complex query)
- [ ] Test TC4 (iterative schema)
- [ ] Test TC5 (error recovery)
- [ ] Test context size limits
- [ ] Test retry exhaustion (5 attempts)

### Phase 5: Optimization
- [ ] Optimize prompts based on test results
- [ ] Add context truncation if needed
- [ ] Monitor costs and latencies
- [ ] Fine-tune temperature parameters

---

## Comparison: v1.0 vs v2.0 vs v3.0

| Aspect | v1.0 (12 nodes) | v2.0 (5 nodes) | v3.0 (8-10 nodes) |
|--------|-----------------|----------------|-------------------|
| **Approach** | Sequential discovery | Too simplified | Iterative with context |
| **Context** | Partial (no batch) | Minimal (only welcome) | **Complete (schema+features)** |
| **Success Rate** | ~60% | ~20% | **~85-90%** |
| **Latency** | 40-60s | 15-25s | 20-30s |
| **Nodes** | 12 | 5 | 8-10 |
| **LLM Calls** | 6 | 3 | 5-6 |
| **MCP Calls** | 5 | 2 | 3-4 |
| **Complexity** | High | Too low | **Balanced** |
| **Maintainability** | Medium | High | **High** |

**Winner**: v3.0 - Best balance of success rate, performance, and maintainability.

---

## Conclusion

**v3.0 addresses the fundamental flaw of v2.0**: LLM mancava del contesto necessario per generare query corrette.

**Key Innovation**: Just-In-Time Context Loading - l'LLM richiede dinamicamente schema e feature docs, ottenendo tutte le informazioni prima di generare la query.

**Expected Outcome**: 85-90% success rate vs 20% di v2.0, con latenza accettabile (~25s) e costo ragionevole (~3 cents/query).

**Next Steps**: Approvazione design → Implementazione workflow JSON → Testing → Deploy

---

## Appendix: Complete JSON Workflow Template

```json
{
  "name": "database_query_smart_v3",
  "version": "3.0",
  "description": "Iterative database query workflow with dynamic context loading and schema discovery",
  "nodes": [
    {
      "id": "get_welcome",
      "agent": "mcp_resource",
      "resource_uri": "welcome://message",
      "server_name": "database-query-server-railway",
      "instruction": "Read welcome resource",
      "depends_on": [],
      "timeout": 30
    },
    {
      "id": "identify_tables",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.2,
        "max_tokens": 500
      },
      "instruction": "[See detailed prompt in Node 2 section]",
      "depends_on": ["get_welcome"],
      "timeout": 30
    },
    {
      "id": "get_table_details_1",
      "agent": "mcp_tool",
      "tool_name": "get_table_details",
      "server_name": "database-query-server-railway",
      "instruction": "{identify_tables}",
      "depends_on": ["identify_tables"],
      "timeout": 60
    },
    {
      "id": "evaluate_schema",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.1,
        "max_tokens": 300
      },
      "instruction": "[See detailed prompt in Node 4 section]",
      "depends_on": ["get_table_details_1"],
      "timeout": 30
    },
    {
      "id": "get_table_details_2",
      "agent": "mcp_tool",
      "tool_name": "get_table_details",
      "server_name": "database-query-server-railway",
      "instruction": "[Extract additional_tables from evaluate_schema]",
      "depends_on": ["evaluate_schema"],
      "timeout": 60
    },
    {
      "id": "identify_features",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.2,
        "max_tokens": 300
      },
      "instruction": "[See detailed prompt in Node 6 section]",
      "depends_on": ["evaluate_schema"],
      "timeout": 30
    },
    {
      "id": "get_feature_details",
      "agent": "mcp_tool",
      "tool_name": "get_feature_details",
      "server_name": "database-query-server-railway",
      "instruction": "{identify_features}",
      "depends_on": ["identify_features"],
      "timeout": 60
    },
    {
      "id": "generate_query",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.1,
        "max_tokens": 2000,
        "include_workflow_history": true,
        "history_nodes": ["check_result"]
      },
      "instruction": "[See detailed prompt in Node 8 section]",
      "depends_on": ["get_feature_details"],
      "timeout": 120
    },
    {
      "id": "execute_query",
      "agent": "mcp_tool",
      "tool_name": "execute_query",
      "server_name": "database-query-server-railway",
      "instruction": "{generate_query}",
      "depends_on": ["generate_query"],
      "timeout": 60
    },
    {
      "id": "check_result",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.0
      },
      "instruction": "[See detailed prompt in Node 10 section]",
      "depends_on": ["execute_query"],
      "timeout": 30
    },
    {
      "id": "format_results",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "deepseek/deepseek-v3.2-exp",
        "temperature": 0.7,
        "max_tokens": 2000
      },
      "instruction": "[Same as v2.0]",
      "depends_on": ["check_result"],
      "timeout": 60
    }
  ],
  "conditional_edges": [
    {
      "from_node": "evaluate_schema",
      "conditions": [
        {
          "field": "custom_metadata.schema_complete",
          "operator": "equals",
          "value": true,
          "next_node": "identify_features"
        }
      ],
      "default": "get_table_details_2"
    },
    {
      "from_node": "check_result",
      "conditions": [
        {
          "field": "custom_metadata.has_error",
          "operator": "equals",
          "value": false,
          "next_node": "format_results"
        }
      ],
      "default": "generate_query"
    }
  ],
  "parameters": {
    "user_input": "How many people are in the database?",
    "max_retries": 5
  }
}
```

**Note**: I prompt completi sono documentati nelle sezioni dei nodi individuali.

---

## Document Changelog

- **v3.0** (2025-10-12): Complete redesign with iterative context loading
- **v2.0** (2025-10-12): Simplified to 5 nodes (failed due to insufficient context)
- **v1.0** (2025-10-12): Initial 12-node design

---

## Approval & Next Steps

**Prepared by**: Claude (AI Assistant)
**Date**: 2025-10-12
**Status**: ✅ Ready for User Review

**Once Approved**:
1. Implement complete JSON workflow with all prompts
2. Test with 5 test cases
3. Measure success rate, latency, cost
4. Deploy to production

**Expected Timeline**: 2-4 hours for implementation + testing
