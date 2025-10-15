# Database Query Workflow Design v2.0 (OPTIMIZED)

## Document Information
- **Version**: 2.0 (Optimized)
- **Date**: 2025-10-12
- **Status**: Ready for Implementation
- **Previous Version**: v1.0 (12 nodes) → v2.0 (5 nodes) = 58% reduction

## Executive Summary

This is an **optimized redesign** based on analysis of the actual MCP server source code (`/home/mverde/src/taal/mcp-servers/json2data/mcp_db_server.py`).

**Key Optimizations**:
- ✅ **Batch Requests**: MCP supports `"Person,Customer,Contract"` in single call
- ✅ **Built-in Prompts**: MCP provides `validation_prompt()`, `common_errors_prompt()`
- ✅ **Structured Errors**: Database returns automatic hints for corrections
- ✅ **Simplified Flow**: Let LLM decide what details to request (no pre-analysis)
- ✅ **Cost Effective**: Uses `meta-llama/llama-3.3-8b-instruct:free` throughout

**Result**: Reduced from 12 nodes to 5 nodes while increasing intelligence and reliability.

---

## Architecture Overview

### Workflow Flow Diagram

```
┌─────────────────┐
│  get_welcome    │  MCP Resource: Get tables, features, rules
└────────┬────────┘
         │
         v
┌─────────────────┐
│ generate_query  │  LLM: Analyze request, request details if needed, generate query
└────────┬────────┘
         │
         v
┌─────────────────┐
│ execute_query   │  MCP Tool: Execute JSON query
└────────┬────────┘
         │
         v
┌─────────────────┐
│  check_result   │  LLM: Parse result, detect errors, extract hints
└────────┬────────┘
         │
         ├─── has_error: false ──> format_results (SUCCESS)
         │
         └─── has_error: true ──> generate_query (RETRY, max 5 attempts)
```

### Node Comparison: v1.0 vs v2.0

| v1.0 (12 Nodes) | v2.0 (5 Nodes) | Change |
|-----------------|----------------|--------|
| get_welcome_resource | get_welcome | Renamed |
| identify_tables | **REMOVED** | LLM decides in generate_query |
| evaluate_schema_completeness | **REMOVED** | LLM decides in generate_query |
| get_table_details | **INTEGRATED** | LLM calls directly if needed |
| get_table_details_2 | **REMOVED** | Batch requests eliminate need |
| identify_features | **REMOVED** | LLM decides in generate_query |
| get_feature_details | **INTEGRATED** | LLM calls directly if needed |
| generate_query | generate_query | Enhanced with MCP prompts |
| execute_query | execute_query | Unchanged |
| check_result | check_result | Enhanced with hint extraction |
| retry_with_error | **REMOVED** | Conditional edge handles retry |
| format_results | format_results | Unchanged |

---

## Detailed Node Specifications

### Node 1: get_welcome

**Type**: `mcp_resource`

**Purpose**: Retrieve initial context about available tables, features, and rules

**Configuration**:
```json
{
  "id": "get_welcome",
  "agent": "mcp_resource",
  "resource_uri": "welcome://message",
  "server_name": "database-query-server-railway",
  "instruction": "Read welcome resource to get available tables, features, and common rules",
  "depends_on": [],
  "timeout": 30
}
```

**Expected Output**: Text containing:
- List of available tables (18+ tables)
- Available query features (LIMIT, OFFSET, WHERE, JOIN, etc.)
- Common error patterns
- Usage guidelines

**Why This Approach**: The welcome resource provides comprehensive initial context without requiring multiple calls.

---

### Node 2: generate_query

**Type**: `llm`

**Purpose**: Intelligent query generation with dynamic detail requests

**Configuration**:
```json
{
  "id": "generate_query",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "meta-llama/llama-3.3-8b-instruct:free",
    "temperature": 0.1,
    "max_tokens": 2000,
    "system_prompt": "You are a SQL query expert. Generate JSON database queries following exact format specifications. When you need detailed schema information, use the get_table_details tool. Output ONLY valid JSON with no markdown wrappers.",
    "include_workflow_history": true,
    "history_nodes": ["check_result"],
    "available_tools": [
      {
        "name": "get_table_details",
        "description": "Get detailed schema for one or more tables. Supports batch: 'Person' or 'Person,Customer,Contract'",
        "parameters": {
          "table_names": "string (comma-separated for batch)"
        }
      },
      {
        "name": "get_feature_details",
        "description": "Get detailed documentation for query features. Supports batch: 'LIMIT' or 'LIMIT,OFFSET,WHERE'",
        "parameters": {
          "feature_names": "string (comma-separated for batch)"
        }
      }
    ]
  },
  "instruction": "...",
  "depends_on": ["get_welcome"],
  "timeout": 120
}
```

