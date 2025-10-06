# ReAct Pattern Controls - Implementation Guide

## Overview

The Cortex Flow multi-agent system implements advanced **ReAct (Reason+Act) pattern controls** to ensure safe, reliable, and observable agent execution.

**Current Status:** FASE 4 (Structured Logging) completed ✓

## What is ReAct?

ReAct is an agent reasoning pattern that combines:
- **Thought**: The agent reasons about what to do next
- **Action**: The agent executes a tool or delegates to another agent
- **Observation**: The agent processes the result and continues

This cycle repeats until the agent reaches a final answer or hits a safety limit.

## Implemented Controls (FASE 1)

### 1. Timeout Control
Prevents agents from running indefinitely.

```bash
REACT_TIMEOUT_SECONDS=120.0  # Maximum execution time
```

**How it works:**
- Each agent tracks `start_time` when execution begins
- Before each iteration, checks: `elapsed_time > timeout`
- If exceeded, agent stops gracefully with timeout message

### 2. Max Iterations Control
Limits the number of ReAct cycles.

```bash
MAX_ITERATIONS=10  # Maximum number of Thought→Action→Observation cycles
```

**How it works:**
- Each agent increments `iteration_count` on every cycle
- Before each iteration, checks: `iteration_count >= max_iterations`
- If exceeded, agent stops to prevent infinite loops

### 3. Consecutive Error Tracking
Prevents agents from getting stuck in error loops.

```bash
REACT_MAX_CONSECUTIVE_ERRORS=3  # Maximum consecutive errors before abort
```

**How it works:**
- Each tool execution tracks `error_count`
- On success: `error_count` resets to 0
- On failure: `error_count` increments by 1
- If `error_count >= max_consecutive_errors`, agent aborts

### 4. Manual Stop Flag
Allows external systems to gracefully stop agent execution.

**How it works:**
- State includes `should_stop` boolean flag
- State includes `early_stop_reason` string
- Before each iteration, agent checks `should_stop`
- If true, agent terminates immediately

### 5. Verbose Logging
Provides detailed console output for debugging and monitoring.

```bash
REACT_ENABLE_VERBOSE_LOGGING=true  # Enable detailed logs
REACT_LOG_THOUGHTS=true            # Log agent reasoning
REACT_LOG_ACTIONS=true             # Log tool calls/delegations
REACT_LOG_OBSERVATIONS=true        # Log tool results
```

**Example output:**
```
INFO:agents.supervisor:[Supervisor ReAct Iteration 1] Planning: ...
INFO:agents.supervisor:[Supervisor ReAct Iteration 1] Delegating to: research_web
INFO:tools.proxy_tools:Successfully called researcher
INFO:agents.supervisor:[Supervisor ReAct Iteration 1] Received: <response>
INFO:agents.supervisor:[Supervisor ReAct Iteration 2] Planning: <next step>
INFO:agents.supervisor:[Supervisor ReAct] Completed successfully after 2 iterations
```

### 6. Structured History
Tracks execution history for observability and debugging.

**State field:** `react_history: List[Dict]`

**History entry format:**
```python
{
    "iteration": 1,
    "timestamp": 1696598400.123,
    "action": "tool_execution",
    "observation": "Result from tool..."
}
```

## Agent-Specific Implementation

### Researcher Agent
- ✅ Full ReAct controls
- ✅ Tool execution tracking (Tavily search)
- ✅ Error handling with retry logic
- ✅ Async tool execution (ainvoke)

### Analyst Agent
- ✅ Basic ReAct controls
- ✅ No tools (single-pass reasoning)
- ✅ Timeout and iteration limits

### Writer Agent
- ✅ Basic ReAct controls
- ✅ No tools (single-pass content generation)
- ✅ Timeout and iteration limits

### Supervisor Agent
- ✅ Full ReAct controls
- ✅ Delegation tracking (calls to other agents)
- ✅ Multi-agent orchestration logging
- ✅ Async tool execution (ainvoke)

## Configuration

### Default Configuration
Located in `config.py`:
```python
react_timeout_seconds: float = 120.0
react_enable_early_stopping: bool = True
react_max_consecutive_errors: int = 3
react_enable_verbose_logging: bool = True
react_log_thoughts: bool = True
react_log_actions: bool = True
react_log_observations: bool = True
```

