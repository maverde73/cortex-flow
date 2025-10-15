"""
Editor Server API

FastAPI server for the Cortex Flow Web Editor.
Provides REST API for project management, workflow editing, prompt management, and MCP configuration.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Add project root to path for DSL imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflows.dsl.parser import WorkflowDSLParser
from workflows.dsl.generator import WorkflowDSLGenerator
from schemas.workflow_schemas import WorkflowTemplate
from servers.ai_service import AIService
from utils.model_registry import MODEL_REGISTRY
from utils.process_manager import ProcessManager, ProcessInfo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Cortex Flow Editor API",
    description="REST API for the Cortex Flow Web Editor",
    version="1.0.0"
)

# CORS middleware for web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ],  # Vite dev server (multiple ports)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Configuration
# ============================================================================

PROJECTS_DIR = Path(__file__).parent.parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

MCP_LIBRARY_DIR = Path(__file__).parent.parent / "mcp_library"
MCP_LIBRARY_DIR.mkdir(exist_ok=True)

# Initialize Process Manager
PROJECT_ROOT = Path(__file__).parent.parent
process_manager = ProcessManager(PROJECT_ROOT)


# ============================================================================
# Pydantic Models
# ============================================================================

class ProjectInfo(BaseModel):
    """Project metadata."""
    name: str
    version: str = "1.0.0"
    description: str = ""
    active: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ProjectCreate(BaseModel):
    """Data for creating a new project."""
    name: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    description: str = ""
    template: Optional[str] = None  # "blank", "default", or project name


class ProjectUpdate(BaseModel):
    """Data for updating project."""
    description: Optional[str] = None
    active: Optional[bool] = None


class AgentsConfig(BaseModel):
    """Agent configuration."""
    config: Dict[str, Any]


class ReActConfig(BaseModel):
    """ReAct configuration."""
    config: Dict[str, Any]


class MCPConfig(BaseModel):
    """MCP configuration."""
    config: Dict[str, Any]


class PromptData(BaseModel):
    """Prompt content."""
    content: str


class WorkflowData(BaseModel):
    """Workflow JSON data."""
    workflow: Dict[str, Any]


class DslConvertRequest(BaseModel):
    """Request to convert JSON workflow to DSL."""
    workflow: Dict[str, Any]
    format: str = "yaml"  # "yaml" or "python"


class DslConvertResponse(BaseModel):
    """Response with DSL content."""
    dsl: str
    format: str


class DslParseRequest(BaseModel):
    """Request to parse DSL to JSON workflow."""
    dsl: str
    format: str = "yaml"  # "yaml" or "python"


class DslParseResponse(BaseModel):
    """Response with parsed workflow JSON."""
    workflow: Dict[str, Any]


class NaturalLanguageConvertRequest(BaseModel):
    """Request to convert workflow to natural language."""
    workflow: Dict[str, Any]
    project_name: str = "default"
    language: str = "it"  # "it" (Italian), "en" (English), etc.


class NaturalLanguageConvertResponse(BaseModel):
    """Response with natural language description."""
    prompt: str
    language: str


class NaturalLanguageParseRequest(BaseModel):
    """Request to parse natural language to workflow."""
    prompt: str
    project_name: str = "default"
    language: str = "it"


class NaturalLanguageParseResponse(BaseModel):
    """Response with parsed workflow JSON."""
    workflow: Dict[str, Any]


class ChatMessage(BaseModel):
    """Chat message in conversation history."""
    role: str  # "user" or "assistant"
    content: str


class WorkflowChatRequest(BaseModel):
    """Request to modify workflow via chat conversation."""
    workflow: Dict[str, Any]
    message: str
    history: List[ChatMessage] = []
    language: str = "it"


class WorkflowChatResponse(BaseModel):
    """Response with modified workflow and explanation."""
    workflow: Dict[str, Any]
    explanation: str
    changes: List[str]


class WorkflowValidationRequest(BaseModel):
    """Workflow validation request."""
    workflow: Dict[str, Any]


class WorkflowGenerateRequest(BaseModel):
    """AI workflow generation request."""
    description: str = Field(..., min_length=10, max_length=5000)
    project_name: str = "default"
    agent_types: Optional[List[str]] = None
    mcp_servers: Optional[List[str]] = None


class MCPTestRequest(BaseModel):
    """MCP server connection test request."""
    server_config: Dict[str, Any]


# ============================================================================
# Utility Functions
# ============================================================================

def get_project_dir(project_name: str) -> Path:
    """Get project directory path."""
    project_dir = PROJECTS_DIR / project_name
    if not project_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_name}' not found"
        )
    return project_dir


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse JSON file."""
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path.name}"
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in {file_path.name}: {str(e)}"
        )


def write_json_file(file_path: Path, data: Dict[str, Any]):
    """Write JSON file with pretty formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_projects() -> List[ProjectInfo]:
    """List all projects."""
    projects = []

    for project_dir in PROJECTS_DIR.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith('.'):
            project_file = project_dir / "project.json"

            if project_file.exists():
                try:
                    data = read_json_file(project_file)
                    projects.append(ProjectInfo(**data))
                except Exception as e:
                    logger.error(f"Error loading project {project_dir.name}: {e}")

    return projects


def read_text_file(file_path: Path) -> str:
    """Read text file."""
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path.name}"
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reading {file_path.name}: {str(e)}"
        )


def write_text_file(file_path: Path, content: str):
    """Write text file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


# ============================================================================
# API Endpoints - Root
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """API information."""
    return {
        "service": "Cortex Flow Editor API",
        "version": "1.0.0",
        "description": "REST API for managing Cortex Flow projects",
        "docs": "/docs"
    }


@app.get("/health", tags=["monitoring"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "editor-server",
        "version": "1.0.0",
        "projects_dir": str(PROJECTS_DIR.absolute())
    }


# ============================================================================
# API Endpoints - Projects
# ============================================================================

@app.get("/api/projects", response_model=List[ProjectInfo], tags=["projects"])
async def get_projects():
    """List all projects."""
    return list_projects()


@app.get("/api/projects/{project_name}", response_model=ProjectInfo, tags=["projects"])
async def get_project(project_name: str):
    """Get project details."""
    project_dir = get_project_dir(project_name)
    project_file = project_dir / "project.json"

    data = read_json_file(project_file)
    return ProjectInfo(**data)


@app.post("/api/projects", response_model=ProjectInfo, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project(project: ProjectCreate):
    """Create a new project."""
    project_dir = PROJECTS_DIR / project.name

    # Check if project already exists
    if project_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{project.name}' already exists"
        )

    # Create project structure
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "workflows").mkdir(exist_ok=True)
    (project_dir / "prompts").mkdir(exist_ok=True)
    (project_dir / "prompts" / "agents").mkdir(exist_ok=True)
    (project_dir / "prompts" / "mcp").mkdir(exist_ok=True)

    # Create project.json
    project_data = ProjectInfo(
        name=project.name,
        description=project.description,
        active=False,
        created_at=datetime.now().isoformat()
    )

    write_json_file(project_dir / "project.json", project_data.model_dump())

    # Create default agents.json
    default_agents = {
        "agents": {
            "researcher": {
                "enabled": True,
                "llm_provider": "openai",
                "model": "gpt-4"
            },
            "analyst": {
                "enabled": True,
                "llm_provider": "openai",
                "model": "gpt-4"
            },
            "writer": {
                "enabled": True,
                "llm_provider": "openai",
                "model": "gpt-4"
            }
        }
    }
    write_json_file(project_dir / "agents.json", default_agents)

    # Create default react.json
    default_react = {
        "max_iterations": 25,
        "timeout_seconds": 300,
        "max_consecutive_errors": 3,
        "enable_verbose_logging": True,
        "log_thoughts": True,
        "log_actions": True,
        "log_observations": True,
        "allow_delegation": True,
        "enable_reflection": False
    }
    write_json_file(project_dir / "react.json", default_react)

    # Create default mcp.json
    default_mcp = {
        "enabled": True,
        "client": {
            "retry_attempts": 3,
            "timeout": 30.0,
            "health_check_interval": 60.0
        },
        "servers": {},
        "tools_enable_logging": True,
        "tools_enable_reflection": False,
        "tools_timeout_multiplier": 1.5
    }
    write_json_file(project_dir / "mcp.json", default_mcp)

    logger.info(f"Created project: {project.name}")

    return project_data