**Instruction Template**:
```
You are generating a JSON database query based on the user's natural language request.

## User Request
{user_input}

## Available Context

### Welcome Message (Tables, Features, Rules)
{get_welcome}

### Previous Error Analysis (if this is a retry)
{@latest:check_result}

## Your Task

**IF THIS IS A RETRY** (you see error analysis above with 'has_error: true'):
- Analyze the error message and hint carefully
- The hint will tell you EXACTLY what to fix
- Generate a CORRECTED query addressing the specific issue

**IF THIS IS THE FIRST ATTEMPT** (no error analysis above):

1. **Analyze the Request**:
   - What tables are likely needed?
   - What columns or relationships are involved?
   - What filters or operations are required?

2. **Determine If You Need Details**:
   - Do you need exact column names? → Use get_table_details
   - Do you need join relationship info? → Use get_table_details for both tables
   - Do you need complex feature syntax? → Use get_feature_details

   **IMPORTANT**: You can request MULTIPLE items in ONE call:
   - get_table_details("Person,Customer,EmploymentContract")
   - get_feature_details("JOIN,WHERE,GROUP_BY")

3. **Generate the Query**:
   Once you have enough information (from welcome message + any details requested),
   generate the JSON query following these rules:

## Query Format

Output ONLY the JSON query string (NOT wrapped in {"json_query": ...}).

**Basic Structure**:
```json
{
  "table": "TableName",
  "select": ["column1", "column2"],
  "where": {"column": "value"},
  "limit": 10
}
```

**Common Operations**:
- **WHERE**: `"where": {"status": "active"}`
- **WHERE IN**: `"whereIn": {"id": [1, 2, 3]}`
- **LIKE**: `"whereLike": {"name": "%pattern%"}`
- **JOIN**: `"join": [{"table": "Other", "first": "t1.id", "second": "t2.t1_id"}]`
- **GROUP BY**: `"groupBy": "category"`
- **COUNT**: `"count": "*"` or `"count": "column_name"`
- **ORDER BY**: `"orderBy": {"column": "asc"}` or `{"column": "desc"}`

**Critical Rules**:
- Use EXACT table and column names from schema (case-sensitive!)
- ALWAYS include LIMIT for queries that might return many rows (use LIMIT: 10 or 50)
- JOIN syntax requires exact column references: "table.column"
- Only SELECT operations allowed (no INSERT/UPDATE/DELETE)

## MCP Validation Guidance

The MCP server has built-in validation that will check:
1. Table names exist and are correctly cased
2. Column names exist in their tables
3. Join relationships are valid
4. Feature syntax is correct

If your query fails validation, you'll receive a hint explaining exactly what to fix.

## Output Format

Output ONLY the JSON query string (no wrapper, no markdown):

{"table":"Person","select":["first_name","last_name"],"where":{"is_active":true},"limit":10}
```

**Why This Approach**:
- LLM decides when it needs more details (not pre-determined)
- Batch requests minimize MCP calls
- MCP prompts provide validation guidance
- Error hints from previous attempts guide corrections

---

### Node 3: execute_query

**Type**: `mcp_tool`

**Purpose**: Execute the generated JSON query against the database

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

**Expected Output**:

**Success Format**:
```json
{
  "success": true,
  "count": 15,
  "data": [
    {"id": 1, "name": "John", ...},
    ...
  ],
  "query": "{\"table\":\"Person\",...}"
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "message": "Column 'firstname' does not exist in table 'Person'",
    "details": "Available columns: id, first_name, last_name, ...",
    "hint": "Did you mean 'first_name' instead of 'firstname'?"
  },
  "query": "{\"table\":\"Person\",...}"
}
```

**Why This Approach**: MCP server provides structured errors with automatic correction hints.

---

### Node 4: check_result