### Environment Variables
Configure in `.env`:
```bash
REACT_TIMEOUT_SECONDS=120.0
REACT_ENABLE_EARLY_STOPPING=true
REACT_MAX_CONSECUTIVE_ERRORS=3
REACT_ENABLE_VERBOSE_LOGGING=true
REACT_LOG_THOUGHTS=true
REACT_LOG_ACTIONS=true
REACT_LOG_OBSERVATIONS=true
```

## Testing Results

✅ **Test 1: Simple Query**
- Query: "What is LangGraph?"
- Result: Completed in 2 iterations
- Time: ~8 seconds
- Status: Success

✅ **Test 2: Multi-Agent Delegation**
- Query: "What is LangGraph and how is it different from LangChain?"
- Supervisor delegated to Researcher
- Result: Completed in 2 iterations
- Delegation: Successful HTTP call to researcher agent
- Status: Success

✅ **Test 3: Async Tool Execution**
- Fixed sync/async issue: `ToolNode.invoke()` → `ToolNode.ainvoke()`
- Result: No NotImplementedError
- All async tools work correctly

## State Schema

```python
class BaseAgentState(TypedDict, total=False):
    # Core message history (required)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # ReAct execution metadata (optional)
    iteration_count: int              # Current iteration number
    error_count: int                  # Consecutive error counter
    start_time: float                 # Execution start timestamp
    react_history: List[Dict]         # Structured log history
    should_stop: bool                 # Manual stop flag
    early_stop_reason: Optional[str]  # Reason for early termination
```

## Safety Checks Order

Each agent performs these checks **before every iteration**:

1. ✅ **Manual Stop**: Check `should_stop` flag
2. ✅ **Timeout**: Check `elapsed_time > timeout`
3. ✅ **Max Iterations**: Check `iteration_count >= max_iterations`
4. ✅ **Max Errors**: Check `error_count >= max_consecutive_errors`
5. ✅ **ReAct Flow**: Check for tool calls (continue vs end)

If any check fails, agent terminates gracefully with appropriate message.

## Implemented Strategies (FASE 2)

### Strategy Types

The system now supports **4 reasoning strategies** with different performance characteristics:

#### 🚀 FAST Strategy
**Use for:** Quick decisions, routing, simple queries

**Parameters:**
- Max iterations: 3
- Temperature: 0.3
- Timeout: 30 seconds

**Best for:**
- Supervisor coordination
- Task routing
- Simple Q&A
- Quick lookups

**Example:** Supervisor uses FAST to quickly delegate tasks without deep reasoning.

#### ⚖️ BALANCED Strategy
**Use for:** Standard analysis, general queries

**Parameters:**
- Max iterations: 10
- Temperature: 0.7
- Timeout: 120 seconds

**Best for:**
- General analysis
- Standard research
- Default fallback
- Most common tasks

**Example:** Analyst uses BALANCED for typical data analysis tasks.

#### 🔬 DEEP Strategy
**Use for:** Complex research, thorough investigation

**Parameters:**
- Max iterations: 20
- Temperature: 0.7
- Timeout: 300 seconds (5 minutes)

**Best for:**
- Web research
- Multi-step investigation
- Comprehensive analysis
- Complex problem solving

**Example:** Researcher uses DEEP for thorough web searches with multiple iterations.

#### 🎨 CREATIVE Strategy
**Use for:** Content generation, brainstorming, creative tasks

**Parameters:**
- Max iterations: 15
- Temperature: 0.9
- Timeout: 180 seconds (3 minutes)

**Best for:**
- Article writing
- Creative content
- Brainstorming
- Exploratory thinking

**Example:** Writer uses CREATIVE for generating engaging content.

### Per-Agent Configuration

Each agent has a default strategy configured in `.env`:

```bash
# Supervisor: Quick delegation decisions
SUPERVISOR_REACT_STRATEGY=fast

# Researcher: Thorough web searches
RESEARCHER_REACT_STRATEGY=deep

# Analyst: Balanced analysis
ANALYST_REACT_STRATEGY=balanced

# Writer: Creative content generation
WRITER_REACT_STRATEGY=creative
```

### Task-Specific Overrides

You can override strategies for specific task types:

