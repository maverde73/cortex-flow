"""
FastAPI server for the Supervisor Agent.

This is the main entry point for user requests. The supervisor
orchestrates other agents to complete complex tasks.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from schemas.mcp_protocol import MCPRequest, MCPResponse, HealthCheckResponse
from agents.supervisor import get_supervisor_agent
from services.registry import initialize_registry_from_config
from services.health_monitor import start_health_monitoring
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supervisor Agent (Cortex Flow)",
    description="Main orchestration agent that coordinates specialized AI agents",
    version="0.1.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize service registry and health monitoring on startup."""
    logger.info("Initializing Cortex Flow Supervisor...")

    # Initialize the registry with configured agents
    await initialize_registry_from_config()

    # Start health monitoring in the background
    await start_health_monitoring()

    logger.info("Supervisor startup complete")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with system information."""
    return {
        "service": "Cortex Flow - Supervisor Agent",
        "version": "0.1.0",
        "status": "operational",
        "description": "Multi-agent AI system orchestrator",
        "endpoints": {
            "health": "/health",
            "invoke": "/invoke",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["monitoring"])
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthCheckResponse(agent_id="supervisor")


@app.post("/invoke", response_model=MCPResponse, tags=["agent"])
async def invoke_agent(request: MCPRequest):
    """
    Main endpoint for invoking the supervisor agent.

    The supervisor will analyze the request and orchestrate
    other specialized agents to complete the task.

    Example request:
    ```json
    {
        "task_id": "unique-id",
        "source_agent_id": "user",
        "target_agent_id": "supervisor",
        "task_description": "Create a report on latest AI trends",
        "context": {}
    }
    ```
    """
    try:
        thread_id = request.task_id
        input_message = HumanMessage(content=request.task_description)

        # Get agent (now async to support dynamic loading)
        agent = await get_supervisor_agent()

        # Invoke the supervisor agent
        result = await agent.ainvoke(
            {"messages": [input_message]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": settings.max_iterations
            }
        )

        final_message = result["messages"][-1]

        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="supervisor",
            status="success",
            result=final_message.content,
            metadata={
                "message_count": len(result["messages"]),
                "thread_id": thread_id,
                "agents_used": _extract_agents_used(result["messages"])
            }
        )

    except Exception as e:
        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="supervisor",
            status="error",
            result=None,
            error_message=str(e),
            metadata={"error_type": type(e).__name__}
        )


def _extract_agents_used(messages) -> list:
    """
    Extract which agents were used during execution.

    This analyzes the message history to determine which
    specialized agents were invoked.
    """
    agents_used = set()

    for message in messages:
        if hasattr(message, "tool_calls"):
            for tool_call in getattr(message, "tool_calls", []):
                tool_name = tool_call.get("name", "")
                if "research" in tool_name:
                    agents_used.add("researcher")
                elif "analyze" in tool_name:
                    agents_used.add("analyst")
                elif "write" in tool_name:
                    agents_used.add("writer")

    return list(agents_used)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.supervisor_port,
        log_level="info"
    )