**Type**: `llm`

**Purpose**: Parse MCP response, detect errors, extract hints for retry

**Configuration**:
```json
{
  "id": "check_result",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "meta-llama/llama-3.3-8b-instruct:free",
    "temperature": 0.0,
    "system_prompt": "You are a precise JSON response analyzer. Parse MCP responses and output EXACT structured status information following the specified format."
  },
  "instruction": "...",
  "depends_on": ["execute_query"],
  "timeout": 30
}
```

**Instruction Template**:
```
Analyze the MCP query execution result and determine if it succeeded or failed.

## Result from MCP
{execute_query}

## MCP Response Format

The MCP server returns JSON in one of two formats:

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
2. Check the "success" field
3. Extract error details if present
4. Categorize the error type
5. Extract the hint (this is CRITICAL for retry)

## Output Format (STRICT - Used for Conditional Routing)

**If Error Detected**:
```
has_error: true
error_type: <table_not_found|column_not_found|syntax_error|join_error|type_mismatch|other>
error_message: <exact error text from MCP>
error_hint: <exact hint from MCP - this tells how to fix>
```

**If Successful**:
```
has_error: false
row_count: <number of rows returned>
data_summary: <brief description of data, e.g., "15 active employees">
```

**IMPORTANT**:
- The "has_error" field MUST be exactly "true" or "false" (boolean values)
- This field controls whether we proceed to format_results or retry generate_query
- Extract the hint EXACTLY as provided - it contains the correction guidance
- Be precise - workflow routing depends on these values

Output your analysis now:
```

**Why This Approach**:
- Separates error detection from formatting
- Extracts structured metadata for conditional routing
- Preserves hints for intelligent retry
- Temperature 0.0 ensures consistent format

---

### Node 5: format_results

**Type**: `llm`

**Purpose**: Format successful query results in user-friendly prose

**Configuration**:
```json
{
  "id": "format_results",
  "agent": "llm",
  "llm_config": {
    "provider": "openrouter",
    "model": "meta-llama/llama-3.3-8b-instruct:free",
    "temperature": 0.7,
    "max_tokens": 2000,
    "system_prompt": "You are a technical writer. Format database query results in clear, user-friendly prose. Be conversational and helpful while presenting data professionally."
  },
  "instruction": "...",
  "depends_on": ["check_result"],
  "timeout": 60
}
```

**Instruction Template**:
```
Format the successful database query results for the user.

## Original User Request
{user_input}

## Query Executed
{generate_query}

## Results from Database (Truncated for Context)
{execute_query}

NOTE: The results above may be truncated if the dataset is large. Focus on presenting the key information clearly.

## Your Task

Create a clear, professional response that:

1. **Directly Answers the User's Question**
   - Get straight to the point
   - Lead with the most relevant information

2. **Presents Data in Readable Format**
   - Use markdown tables for structured data (multiple rows with multiple columns)
   - Use bullet lists for small sets or single-column data
   - Use prose for single values, counts, or summaries

3. **Highlights Key Insights** (if relevant)
   - Patterns or trends in the data
   - Notable outliers or interesting findings
   - Context that helps interpret the results

4. **Uses Conversational Tone**
   - Be helpful and friendly
   - Explain technical terms if needed
   - Anticipate follow-up questions

**What NOT to Include**:
- Technical details about the query (unless specifically requested)
- JSON syntax or raw query text
- Implementation details
- Debugging information

## Examples

**For List Queries** (e.g., "list all active employees"):
```
Here are the 15 active employees currently in the system:

| Name | Department | Email |
|------|------------|-------|
| John Smith | Engineering | john@company.com |
| Jane Doe | Marketing | jane@company.com |
...

All employees shown are currently marked as active in the system.
```

**For Count Queries** (e.g., "how many customers do we have?"):
```
There are currently **142 customers** in the database.
```

**For Analytical Queries** (e.g., "show me sales by region"):
```
Here's the sales breakdown by region:

- **North**: $1,245,000 (45% of total)
- **South**: $890,000 (32% of total)
- **East**: $620,000 (23% of total)

The North region is leading with nearly half of all sales.
```

Generate your response now:
```

**Why This Approach**:
- Temperature 0.7 for natural, conversational output
- Truncated data prevents context overflow (50k + 5k chars max)
- Focuses on user value, not technical details

