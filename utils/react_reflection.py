"""
ReAct Self-Reflection Module (FASE 3)

Implements reflection mechanism for agent responses:
- Quality assessment of generated responses
- Decision to refine or accept answer
- Structured feedback for improvement
- Configurable reflection strategies
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Literal
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
import logging

logger = logging.getLogger(__name__)


class ReflectionDecision(str, Enum):
    """Decision after reflection."""
    ACCEPT = "accept"           # Response is satisfactory
    REFINE = "refine"          # Response needs improvement
    INSUFFICIENT = "insufficient"  # Response incomplete or incorrect


@dataclass
class ReflectionResult:
    """Result of reflection analysis."""
    decision: ReflectionDecision
    quality_score: float  # 0.0-1.0
    reasoning: str
    suggestions: List[str]
    should_continue: bool

    def __repr__(self) -> str:
        return (
            f"ReflectionResult(decision={self.decision.value}, "
            f"quality={self.quality_score:.2f}, "
            f"continue={self.should_continue})"
        )


@dataclass
class ReflectionConfig:
    """Configuration for reflection behavior."""
    enabled: bool = False
    quality_threshold: float = 0.7  # Accept if score >= threshold
    max_refinement_iterations: int = 2  # Max times to refine
    require_complete_answer: bool = True
    require_sources: bool = False  # For research tasks

    @classmethod
    def from_agent(cls, agent_name: str) -> "ReflectionConfig":
        """Get reflection config for specific agent."""
        from config_legacy import settings

        # Check if reflection is enabled for this agent
        enabled_key = f"{agent_name}_enable_reflection"
        enabled = getattr(settings, enabled_key, False)

        # Get agent-specific threshold if exists
        threshold_key = f"{agent_name}_reflection_threshold"
        threshold = getattr(settings, threshold_key, 0.7)

        # Get max refinement iterations
        max_iter_key = f"{agent_name}_reflection_max_iterations"
        max_iter = getattr(settings, max_iter_key, 2)

        # Special requirements for different agents
        require_sources = agent_name == "researcher"

        return cls(
            enabled=enabled,
            quality_threshold=threshold,
            max_refinement_iterations=max_iter,
            require_complete_answer=True,
            require_sources=require_sources
        )


class ReflectionPrompts:
    """Prompt templates for reflection."""

    GENERAL_REFLECTION = """You are evaluating the quality of a response to determine if it needs improvement.

Original Query:
{query}

Current Response:
{response}

Evaluate this response on the following criteria:
1. **Completeness**: Does it fully answer the question?
2. **Accuracy**: Is the information correct and reliable?
3. **Clarity**: Is it well-structured and easy to understand?
4. **Relevance**: Does it stay focused on the query?

Provide your evaluation in this format:

QUALITY_SCORE: [0.0-1.0]
DECISION: [ACCEPT/REFINE/INSUFFICIENT]
REASONING: [Brief explanation of your decision]
SUGGESTIONS: [Specific improvements needed, if any]

If QUALITY_SCORE >= 0.7, you should ACCEPT.
If the response is completely wrong or missing, mark as INSUFFICIENT.
Otherwise, mark as REFINE and provide specific suggestions."""

    RESEARCHER_REFLECTION = """You are evaluating a research response.

Original Query:
{query}

Current Response:
{response}

Evaluate specifically for research quality:
1. **Source Quality**: Are credible sources cited?
2. **Depth**: Is the research thorough enough?
3. **Recency**: Is the information current?
4. **Coverage**: Are multiple perspectives included?
5. **Factual Accuracy**: Are claims verifiable?

Provide evaluation in this format:

QUALITY_SCORE: [0.0-1.0]
DECISION: [ACCEPT/REFINE/INSUFFICIENT]
REASONING: [Brief explanation]
SUGGESTIONS: [What to improve or add]

Research responses should include sources. If missing, suggest REFINE."""

    WRITER_REFLECTION = """You are evaluating written content quality.

Original Request:
{query}

Current Content:
{response}

Evaluate for writing quality:
1. **Engagement**: Is it interesting and readable?
2. **Structure**: Is it well-organized with clear flow?
3. **Tone**: Is the tone appropriate for the audience?
4. **Completeness**: Does it cover all requested points?
5. **Grammar**: Is it well-written?

Provide evaluation in this format:

QUALITY_SCORE: [0.0-1.0]
DECISION: [ACCEPT/REFINE/INSUFFICIENT]
REASONING: [Brief explanation]
SUGGESTIONS: [How to improve the content]

Creative content should be engaging and well-structured."""

    ANALYST_REFLECTION = """You are evaluating an analytical response.

Original Query:
{query}

Current Analysis:
{response}

Evaluate for analytical quality:
1. **Logic**: Is the reasoning sound?
2. **Evidence**: Are conclusions supported by data?
3. **Depth**: Is the analysis thorough?
4. **Clarity**: Are insights clearly explained?
5. **Actionability**: Are recommendations practical?

Provide evaluation in this format:

QUALITY_SCORE: [0.0-1.0]
DECISION: [ACCEPT/REFINE/INSUFFICIENT]
REASONING: [Brief explanation]
SUGGESTIONS: [What to strengthen or add]