@app.put("/api/projects/{project_name}", response_model=ProjectInfo, tags=["projects"])
async def update_project(project_name: str, update: ProjectUpdate):
    """Update project metadata."""
    project_dir = get_project_dir(project_name)
    project_file = project_dir / "project.json"

    data = read_json_file(project_file)
    project_info = ProjectInfo(**data)

    # Update fields
    if update.description is not None:
        project_info.description = update.description
    if update.active is not None:
        project_info.active = update.active

        # If setting active, deactivate others
        if update.active:
            for other_project in list_projects():
                if other_project.name != project_name and other_project.active:
                    other_dir = PROJECTS_DIR / other_project.name
                    other_file = other_dir / "project.json"
                    other_data = read_json_file(other_file)
                    other_data["active"] = False
                    write_json_file(other_file, other_data)

    write_json_file(project_file, project_info.model_dump())

    logger.info(f"Updated project: {project_name}")

    return project_info


@app.delete("/api/projects/{project_name}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
async def delete_project(project_name: str):
    """Delete a project."""
    project_dir = get_project_dir(project_name)

    # Safety check: don't delete if active
    project_file = project_dir / "project.json"
    data = read_json_file(project_file)
    if data.get("active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete active project. Deactivate it first."
        )

    # Delete directory
    import shutil
    shutil.rmtree(project_dir)

    logger.info(f"Deleted project: {project_name}")


@app.post("/api/projects/{project_name}/activate", response_model=ProjectInfo, tags=["projects"])
async def activate_project(project_name: str):
    """Set project as active."""
    update = ProjectUpdate(active=True)
    return await update_project(project_name, update)


# ============================================================================
# API Endpoints - Agents & ReAct
# ============================================================================

@app.get("/api/projects/{project_name}/agents", tags=["agents"])
async def get_agents_config(project_name: str):
    """Get agents configuration."""
    project_dir = get_project_dir(project_name)
    agents_file = project_dir / "agents.json"

    return read_json_file(agents_file)


@app.put("/api/projects/{project_name}/agents", tags=["agents"])
async def update_agents_config(project_name: str, config: AgentsConfig):
    """Update agents configuration."""
    project_dir = get_project_dir(project_name)
    agents_file = project_dir / "agents.json"

    write_json_file(agents_file, config.config)

    logger.info(f"Updated agents config for project: {project_name}")

    return {"status": "success", "message": "Agents configuration updated"}


@app.get("/api/projects/{project_name}/react", tags=["agents"])
async def get_react_config(project_name: str):
    """Get ReAct configuration."""
    project_dir = get_project_dir(project_name)
    react_file = project_dir / "react.json"

    return read_json_file(react_file)


@app.put("/api/projects/{project_name}/react", tags=["agents"])
async def update_react_config(project_name: str, config: ReActConfig):
    """Update ReAct configuration."""
    project_dir = get_project_dir(project_name)
    react_file = project_dir / "react.json"

    write_json_file(react_file, config.config)

    logger.info(f"Updated ReAct config for project: {project_name}")

    return {"status": "success", "message": "ReAct configuration updated"}


# ============================================================================
# API Endpoints - Prompts
# ============================================================================

@app.get("/api/projects/{project_name}/prompts", tags=["prompts"])
async def list_prompts(project_name: str):
    """List all prompts in project."""
    project_dir = get_project_dir(project_name)
    prompts_dir = project_dir / "prompts"

    prompts = {
        "system": None,
        "agents": {},
        "mcp": {}
    }

    # System prompt
    system_file = prompts_dir / "system.txt"
    if system_file.exists():
        prompts["system"] = system_file.name

    # Agent prompts
    agents_dir = prompts_dir / "agents"
    if agents_dir.exists():
        for prompt_file in agents_dir.glob("*.txt"):
            agent_name = prompt_file.stem
            prompts["agents"][agent_name] = prompt_file.name

    # MCP prompts
    mcp_dir = prompts_dir / "mcp"
    if mcp_dir.exists():
        for prompt_file in mcp_dir.glob("*.txt"):
            server_name = prompt_file.stem
            prompts["mcp"][server_name] = prompt_file.name

    return prompts


@app.get("/api/projects/{project_name}/prompts/system", tags=["prompts"])
async def get_system_prompt(project_name: str):
    """Get system prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "system.txt"

    if not prompt_file.exists():
        return {"content": ""}

    content = read_text_file(prompt_file)
    return {"content": content}


@app.put("/api/projects/{project_name}/prompts/system", tags=["prompts"])
async def update_system_prompt(project_name: str, data: PromptData):
    """Update system prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "system.txt"

    write_text_file(prompt_file, data.content)

    logger.info(f"Updated system prompt for project: {project_name}")

    return {"status": "success", "message": "System prompt updated"}


@app.get("/api/projects/{project_name}/prompts/agents/{agent_name}", tags=["prompts"])
async def get_agent_prompt(project_name: str, agent_name: str):
    """Get agent prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "agents" / f"{agent_name}.txt"

    if not prompt_file.exists():
        return {"content": ""}

    content = read_text_file(prompt_file)
    return {"content": content}


@app.put("/api/projects/{project_name}/prompts/agents/{agent_name}", tags=["prompts"])
async def update_agent_prompt(project_name: str, agent_name: str, data: PromptData):
    """Update agent prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "agents" / f"{agent_name}.txt"

    write_text_file(prompt_file, data.content)

    logger.info(f"Updated agent prompt for {agent_name} in project: {project_name}")

    return {"status": "success", "message": f"Agent prompt for {agent_name} updated"}


@app.get("/api/projects/{project_name}/prompts/mcp/{server_name}", tags=["prompts"])
async def get_mcp_prompt(project_name: str, server_name: str):
    """Get MCP server prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "mcp" / f"{server_name}.txt"

    if not prompt_file.exists():
        return {"content": ""}

    content = read_text_file(prompt_file)
    return {"content": content}


@app.put("/api/projects/{project_name}/prompts/mcp/{server_name}", tags=["prompts"])
async def update_mcp_prompt(project_name: str, server_name: str, data: PromptData):
    """Update MCP server prompt."""
    project_dir = get_project_dir(project_name)
    prompt_file = project_dir / "prompts" / "mcp" / f"{server_name}.txt"

    write_text_file(prompt_file, data.content)

    logger.info(f"Updated MCP prompt for {server_name} in project: {project_name}")

    return {"status": "success", "message": f"MCP prompt for {server_name} updated"}


# ============================================================================
# API Endpoints - Workflows
# ============================================================================

@app.get("/api/projects/{project_name}/workflows", tags=["workflows"])
async def list_workflows(project_name: str):
    """List all workflows in project."""
    project_dir = get_project_dir(project_name)
    workflows_dir = project_dir / "workflows"

    workflows = []

    if workflows_dir.exists():
        for workflow_file in workflows_dir.glob("*.json"):
            try:
                data = read_json_file(workflow_file)
                workflows.append({
                    "name": workflow_file.stem,
                    "description": data.get("description", ""),
                    "version": data.get("version", "1.0.0"),
                    "agents": list(data.get("agents", {}).keys())
                })
            except Exception as e:
                logger.error(f"Error loading workflow {workflow_file.name}: {e}")

    return workflows


@app.get("/api/projects/{project_name}/workflows/{workflow_name}", tags=["workflows"])
async def get_workflow(project_name: str, workflow_name: str):
    """Get workflow details."""
    project_dir = get_project_dir(project_name)
    workflow_file = project_dir / "workflows" / f"{workflow_name}.json"

    return read_json_file(workflow_file)


@app.post("/api/projects/{project_name}/workflows/{workflow_name}",
          status_code=status.HTTP_201_CREATED, tags=["workflows"])
async def create_workflow(project_name: str, workflow_name: str, data: WorkflowData):
    """Create a new workflow."""
    project_dir = get_project_dir(project_name)
    workflow_file = project_dir / "workflows" / f"{workflow_name}.json"

    if workflow_file.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Workflow '{workflow_name}' already exists"
        )

    write_json_file(workflow_file, data.workflow)

    logger.info(f"Created workflow {workflow_name} in project: {project_name}")

    return {"status": "success", "message": f"Workflow {workflow_name} created"}


@app.put("/api/projects/{project_name}/workflows/{workflow_name}", tags=["workflows"])
async def update_workflow(project_name: str, workflow_name: str, data: WorkflowData):
    """Update workflow."""
    project_dir = get_project_dir(project_name)
    workflow_file = project_dir / "workflows" / f"{workflow_name}.json"

    write_json_file(workflow_file, data.workflow)

    logger.info(f"Updated workflow {workflow_name} in project: {project_name}")

    return {"status": "success", "message": f"Workflow {workflow_name} updated"}


@app.delete("/api/projects/{project_name}/workflows/{workflow_name}",
            status_code=status.HTTP_204_NO_CONTENT, tags=["workflows"])
async def delete_workflow(project_name: str, workflow_name: str):
    """Delete a workflow."""
    project_dir = get_project_dir(project_name)
    workflow_file = project_dir / "workflows" / f"{workflow_name}.json"

    if not workflow_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{workflow_name}' not found"
        )

    workflow_file.unlink()

    logger.info(f"Deleted workflow {workflow_name} from project: {project_name}")


@app.post("/api/projects/{project_name}/workflows/validate", tags=["workflows"])
async def validate_workflow(project_name: str, data: WorkflowValidationRequest):
    """Validate workflow JSON structure."""
    # Basic validation
    workflow = data.workflow
    errors = []

    # Check required fields
    required_fields = ["name", "description", "version", "agents"]
    for field in required_fields:
        if field not in workflow:
            errors.append(f"Missing required field: {field}")

    # Check agents structure
    if "agents" in workflow:
        agents = workflow["agents"]
        if not isinstance(agents, dict):
            errors.append("'agents' must be a dictionary")
        else:
            for agent_name, agent_config in agents.items():
                if "type" not in agent_config:
                    errors.append(f"Agent '{agent_name}' missing 'type' field")
                if "steps" not in agent_config:
                    errors.append(f"Agent '{agent_name}' missing 'steps' field")

    # Check routing if present
    if "routing" in workflow:
        routing = workflow["routing"]
        if not isinstance(routing, dict):
            errors.append("'routing' must be a dictionary")

    if errors:
        return {
            "valid": False,
            "errors": errors
        }

    return {
        "valid": True,
        "message": "Workflow structure is valid"
    }


@app.post("/api/projects/{project_name}/workflows/{workflow_name}/preview", tags=["workflows"])
async def preview_workflow(project_name: str, workflow_name: str):
    """Preview workflow execution (dry-run)."""
    project_dir = get_project_dir(project_name)
    workflow_file = project_dir / "workflows" / f"{workflow_name}.json"

    workflow_data = read_json_file(workflow_file)

    # Generate execution preview
    preview = {
        "workflow_name": workflow_name,
        "agents": [],
        "estimated_steps": 0
    }

    if "agents" in workflow_data:
        for agent_name, agent_config in workflow_data["agents"].items():
            steps = agent_config.get("steps", [])
            preview["agents"].append({
                "name": agent_name,
                "type": agent_config.get("type", "unknown"),
                "steps_count": len(steps),
                "steps": [step.get("action", "unknown") for step in steps]
            })
            preview["estimated_steps"] += len(steps)

    preview["routing"] = workflow_data.get("routing", {})

    return preview


@app.post("/api/workflows/convert-to-dsl", tags=["workflows"])
async def convert_workflow_to_dsl(request: DslConvertRequest) -> DslConvertResponse:
    """
    Convert JSON workflow to DSL format (YAML or Python).

    This endpoint takes a WorkflowTemplate JSON and converts it to human-readable DSL.
    """
    try:
        # Convert dict to WorkflowTemplate
        template = WorkflowTemplate(**request.workflow)

        # Generate DSL
        generator = WorkflowDSLGenerator()
        dsl_content = generator.generate(template, format=request.format)

        logger.info(f"Converted workflow '{template.name}' to {request.format.upper()} DSL")

        return DslConvertResponse(
            dsl=dsl_content,
            format=request.format
        )

    except Exception as e:
        logger.error(f"DSL conversion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to convert workflow to DSL: {str(e)}"
        )


@app.post("/api/workflows/parse-dsl", tags=["workflows"])
async def parse_dsl_to_workflow(request: DslParseRequest) -> DslParseResponse:
    """
    Parse DSL (YAML or Python) to JSON workflow.

    This endpoint takes DSL content and converts it to WorkflowTemplate JSON.
    """
    try:
        # Parse DSL
        parser = WorkflowDSLParser()
        template = parser.parse_string(request.dsl, format=request.format)

        # Convert to dict
        workflow_dict = template.model_dump(exclude_none=True)

        logger.info(f"Parsed {request.format.upper()} DSL to workflow '{template.name}'")

        return DslParseResponse(
            workflow=workflow_dict
        )

    except Exception as e:
        logger.error(f"DSL parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse DSL: {str(e)}"
        )


@app.post("/api/workflows/to-natural-language", tags=["workflows", "ai"])
async def convert_workflow_to_natural_language(
    request: NaturalLanguageConvertRequest
) -> NaturalLanguageConvertResponse:
    """
    Convert workflow JSON to natural language description.

    Uses AI to generate a human-readable description of the workflow
    in the specified language. Uses the web_app_model configured for the project.
    """
    try:
        # Create AIService with project-specific web_app_model
        ai_service = AIService(project_name=request.project_name, use_web_app_model=True)

        prompt = await ai_service.workflow_to_natural_language(
            workflow=request.workflow,
            language=request.language
        )

        logger.info(f"Converted workflow to natural language ({request.language}) using {ai_service.provider}/{ai_service.model}")

        return NaturalLanguageConvertResponse(
            prompt=prompt,
            language=request.language
        )

    except Exception as e:
        logger.error(f"Natural language conversion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert workflow to natural language: {str(e)}"
        )


@app.post("/api/workflows/from-natural-language", tags=["workflows", "ai"])
async def parse_natural_language_to_workflow(
    request: NaturalLanguageParseRequest
) -> NaturalLanguageParseResponse:
    """
    Parse natural language description to workflow JSON.

    Uses AI to convert a human-readable description into a valid
    WorkflowTemplate JSON structure. Uses the web_app_model configured for the project.
    """
    try:
        # Create AIService with project-specific web_app_model
        ai_service = AIService(project_name=request.project_name, use_web_app_model=True)

        workflow = await ai_service.natural_language_to_workflow(
            description=request.prompt,
            language=request.language
        )

        # Validate the generated workflow
        try:
            template = WorkflowTemplate(**workflow)
            # Use validated workflow
            workflow = template.model_dump(exclude_none=True)
        except Exception as validation_error:
            logger.warning(f"Generated workflow failed validation: {validation_error}")
            # Return anyway but log the issue
            # In production, might want to retry with AI

        logger.info(f"Parsed natural language to workflow '{workflow.get('name', 'unknown')}' using {ai_service.provider}/{ai_service.model}")

        return NaturalLanguageParseResponse(
            workflow=workflow
        )

    except ValueError as e:
        # AI generated invalid JSON
        logger.error(f"AI generated invalid response: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Natural language parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse natural language to workflow: {str(e)}"
        )


@app.post("/api/workflows/chat-modify", tags=["workflows", "ai"])
async def chat_modify_workflow(
    request: WorkflowChatRequest
) -> WorkflowChatResponse:
    """
    Modify workflow through conversational AI chat.

    Allows users to make incremental changes to a workflow by chatting
    with an AI assistant in natural language (Italian by default).

    Example requests:
    - "aggiungi un timeout di 10 minuti al nodo di ricerca"
    - "se la query fallisce, riprova massimo 3 volte"
    - "esegui ricerca e analisi in parallelo"
    """
    try:
        # Convert ChatMessage models to dicts for AI service
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]

        result = await ai_service.chat_modify_workflow(
            workflow=request.workflow,
            user_message=request.message,
            conversation_history=history,
            language=request.language
        )

        # Validate the modified workflow
        try:
            template = WorkflowTemplate(**result["workflow"])
            # Use validated workflow
            validated_workflow = template.model_dump(exclude_none=True)
            result["workflow"] = validated_workflow
        except Exception as validation_error:
            logger.warning(f"Modified workflow failed validation: {validation_error}")
            # Return anyway but log the issue
            # The frontend can show a warning to the user

        logger.info(f"Chat modified workflow: {len(result['changes'])} changes made")

        return WorkflowChatResponse(
            workflow=result["workflow"],
            explanation=result["explanation"],
            changes=result["changes"]
        )

    except ValueError as e:
        # AI generated invalid JSON
        logger.error(f"AI chat generated invalid response: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Chat workflow modification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to modify workflow via chat: {str(e)}"
        )


# ============================================================================
# API Endpoints - MCP
# ============================================================================

@app.get("/api/mcp/registry", tags=["mcp"])
async def browse_mcp_registry():
    """Browse MCP Registry (simplified mock)."""
    # In a real implementation, this would fetch from:
    # https://github.com/modelcontextprotocol/servers or MCP API

    # For now, return a mock list of common MCP servers
    servers = [
        {
            "id": "filesystem",
            "name": "Filesystem MCP",
            "description": "Access and manipulate local files and directories",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem"
        },
        {
            "id": "github",
            "name": "GitHub MCP",
            "description": "Interact with GitHub repositories, issues, and pull requests",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/github"
        },
        {
            "id": "postgres",
            "name": "PostgreSQL MCP",
            "description": "Query and manage PostgreSQL databases",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres"
        },
        {
            "id": "puppeteer",
            "name": "Puppeteer MCP",
            "description": "Browser automation and web scraping",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer"
        }
    ]

    return {"servers": servers}


@app.get("/api/mcp/registry/{server_id}", tags=["mcp"])
async def get_mcp_server_details(server_id: str):
    """Get MCP server details from registry."""
    # Mock implementation - in production, fetch from real registry
    servers = {
        "filesystem": {
            "id": "filesystem",
            "name": "Filesystem MCP",
            "description": "Access and manipulate local files and directories",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
            "tools": ["read_file", "write_file", "list_directory", "create_directory"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "root_path": {"type": "string", "description": "Root directory path"}
                },
                "required": ["root_path"]
            }
        },
        "github": {
            "id": "github",
            "name": "GitHub MCP",
            "description": "Interact with GitHub repositories",
            "repository": "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
            "tools": ["search_repositories", "get_file_contents", "create_issue", "list_commits"],
            "config_schema": {
                "type": "object",
                "properties": {
                    "token": {"type": "string", "description": "GitHub personal access token"}
                },
                "required": ["token"]
            }
        }
    }

    if server_id not in servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found in registry"
        )

    return servers[server_id]


@app.get("/api/projects/{project_name}/mcp", tags=["mcp"])
async def get_mcp_config(project_name: str):
    """Get MCP configuration for project."""
    project_dir = get_project_dir(project_name)
    mcp_file = project_dir / "mcp.json"

    return read_json_file(mcp_file)


@app.put("/api/projects/{project_name}/mcp", tags=["mcp"])
async def update_mcp_config(project_name: str, config: MCPConfig):
    """Update MCP configuration for project."""
    project_dir = get_project_dir(project_name)
    mcp_file = project_dir / "mcp.json"

    write_json_file(mcp_file, config.config)

    logger.info(f"Updated MCP config for project: {project_name}")

    return {"status": "success", "message": "MCP configuration updated"}


# ============================================================================
# API Endpoints - MCP Testing
# ============================================================================

class MCPTestConnectionRequest(BaseModel):
    """Request to test MCP connection."""
    server_config: Dict[str, Any]


class MCPTestActionRequest(BaseModel):
    """Request for MCP test actions (resources, tools, prompts)."""
    server_config: Dict[str, Any]
    action: str  # "list", "read", "call", "get", etc.
    params: Optional[Dict[str, Any]] = None


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/connection", tags=["mcp"])
async def test_mcp_connection(
    project_name: str,
    server_name: str,
    request: MCPTestConnectionRequest
):
    """
    Test MCP server connection and initialize session.

    Returns server info, capabilities, and session ID for stateful servers.
    """
    try:
        from utils.mcp_tester import MCPServerTester

        # Create tester instance
        tester = MCPServerTester(request.server_config)

        # Test connection
        result = await tester.test_connection()

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Connection test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Connection test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/resources", tags=["mcp"])
async def test_mcp_resources(
    project_name: str,
    server_name: str,
    request: MCPTestActionRequest
):
    """
    Test MCP resources operations (list, read, templates).

    Actions:
    - list: List all resources
    - read: Read a specific resource (requires params: {"uri": "..."})
    - templates: List resource templates
    """
    try:
        from utils.mcp_tester import MCPServerTester

        tester = MCPServerTester(request.server_config)

        # Route to appropriate method based on action
        if request.action == "list":
            result = await tester.list_resources()
        elif request.action == "read":
            if not request.params or "uri" not in request.params:
                raise ValueError("Missing 'uri' parameter for read action")
            result = await tester.read_resource(request.params["uri"])
        elif request.action == "templates":
            result = await tester.list_resource_templates()
        else:
            raise ValueError(f"Unknown action: {request.action}")

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Resources test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Resources test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/tools", tags=["mcp"])
async def test_mcp_tools(
    project_name: str,
    server_name: str,
    request: MCPTestActionRequest
):
    """
    Test MCP tools operations (list, call).

    Actions:
    - list: List all tools
    - call: Call a tool (requires params: {"tool_name": "...", "arguments": {...}})
    """
    try:
        from utils.mcp_tester import MCPServerTester

        tester = MCPServerTester(request.server_config)

        # Route to appropriate method based on action
        if request.action == "list":
            result = await tester.list_tools()
        elif request.action == "call":
            if not request.params:
                raise ValueError("Missing params for call action")
            if "tool_name" not in request.params:
                raise ValueError("Missing 'tool_name' parameter")

            tool_name = request.params["tool_name"]
            arguments = request.params.get("arguments", {})

            result = await tester.call_tool(tool_name, arguments)
        else:
            raise ValueError(f"Unknown action: {request.action}")

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Tools test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Tools test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/prompts", tags=["mcp"])
async def test_mcp_prompts(
    project_name: str,
    server_name: str,
    request: MCPTestActionRequest
):
    """
    Test MCP prompts operations (list, get).

    Actions:
    - list: List all prompts
    - get: Get a specific prompt (requires params: {"prompt_name": "...", "arguments": {...}})
    """
    try:
        from utils.mcp_tester import MCPServerTester

        tester = MCPServerTester(request.server_config)

        # Route to appropriate method based on action
        if request.action == "list":
            result = await tester.list_prompts()
        elif request.action == "get":
            if not request.params or "prompt_name" not in request.params:
                raise ValueError("Missing 'prompt_name' parameter for get action")

            prompt_name = request.params["prompt_name"]
            arguments = request.params.get("arguments")

            result = await tester.get_prompt(prompt_name, arguments)
        else:
            raise ValueError(f"Unknown action: {request.action}")

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Prompts test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Prompts test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/completions", tags=["mcp"])
async def test_mcp_completions(
    project_name: str,
    server_name: str,
    request: MCPTestActionRequest
):
    """
    Test MCP completions.

    Requires params: {"ref": {...}, "argument": {"name": "...", "value": "..."}}
    """
    try:
        from utils.mcp_tester import MCPServerTester

        tester = MCPServerTester(request.server_config)

        if not request.params:
            raise ValueError("Missing params for completions")
        if "ref" not in request.params or "argument" not in request.params:
            raise ValueError("Missing 'ref' or 'argument' parameters")

        result = await tester.get_completions(
            ref=request.params["ref"],
            argument=request.params["argument"]
        )

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Completions test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Completions test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/test/{server_name}/session", tags=["mcp"])
async def test_mcp_session(
    project_name: str,
    server_name: str,
    request: MCPTestActionRequest
):
    """
    Manage MCP test session.

    Actions:
    - reset: Reset session (re-initialize)
    """
    try:
        from utils.mcp_tester import MCPServerTester

        tester = MCPServerTester(request.server_config)

        if request.action == "reset":
            result = await tester.reset_session()
        else:
            raise ValueError(f"Unknown action: {request.action}")

        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata
        }

    except Exception as e:
        logger.error(f"Session test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "data": None,
            "error": f"Session test error: {str(e)}",
            "metadata": {}
        }


@app.post("/api/projects/{project_name}/mcp/{server_name}/auto-test", tags=["mcp"])
async def auto_test_mcp_server(
    project_name: str,
    server_name: str,
    request: MCPTestConnectionRequest
):
    """
    Automatically test MCP server and update configuration with results.

    This endpoint:
    1. Runs comprehensive tests (connection, tools, prompts, resources)
    2. Caches test results in mcp.json
    3. Sets server health status (healthy|unhealthy|untested)
    4. Returns updated server configuration

    Called automatically after saving MCP configuration from frontend.
    """
    try:
        from utils.mcp_auto_test import update_server_test_results

        logger.info(f"🧪 Auto-testing MCP server '{server_name}' in project '{project_name}'")

        # Run comprehensive tests and get updated config
        updated_config = await update_server_test_results(
            project_name=project_name,
            server_name=server_name,
            server_config=request.server_config
        )

        # Read current MCP config
        project_dir = get_project_dir(project_name)
        mcp_file = project_dir / "mcp.json"
        mcp_data = read_json_file(mcp_file)

        # Update only this server's configuration with test results
        if "servers" in mcp_data and server_name in mcp_data["servers"]:
            mcp_data["servers"][server_name].update(updated_config)

            # Write back to file
            write_json_file(mcp_file, mcp_data)

            logger.info(
                f"✅ Auto-test complete for '{server_name}': "
                f"status={updated_config.get('status')}"
            )

            return {
                "success": True,
                "server_config": updated_config,
                "message": f"MCP server '{server_name}' tested successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server '{server_name}' not found in project MCP config"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-test failed for {server_name}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Auto-test error: {str(e)}",
            "server_config": request.server_config
        }


@app.get("/api/mcp/library", tags=["mcp"])
async def list_mcp_library():
    """List MCP servers in common library."""
    servers = []

    if MCP_LIBRARY_DIR.exists():
        for server_file in MCP_LIBRARY_DIR.glob("*.json"):
            try:
                data = read_json_file(server_file)
                servers.append({
                    "id": server_file.stem,
                    "name": data.get("name", server_file.stem),
                    "description": data.get("description", "")
                })
            except Exception as e:
                logger.error(f"Error loading MCP library server {server_file.name}: {e}")

    return {"servers": servers}


@app.post("/api/mcp/library", status_code=status.HTTP_201_CREATED, tags=["mcp"])
async def add_to_mcp_library(server_id: str, config: MCPConfig):
    """Add MCP server to common library."""
    server_file = MCP_LIBRARY_DIR / f"{server_id}.json"

    if server_file.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MCP server '{server_id}' already exists in library"
        )

    write_json_file(server_file, config.config)

    logger.info(f"Added MCP server {server_id} to library")

    return {"status": "success", "message": f"MCP server {server_id} added to library"}


@app.delete("/api/mcp/library/{server_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["mcp"])
async def remove_from_mcp_library(server_id: str):
    """Remove MCP server from common library."""
    server_file = MCP_LIBRARY_DIR / f"{server_id}.json"

    if not server_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MCP server '{server_id}' not found in library"
        )

    server_file.unlink()

    logger.info(f"Removed MCP server {server_id} from library")


# ============================================================================
# API Endpoints - AI Generation
# ============================================================================

@app.post("/api/workflows/generate", tags=["ai"])
async def generate_workflow(request: WorkflowGenerateRequest):
    """Generate workflow from natural language description using AI.

    Uses the web_app_model configured in the project's agents.json.
    Falls back to default_model if not configured.
    """
    try:
        # Initialize AIService with project configuration (use web_app_model)
        ai_service = AIService(request.project_name, use_web_app_model=True)

        # Generate workflow using configured AI provider
        workflow = await ai_service.generate_workflow_from_description(
            description=request.description,
            agent_types=request.agent_types,
            mcp_servers=request.mcp_servers,
            language="it"  # Default to Italian based on project context
        )

        return {
            "workflow": workflow,
            "message": f"Workflow generato con successo usando {ai_service.provider}/{ai_service.model}",
            "confidence": 0.9
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI-generated workflow JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI ha generato JSON non valido: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore nella generazione del workflow: {str(e)}"
        )


# ============================================================================
# Execution & Testing Endpoints
# ============================================================================

class AgentInvokeRequest(BaseModel):
    """Request to invoke a standalone agent."""
    agent_name: str = Field(..., description="Name of the agent to invoke")
    task: str = Field(..., min_length=1, description="Task description for the agent")
    project_name: str = "default"
    stream: bool = Field(default=False, description="Enable streaming responses")


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_name: str = Field(..., description="Name of the workflow to execute")
    user_input: str = Field(..., min_length=1, description="User input for the workflow")
    project_name: str = "default"
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Workflow parameters")
    stream: bool = Field(default=False, description="Enable streaming responses")


class ExecutionStep(BaseModel):
    """A single step in execution (for debugging)."""
    step_type: str  # "thought", "action", "observation", "reflection", "decision"
    agent: Optional[str] = None
    node_id: Optional[str] = None
    iteration: int
    timestamp: float
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionResult(BaseModel):
    """Result of agent or workflow execution."""
    status: str  # "success", "error", "timeout"
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    execution_id: Optional[str] = None  # UUID for retrieving logs
    steps: List[ExecutionStep] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


@app.post("/api/agents/invoke", response_model=ExecutionResult, tags=["execution"])
async def invoke_agent(request: AgentInvokeRequest):
    """
    Invoke a standalone agent directly for testing.

    Returns detailed execution steps for debugging.
    """
    try:
        import httpx
        from schemas.mcp_protocol import MCPRequest, MCPResponse

        start_time = time.time()

        # Load project config to get agent details
        project_dir = get_project_dir(request.project_name)
        agents_file = project_dir / "agents.json"
        agents_config = read_json_file(agents_file)

        if not agents_config or request.agent_name not in agents_config.get("agents", {}):
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{request.agent_name}' not found in project '{request.project_name}'"
            )

        agent_config = agents_config["agents"][request.agent_name]

        if not agent_config.get("enabled", False):
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{request.agent_name}' is disabled"
            )

        # Build agent URL
        host = agent_config.get("host", "localhost")
        port = agent_config.get("port")
        agent_url = f"http://{host}:{port}/invoke"

        # Create MCP request
        mcp_request = MCPRequest(
            source_agent_id="web_client",
            target_agent_id=request.agent_name,
            task_description=request.task,
            context={"project": request.project_name}
        )

        # Invoke agent
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(agent_url, json=mcp_request.model_dump(mode='json'))
            response.raise_for_status()
            mcp_response = MCPResponse(**response.json())

        execution_time = time.time() - start_time

        # Build execution steps (simplified - agents don't expose internal steps yet)
        steps = [
            ExecutionStep(
                step_type="action",
                agent=request.agent_name,
                iteration=1,
                timestamp=start_time,
                content=f"Invoked agent '{request.agent_name}' with task",
                metadata={"url": agent_url}
            ),
            ExecutionStep(
                step_type="observation",
                agent=request.agent_name,
                iteration=1,
                timestamp=time.time(),
                content=mcp_response.result or "",
                metadata=mcp_response.metadata
            )
        ]

        return ExecutionResult(
            status=mcp_response.status,
            result=mcp_response.result,
            error=mcp_response.error_message,
            execution_time=execution_time,
            steps=steps,
            metadata={
                "agent": request.agent_name,
                "task_id": mcp_response.task_id,
                **mcp_response.metadata
            }
        )

    except httpx.HTTPError as e:
        logger.error(f"Agent invocation failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Agent server not reachable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error invoking agent: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent invocation error: {str(e)}"
        )


@app.post("/api/workflows/execute", response_model=ExecutionResult, tags=["execution"])
async def execute_workflow(request: WorkflowExecuteRequest):
    """
    Execute a workflow with detailed step-by-step debugging.

    Returns all intermediate steps for debugging.
    """
    try:
        from workflows.engine import WorkflowEngine
        from schemas.workflow_schemas import WorkflowTemplate

        start_time = time.time()

        # Load workflow
        workflow_path = PROJECTS_DIR / request.project_name / "workflows" / f"{request.workflow_name}.json"
        if not workflow_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Workflow '{request.workflow_name}' not found"
            )

        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)

        workflow = WorkflowTemplate(**workflow_data)

        # Load project-specific MCP configuration before execution
        try:
            from utils.mcp_registry import initialize_mcp_registry_from_project
            await initialize_mcp_registry_from_project(request.project_name)
            logger.info(f"✅ MCP config loaded for project '{request.project_name}'")
        except Exception as e:
            logger.warning(f"⚠️ Could not load MCP config for project '{request.project_name}': {e}")

        # Execute workflow
        engine = WorkflowEngine(mode="langgraph")
        result = await engine.execute_workflow(
            template=workflow,
            user_input=request.user_input,
            params=request.parameters
        )

        execution_time = time.time() - start_time

        # Convert workflow logs to execution steps
        steps = []
        for i, log_entry in enumerate(result.execution_log):
            step_type = "action" if log_entry.action == "executing" else "observation"
            # Handle timestamp - could be float or datetime
            ts = log_entry.timestamp
            if hasattr(ts, 'timestamp'):
                ts = ts.timestamp()

            # Generate content from action and details
            content = f"{log_entry.action} node '{log_entry.node_id}'"
            if log_entry.details:
                if 'error' in log_entry.details:
                    content = f"Error: {log_entry.details['error']}"
                elif 'output' in log_entry.details:
                    content = str(log_entry.details['output'])[:500]  # Limit length

            steps.append(ExecutionStep(
                step_type=step_type,
                agent=log_entry.agent,
                node_id=log_entry.node_id,
                iteration=i + 1,
                timestamp=ts,
                content=content,
                metadata=log_entry.details
            ))

        # Map WorkflowResult to ExecutionResult
        return ExecutionResult(
            status="success" if result.success else "error",
            result=result.final_output,
            error=result.error,
            execution_time=execution_time,
            execution_id=result.execution_id,  # Pass execution_id for log retrieval
            steps=steps,
            metadata={
                "workflow": request.workflow_name,
                "total_execution_time": result.total_execution_time,
                "node_results": [
                    {"node_id": nr.node_id, "agent": nr.agent, "time": nr.execution_time}
                    for nr in result.node_results
                ]
            }
        )

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Workflow execution error: {str(e)}"
        )


@app.get("/api/workflows/logs/{execution_id}", tags=["execution"])
async def get_workflow_logs(execution_id: str):
    """
    Retrieve execution logs for a specific workflow execution by ID.

    Parses the /tmp/editor-server.log file to extract all log entries
    for the given execution_id and returns structured execution steps.

    Args:
        execution_id: UUID of the workflow execution

    Returns:
        Dictionary with execution steps and metadata
    """
    try:
        import re
        from pathlib import Path

        log_file = Path("/tmp/editor-server.log")

        if not log_file.exists():
            return {
                "success": False,
                "error": "Log file not found",
                "steps": [],
                "metadata": {}
            }

        # Extract first 8 chars of execution_id for matching [exec:XXXXXXXX] pattern
        exec_id_short = execution_id[:8] if len(execution_id) >= 8 else execution_id

        # Read log file and filter by execution_id
        matching_logs = []
        with open(log_file, 'r') as f:
            for line in f:
                # Look for lines with [exec:ID] pattern or lines between workflow start/end
                if f"[exec:{exec_id_short}]" in line or f"exec:{exec_id_short}" in line:
                    matching_logs.append(line.strip())

        if not matching_logs:
            return {
                "success": True,
                "message": f"No logs found for execution {exec_id_short}",
                "steps": [],
                "metadata": {
                    "execution_id": execution_id,
                    "log_count": 0
                }
            }

        # Parse logs into structured steps
        steps = []
        current_node = None
        step_counter = 0

        for log_line in matching_logs:
            step_counter += 1

            # Extract timestamp and message
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', log_line)
            timestamp_str = timestamp_match.group(1) if timestamp_match else ""

            # Determine step type from log content
            if "NODE START:" in log_line or "🚀" in log_line:
                # Extract node_id from log
                node_match = re.search(r"NODE START: (\w+)", log_line)
                if node_match:
                    current_node = node_match.group(1)
                    steps.append({
                        "step_type": "action",
                        "node_id": current_node,
                        "iteration": step_counter,
                        "timestamp": timestamp_str,
                        "content": f"Starting node '{current_node}'",
                        "metadata": {"log_line": log_line}
                    })

            elif "NODE COMPLETE:" in log_line or "✅" in log_line:
                # Node completion
                node_match = re.search(r"NODE COMPLETE: (\w+)", log_line)
                if node_match:
                    current_node = node_match.group(1)
                    steps.append({
                        "step_type": "observation",
                        "node_id": current_node,
                        "iteration": step_counter,
                        "timestamp": timestamp_str,
                        "content": f"Completed node '{current_node}'",
                        "metadata": {"log_line": log_line}
                    })

            elif "NODE ERROR:" in log_line or "❌" in log_line or "ERROR" in log_line:
                # Error during execution
                steps.append({
                    "step_type": "error",
                    "node_id": current_node,
                    "iteration": step_counter,
                    "timestamp": timestamp_str,
                    "content": log_line,
                    "metadata": {"log_line": log_line}
                })

            elif "Executing node" in log_line or "📍" in log_line:
                # Node execution start with context
                node_match = re.search(r"Executing node '(\w+)'", log_line)
                if node_match:
                    current_node = node_match.group(1)
                    steps.append({
                        "step_type": "action",
                        "node_id": current_node,
                        "iteration": step_counter,
                        "timestamp": timestamp_str,
                        "content": f"Executing node '{current_node}'",
                        "metadata": {"log_line": log_line}
                    })

        return {
            "success": True,
            "execution_id": execution_id,
            "steps": steps,
            "metadata": {
                "execution_id": execution_id,
                "exec_id_short": exec_id_short,
                "log_count": len(matching_logs),
                "step_count": len(steps)
            }
        }

    except Exception as e:
        logger.error(f"Error retrieving logs for execution {execution_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Failed to retrieve logs: {str(e)}",
            "steps": [],
            "metadata": {}
        }


@app.get("/api/agents/{agent_name}/health", tags=["execution"])
async def check_agent_health(agent_name: str, project_name: str = "default"):
    """Check if an agent server is running and healthy."""
    try:
        import httpx

        # Load agent config
        project_dir = get_project_dir(project_name)
        agents_file = project_dir / "agents.json"
        agents_config = read_json_file(agents_file)

        if not agents_config or agent_name not in agents_config.get("agents", {}):
            raise HTTPException(status_code=404, detail="Agent not found")

        agent_config = agents_config["agents"][agent_name]
        host = agent_config.get("host", "localhost")
        port = agent_config.get("port")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{host}:{port}/health")
            response.raise_for_status()
            return {
                "agent": agent_name,
                "status": "healthy",
                "url": f"http://{host}:{port}",
                "enabled": agent_config.get("enabled", False),
                "response": response.json()
            }
    except httpx.HTTPError:
        return {
            "agent": agent_name,
            "status": "unhealthy",
            "enabled": agent_config.get("enabled", False) if 'agent_config' in locals() else False,
            "error": "Server not reachable"
        }
    except Exception as e:
        return {
            "agent": agent_name,
            "status": "error",
            "error": str(e)
        }


# ============================================================================
# LLM Configuration Endpoints
# ============================================================================

@app.get("/api/llm/registry")
async def get_model_registry():
    """
    Get the model registry with all available LLM models.

    Returns:
        ModelRegistry with providers and their models
    """
    try:
        # Transform MODEL_REGISTRY to match frontend ModelRegistry type
        providers = {}
        for provider, models in MODEL_REGISTRY.items():
            providers[provider] = [
                {
                    "provider": provider,
                    "model_id": model.model_id,
                    "display_name": model.display_name,
                    "context_window": model.context_window,
                    "supports_tools": model.supports_tools,
                    "supports_streaming": model.supports_streaming,
                    "cost_tier": model.cost_tier,
                    "recommended_for": model.recommended_for
                }
                for model in models
            ]

        return {"providers": providers}

    except Exception as e:
        logger.error(f"Error getting model registry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model registry: {str(e)}"
        )


@app.get("/api/llm/api-keys/status")
async def get_api_key_status():
    """
    Check the status of API keys for all providers.

    Returns:
        List of APIKeyStatus for each provider
    """
    try:
        providers = ["openai", "anthropic", "google", "groq", "openrouter"]
        status_list = []

        for provider in providers:
            # Check if API key is configured in environment
            env_var_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "groq": "GROQ_API_KEY",
                "openrouter": "OPENROUTER_API_KEY"
            }

            env_var = env_var_map.get(provider)
            api_key = os.getenv(env_var) if env_var else None

            status_list.append({
                "provider": provider,
                "configured": bool(api_key),
                "valid": None,  # TODO: Implement actual API key validation
                "error": None if api_key else f"{env_var} not set in environment"
            })

        return status_list

    except Exception as e:
        logger.error(f"Error checking API key status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check API key status: {str(e)}"
        )


def _mask_api_key(key: str) -> str:
    """
    Mask an API key showing only first 4 and last 4 characters.

    Args:
        key: The API key to mask

    Returns:
        Masked key in format "sk-...ab12"
    """
    if not key or len(key) < 8:
        return "****"

    return f"{key[:4]}...{key[-4:]}"


def _get_env_file_path() -> Path:
    """Get the path to the .env file."""
    return Path(__file__).parent.parent / ".env"


def _read_env_file() -> Dict[str, str]:
    """
    Read and parse .env file.

    Returns:
        Dictionary of environment variables
    """
    env_file = _get_env_file_path()
    env_vars = {}

    if not env_file.exists():
        return env_vars

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def _write_env_file(env_vars: Dict[str, str]):
    """
    Write environment variables back to .env file.
    Preserves comments and structure.

    Args:
        env_vars: Dictionary of environment variables to write
    """
    env_file = _get_env_file_path()

    # Read original file to preserve structure
    original_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            original_lines = f.readlines()

    # Update values while preserving structure
    new_lines = []
    updated_keys = set()

    for line in original_lines:
        stripped = line.strip()

        # Preserve comments and empty lines
        if not stripped or stripped.startswith('#'):
            new_lines.append(line)
            continue

        # Update KEY=VALUE
        if '=' in stripped:
            key = stripped.split('=', 1)[0].strip()
            if key in env_vars:
                new_lines.append(f"{key}={env_vars[key]}\n")
                updated_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add any new keys that weren't in the original file
    for key, value in env_vars.items():
        if key not in updated_keys:
            new_lines.append(f"\n{key}={value}\n")

    # Write back
    with open(env_file, 'w') as f:
        f.writelines(new_lines)


@app.get("/api/llm/api-keys")
async def get_api_keys():
    """
    Get all API keys with masked values.

    Returns:
        List of API key configurations
    """
    try:
        env_vars = _read_env_file()

        providers = ["openai", "anthropic", "google", "groq", "openrouter"]
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }

        api_keys = []
        for provider in providers:
            env_var = env_var_map[provider]
            key = env_vars.get(env_var, "")

            api_keys.append({
                "provider": provider,
                "key": None,  # Never send actual key to frontend
                "masked_key": _mask_api_key(key) if key else None,
                "configured": bool(key),
                "last_validated": None
            })

        return api_keys

    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API keys: {str(e)}"
        )


class APIKeyUpdateRequest(BaseModel):
    """Request to update an API key."""
    key: str


@app.put("/api/llm/api-keys/{provider}")
async def update_api_key(provider: str, request: APIKeyUpdateRequest):
    """
    Update an API key for a specific provider.

    Args:
        provider: Provider name (openai, anthropic, google, groq, openrouter)
        request: New API key value

    Returns:
        Success response
    """
    try:
        # Validate provider
        valid_providers = ["openai", "anthropic", "google", "groq", "openrouter"]
        if provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )

        # Map provider to env variable name
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }

        env_var = env_var_map[provider]

        # Read current env vars
        env_vars = _read_env_file()

        # Update the key
        env_vars[env_var] = request.key

        # Write back to file
        _write_env_file(env_vars)

        # Update in current process environment
        os.environ[env_var] = request.key

        logger.info(f"Updated API key for provider: {provider}")

        return {
            "status": "success",
            "message": f"API key for {provider} updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating API key for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update API key: {str(e)}"
        )


@app.post("/api/llm/api-keys/validate/{provider}")
async def validate_api_key(provider: str):
    """
    Validate an API key by making a test request.

    Args:
        provider: Provider name

    Returns:
        Validation result
    """
    try:
        # Validate provider
        valid_providers = ["openai", "anthropic", "google", "groq", "openrouter"]
        if provider not in valid_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
            )

        # Get API key from environment
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "groq": "GROQ_API_KEY",
            "openrouter": "OPENROUTER_API_KEY"
        }

        env_var = env_var_map[provider]
        api_key = os.getenv(env_var)

        if not api_key:
            return {
                "valid": False,
                "error": f"{env_var} not configured"
            }

        # Perform provider-specific validation
        # For now, just check if key is set (actual API calls would be implemented here)
        # TODO: Implement actual API validation calls for each provider

        return {
            "valid": True,
            "error": None,
            "model_info": f"API key configured for {provider}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key for {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate API key: {str(e)}"
        )


# ============================================================================
# Process Management
# ============================================================================

class ProcessStartRequest(BaseModel):
    """Request to start a process."""
    name: str


class ProcessLogsResponse(BaseModel):
    """Response with process logs."""
    name: str
    logs: List[str]


@app.get("/api/processes/status", response_model=List[ProcessInfo], tags=["processes"])
async def get_processes_status():
    """Get status of all agents and processes."""
    try:
        agents_status = process_manager.get_all_agents_status()
        return agents_status
    except Exception as e:
        logger.error(f"Error getting process status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get process status: {str(e)}"
        )


@app.get("/api/processes/{process_name}/status", response_model=ProcessInfo, tags=["processes"])
async def get_process_status(process_name: str):
    """Get status of a specific process."""
    try:
        return process_manager.get_agent_status(process_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting process status for {process_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get process status: {str(e)}"
        )


@app.post("/api/processes/start", response_model=ProcessInfo, tags=["processes"])
async def start_process(request: ProcessStartRequest):
    """Start a process (agent)."""
    try:
        return process_manager.start_agent(request.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error starting process {request.name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start process: {str(e)}"
        )


@app.post("/api/processes/{process_name}/stop", response_model=ProcessInfo, tags=["processes"])
async def stop_process(process_name: str):
    """Stop a process (agent)."""
    try:
        return process_manager.stop_agent(process_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error stopping process {process_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop process: {str(e)}"
        )


@app.post("/api/processes/{process_name}/restart", response_model=ProcessInfo, tags=["processes"])
async def restart_process(process_name: str):
    """Restart a process (agent)."""
    try:
        return process_manager.restart_agent(process_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error restarting process {process_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart process: {str(e)}"
        )


@app.post("/api/processes/start-all", response_model=List[ProcessInfo], tags=["processes"])
async def start_all_processes():
    """Start all agents."""
    try:
        return process_manager.start_all_agents()
    except Exception as e:
        logger.error(f"Error starting all processes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start all processes: {str(e)}"
        )


@app.post("/api/processes/stop-all", response_model=List[ProcessInfo], tags=["processes"])
async def stop_all_processes():
    """Stop all agents."""
    try:
        return process_manager.stop_all_agents()
    except Exception as e:
        logger.error(f"Error stopping all processes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop all processes: {str(e)}"
        )


@app.get("/api/processes/{process_name}/logs", response_model=ProcessLogsResponse, tags=["processes"])
async def get_process_logs(process_name: str, lines: int = 50):
    """Get last N lines from a process log file."""
    try:
        logs = process_manager.get_logs(process_name, lines)
        return ProcessLogsResponse(name=process_name, logs=logs)
    except Exception as e:
        logger.error(f"Error getting logs for {process_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )


# ============================================================================
# Static Files - Frontend (React SPA)
# ============================================================================

# Frontend dist directory
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

# Mount static files (JS, CSS, assets)
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    logger.info(f"✅ Frontend static files mounted from: {FRONTEND_DIST}")
else:
    logger.warning(f"⚠️ Frontend build not found at: {FRONTEND_DIST}")
    logger.warning("   Run 'cd frontend && npm run build' to build the frontend")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    Serve the React SPA for all non-API routes.

    This catch-all route handles client-side routing by always serving index.html
    for any path that doesn't match an API endpoint or static file.
    """
    # Return index.html for SPA routing
    index_file = FRONTEND_DIST / "index.html"

    if index_file.exists():
        return FileResponse(index_file)
    else:
        raise HTTPException(
            status_code=404,
            detail="Frontend not built. Run 'npm run build' in the frontend directory."
        )


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("EDITOR_PORT", "8002"))

    logger.info(f"Starting Cortex Flow Editor API on port {port}")
    logger.info(f"Projects directory: {PROJECTS_DIR.absolute()}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