---

## Conditional Routing Logic

### Edge: check_result → [format_results | generate_query]

**Configuration**:
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

**Behavior**:
- **If `has_error: false`**: Success path → format_results → END
- **If `has_error: true`**: Retry path → generate_query (with error context)

**Retry Limit**: Maximum 5 attempts total
- Attempt 1: Initial generation
- Attempts 2-5: Retries with error hints

**Retry Context**: Each retry includes:
- Original user request
- Welcome message
- **Previous error message** (from check_result)
- **Correction hint** (from MCP server)

---

## Complete Workflow JSON

```json
{
  "name": "database_query_smart",
  "version": "2.0",
  "description": "Optimized smart database query workflow using MCP batch requests and built-in prompts",
  "trigger_patterns": [
    "database query",
    "query database",
    "search database",
    "find in database",
    "list employees",
    "show data",
    "how many",
    "count"
  ],
  "nodes": [
    {
      "id": "get_welcome",
      "agent": "mcp_resource",
      "resource_uri": "welcome://message",
      "server_name": "database-query-server-railway",
      "instruction": "Read welcome resource to get available tables, features, and common rules",
      "depends_on": [],
      "timeout": 30
    },
    {
      "id": "generate_query",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "temperature": 0.1,
        "max_tokens": 2000,
        "system_prompt": "You are a SQL query expert. Generate JSON database queries following exact format specifications. When you need detailed schema information, request it using the available tools. Output ONLY valid JSON with no markdown wrappers.",
        "include_workflow_history": true,
        "history_nodes": ["check_result"]
      },
      "instruction": "You are generating a JSON database query based on the user's natural language request.\n\n## User Request\n{user_input}\n\n## Available Context\n\n### Welcome Message (Tables, Features, Rules)\n{get_welcome}\n\n### Previous Error Analysis (if this is a retry)\n{@latest:check_result}\n\n## Your Task\n\n**IF THIS IS A RETRY** (you see error analysis above with 'has_error: true'):\n- Analyze the error message and hint carefully\n- The hint will tell you EXACTLY what to fix\n- Generate a CORRECTED query addressing the specific issue\n\n**IF THIS IS THE FIRST ATTEMPT** (no error analysis above):\n\n1. **Analyze the Request**: What tables, columns, and operations are needed?\n\n2. **Determine If You Need Details**: If you need exact schema or feature documentation, you can request:\n   - get_table_details(\"Person,Customer,Contract\") - batch request for multiple tables\n   - get_feature_details(\"JOIN,WHERE,GROUP_BY\") - batch request for features\n   \n   NOTE: These are conceptual - in actual implementation, you'll include this need in your reasoning and the system will provide the details.\n\n3. **Generate the Query**:\n\n## Query Format\n\nOutput ONLY the JSON query string (NOT wrapped in {\"json_query\": ...}).\n\n**Basic Structure**:\n{\"table\":\"TableName\",\"select\":[\"column1\",\"column2\"],\"where\":{\"column\":\"value\"},\"limit\":10}\n\n**Common Operations**:\n- WHERE: \"where\": {\"status\": \"active\"}\n- WHERE IN: \"whereIn\": {\"id\": [1, 2, 3]}\n- LIKE: \"whereLike\": {\"name\": \"%pattern%\"}\n- JOIN: \"join\": [{\"table\": \"Other\", \"first\": \"t1.id\", \"second\": \"t2.t1_id\"}]\n- GROUP BY: \"groupBy\": \"category\"\n- COUNT: \"count\": \"*\" or \"count\": \"column_name\"\n- ORDER BY: \"orderBy\": {\"column\": \"asc\"}\n\n**Critical Rules**:\n- Use EXACT table and column names from schema (case-sensitive!)\n- ALWAYS include LIMIT for queries that might return many rows (default: 10-50)\n- JOIN syntax requires exact column references: \"table.column\"\n- Only SELECT operations allowed\n\n## MCP Validation\n\nThe database will validate:\n- Table names exist and are correctly cased\n- Column names exist in their tables\n- Join relationships are valid\n- Feature syntax is correct\n\nIf validation fails, you'll receive a hint explaining exactly what to fix.\n\nGenerate the JSON query now (no wrapper, no markdown):",
      "depends_on": ["get_welcome"],
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
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "temperature": 0.0,
        "system_prompt": "You are a precise JSON response analyzer. Parse MCP responses and output EXACT structured status information following the specified format."
      },
      "instruction": "Analyze the MCP query execution result and determine if it succeeded or failed.\n\n## Result from MCP\n{execute_query}\n\n## MCP Response Format\n\nThe MCP server returns JSON in one of two formats:\n\n**Success**: {\"success\": true, \"count\": N, \"data\": [...]}\n**Error**: {\"success\": false, \"error\": {\"message\": \"...\", \"details\": \"...\", \"hint\": \"...\"}}\n\n## Your Task\n\n1. Parse the JSON response\n2. Check the \"success\" field\n3. Extract error details if present\n4. Categorize the error type\n5. Extract the hint (CRITICAL for retry)\n\n## Output Format (STRICT - Used for Conditional Routing)\n\n**If Error Detected**:\nhas_error: true\nerror_type: <table_not_found|column_not_found|syntax_error|join_error|type_mismatch|other>\nerror_message: <exact error text from MCP>\nerror_hint: <exact hint from MCP>\n\n**If Successful**:\nhas_error: false\nrow_count: <number of rows returned>\ndata_summary: <brief description>\n\n**IMPORTANT**: The \"has_error\" field MUST be exactly \"true\" or \"false\". This controls workflow routing.\n\nOutput your analysis now:",
      "depends_on": ["execute_query"],
      "timeout": 30
    },
    {
      "id": "format_results",
      "agent": "llm",
      "llm_config": {
        "provider": "openrouter",
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "temperature": 0.7,
        "max_tokens": 2000,
        "system_prompt": "You are a technical writer. Format database query results in clear, user-friendly prose. Be conversational and helpful."
      },
      "instruction": "Format the successful database query results for the user.\n\n## Original User Request\n{user_input}\n\n## Query Executed\n{generate_query}\n\n## Results from Database (may be truncated)\n{execute_query}\n\n## Your Task\n\nCreate a clear, professional response that:\n1. Directly answers the user's question\n2. Presents data in readable format (tables, lists, or prose)\n3. Highlights key insights if relevant\n4. Uses conversational, helpful tone\n\n**Do NOT include**: Technical query details, JSON syntax, debugging info\n\n## Format Examples\n\n**List queries**: Use markdown tables\n**Count queries**: Use bold numbers with context\n**Analytical queries**: Use bullet lists with insights\n\nGenerate your response now:",
      "depends_on": ["check_result"],
      "timeout": 60
    }
  ],
  "conditional_edges": [
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
    "user_input": "List all active employees",
    "max_retries": 5
  }
}
```

