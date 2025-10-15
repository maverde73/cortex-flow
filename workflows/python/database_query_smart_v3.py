"""
Smart Database Query Workflow (Python Version)

This is a complete rewrite of database_query_smart_v3_simplified.json in Python,
demonstrating the benefits of Python workflow definition:

1. Type safety with IDE autocomplete
2. Reusable helper functions
3. Clear documentation with inline comments
4. Dynamic configuration
5. Easier testing and maintenance

Workflow Steps:
1. get_welcome - Fetch database welcome message (schema overview)
2. get_schema - Fetch detailed schema for relevant tables
3. generate_query - LLM generates JSON query based on user input
4. execute_query - Execute the generated query via MCP
5. check_result - LLM validates if query succeeded or failed
6. CONDITIONAL:
   - If error (has_error=true) → retry generate_query (with error context)
   - If success (has_error=false) → format_results
7. format_results - LLM formats results in user-friendly markdown

Max retries: 5 (configured in parameters)
"""

from schemas.workflow_schemas import WorkflowTemplate, LLMConfig
from workflows.python.helpers import (
    llm_node,
    mcp_tool_node,
    mcp_resource_node,
    retry_on_error
)


# ============================================================================
# Configuration
# ============================================================================

# LLM configuration for query generation
# Uses DeepSeek for fast, accurate JSON generation
QUERY_GEN_CONFIG = LLMConfig(
    provider="openrouter",
    model="deepseek/deepseek-v3.2-exp",
    temperature=0.1,  # Low temperature for precise JSON
    max_tokens=2000,
    system_prompt="You are a SQL query expert. Generate ONLY valid JSON database queries. Output raw JSON without markdown wrappers.",
    include_workflow_history=True,
    history_nodes=["check_result"]  # Include error feedback for retries
)

# LLM configuration for result validation
# Temperature 0.0 for deterministic error detection
VALIDATION_CONFIG = LLMConfig(
    provider="openrouter",
    model="deepseek/deepseek-v3.2-exp",
    temperature=0.0,  # Zero temperature for consistent parsing
    system_prompt="You analyze database query results. Output EXACT format: 'has_error: true/false' on first line."
)

# LLM configuration for result formatting
# Higher temperature for natural, conversational output
FORMATTING_CONFIG = LLMConfig(
    provider="openrouter",
    model="deepseek/deepseek-v3.2-exp",
    temperature=0.7,  # Higher temperature for creative formatting
    max_tokens=2000,
    system_prompt="You format database results in clear, user-friendly prose."
)

# Tables to fetch schema for
# These cover most common business database queries
SCHEMA_TABLES = "Person,Customer,Employee,Address,SalesOrder,Product,BusinessEntity"


# ============================================================================
# Instruction Templates
# ============================================================================

QUERY_GENERATION_PROMPT = """Generate a JSON database query for: {user_input}

## Available Context

### Welcome Message
{get_welcome}

### Complete Database Schema
{get_schema}

### Previous Error (if retry)
{@latest:check_result}

## Instructions

**IF THIS IS A RETRY** (you see error above):
- Read the error hint CAREFULLY
- Fix the EXACT issue mentioned
- Generate corrected query

**IF FIRST ATTEMPT**:
1. Use EXACT table and column names from schema (case-sensitive!)
2. Always include LIMIT for multi-row queries (default: 20)
3. Follow these patterns:

**Simple query**:
{"table":"Person","select":["FirstName","LastName"],"where":{"PersonType":"EM"},"limit":20}

**With JOIN**:
{"table":"Employee","select":["Person.FirstName","Employee.JobTitle"],"join":[{"table":"Person","first":"Employee.BusinessEntityID","second":"Person.BusinessEntityID"}],"limit":20}

**Count**:
{"table":"Person","count":"*","where":{"PersonType":"EM"}}

**CRITICAL**:
- Output ONLY the JSON query (no markdown, no wrapper)
- Use exact column names from schema
- Include LIMIT for SELECT queries

Generate the query now:"""

VALIDATION_PROMPT = """Analyze this database query result:

{execute_query}

## Task

1. Check if there's an error (look for "success": false or "error" field)
2. Output in EXACT format below

## Output Format (STRICT)

**If error**:
has_error: true
error_message: [exact error from database]

**If success**:
has_error: false
row_count: [number]

**CRITICAL**: First line MUST be exactly "has_error: true" or "has_error: false"
"""

FORMATTING_PROMPT = """Format these successful database results for the user.

## User Request
{user_input}

## Query Results
{execute_query}

## Task

Create a clear response that:
- Directly answers the user's question
- Presents data in markdown table or list format
- Is conversational and helpful
- Doesn't include technical JSON or query details

Generate your response:"""


# ============================================================================
# Workflow Definition
# ============================================================================