```bash
# Researcher: Fast mode for quick lookups
RESEARCHER_QUICK_SEARCH_REACT_STRATEGY=fast

# Researcher: Deep mode for comprehensive research
RESEARCHER_DEEP_ANALYSIS_REACT_STRATEGY=deep

# Writer: Balanced mode for technical documentation
WRITER_TECHNICAL_REACT_STRATEGY=balanced

# Writer: Creative mode for articles
WRITER_CREATIVE_REACT_STRATEGY=creative
```

### Strategy Selection Priority

The system selects strategies in this order:

1. **Explicit parameter** to `get_llm(react_strategy="fast")`
2. **Task-specific config**: `{AGENT}_{TASK}_REACT_STRATEGY`
3. **Agent-specific config**: `{AGENT}_REACT_STRATEGY`
4. **Default fallback**: `balanced`

### Usage in Code

```python
from utils.llm_factory import get_llm

# Use agent's default strategy
llm, react_config = get_llm(agent="researcher")
# Returns: DEEP strategy (20 iter, 0.7 temp, 300s timeout)

# Override with explicit strategy
llm, react_config = get_llm(agent="researcher", react_strategy="fast")
# Returns: FAST strategy (3 iter, 0.3 temp, 30s timeout)

# Use strategy parameters
if iteration_count >= react_config.max_iterations:
    # Stop execution
    pass

if time.time() - start_time > react_config.timeout_seconds:
    # Timeout
    pass
```

### ReactConfig Structure

```python
@dataclass
class ReactConfig:
    strategy: ReactStrategy              # FAST, BALANCED, DEEP, CREATIVE
    max_iterations: int                  # Maximum ReAct cycles
    temperature: float                   # LLM temperature (0.0-1.0)
    timeout_seconds: float               # Execution timeout
    description: str                     # Human-readable description
```

### Testing Results

✅ **30 unit tests** covering:
- Strategy enum functionality
- ReactConfig creation and validation
- Convenience functions
- Agent strategy selection
- LLM factory integration
- Parameter range validation

✅ **23 regression tests** ensuring:
- FASE 1 features still work
- Backward compatibility maintained
- State schema intact
- Health endpoints functional

✅ **End-to-end test:**
- Query: "Research latest AI reasoning strategies for 2025"
- Supervisor used FAST strategy (2 iterations, quick delegation)
- Researcher used DEEP strategy (thorough web search)
- Result: Successful completion with correct strategy application

### Strategy Comparison

| Strategy | Iterations | Timeout | Temperature | Best Use Case |
|----------|-----------|---------|-------------|---------------|
| FAST     | 3         | 30s     | 0.3         | Quick decisions, routing |
| BALANCED | 10        | 120s    | 0.7         | Standard analysis |
| DEEP     | 20        | 300s    | 0.7         | Complex research |
| CREATIVE | 15        | 180s    | 0.9         | Content generation |

### Logs Example

```
INFO:utils.react_strategies:Using agent-specific strategy for supervisor: fast
INFO:utils.llm_factory:Creating openrouter LLM: meta-llama/llama-3.3-70b-instruct (temp=0.3)
INFO:utils.llm_factory:Created LLM with ReactConfig(strategy=fast, max_iter=3, temp=0.3, timeout=30.0s)
INFO:agents.supervisor:Supervisor initialized with ReactConfig(strategy=fast, max_iter=3, temp=0.3, timeout=30.0s)
INFO:agents.supervisor:[Supervisor ReAct Iteration 1] Planning: Analyzing query...
INFO:agents.supervisor:[Supervisor ReAct Iteration 1] Delegating to: research_web
INFO:agents.supervisor:[Supervisor ReAct Iteration 2] Planning: Reviewing results...
INFO:agents.supervisor:[Supervisor ReAct] Completed successfully after 2 iterations
```

## Implemented Self-Reflection (FASE 3)

### Reflection Mechanism

The system now supports **self-reflection** where agents can evaluate and improve their own responses before finalizing them.

**Status:** Implemented in Writer agent, prepared for Researcher
**Default:** Disabled (enable per-agent in configuration)

#### How Reflection Works

1. **Agent generates initial response**
2. **Reflection node evaluates quality** using specialized prompts
3. **Decision made**: ACCEPT, REFINE, or INSUFFICIENT
4. **If REFINE**: Agent improves response based on feedback
5. **Loop continues** until quality threshold met or max iterations reached