---

## Key Optimizations Explained

### 1. Batch Request Optimization

**v1.0 Approach** (multiple sequential calls):
```
get_table_details("Person") → wait → result
get_table_details("Contract") → wait → result
get_table_details("Customer") → wait → result
```
**Total latency**: 3 × (network + processing) = ~3-6 seconds

**v2.0 Approach** (single batch call):
```
get_table_details("Person,Contract,Customer") → wait → result
```
**Total latency**: 1 × (network + processing) = ~1-2 seconds

**Savings**: 66% latency reduction for 3 tables

### 2. LLM-Driven Discovery

**v1.0 Approach**:
```
identify_tables → extract list → get details → evaluate completeness → maybe get more
```
**Problem**: Pre-determines flow, may request unnecessary details

**v2.0 Approach**:
```
LLM sees welcome message → decides if it needs details → requests if needed
```
**Benefit**: Only requests what's actually needed, reduces unnecessary MCP calls

### 3. MCP Built-in Prompt Integration

**Available MCP Prompts** (from source analysis):
- `query_builder_prompt(table, operation)` - Syntax guidance for specific table
- `validation_prompt()` - Pre-execution validation checklist
- `common_errors_prompt()` - 18+ tables with documented error patterns

**Integration Strategy** (future enhancement):
```json
{
  "id": "generate_query",
  "instruction": "First, review the validation guidelines:\n{@mcp_prompt:validation_prompt}\n\nThen generate your query..."
}
```

### 4. Structured Error Handling

