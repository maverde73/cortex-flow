"""
FastAPI server for the Writer Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from schemas.mcp_protocol import MCPRequest, MCPResponse, HealthCheckResponse
from agents.writer import get_writer_agent
from config import settings

app = FastAPI(
    title="Writer Agent",
    description="Specialized agent for professional content creation",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(agent_id="writer")


@app.post("/invoke", response_model=MCPResponse)
async def invoke_agent(request: MCPRequest):
    try:
        thread_id = request.task_id
        input_message = HumanMessage(content=request.task_description)

        agent = get_writer_agent()

        result = await agent.ainvoke(
            {"messages": [input_message]},
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": settings.max_iterations
            }
        )

        final_message = result["messages"][-1]

        # Extract react_history if present
        react_history = result.get("react_history", [])

        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="writer",
            status="success",
            result=final_message.content,
            metadata={
                "message_count": len(result["messages"]),
                "thread_id": thread_id,
                "react_history": react_history,  # Include history in metadata
                "iteration_count": result.get("iteration_count", 0),
                "refinement_count": result.get("refinement_count", 0)
            }
        )

    except Exception as e:
        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="writer",
            status="error",
            result=None,
            error_message=str(e),
            metadata={"error_type": type(e).__name__}
        )


@app.get("/react_history/{task_id}")
async def get_react_history(task_id: str):
    """
    Get ReAct execution history for a specific task.

    Note: This endpoint returns cached history from the last execution.
    For real-time history, use a persistent store (PostgreSQL/Redis checkpointer).
    """
    # In production, this would query the checkpointer for the thread_id
    # For now, return a message indicating the feature
    return {
        "task_id": task_id,
        "agent_id": "writer",
        "note": "ReAct history is included in the /invoke response metadata",
        "recommendation": "Use POST /invoke and check metadata.react_history for execution details"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.writer_port, log_level="info")
