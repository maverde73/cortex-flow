# Cortex-Flow Documentation

**Welcome to Cortex-Flow** - A distributed multi-agent AI system using the Model Context Protocol (MCP), LangChain, LangGraph, and FastAPI.

---

## 📚 Documentation Index

### 🚀 Getting Started
Start here if you're new to Cortex-Flow.

- [**Installation Guide**](getting-started/installation.md) - Setup, dependencies, environment configuration
- [**Quick Start**](getting-started/quick-start.md) - Your first workflow in 5 minutes
- [**Configuration Guide**](getting-started/configuration.md) - Understanding .env and system settings

### 🏗️ Architecture
Understand how Cortex-Flow works under the hood.

- [**System Architecture Overview**](architecture/README.md) - Distributed multi-agent design
- [**Backend Design**](architecture/backend-design.md) - Microservices architecture blueprint
- [**Multi-Agent System**](architecture/multi-agent-system.md) - ReAct pattern and agent coordination
- [**Project Structure**](architecture/project-structure.md) - File organization and modules

### 🤖 Agents
Learn about the ReAct agents that power Cortex-Flow.

- [**Agents Overview**](agents/README.md) - Supervisor, Researcher, Analyst, Writer
- [**ReAct Pattern**](agents/react-pattern.md) - Reasoning-Action-Observation cycle
- [**Agent Management**](agents/agent-management.md) - Health checks, retries, service discovery
- [**Agent Factory**](agents/factory.md) - Dynamic agent instantiation

### 🔌 MCP Integration
Connect external tools and services via the Model Context Protocol.

- [**MCP Overview**](mcp/README.md) - What is MCP and why use it
- [**Getting Started with MCP**](mcp/getting-started.md) - First MCP server integration
- [**Protocol Implementation**](mcp/protocol-implementation.md) - Technical details and testing
- [**Manual Prompts**](mcp/manual-prompts.md) - Configuring prompts for servers without prompts/list
- [**Configuration Reference**](mcp/configuration.md) - All MCP environment variables
- [**Troubleshooting**](mcp/troubleshooting.md) - Common issues and solutions

### 🔄 Workflows
Build structured workflows with templates and conditional routing.

- [**Workflows Overview**](workflows/README.md) - Template-based vs ReAct execution
- [**Creating Templates**](workflows/01_creating_templates.md) - Define reusable workflow templates
- [**Conditional Routing**](workflows/02_conditional_routing.md) - Dynamic branching logic
- [**MCP Integration**](workflows/03_mcp_integration.md) - Using MCP tools in workflows
- [**Visual Diagrams**](workflows/04_visual_diagrams.md) - Visualize workflow execution
- [**Cookbook**](workflows/05_cookbook.md) - Example workflows and patterns
- [**Migration Guide**](workflows/06_migration_guide.md) - Hybrid ReAct/Workflow migration
- [**LangGraph Compatibility**](workflows/07_langgraph_compatibility.md) - ✨ **NEW v0.4.0** - Native LangGraph compilation

### 📚 Libraries
Extend workflows with custom Python libraries for any functionality.

- [**Libraries Overview**](libraries/README.md) - ✨ **NEW** - Custom Python library integration
- [**Creating Libraries**](libraries/creating-libraries.md) - Build custom libraries with decorators
- [**Using in Workflows**](libraries/using-in-workflows.md) - Integrate libraries in workflow nodes
- [**Security & Capabilities**](libraries/security.md) - Access control and sandboxing
- [**Built-in Libraries**](libraries/built-in-libraries.md) - REST API, Filesystem, and more

### 🌐 Web Application
Powerful visual interface for building and managing AI workflows.

- [**Web App Overview**](web-app/README.md) - ✨ **NEW** - Complete web application guide
- [**User Guide**](web-app/user-guide.md) - Comprehensive usage instructions
- [**Architecture**](web-app/architecture.md) - Frontend technical architecture
- [**API Reference**](web-app/api-reference.md) - Complete REST API documentation
- [**Process Management**](web-app/process-management.md) - Agent lifecycle control
- [**Troubleshooting**](web-app/troubleshooting.md) - Common issues and solutions

### 💬 Chatbot & API
Use Cortex-Flow as an OpenAI-compatible chatbot with conversation memory.