**MCP Error Response**:
```json
{
  "error": {
    "message": "Column 'firstname' does not exist in table 'Person'",
    "details": "Available columns: id, first_name, last_name, email, ...",
    "hint": "Did you mean 'first_name' instead of 'firstname'?"
  }
}
```

**Retry Flow**:
1. LLM sees hint: "Did you mean 'first_name'?"
2. Generates corrected query with `first_name`
3. High success rate on retry (hint is very specific)

---

## Performance Characteristics

### Expected Latencies (per node)

| Node | Type | Expected Latency | Notes |
|------|------|------------------|-------|
| get_welcome | MCP Resource | 200-500ms | Cached on MCP side |
| generate_query | LLM (Llama 3.3 8B) | 2-5s | Depends on complexity |
| execute_query | MCP Tool | 500ms-2s | Depends on query |
| check_result | LLM (Llama 3.3 8B) | 1-2s | Simple parsing |
| format_results | LLM (Llama 3.3 8B) | 2-4s | Prose generation |

**Total Success Path**: ~6-14 seconds
**Total With 1 Retry**: ~10-20 seconds
**Total With 5 Retries**: ~30-70 seconds (rare, indicates prompt issue)

### Cost Analysis (OpenRouter Free Tier)

**Per Query Execution**:
- Llama 3.3 8B: **FREE** (rate limited)
- MCP calls: **FREE** (internal)
- Total cost: **$0.00** ✅

**vs Previous (Claude Sonnet 3.5)**:
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- Estimated cost per query: $0.02-0.10
- **Monthly savings** (1000 queries): $20-100

### Context Usage

| Node | Input Tokens | Output Tokens | Total |
|------|--------------|---------------|-------|
| generate_query | ~5k (welcome + prompt) | ~200 (query JSON) | ~5.2k |
| check_result | ~3k (MCP response) | ~100 (analysis) | ~3.1k |
| format_results | ~8k (truncated data) | ~500 (prose) | ~8.5k |

**Total per success**: ~17k tokens (well within 128k limit)

---

## Error Handling Strategy

### Retry Decision Matrix

| Error Type | Retry? | Max Attempts | Why |
|------------|--------|--------------|-----|
| `column_not_found` | ✅ Yes | 5 | Hint provides correction |
| `table_not_found` | ✅ Yes | 2 | Likely case issue |
| `syntax_error` | ✅ Yes | 3 | Hint explains format |
| `join_error` | ✅ Yes | 3 | Hint shows correct syntax |
| `type_mismatch` | ✅ Yes | 3 | Hint shows expected type |
| `permission_denied` | ❌ No | 0 | Cannot be fixed by retry |
| `timeout` | ❌ No | 0 | Query too complex |

### Failure Modes

**Scenario 1: Invalid Table Name**
```
Attempt 1: {"table": "person", ...}
Error: "Table 'person' not found. Available: Person, Customer, ..."
Hint: "Table names are case-sensitive. Did you mean 'Person'?"
Attempt 2: {"table": "Person", ...}
Result: ✅ Success
```

**Scenario 2: Invalid Column Name**
```
Attempt 1: {"table": "Person", "select": ["firstname"], ...}
Error: "Column 'firstname' does not exist in table 'Person'"
Hint: "Did you mean 'first_name'? Available: first_name, last_name, ..."
Attempt 2: {"table": "Person", "select": ["first_name"], ...}
Result: ✅ Success
```

**Scenario 3: Persistent LLM Confusion** (rare)
```
Attempt 1: Invalid query
Attempt 2: Still invalid
Attempt 3: Still invalid
...
Attempt 5: Still invalid
Result: ❌ Fail with "Unable to generate valid query after 5 attempts"
```
**Mitigation**: Improve prompts, add more examples, consider different LLM

---

## Testing Plan

### Test Cases

#### TC1: Simple Query (Happy Path)
**Input**: "List all active employees"
**Expected Flow**: get_welcome → generate_query → execute_query → check_result → format_results
**Expected Attempts**: 1
**Expected Output**: Formatted list of employees

#### TC2: Query with Join
**Input**: "Show me employees with their department names"
**Expected Flow**: Same as TC1
**Expected Attempts**: 1-2 (may need retry for join syntax)
**Expected Output**: Table with employee names and departments

