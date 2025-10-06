"""
FastAPI server for the Web Researcher Agent.

Exposes the researcher agent via HTTP using the MCP protocol.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from schemas.mcp_protocol import MCPRequest, MCPResponse, HealthCheckResponse
from agents.researcher import get_researcher_agent
from config_legacy import settings

# Create FastAPI app
app = FastAPI(
    title="Web Researcher Agent",
    description="Specialized agent for web research and information gathering",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthCheckResponse(agent_id="researcher")


@app.post("/invoke", response_model=MCPResponse)
async def invoke_agent(request: MCPRequest):
    """
    Main endpoint for invoking the researcher agent.

    Accepts an MCP request and returns the research results.
    """
    try:
        # Create a unique thread ID for this conversation
        thread_id = request.task_id

        # Prepare the input for the agent
        input_message = HumanMessage(content=request.task_description)

        # Get the agent instance
        agent = get_researcher_agent()

        # Invoke the agent
        result = await agent.ainvoke(
            {"messages": [input_message]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": settings.max_iterations
            }
        )

        # Extract the final response
        final_message = result["messages"][-1]
        response_content = final_message.content

        # Return MCP response
        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="researcher",
            status="success",
            result=response_content,
            metadata={
                "message_count": len(result["messages"]),
                "thread_id": thread_id
            }
        )

    except Exception as e:
        # Return error response
        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="researcher",
            status="error",
            result=None,
            error_message=str(e),
            metadata={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.researcher_port,
        log_level="info"
    )
