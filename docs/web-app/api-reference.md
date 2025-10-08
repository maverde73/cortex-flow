# Cortex Flow API Reference

## Base URL

```
http://localhost:8002/api
```

## Authentication

Currently, the API doesn't require authentication for local development. In production, use API keys or JWT tokens.

## Response Format

All API responses follow this format:

```json
{
  "status": "success|error",
  "data": {}, // Response data
  "error": null, // Error message if status is "error"
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Endpoints

### Projects

#### List All Projects
```http
GET /api/projects
```

**Response:**
```json
[
  {
    "name": "default",
    "description": "Default project",
    "active": true,
    "created_at": "2024-01-01T12:00:00Z",
    "config": {}
  }
]
```

#### Get Project
```http
GET /api/projects/{name}
```

**Parameters:**
- `name` (path): Project name

**Response:**
```json
{
  "name": "default",
  "description": "Default project",
  "active": true,
  "workflows": [],
  "prompts": [],
  "config": {}
}
```

#### Create Project
```http
POST /api/projects
```

**Request Body:**
```json
{
  "name": "my-project",
  "description": "My new project"
}
```

**Response:**
```json
{
  "name": "my-project",
  "description": "My new project",
  "active": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

#### Activate Project
```http
POST /api/projects/{name}/activate
```

**Parameters:**
- `name` (path): Project name to activate

**Response:**
```json
{
  "name": "my-project",
  "active": true
}
```

#### Delete Project
```http
DELETE /api/projects/{name}
```

**Parameters:**
- `name` (path): Project name to delete

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

### Workflows

#### List Workflows
```http
GET /api/workflows
```

**Query Parameters:**
- `project` (optional): Filter by project name

**Response:**
```json
[
  {
    "id": "workflow-1",
    "name": "Research Workflow",
    "description": "Automated research workflow",
    "project": "default",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z",
    "nodes": [],
    "edges": []
  }
]
```

#### Get Workflow
```http
GET /api/workflows/{id}
```

**Parameters:**
- `id` (path): Workflow ID

**Response:**
```json
{
  "id": "workflow-1",
  "name": "Research Workflow",
  "description": "Automated research workflow",
  "project": "default",
  "nodes": [
    {
      "id": "node-1",
      "type": "agent",
      "agent": "researcher",
      "position": { "x": 100, "y": 100 },
      "data": {
        "label": "Research",
        "config": {}
      }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2"
    }
  ]
}
```

#### Create Workflow
```http
POST /api/workflows
```

**Request Body:**
```json
{
  "name": "New Workflow",
  "description": "Workflow description",
  "project": "default",
  "nodes": [],
  "edges": []
}
```

#### Update Workflow
```http
PUT /api/workflows/{id}
```

**Request Body:**
```json
{
  "name": "Updated Workflow",
  "description": "Updated description",
  "nodes": [],
  "edges": []
}
```

#### Delete Workflow
```http
DELETE /api/workflows/{id}
```

#### Execute Workflow
```http
POST /api/workflows/{id}/execute
```

**Request Body:**
```json
{
  "input": {
    "user_request": "Research AI trends"
  },
  "config": {
    "timeout": 300,
    "debug": true
  }
}
```

**Response:**
```json
{
  "execution_id": "exec-123",
  "status": "running",
  "started_at": "2024-01-01T12:00:00Z"
}
```

#### Get Workflow Execution
```http
GET /api/workflows/executions/{execution_id}
```

**Response:**
```json
{
  "execution_id": "exec-123",
  "workflow_id": "workflow-1",
  "status": "completed",
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:05:00Z",
  "result": {
    "output": "Research results..."
  },
  "trace": []
}
```

#### Validate Workflow
```http
POST /api/workflows/validate
```

**Request Body:**
```json
{
  "nodes": [],
  "edges": []
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": []
}
```

#### Generate Workflow from Natural Language
```http
POST /api/workflows/generate
```

**Request Body:**
```json
{
  "description": "Research a topic, analyze findings, and write a report"
}
```

**Response:**
```json
{
  "workflow": {
    "nodes": [],
    "edges": []
  }
}
```

### Agents

#### List Agents
```http
GET /api/agents
```

**Response:**
```json
[
  {
    "name": "researcher",
    "type": "agent",
    "description": "Web research specialist",
    "status": "running",
    "port": 8001,
    "config": {
      "model": "gpt-4",
      "temperature": 0.7
    }
  }
]
```

#### Get Agent Config
```http
GET /api/agents/{name}/config
```

**Response:**
```json
{
  "name": "researcher",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "tools": ["web_search", "extract"],
  "system_prompt": "You are a research specialist..."
}
```

#### Update Agent Config
```http
PUT /api/agents/{name}/config
```

**Request Body:**
```json
{
  "model": "gpt-4",
  "temperature": 0.5,
  "max_tokens": 3000
}
```

#### Test Agent
```http
POST /api/agents/{name}/test
```

**Request Body:**
```json
{
  "input": "Research quantum computing",
  "config": {
    "temperature": 0.7
  }
}
```

**Response:**
```json
{
  "output": "Research results...",
  "execution_time": 5.2,
  "tokens_used": 1500,
  "trace": []
}
```

### Process Management

#### Get Process Status
```http
GET /api/processes/status
```

**Response:**
```json
[
  {
    "pid": 12345,
    "name": "researcher",
    "type": "agent",
    "status": "running",
    "port": 8001,
    "cpu_percent": 2.5,
    "memory_mb": 150.3,
    "uptime_seconds": 3600,
    "log_file": "/logs/researcher.log"
  }
]
```

#### Start Process
```http
POST /api/processes/start
```

**Request Body:**
```json
{
  "name": "researcher"
}
```

**Response:**
```json
{
  "pid": 12345,
  "name": "researcher",
  "status": "starting",
  "message": "Process started successfully"
}
```

#### Stop Process
```http
POST /api/processes/stop
```

**Request Body:**
```json
{
  "name": "researcher"
}
```

**Response:**
```json
{
  "name": "researcher",
  "status": "stopped",
  "message": "Process stopped successfully"
}
```

#### Restart Process
```http
POST /api/processes/restart
```

**Request Body:**
```json
{
  "name": "researcher"
}
```

#### Start All Processes
```http
POST /api/processes/start-all
```

**Response:**
```json
[
  {
    "name": "researcher",
    "status": "starting"
  },
  {
    "name": "analyst",
    "status": "starting"
  }
]
```

#### Stop All Processes
```http
POST /api/processes/stop-all
```

#### Get Process Logs
```http
GET /api/processes/{name}/logs
```

**Query Parameters:**
- `lines` (optional, default: 100): Number of lines to return

**Response:**
```json
{
  "name": "researcher",
  "logs": [
    "2024-01-01 12:00:00 - Starting researcher agent...",
    "2024-01-01 12:00:01 - Agent initialized"
  ]
}
```

### Prompts

#### List Prompts
```http
GET /api/prompts
```

**Query Parameters:**
- `project` (optional): Filter by project

**Response:**
```json
[
  {
    "id": "prompt-1",
    "name": "research_prompt",
    "description": "Research prompt template",
    "template": "Research {topic} and provide {num_points} key findings",
    "variables": ["topic", "num_points"],
    "project": "default"
  }
]
```

#### Get Prompt
```http
GET /api/prompts/{id}
```

#### Create Prompt
```http
POST /api/prompts
```

**Request Body:**
```json
{
  "name": "analysis_prompt",
  "description": "Analysis template",
  "template": "Analyze {data} focusing on {aspects}",
  "variables": ["data", "aspects"],
  "project": "default"
}
```

#### Update Prompt
```http
PUT /api/prompts/{id}
```

#### Delete Prompt
```http
DELETE /api/prompts/{id}
```

#### Test Prompt
```http
POST /api/prompts/{id}/test
```

**Request Body:**
```json
{
  "variables": {
    "topic": "AI",
    "num_points": 5
  }
}
```

**Response:**
```json
{
  "rendered": "Research AI and provide 5 key findings",
  "valid": true
}
```

### MCP Servers

#### List MCP Servers
```http
GET /api/mcp/servers
```

**Response:**
```json
[
  {
    "name": "filesystem",
    "url": "http://localhost:9000",
    "status": "connected",
    "tools": ["read_file", "write_file"],
    "config": {}
  }
]
```

#### Add MCP Server
```http
POST /api/mcp/servers
```

**Request Body:**
```json
{
  "name": "custom-server",
  "url": "http://localhost:9001",
  "auth": {
    "type": "api_key",
    "key": "secret-key"
  }
}
```

#### Test MCP Server
```http
POST /api/mcp/servers/{name}/test
```

**Response:**
```json
{
  "status": "connected",
  "latency_ms": 15,
  "available_tools": ["tool1", "tool2"]
}
```

#### Remove MCP Server
```http
DELETE /api/mcp/servers/{name}
```

### LLM Configuration

#### List LLM Providers
```http
GET /api/llm/providers
```

**Response:**
```json
[
  {
    "name": "openai",
    "enabled": true,
    "models": ["gpt-4", "gpt-3.5-turbo"],
    "default_model": "gpt-4"
  }
]
```

#### Get LLM Config
```http
GET /api/llm/config
```

**Response:**
```json
{
  "primary_provider": "openai",
  "primary_model": "gpt-4",
  "fallback_providers": ["anthropic"],
  "rate_limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 90000
  }
}
```

#### Update LLM Config
```http
PUT /api/llm/config
```

**Request Body:**
```json
{
  "primary_provider": "anthropic",
  "primary_model": "claude-3",
  "temperature": 0.7
}
```

#### Test LLM
```http
POST /api/llm/test
```

**Request Body:**
```json
{
  "provider": "openai",
  "model": "gpt-4",
  "prompt": "Hello, world!"
}
```

**Response:**
```json
{
  "response": "Hello! How can I help you today?",
  "tokens_used": 15,
  "latency_ms": 500
}
```

### System

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "agents": {
      "researcher": "running",
      "analyst": "stopped"
    }
  }
}
```

#### System Info
```http
GET /api/system/info
```

**Response:**
```json
{
  "version": "1.0.0",
  "python_version": "3.10.0",
  "platform": "linux",
  "cpu_count": 8,
  "memory_total_gb": 16,
  "memory_available_gb": 8,
  "disk_usage_percent": 45
}
```

#### Export Configuration
```http
GET /api/system/export
```

**Response:** (File download)
```json
{
  "projects": [],
  "workflows": [],
  "prompts": [],
  "config": {}
}
```

#### Import Configuration
```http
POST /api/system/import
```

**Request Body:** (Multipart form data with file)

## WebSocket Endpoints

### Real-time Process Status
```ws
ws://localhost:8002/ws/processes
```

**Messages:**
```json
{
  "type": "status_update",
  "data": {
    "name": "researcher",
    "status": "running",
    "cpu_percent": 3.2
  }
}
```

### Workflow Execution Stream
```ws
ws://localhost:8002/ws/workflows/{execution_id}
```

**Messages:**
```json
{
  "type": "node_started",
  "data": {
    "node_id": "node-1",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation failed |
| 500 | Internal Server Error |
| 503 | Service Unavailable - Service temporarily down |

## Rate Limiting

API requests are rate limited to:
- 100 requests per minute per IP
- 1000 requests per hour per IP

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110460
```

## CORS

CORS is enabled for development:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

## Examples

### cURL

```bash
# List projects
curl http://localhost:8002/api/projects

# Start an agent
curl -X POST http://localhost:8002/api/processes/start \
  -H "Content-Type: application/json" \
  -d '{"name": "researcher"}'

# Execute workflow
curl -X POST http://localhost:8002/api/workflows/workflow-1/execute \
  -H "Content-Type: application/json" \
  -d '{"input": {"user_request": "Research AI trends"}}'
```

### JavaScript (Fetch)

```javascript
// List projects
const response = await fetch('http://localhost:8002/api/projects');
const projects = await response.json();

// Start an agent
await fetch('http://localhost:8002/api/processes/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'researcher' })
});
```

### Python (Requests)

```python
import requests

# List projects
response = requests.get('http://localhost:8002/api/projects')
projects = response.json()

# Start an agent
response = requests.post(
    'http://localhost:8002/api/processes/start',
    json={'name': 'researcher'}
)
```