# Cortex Flow

A distributed multi-agent AI system with a powerful web-based editor for building and managing AI workflows using the Model Context Protocol (MCP).

## 🌟 Key Features

### Web Application
- **🎨 Visual Workflow Editor**: Drag-and-drop interface for building complex AI workflows
- **🚀 Real-time Process Management**: Start, stop, and monitor agents with live status updates
- **🧪 Testing & Debugging**: Interactive playground for testing agents and workflows
- **📊 Project Management**: Multi-project support with isolated configurations
- **🔌 MCP Integration**: Seamlessly connect external tools and services

### Multi-Agent System
- **🤖 Specialized Agents**: Supervisor, Researcher, Analyst, Writer working in coordination
- **🔄 ReAct Pattern**: Transparent reasoning with Thought→Action→Observation cycles
- **📈 LangGraph Orchestration**: Stateful workflow graphs with persistent checkpointing
- **🌐 Distributed Architecture**: HTTP-based MCP protocol for inter-agent messaging
- **⚡ Async Performance**: Non-blocking I/O throughout the stack
- **🔍 Full Observability**: LangSmith integration for distributed tracing

### Workflow System
- **🔗 Composable Workflows**: Workflows can call other workflows as building blocks
- **♻️ Reusable Components**: Create modular workflow libraries
- **🎯 Template-Based**: JSON templates for predefined execution paths
- **🔀 Conditional Routing**: Dynamic branching based on conditions
- **⚡ Parallel Execution**: Run multiple nodes or workflows simultaneously
- **🛡️ Safety Controls**: Built-in recursion limits and circular dependency detection

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Virtual environment tool (venv, conda, etc.)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/cortex-flow.git
cd cortex-flow
```

2. **Backend Setup**
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY (optional)
# - Other LLM provider keys as needed
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm run build
cd ..
```

4. **Start the Application**
```bash
# Start the editor server (includes all services)
python servers/editor_server.py

# The web app will be available at http://localhost:8002
```

5. **Start Individual Agents** (via Web UI or CLI)
```bash
# Via Web UI: Click on agent badges in the status bar

# Or via CLI:
python servers/supervisor_server.py  # Port 8000
python servers/researcher_server.py  # Port 8001
python servers/analyst_server.py     # Port 8003
python servers/writer_server.py      # Port 8004
```

## 📸 Web Application Overview

The Cortex Flow web application provides a comprehensive interface for managing your AI workflows:

### Dashboard
- System overview with real-time metrics
- Quick access to recent projects and workflows
- Agent status monitoring

### Projects
- Create and manage multiple projects
- Isolated configurations per project
- Import/export project templates

### Workflow Editor
- Visual workflow designer with drag-and-drop
- Node-based workflow creation
- Real-time validation and testing
- Natural language to workflow conversion

### Agent Playground
- Test individual agents with custom inputs
- View detailed execution traces
- Debug agent interactions

### Process Management
- Real-time agent status monitoring
- One-click start/stop controls
- CPU and memory usage tracking
- Log viewing and debugging

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Web Application (React)           │
│  - Visual Editor - Process Manager          │
│  - Testing Tools - Project Management       │
└─────────────────┬───────────────────────────┘
                  │ REST API
                  ▼
┌─────────────────────────────────────────────┐
│         Editor Server (FastAPI)             │
│  - API Gateway    - Workflow Engine         │
│  - AI Service     - Process Management      │
└─────────────────┬───────────────────────────┘
                  │ MCP Protocol
    ┌─────────────┴──────────────┬────────────┐
    ▼                            ▼            ▼
┌──────────┐            ┌──────────┐  ┌──────────┐
│Supervisor│            │Researcher│  │ Analyst  │
│  Agent   │ ◄────────► │  Agent   │  │  Agent   │
└──────────┘            └──────────┘  └──────────┘
                               ▲            ▲
                               └────┬───────┘
                                    ▼
                              ┌──────────┐
                              │  Writer  │
                              │  Agent   │
                              └──────────┘
```

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Getting Started Guide](docs/getting-started/README.md)** - Installation and setup
- **[Web Application Guide](docs/web-app/README.md)** - Using the web interface
- **[Architecture Overview](docs/architecture/README.md)** - System design and patterns
- **[Agent Development](docs/agents/README.md)** - Creating custom agents
- **[Workflow System](docs/workflows/README.md)** - Building composable workflows
- **[MCP Integration](docs/mcp/README.md)** - Connecting external tools
- **[API Reference](docs/api/README.md)** - Complete API documentation

## 🧪 Testing

### Run Tests
```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend
npm test
```

### Test a Workflow
1. Open http://localhost:8002 in your browser
2. Navigate to **Testing** → **Workflow Debugger**
3. Select a workflow and provide input
4. Click **Execute** to see step-by-step execution

### Test Composable Workflows
```python
# Example: Test a workflow that calls other workflows
python -m pytest tests/test_composable_workflows.py -v

# Or test directly via API
curl -X POST http://localhost:8002/api/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_name": "research_and_report",
    "params": {
      "topic": "AI trends 2024"
    }
  }'
```

## 🛠️ Development

### Project Structure
```
cortex-flow/
├── frontend/           # React TypeScript web application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API services
│   │   └── types/      # TypeScript types
├── agents/            # LangGraph agent definitions
├── servers/           # FastAPI server implementations
├── tools/             # Agent tools and integrations
├── schemas/           # Pydantic models and schemas
├── workflows/         # Workflow engine and templates
├── utils/             # Utility functions and helpers
├── projects/          # Project configurations and data
└── docs/              # Documentation
```

### Adding a New Agent
1. Create agent definition in `agents/your_agent.py`
2. Create server in `servers/your_agent_server.py`
3. Add to ProcessManager config in `utils/process_manager.py`
4. Update documentation

### Contributing
Please read our [Contributing Guide](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
# LLM Providers
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here

# Optional Providers
GOOGLE_API_KEY=your-key-here
GROQ_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here

# LangSmith Tracing (optional)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key-here
LANGCHAIN_PROJECT=cortex-flow

# MCP Servers (optional)
MCP_SERVERS='{"filesystem": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}}'
```

### Port Configuration
Default ports for services:
- Editor Server: 8002
- Supervisor Agent: 8000
- Researcher Agent: 8001
- Analyst Agent: 8003
- Writer Agent: 8004

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/cortex-flow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/cortex-flow/discussions)
- **Documentation**: [Full Documentation](docs/README.md)

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) & [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/) & [TypeScript](https://www.typescriptlang.org/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [TailwindCSS](https://tailwindcss.com/)

---

**Cortex Flow** - Empowering AI workflows through intelligent agent orchestration 🚀