#### Reflection Decisions

- **ACCEPT**: Response meets quality threshold, execution ends
- **REFINE**: Response needs improvement, create refinement
- **INSUFFICIENT**: Response completely wrong, may need restart

#### Configuration

```bash
# Global setting (master switch)
REACT_ENABLE_REFLECTION=false

# Quality threshold (0.0-1.0)
REACT_REFLECTION_QUALITY_THRESHOLD=0.7

# Maximum refinement iterations
REACT_REFLECTION_MAX_ITERATIONS=2

# Per-Agent Settings
WRITER_ENABLE_REFLECTION=false
WRITER_REFLECTION_THRESHOLD=0.8  # Stricter for content quality
WRITER_REFLECTION_MAX_ITERATIONS=3  # Allow more refinements

RESEARCHER_ENABLE_REFLECTION=false
RESEARCHER_REFLECTION_THRESHOLD=0.7
RESEARCHER_REFLECTION_MAX_ITERATIONS=2
```

#### Reflection Prompts

Each agent type has specialized reflection criteria:

**Writer (Content Quality):**
- Engagement and readability
- Structure and flow
- Tone appropriateness
- Completeness
- Grammar and style

**Researcher (Research Quality):**
- Source quality and credibility
- Research depth and thoroughness
- Information recency
- Multiple perspectives
- Factual accuracy

**Analyst (Analytical Rigor):**
- Logical reasoning
- Evidence-based conclusions
- Analysis depth
- Clarity of insights
- Actionability of recommendations

**Supervisor (General Quality):**
- Completeness of answer
- Accuracy of information
- Clarity of presentation
- Relevance to query

#### Usage Example

```python
from utils.react_reflection import get_reflection_config

# Get reflection config for agent
config = get_reflection_config("writer")

# Reflection is used automatically if enabled
# Writer agent graph: agent → reflect → refine → reflect → end
```

#### Reflection Flow (Writer Agent)

```
┌──────┐
│Agent │ (Generate initial response)
└──┬───┘
   │
   ↓
┌──────────┐
│ Reflect  │ (Evaluate quality: score, decision, suggestions)
└──┬───────┘
   │
   ├─→ [ACCEPT] → END
   │
   ├─→ [INSUFFICIENT] → END
   │
   └─→ [REFINE] ↓
              ┌───────┐
              │Refine │ (Improve based on feedback)
              └───┬───┘
                  │
                  └─→ (back to Reflect for re-evaluation)
```

#### State Tracking

Reflection adds these fields to agent state:

```python
{
    "refinement_count": 0,           # Number of refinements performed
    "reflection_decision": "accept", # Last reflection decision
    "reflection_score": 0.85,        # Last quality score
    "reflection_suggestions": []     # Improvement suggestions
}
```

#### Performance Considerations

- **Cost**: Each reflection adds ~1 LLM call per iteration
- **Latency**: Refinement loop adds ~2-5 seconds per iteration
- **Quality**: Can significantly improve output quality for creative tasks
- **Use Cases**: Best for Writer (content), less critical for Supervisor (speed)

#### Testing Results

✅ 26/26 unit tests passed:
- ReflectionDecision enum
- ReflectionResult parsing
- ReflectionConfig per-agent
- Reflection prompts
- Quality score validation
- Threshold configuration
- Integration readiness

✅ 47/47 regression tests passed (FASE 1+2 backward compatibility)

## Implemented Structured Logging (FASE 4)

### ReactLogger System

The system now includes **comprehensive structured logging** for ReAct execution, providing detailed event tracking, metrics, and execution history.

**Status:** Implemented with ReactLogger module
**Default:** Disabled (enable via configuration)

#### How Structured Logging Works

1. **Event-based tracking**: Each ReAct component logged as structured event
2. **Multiple output formats**: JSON (machine-readable) and human-readable
3. **Performance metrics**: Duration tracking, iteration counts, timestamps
4. **Execution summary**: Aggregate statistics and event counts
5. **API exposure**: History available via `/react_history/{task_id}` endpoint

#### Event Types

The system tracks 9 types of ReAct events:

