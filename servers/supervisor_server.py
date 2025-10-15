"""
FastAPI server for the Supervisor Agent.

This is the main entry point for user requests. The supervisor
orchestrates other agents to complete complex tasks.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

from schemas.mcp_protocol import MCPRequest, MCPResponse, HealthCheckResponse
from agents.workflow_supervisor import get_workflow_supervisor
from services.registry import initialize_registry_from_config
from services.health_monitor import start_health_monitoring
from config_legacy import settings
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

    # Initialize MCP registry if enabled
    if settings.mcp_enable:
        try:
            from utils.mcp_registry import initialize_mcp_registry_from_config
            await initialize_mcp_registry_from_config()
            logger.info("MCP registry initialized")
        except Exception as e:
            logger.error(f"Error initializing MCP registry: {e}")

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
        agent = await get_workflow_supervisor()

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


@app.post(settings.supervisor_mcp_path if settings.supervisor_mcp_enable else "/mcp-disabled", tags=["mcp"])
@app.get(settings.supervisor_mcp_path if settings.supervisor_mcp_enable else "/mcp-disabled", tags=["mcp"])
async def mcp_endpoint(request: Request):
    """
    MCP (Model Context Protocol) endpoint.

    Exposes the Supervisor agent as an MCP server using Streamable HTTP transport.
    This allows external systems to discover and call the Supervisor's capabilities
    using the standard MCP protocol.

    Supports:
    - GET: Server information and capabilities discovery
    - POST: Tool calls and other MCP operations
    """
    if not settings.supervisor_mcp_enable:
        return JSONResponse(
            status_code=503,
            content={
                "error": "MCP server is not enabled",
                "message": "Set SUPERVISOR_MCP_ENABLE=true in .env to enable MCP endpoint"
            }
        )

    try:
        # Parse JSON-RPC request
        body = await request.json()

        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id", 1)

        # Handle different MCP methods
        if method == "tools/list":
            # Return available tools
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "execute_task",
                            "description": (
                                "Execute a complex task using the Cortex Flow multi-agent system. "
                                "The Supervisor will orchestrate specialized agents (Researcher, Analyst, Writer) "
                                "to complete the task efficiently."
                            ),
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "task_description": {
                                        "type": "string",
                                        "description": "Natural language description of the task to execute"
                                    },
                                    "thread_id": {
                                        "type": "string",
                                        "description": "Optional conversation thread ID for maintaining context"
                                    }
                                },
                                "required": ["task_description"]
                            }
                        }
                    ]
                }
            })

        elif method == "tools/call":
            # Execute tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name != "execute_task":
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
                )

            # Execute the task using supervisor
            task_description = arguments.get("task_description")
            thread_id = arguments.get("thread_id", f"mcp_{request_id}")

            if not task_description:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": "Missing required parameter: task_description"
                        }
                    }
                )

            try:
                # Invoke supervisor agent
                agent = await get_workflow_supervisor()
                input_message = HumanMessage(content=task_description)

                result = await agent.ainvoke(
                    {"messages": [input_message]},
                    config={
                        "configurable": {"thread_id": thread_id},
                        "recursion_limit": settings.max_iterations
                    }
                )

                final_message = result["messages"][-1]

                # Return MCP response
                return JSONResponse(content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": final_message.content
                            }
                        ],
                        "isError": False
                    }
                })

            except Exception as e:
                logger.error(f"Error executing MCP task: {e}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                )

        elif request.method == "GET":
            # Return server information
            return JSONResponse(content={
                "name": "cortex-flow-supervisor",
                "version": "0.1.0",
                "description": "Cortex Flow Supervisor - Multi-agent AI orchestration system",
                "transport": settings.supervisor_mcp_transport,
                "capabilities": {
                    "tools": True,
                    "resources": False,
                    "prompts": False
                }
            })

        else:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            )

    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.supervisor_port,
        log_level="info"
    )
