# Manual Prompts Configuration

**Status**: ✅ Production Ready

This guide explains how to manually configure prompts for MCP servers that don't expose prompts via the `prompts/list` endpoint.

---

## Problem Statement

Some MCP servers:
- ✅ Expose tools via `tools/list`
- ❌ **Do NOT expose prompts** via `prompts/list`
- ❌ Tool descriptions are generic
- ❌ ReAct agents lack context to use tools correctly

### Example: Corporate Database MCP Server

The corporate MCP server on `http://localhost:8005/mcp`:
- ✅ Exposes `query_database` tool
- ❌ No prompts exposed
- ❌ Generic description: "Execute a database query using the JSON API"
- ❌ ReAct agents don't know the database schema
- ❌ High risk of hallucinated queries

---

## Solution: Manual Prompt Files

Configure prompts via `.env` that:
1. Load prompt content from an external file (e.g., `PROMPT.md`)
2. Associate prompt with a specific tool
3. Inject prompt into LangChain tool description
4. Make prompt available for workflow auto-population

---

## Configuration

### Step 1: Create Prompt File

Create a markdown file with complete tool documentation:

**File**: `/home/mverde/src/taal/json_api/PROMPT.md`

```markdown
# Database Query Tool - Usage Guide

## Database Schema

### Tables
- **employees**: id, first_name, last_name, email, department_id
- **departments**: id, name, budget
- **projects**: id, name, start_date, end_date

### Foreign Keys
- employees.department_id → departments.id

### Enums
- status: active, inactive, pending

## JSON API Format

Use Knex query builder format:

```json
{
  "table": "employees",
  "select": ["id", "first_name", "last_name"],
  "where": {"is_active": true},
  "limit": 10
}
```

## Examples

### Example 1: Simple Query
Query: "List all active employees"
```json
{
  "table": "employees",
  "select": ["*"],
  "where": {"status": "active"}
}
```

### Example 2: Join Query
Query: "Show employees with their departments"
```json
{
  "table": "employees",
  "select": ["employees.*", "departments.name as dept_name"],
  "join": [{
    "table": "departments",
    "first": "employees.department_id",
    "second": "departments.id"
  }]
}
```

## Rules

1. **No hallucination**: Use ONLY tables and columns listed above
2. **Validate schema**: Check foreign keys before joining
3. **Use enums correctly**: Only use enum values listed above
```

### Step 2: Configure in .env

Add two environment variables for the MCP server:

```bash
# Enable MCP
MCP_ENABLE=true

# Server configuration
MCP_SERVER_CORPORATE_TYPE=remote
MCP_SERVER_CORPORATE_TRANSPORT=streamable_http
MCP_SERVER_CORPORATE_URL=http://localhost:8005/mcp
MCP_SERVER_CORPORATE_ENABLED=true
MCP_SERVER_CORPORATE_TIMEOUT=30.0

# Manual prompts configuration
MCP_SERVER_CORPORATE_PROMPTS_FILE=/home/mverde/src/taal/json_api/PROMPT.md
MCP_SERVER_CORPORATE_PROMPT_TOOL_ASSOCIATION=query_database
```

### Step 3: Restart Supervisor

```bash
python -m servers.supervisor_server
```

### Step 4: Verify

Check logs:

```
INFO:utils.mcp_registry:Registering MCP server 'corporate'
INFO:utils.mcp_registry:📋 Loaded prompt from file: /home/mverde/src/taal/json_api/PROMPT.md
INFO:utils.mcp_registry:✅ Prompt associated with tool: query_database
INFO:utils.mcp_registry:📋 Found 1 tools from 'corporate'
```

---

## How It Works

### 1. Prompt Discovery

The `MCPToolRegistry` checks for manual prompt file first:

**File**: `utils/mcp_registry.py` (lines 671-710)

```python
async def _discover_prompts(self, server: MCPServerConfig):
    prompts = []

    # Check if manual prompts file is specified
    if server.prompts_file:
        prompts = await self._load_prompts_from_file(server)
    elif server.server_type == MCPServerType.REMOTE:
        prompts = await self._discover_remote_prompts(server)
    else:
        prompts = await self._discover_local_prompts(server)

    # Associate with tool if specified
    if server.prompt_tool_association:
        tool = self._tools.get(server.prompt_tool_association)
        if tool:
            tool.associated_prompt = prompt.name
```