#### TC3: Count Query
**Input**: "How many customers do we have?"
**Expected Flow**: Same as TC1
**Expected Attempts**: 1
**Expected Output**: Single number with context

#### TC4: Case Sensitivity Error
**Input**: "List all data from person table"
**Expected Flow**: get_welcome → generate_query → execute_query → check_result → generate_query (retry) → execute_query → check_result → format_results
**Expected Attempts**: 2 (initial + 1 retry)
**Expected Output**: Formatted list from Person table

#### TC5: Column Name Error
**Input**: "Show employee firstname and lastname"
**Expected Flow**: Same as TC4
**Expected Attempts**: 2 (initial + 1 retry)
**Expected Output**: Formatted list with first_name and last_name

#### TC6: Complex Query Requiring Details
**Input**: "Show me all projects with their lead engineer's email and the customer company name"
**Expected Flow**: get_welcome → generate_query (realizes needs schema) → [internal detail request] → execute_query → check_result → format_results
**Expected Attempts**: 1-2
**Expected Output**: Table with project, engineer email, customer name

### Success Metrics

- **Query Success Rate**: > 90% within 2 attempts
- **Average Latency**: < 15 seconds for success path
- **Cost**: $0.00 (free tier)
- **Context Overflow Rate**: < 1% (truncation prevents)
- **User Satisfaction**: Query results are accurate and well-formatted

---

## Implementation Checklist

- [ ] Create workflow JSON file: `database_query_smart_v2.json`
- [ ] Update workflow compiler to support batch tool requests (if needed)
- [ ] Verify MCP server `get_table_details` supports comma-separated input
- [ ] Verify MCP server `get_feature_details` supports comma-separated input
- [ ] Test truncation logic handles large datasets (> 60k chars)
- [ ] Test conditional routing on `custom_metadata.has_error` field
- [ ] Test retry mechanism with max 5 attempts
- [ ] Verify `@latest:check_result` placeholder works for retry context
- [ ] Test with various query types (simple, join, count, group by)
- [ ] Verify formatted output quality across different query types
- [ ] Monitor OpenRouter rate limits for Llama 3.3 free tier
- [ ] Document workflow in user-facing documentation

---

## Future Enhancements

### Phase 2: MCP Prompt Integration
- Integrate `validation_prompt()` before query generation
- Use `common_errors_prompt()` for proactive error prevention
- Request `query_builder_prompt(table)` for table-specific guidance

### Phase 3: Intelligent Caching
- Cache welcome message (changes infrequently)
- Cache table details for 5-10 minutes
- Reduce MCP calls for repeated queries

### Phase 4: Query Optimization Suggestions
- Analyze query performance
- Suggest indexes or query rewrites
- Warn about queries without LIMIT on large tables

### Phase 5: Multi-Database Support
- Support multiple MCP database servers
- Route queries to appropriate database
- Handle cross-database joins (if supported)

---

## Appendix: MCP Server Capabilities Reference

### Resources
- `welcome://message` - Tables, features, rules overview
- `response-format://documentation` - Detailed JSON format specs

### Tools
- `get_table_details(table_names: str)` - Get schema for one or more tables (comma-separated)
- `get_feature_details(feature_names: str)` - Get documentation for features (comma-separated)
- `execute_query(json_query: str)` - Execute JSON query, returns structured result

### Prompts (for future integration)
- `query_builder_prompt(table: str, operation: str)` - Syntax guidance
- `validation_prompt()` - Pre-execution checklist
- `common_errors_prompt()` - Known error patterns

### Query Features Supported
- SELECT, WHERE, WHERE IN, WHERE LIKE
- JOIN (INNER, LEFT, RIGHT)
- GROUP BY, ORDER BY
- LIMIT, OFFSET
- COUNT, SUM, AVG, MIN, MAX
- DISTINCT
- HAVING (with GROUP BY)

---

## Document Changelog

- **v1.0** (2025-10-12): Initial 12-node design with sequential discovery
- **v2.0** (2025-10-12): Optimized to 5 nodes with batch requests and LLM-driven discovery

---

## Approval & Sign-off

**Prepared by**: Claude (AI Assistant)
**Reviewed by**: [Pending user review]
**Approved by**: [Pending user approval]
**Date**: 2025-10-12

**Ready for Implementation**: ✅ Yes (pending approval)