```python
class ReactEventType(str, Enum):
    THOUGHT = "thought"           # Agent reasoning/planning
    ACTION = "action"             # Tool call or delegation
    OBSERVATION = "observation"   # Tool result or response
    REFLECTION = "reflection"     # Quality assessment (FASE 3)
    REFINEMENT = "refinement"     # Response improvement (FASE 3)
    COMPLETION = "completion"     # Successful finish
    ERROR = "error"              # Error during execution
    TIMEOUT = "timeout"          # Timeout exceeded
    MAX_ITERATIONS = "max_iterations"  # Iteration limit reached
```

#### ReactLogger API

```python
from utils.react_logger import create_react_logger

# Create logger for task
logger = create_react_logger(agent_name="writer", task_id="task-123")

# Log events
logger.log_thought(iteration=1, thought="I need to write an article...")
logger.log_action(iteration=1, action_name="generate_content", action_input={"topic": "AI"})
logger.log_observation(iteration=1, observation="Generated 500 words", duration_ms=1250.5)
logger.log_reflection(iteration=1, quality_score=0.75, decision="refine", reasoning="Needs more examples")
logger.log_refinement(iteration=2, refinement_count=1)
logger.log_completion(total_iterations=2, success=True, final_answer="Article complete")

# Retrieve history
history = logger.get_history()  # List of dicts
json_history = logger.get_history_json()  # JSON string
summary = logger.get_summary()  # Aggregate metrics
```

#### Event Structure

Each event is a structured dataclass with:

```python
@dataclass
class ReactEvent:
    event_type: ReactEventType     # Type of event
    iteration: int                 # ReAct iteration number
    timestamp: float               # Unix timestamp
    duration_ms: Optional[float]   # Duration in milliseconds

    # Event-specific fields
    thought: Optional[str]
    action_name: Optional[str]
    action_input: Optional[Dict]
    observation: Optional[str]
    reflection_score: Optional[float]
    reflection_decision: Optional[str]
    error_message: Optional[str]
    metadata: Optional[Dict]
```

#### Output Formats

**JSON Output (machine-readable):**
```json
{
  "event_type": "thought",
  "iteration": 1,
  "timestamp": 1696598400.123,
  "thought": "I need to search for information..."
}
```

**Human-readable Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Iteration 1 - THOUGHT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Thought: I need to search for information...
Time: 2024-10-06 15:30:00
```

#### Execution Summary

```python
summary = logger.get_summary()

# Returns:
{
    "agent_name": "writer",
    "task_id": "task-123",
    "start_time": 1696598400.0,
    "end_time": 1696598415.5,
    "total_duration_ms": 15500.0,
    "total_events": 8,
    "event_counts": {
        "thought": 2,
        "action": 1,
        "observation": 1,
        "reflection": 2,
        "refinement": 1,
        "completion": 1
    }
}
```

#### Configuration

```bash
# Enable structured logging
REACT_ENABLE_STRUCTURED_LOGGING=false  # Default: disabled

# Output format
REACT_LOG_FORMAT=human  # Options: json, human, both

# Save logs to file
REACT_SAVE_LOGS=false  # Save to logs/react/{agent}/{task_id}.json

# Log retention
REACT_LOG_RETENTION_DAYS=30  # Auto-cleanup old logs (0 = keep forever)

# Privacy settings
REACT_LOG_INCLUDE_CONTENT=true  # Include full message content (may be sensitive)

# Event filtering
REACT_LOG_EVENTS=thought,action,observation,reflection,refinement,completion,error
```

#### API Endpoint

Access execution history via REST API:

```bash
# Get ReAct history for task
GET /react_history/{task_id}

# Response guidance (history in /invoke metadata)
{
  "task_id": "task-123",
  "agent_id": "writer",
  "note": "ReAct history is included in the /invoke response metadata",
  "recommendation": "Use POST /invoke and check metadata.react_history"
}

# Actual history in /invoke response
POST /invoke
{
  "task_id": "task-123",
  "status": "success",
  "result": "...",
  "metadata": {
    "react_history": [
      {"iteration": 1, "event_type": "thought", ...},
      {"iteration": 1, "event_type": "action", ...},
      ...
    ]
  }
}
```

#### Integration with Agents

ReactLogger is ready for integration in all agents:

```python
# In agent graph
def call_model(state):
    # Create logger
    logger = create_react_logger(
        agent_name="writer",
        task_id=state.get("task_id", "unknown")
    )

    # Log thought
    logger.log_thought(
        iteration=state["iteration_count"],
        thought=response.content
    )

    # Store in state
    state["react_logger"] = logger