### 2. File Loading

**File**: `utils/mcp_registry.py` (lines 902-954)

```python
async def _load_prompts_from_file(
    self,
    server: MCPServerConfig
) -> List[MCPPrompt]:
    """Load prompts from a file (markdown, text, etc.)"""

    prompt_file = Path(server.prompts_file)

    # Read file content
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_content = f.read()

    # Create MCPPrompt with file content
    prompt = MCPPrompt(
        name=prompt_file.stem,  # Filename without extension
        description=prompt_content,
        arguments=[],
        server_name=server.name
    )

    return [prompt]
```

### 3. Prompt Injection

When creating LangChain tools, the prompt is injected into the tool description:

**File**: `utils/mcp_client.py` (lines 200-250)

```python
# Get associated prompt if configured
prompt = None
if tool.associated_prompt:
    prompt = await registry.get_prompt(tool.associated_prompt)

# Build tool description
description = tool.description
if prompt:
    description += f"\n\n## Usage Guide\n{prompt.description}"

# Create LangChain tool with enhanced description
langchain_tool = StructuredTool.from_function(
    func=tool_func,
    name=tool.name,
    description=description,  # Full prompt injected here
    args_schema=input_schema
)
```

### 4. ReAct Agent Usage

When the ReAct agent considers using the tool, it sees:

```
Tool: query_database

Description:
Execute a database query using the JSON API. The payload should follow the Knex query builder format.

## Usage Guide
# Database Query Tool - Usage Guide

## Database Schema
[... full 18,000+ character prompt with schema, examples, rules ...]
```

The agent can now:
- See complete database schema
- Understand JSON API format
- Follow examples
- Apply validation rules
- **Generate zero-hallucination queries**

---

## Testing

### Test 1: Prompt Discovery

**Script**: `scripts/test_corporate_prompts.py`

```bash
python scripts/test_corporate_prompts.py
```

**Expected Output**:
```
✓ Corporate server: healthy
✓ Prompts discovered: 1
✓ Prompt: PROMPT
  - Server: corporate
  - Description length: 18,301 chars
  - Associated with tool: query_database
```

### Test 2: LangChain Tool Prompt Injection

**Script**: `scripts/test_langchain_tool_prompts.py`

```bash
python scripts/test_langchain_tool_prompts.py
```

**Expected Output**:
```
✓ LangChain tools created: 1
✓ query_database tool found: YES
✓ Description length: 18,419 chars
✓ Prompt injected: YES

Prompt Injection Markers:
  ✓ Usage Guide section
  ✓ Database schema information
  ✓ JSON API format
  ✓ Examples
  ✓ Rules/Guidelines
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PROMPTS_FILE` | No | Path to markdown/text file with prompt | `/path/to/PROMPT.md` |
| `PROMPT_TOOL_ASSOCIATION` | No | Tool name to associate with prompt | `query_database` |

### Parameter Format

```bash
MCP_SERVER_{NAME}_PROMPTS_FILE=/path/to/file.md
MCP_SERVER_{NAME}_PROMPT_TOOL_ASSOCIATION=tool_name
```

Where `{NAME}` is your server name (e.g., `CORPORATE`, `LOCAL_TOOLS`).

### Notes

- If `PROMPTS_FILE` is specified, `prompts/list` is **not called**
- Prompt name defaults to filename without extension (e.g., `PROMPT.md` → `PROMPT`)
- Multiple prompts in one file: **not supported** (use one file = one prompt)
- Tool association is automatic if `PROMPT_TOOL_ASSOCIATION` is set

---

## Use Cases

### 1. Database Query APIs

**Problem**: MCP server wraps a database but doesn't expose schema

**Solution**: Create `PROMPT.md` with full schema, associate with `query_*` tool

**Benefit**: Zero hallucination, LLM knows exact tables, columns, foreign keys

### 2. Custom Tool Documentation

**Problem**: Tool needs complex usage instructions

**Solution**: Write markdown guide, attach to tool via `PROMPTS_FILE`

