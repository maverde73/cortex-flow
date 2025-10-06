"""
FastAPI server for the Analyst Agent.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from schemas.mcp_protocol import MCPRequest, MCPResponse, HealthCheckResponse
from agents.analyst import get_analyst_agent
from config import settings

app = FastAPI(
    title="Analyst Agent",
    description="Specialized agent for data analysis and synthesis",
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
    return HealthCheckResponse(agent_id="analyst")


@app.post("/invoke", response_model=MCPResponse)
async def invoke_agent(request: MCPRequest):
    try:
        thread_id = request.task_id
        input_message = HumanMessage(content=request.task_description)

        agent = get_analyst_agent()

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
            source_agent_id="analyst",
            status="success",
            result=final_message.content,
            metadata={
                "message_count": len(result["messages"]),
                "thread_id": thread_id
            }
        )

    except Exception as e:
        return MCPResponse(
            task_id=request.task_id,
            source_agent_id="analyst",
            status="error",
            result=None,
            error_message=str(e),
            metadata={"error_type": type(e).__name__}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.analyst_port, log_level="info")