def create_workflow() -> WorkflowTemplate:
    """
    Create the database query workflow.

    This factory function allows for dynamic workflow creation,
    parameter customization, and easier testing.

    Returns:
        Complete WorkflowTemplate ready for registration
    """

    # Define nodes using helper functions
    nodes = [
        # Step 1: Fetch database welcome message
        # This provides high-level schema information
        mcp_resource_node(
            node_id="get_welcome",
            resource_uri="welcome://message",
            server_name="database-query-server-railway",
            instruction="Read welcome resource",
            depends_on=[],  # Entry node
            timeout=30
        ),

        # Step 2: Fetch detailed schema for relevant tables
        # Instruction is a comma-separated list of table names
        mcp_tool_node(
            node_id="get_schema",
            tool_name="get_table_details",
            instruction=SCHEMA_TABLES,  # Uses fixed constant
            server_name="database-query-server-railway",
            depends_on=["get_welcome"],
            timeout=60
        ),

        # Step 3: Generate JSON query using LLM
        # Uses error feedback from check_result on retries
        llm_node(
            node_id="generate_query",
            instruction=QUERY_GENERATION_PROMPT,
            provider=QUERY_GEN_CONFIG.provider,
            model=QUERY_GEN_CONFIG.model,
            temperature=QUERY_GEN_CONFIG.temperature,
            max_tokens=QUERY_GEN_CONFIG.max_tokens,
            system_prompt=QUERY_GEN_CONFIG.system_prompt,
            include_history=QUERY_GEN_CONFIG.include_workflow_history,
            history_nodes=QUERY_GEN_CONFIG.history_nodes,
            depends_on=["get_schema"],
            timeout=120
        ),

        # Step 4: Execute the generated query
        # Instruction is the query JSON from previous step
        mcp_tool_node(
            node_id="execute_query",
            tool_name="execute_query",
            instruction="{generate_query}",  # Reference previous node output
            server_name="database-query-server-railway",
            depends_on=["generate_query"],
            timeout=60
        ),

        # Step 5: Validate query result
        # LLM checks if result contains errors
        llm_node(
            node_id="check_result",
            instruction=VALIDATION_PROMPT,
            provider=VALIDATION_CONFIG.provider,
            model=VALIDATION_CONFIG.model,
            temperature=VALIDATION_CONFIG.temperature,
            system_prompt=VALIDATION_CONFIG.system_prompt,
            depends_on=["execute_query"],
            timeout=30
        ),

        # Step 6: Format successful results
        # Only reached if check_result indicates success
        llm_node(
            node_id="format_results",
            instruction=FORMATTING_PROMPT,
            provider=FORMATTING_CONFIG.provider,
            model=FORMATTING_CONFIG.model,
            temperature=FORMATTING_CONFIG.temperature,
            max_tokens=FORMATTING_CONFIG.max_tokens,
            system_prompt=FORMATTING_CONFIG.system_prompt,
            depends_on=["check_result"],
            timeout=60
        ),
    ]

    # Define conditional routing
    # If check_result detects error, retry from generate_query
    # If success, proceed to format_results
    conditional_edges = [
        retry_on_error(
            check_node="check_result",
            retry_node="generate_query",  # Retry from here on error
            success_node="format_results",  # Go here on success
            error_field="custom_metadata.has_error"
        )
    ]

    # Create and return the complete workflow template
    return WorkflowTemplate(
        name="database_query_smart_v3_python",
        version="3.2",
        description="Smart database query workflow with full schema context and retry logic (Python version)",
        trigger_patterns=[
            "database query",
            "query database",
            "search database",
            "find in database",
            "list employees",
            "show data",
            "how many",
            "count"
        ],
        nodes=nodes,
        conditional_edges=conditional_edges,
        parameters={
            "user_input": "List all active employees",
            "max_retries": 5  # Maximum number of query generation attempts
        }
    )


# ============================================================================
# Export for Registry
# ============================================================================

# The registry will look for a module-level variable named 'workflow'
workflow = create_workflow()


# ============================================================================
# Testing & Validation
# ============================================================================

if __name__ == "__main__":
    """
    Run this file directly to validate the workflow structure.
    This helps catch errors before loading into the registry.
    """
    import json
    from workflows.registry import WorkflowRegistry

    # Create workflow
    wf = create_workflow()

    # Print summary
    print(f"Workflow: {wf.name} v{wf.version}")
    print(f"Description: {wf.description}")
    print(f"\nNodes ({len(wf.nodes)}):")
    for node in wf.nodes:
        deps = f" (depends on: {', '.join(node.depends_on)})" if node.depends_on else ""
        print(f"  - {node.id} [{node.agent}]{deps}")

    print(f"\nConditional Edges ({len(wf.conditional_edges)}):")
    for edge in wf.conditional_edges:
        print(f"  - {edge.from_node} →")
        for cond in edge.conditions:
            print(f"      if {cond.field} {cond.operator.value} {cond.value} → {cond.next_node}")
        print(f"      else → {edge.default}")

    # Validate
    registry = WorkflowRegistry()
    errors = registry.validate_template(wf)

    if errors:
        print(f"\n❌ Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ Validation PASSED")

    # Export as JSON for comparison
    print(f"\n📄 JSON export:")
    print(json.dumps(wf.dict(), indent=2))