**Benefit**: Detailed examples, rules, edge cases documented

### 3. Multi-Language Tools

**Problem**: Need different instructions per language

**Solution**: Create `PROMPT_IT.md`, `PROMPT_EN.md`, configure per server

**Benefit**: Localized instructions for international teams

### 4. Version-Specific Guidance

**Problem**: API v1 vs v2 have different formats

**Solution**: `PROMPT_V1.md` and `PROMPT_V2.md` for different server configs

**Benefit**: Version-specific instructions without code changes

---

## Workflow Integration

Workflows can use `use_mcp_prompt: true` to automatically populate instructions:

```json
{
  "id": "query_db",
  "agent": "mcp_tool",
  "tool_name": "query_database",
  "use_mcp_prompt": true,
  "params": {
    "query_payload": "{generated_json}"
  }
}
```

The workflow engine will automatically inject the full prompt into the node instruction.

---

## Architecture Benefits

### 1. Zero Hallucination

The prompt explicitly lists all tables, columns, foreign keys, and enums. The LLM cannot invent non-existent schema elements.

### 2. Centralized Maintenance

- Prompt is in external file (e.g., `/path/to/PROMPT.md`)
- Update once, automatically propagates to all agents
- No code changes needed for schema updates

### 3. ReAct Pattern Enhancement

The ReAct agent sees the full prompt in the tool description and can reason:

```
REASONING:
"I need to query the database for employee information. I see the query_database tool
has detailed schema showing employees table with columns: id, first_name, last_name,
email, department_id. There's a FK to departments table. I'll construct a JSON query
following the examples..."

TOOL SELECTION: query_database

ACTION:
{
  "query_payload": {
    "table": "employees",
    "select": ["id", "first_name", "last_name"],
    "join": [{
      "table": "departments",
      "first": "employees.department_id",
      "second": "departments.id"
    }],
    "where": {"is_active": true},
    "limit": 10
  }
}
```

---

## Limitations

### Current Limitations

1. **One prompt per file**: Cannot split prompt into sections
2. **Static content**: Prompt file is read once at startup
3. **No validation**: File content isn't validated against tool schema
4. **Manual association only**: Cannot auto-detect which tool needs which prompt

### Potential Enhancements

1. **Hot reload**: Watch prompt file for changes, reload automatically
2. **Prompt templating**: Support variables in prompt file (e.g., `{{server_url}}`)
3. **Multi-prompt files**: Support multiple prompts in one file with sections
4. **Prompt validation**: Check that prompt examples match tool input schema
5. **Auto-association**: Match prompt to tool by name convention or keywords

---

## Troubleshooting

### Prompt Not Loaded

**Check**:
1. File path is absolute and exists
2. File is readable (check permissions)
3. `.env` has correct variable names
4. Supervisor restarted after `.env` changes

**Debug**:
```bash
# Check if file exists
ls -la /path/to/PROMPT.md

# Check supervisor logs
grep "Loaded prompt from file" supervisor.log
```

### Prompt Not Injected

**Check**:
1. `PROMPT_TOOL_ASSOCIATION` matches tool name exactly
2. Tool was discovered from MCP server
3. LangChain tools created successfully

**Debug**:
```bash
python scripts/test_langchain_tool_prompts.py
```

### Prompt Too Large

**Symptom**: Tool description exceeds LLM context window

**Solution**:
1. Reduce prompt size (remove redundant examples)
2. Use more concise schema documentation
3. Consider using retrieval for large schemas

---

## Next Steps

- [**Configuration Reference**](configuration.md) - All MCP environment variables
- [**Testing Guide**](testing.md) - Test MCP prompts integration
- [**Troubleshooting**](troubleshooting.md) - Debug common issues

---

**Related Files**:
- `utils/mcp_registry.py:902-954` - `_load_prompts_from_file()` implementation
- `utils/mcp_client.py:200-250` - Prompt injection in LangChain tools
- `config.py:353-393` - Environment variable parsing
- `scripts/test_corporate_prompts.py` - Prompt discovery test
- `scripts/test_langchain_tool_prompts.py` - Prompt injection test

**Last Updated**: 2025-10-06