```

#### Performance Metrics

The logger tracks:
- **Per-event duration**: Time spent in each step
- **Total execution time**: Start to completion
- **Iteration efficiency**: Events per iteration
- **Success/failure rates**: Completion vs error events

#### Backward Compatibility

ReactLogger maintains compatibility with existing `react_history` format:

```python
# Existing format still works
state["react_history"] = [
    {"iteration": 1, "timestamp": ..., "action": "...", "observation": "..."}
]

# New ReactLogger format is additive
logger.get_history()  # Returns same structure, enhanced
```

#### Testing Results

✅ 19/19 unit tests passed:
- ReactEventType enum validation
- ReactEvent dataclass methods (to_dict, to_json, to_human_readable)
- ReactLogger creation and all logging methods
- History retrieval (get_history, get_history_json, get_summary)
- Complete ReAct cycle integration
- Reflection cycle integration
- Backward compatibility with react_history

✅ 73/73 regression tests passed (FASE 1+2+3 backward compatibility)

#### Use Cases

**Development/Debugging:**
- Human-readable logs for understanding agent behavior
- Step-by-step execution tracking
- Error diagnosis and troubleshooting

**Production Monitoring:**
- JSON logs for automated analysis
- Performance metrics dashboard
- Execution pattern analysis

**Auditing/Compliance:**
- Complete execution trail
- Decision point tracking
- Quality assessment history

**Optimization:**
- Identify bottlenecks
- Measure refinement effectiveness
- Compare strategy performance

#### Files Created/Modified

**New Files:**
- `utils/react_logger.py` - ReactLogger implementation (500+ lines)
- `tests/test_fase4_logging.py` - 19 unit tests

**Modified Files:**
- `agents/writer.py` - ReactLogger import added
- `servers/writer_server.py` - `/react_history/{task_id}` endpoint, metadata enhancement
- `tests/conftest.py` - fase4 marker registered
- `.env.example` - REACT STRUCTURED LOGGING section

## Next Steps (Future Phases)

### FASE 5: Human-in-the-Loop
- Approval mechanisms
- Interactive confirmation
- Feedback loops

### FASE 6: Advanced Reasoning Modes
- Chain-of-Thought (CoT)
- Tree-of-Thought (ToT)
- Adaptive reasoning

### FASE 7: Metrics & Optimization
- Performance tracking
- Cost analysis
- Automatic tuning

## Files Modified

### Core Implementation
- `config.py` - ReAct configuration parameters (FASE 1, 2, 3)
- `schemas/agent_state.py` - State metadata fields
- `agents/researcher.py` - Full ReAct controls + async tools + reflection prepared
- `agents/analyst.py` - Basic ReAct controls
- `agents/writer.py` - Full ReAct controls + self-reflection + structured logging
- `agents/supervisor.py` - Full ReAct controls + delegation tracking
- `utils/react_strategies.py` - Reasoning strategies (FASE 2)
- `utils/react_reflection.py` - Self-reflection system (FASE 3)
- `utils/react_logger.py` - Structured logging system (FASE 4)

### Testing
- `tests/conftest.py` - Pytest configuration and fixtures
- `tests/test_fase2_strategies.py` - 30 unit tests for strategies
- `tests/test_fase3_reflection.py` - 26 unit tests for reflection
- `tests/test_fase4_logging.py` - 19 unit tests for structured logging
- `tests/test_regression_fase1.py` - 23 regression tests for FASE 1
- `tests/run_tests.sh` - Test runner script

### Documentation
- `.env.example` - Environment variable examples (all phases)
- `REACT_IMPLEMENTATION_CHECKLIST.md` - Detailed implementation tracking
- `docs/REACT_CONTROLS.md` - This document

## References

- [ReAct Paper](https://arxiv.org/abs/2210.03629) - Original research
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/) - Framework reference
- [REACT_IMPLEMENTATION_CHECKLIST.md](../REACT_IMPLEMENTATION_CHECKLIST.md) - Full implementation plan