- [**Chatbot Overview**](chatbot/README.md) - Chatbot documentation index
- [**API Guide**](chatbot/api_guide.md) - OpenAI-compatible chat completions
- [**Implementation Summary**](chatbot/implementation_summary.md) - Technical implementation details
- [**Quick Start**](chatbot/api_guide.md#quick-start) - Get started in 5 minutes
- [**LangChain Integration**](chatbot/api_guide.md#langchain-integration) - Seamless LangChain compatibility

### 💻 Development
Contribute to Cortex-Flow or extend it with custom agents.

- [**Development Guide**](development/README.md) - Setup, testing, best practices
- [**Contributing**](development/contributing.md) - How to contribute to the project
- [**Testing**](development/testing.md) - Unit tests, integration tests, MCP tests
- [**Scripts**](development/scripts.md) - Utility scripts for development
- [**Working with Claude Code**](development/claude-code.md) - AI-assisted development guidelines

### 📖 Reference
Complete reference documentation for all configuration options.

- [**Multi-Project Configuration**](reference/multi-project-config.md) - JSON-based config system (NEW!)
- [**Environment Variables**](reference/environment-variables.md) - Complete .env reference
- [**Configuration API**](reference/configuration.md) - config.py and Pydantic settings
- [**REST API**](reference/api.md) - HTTP endpoints for agents
- [**CLI Tools**](reference/cli.md) - Command-line utilities

---

## 🎯 What to Read First

**New to Cortex-Flow?**
1. [Installation Guide](getting-started/installation.md)
2. [Quick Start](getting-started/quick-start.md)
3. [Web App Overview](web-app/README.md)

**Using the Web Interface?**
1. [Web App User Guide](web-app/user-guide.md)
2. [Process Management](web-app/process-management.md)
3. [Troubleshooting](web-app/troubleshooting.md)

**Want to add MCP tools?**
1. [MCP Overview](mcp/README.md)
2. [Getting Started with MCP](mcp/getting-started.md)
3. [Configuration Reference](mcp/configuration.md)

**Building custom workflows?**
1. [Workflows Overview](workflows/README.md)
2. [Creating Templates](workflows/01_creating_templates.md)
3. [Cookbook](workflows/05_cookbook.md)

**Using as a chatbot?**
1. [Chatbot Overview](chatbot/README.md)
2. [Quick Start Example](chatbot/api_guide.md#quick-start)
3. [LangChain Integration](chatbot/api_guide.md#langchain-integration)

**Extending the system?**
1. [Development Guide](development/README.md)
2. [System Architecture](architecture/backend-design.md)
3. [Agent Factory](agents/factory.md)

---

## 📦 Additional Resources

- [**Release Notes**](RELEASE_NOTES.md) - Version history and changelog
- [**Project Overview**](../README.md) - Main project README
- [**Migration Guides**](DOCS_MIGRATION_SUMMARY.md) - Documentation migration summary

---

## 🔍 Quick Navigation

| Topic | Beginner | Intermediate | Advanced |
|-------|----------|--------------|----------|
| **Setup** | [Installation](getting-started/installation.md) | [Configuration](getting-started/configuration.md) | [Environment Variables](reference/environment-variables.md) |
| **Web App** | [Web App Overview](web-app/README.md) | [User Guide](web-app/user-guide.md) | [Architecture](web-app/architecture.md) |
| **Agents** | [Agents Overview](agents/README.md) | [ReAct Pattern](agents/react-pattern.md) | [Agent Management](agents/agent-management.md) |
| **MCP** | [MCP Overview](mcp/README.md) | [Getting Started](mcp/getting-started.md) | [Protocol Implementation](mcp/protocol-implementation.md) |
| **Workflows** | [Workflows Overview](workflows/README.md) | [Creating Templates](workflows/01_creating_templates.md) | [Conditional Routing](workflows/02_conditional_routing.md) |
| **API** | [API Reference](web-app/api-reference.md) | [Chatbot API](chatbot/api_guide.md) | [Process Management](web-app/process-management.md) |
| **Development** | [Development Guide](development/README.md) | [Testing](development/testing.md) | [Contributing](development/contributing.md) |

---

**Last Updated**: 2025-10-08
**Documentation Version**: 1.1
**Cortex-Flow Version**: 1.0.0