Analysis should be logical, evidence-based, and actionable."""

    @classmethod
    def get_prompt_for_agent(cls, agent_name: str) -> str:
        """Get reflection prompt for specific agent type."""
        prompts = {
            "researcher": cls.RESEARCHER_REFLECTION,
            "writer": cls.WRITER_REFLECTION,
            "analyst": cls.ANALYST_REFLECTION,
            "supervisor": cls.GENERAL_REFLECTION
        }
        return prompts.get(agent_name, cls.GENERAL_REFLECTION)


def parse_reflection_response(response_text: str) -> ReflectionResult:
    """Parse LLM reflection response into structured result."""
    lines = response_text.strip().split('\n')

    quality_score = 0.7
    decision = ReflectionDecision.ACCEPT
    reasoning = "No reasoning provided"
    suggestions = []

    for line in lines:
        line = line.strip()

        if line.startswith("QUALITY_SCORE:"):
            try:
                score_str = line.split(":", 1)[1].strip()
                quality_score = float(score_str)
                quality_score = max(0.0, min(1.0, quality_score))
            except (ValueError, IndexError):
                logger.warning(f"Failed to parse quality score: {line}")

        elif line.startswith("DECISION:"):
            decision_str = line.split(":", 1)[1].strip().upper()
            if decision_str in ["ACCEPT", "REFINE", "INSUFFICIENT"]:
                decision = ReflectionDecision(decision_str.lower())

        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()

        elif line.startswith("SUGGESTIONS:"):
            suggestion_text = line.split(":", 1)[1].strip()
            if suggestion_text and suggestion_text != "None":
                suggestions.append(suggestion_text)

    # Determine if should continue refining
    should_continue = decision == ReflectionDecision.REFINE

    return ReflectionResult(
        decision=decision,
        quality_score=quality_score,
        reasoning=reasoning,
        suggestions=suggestions,
        should_continue=should_continue
    )


async def reflect_on_response(
    query: str,
    response: str,
    agent_name: str,
    llm,
    iteration: int = 0,
    config: Optional[ReflectionConfig] = None
) -> ReflectionResult:
    """
    Perform reflection on agent response.

    Args:
        query: Original user query
        response: Agent's current response
        agent_name: Name of agent (for prompt selection)
        llm: Language model for reflection
        iteration: Current refinement iteration
        config: Reflection configuration

    Returns:
        ReflectionResult with decision and feedback
    """
    if config is None:
        config = ReflectionConfig.from_agent(agent_name)

    # If reflection disabled, always accept
    if not config.enabled:
        return ReflectionResult(
            decision=ReflectionDecision.ACCEPT,
            quality_score=1.0,
            reasoning="Reflection disabled",
            suggestions=[],
            should_continue=False
        )

    # If max refinement iterations reached, accept
    if iteration >= config.max_refinement_iterations:
        logger.info(f"Max refinement iterations ({config.max_refinement_iterations}) reached")
        return ReflectionResult(
            decision=ReflectionDecision.ACCEPT,
            quality_score=0.7,
            reasoning="Maximum refinement iterations reached",
            suggestions=[],
            should_continue=False
        )

    # Get agent-specific reflection prompt
    prompt_template = ReflectionPrompts.get_prompt_for_agent(agent_name)
    prompt = prompt_template.format(query=query, response=response)

    # Call LLM for reflection
    logger.info(f"[{agent_name} Reflection {iteration + 1}] Evaluating response quality...")

    try:
        messages = [HumanMessage(content=prompt)]
        reflection_response = await llm.ainvoke(messages)
        reflection_text = reflection_response.content

        # Parse reflection response
        result = parse_reflection_response(reflection_text)

        logger.info(f"[{agent_name} Reflection {iteration + 1}] {result}")

        if result.suggestions:
            logger.info(f"[{agent_name} Reflection {iteration + 1}] Suggestions: {', '.join(result.suggestions)}")

        return result

    except Exception as e:
        logger.error(f"Reflection failed: {e}")
        # On error, accept the response
        return ReflectionResult(
            decision=ReflectionDecision.ACCEPT,
            quality_score=0.7,
            reasoning=f"Reflection error: {e}",
            suggestions=[],
            should_continue=False
        )


def create_refinement_prompt(
    original_query: str,
    current_response: str,
    reflection_result: ReflectionResult
) -> str:
    """Create prompt for refining response based on reflection feedback."""
    suggestions_text = "\n".join(f"- {s}" for s in reflection_result.suggestions)

    prompt = f"""Your previous response needs improvement.

Original Query:
{original_query}

Your Previous Response:
{current_response}

Reflection Feedback:
Quality Score: {reflection_result.quality_score:.2f}
Reasoning: {reflection_result.reasoning}

Suggestions for Improvement:
{suggestions_text}

Please provide an improved response that addresses the feedback above.
Focus on the specific suggestions while maintaining what was already good.
"""

    return prompt


# Convenience functions

def get_reflection_config(agent_name: str) -> ReflectionConfig:
    """Get reflection configuration for agent."""
    return ReflectionConfig.from_agent(agent_name)


def is_reflection_enabled(agent_name: str) -> bool:
    """Check if reflection is enabled for agent."""
    config = get_reflection_config(agent_name)
    return config.enabled
