"""
Chain-of-Thought (CoT) Reasoning Support (FASE 6)

Provides explicit chain-of-thought prompting and step tracking.
Enhances reasoning transparency and debuggability.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ReasoningStep:
    """
    Represents a single step in chain-of-thought reasoning.

    Attributes:
        step_number: Sequential step number (1-indexed)
        thought: The reasoning/thinking text
        action: Optional action taken at this step
        observation: Optional observation from action
        timestamp: When this step was created
        confidence: Self-assessed confidence (0.0-1.0)
    """
    step_number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_number": self.step_number,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence
        }


@dataclass
class ChainOfThought:
    """
    Manages a chain-of-thought reasoning process.

    Tracks all reasoning steps and provides analysis capabilities.
    """
    task_description: str
    steps: List[ReasoningStep] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def add_step(
        self,
        thought: str,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        confidence: float = 1.0
    ) -> ReasoningStep:
        """
        Add a new reasoning step to the chain.

        Args:
            thought: The reasoning/thinking text
            action: Optional action taken
            observation: Optional observation from action
            confidence: Self-assessed confidence (0.0-1.0)

        Returns:
            The created ReasoningStep
        """
        step_number = len(self.steps) + 1
        step = ReasoningStep(
            step_number=step_number,
            thought=thought,
            action=action,
            observation=observation,
            confidence=confidence
        )
        self.steps.append(step)

        logger.debug(f"CoT Step {step_number}: {thought[:100]}...")

        return step

    def complete(self):
        """Mark the chain as completed."""
        self.completed_at = datetime.now()
        logger.info(
            f"CoT completed: {len(self.steps)} steps in "
            f"{(self.completed_at - self.started_at).total_seconds():.1f}s"
        )

    def get_summary(self) -> str:
        """
        Generate a summary of the reasoning chain.

        Returns:
            Human-readable summary
        """
        if not self.steps:
            return "No reasoning steps recorded"

        duration = (
            (self.completed_at or datetime.now()) - self.started_at
        ).total_seconds()

        avg_confidence = sum(s.confidence for s in self.steps) / len(self.steps)

        summary = [
            f"Chain-of-Thought Summary:",
            f"- Task: {self.task_description}",
            f"- Steps: {len(self.steps)}",
            f"- Duration: {duration:.1f}s",
            f"- Avg Confidence: {avg_confidence:.2f}",
            f"",
            "Steps:"
        ]

        for step in self.steps:
            summary.append(
                f"  {step.step_number}. {step.thought[:80]}... "
                f"(confidence: {step.confidence:.2f})"
            )

        return "\n".join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_description": self.task_description,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_steps": len(self.steps)
        }


def get_cot_system_prompt() -> str:
    """
    Get the system prompt for Chain-of-Thought reasoning.

    Returns:
        System prompt that encourages step-by-step thinking
    """
    return """You are an expert problem solver that uses explicit Chain-of-Thought reasoning.

For each task, you must:
1. Break down the problem into clear, logical steps
2. Explain your reasoning for each step explicitly
3. State any assumptions you're making
4. Evaluate the confidence in your reasoning
5. Proceed step-by-step until you reach a conclusion

Format your thinking as:
Step 1: [State what you need to do first]
Reasoning: [Explain why this step is necessary]
Confidence: [Rate 0-100%]

Step 2: [State the next step]
Reasoning: [Explain the logic]
Confidence: [Rate 0-100%]

... continue until complete ...

Final Answer: [Your conclusion based on the chain of reasoning]

Be thorough, explicit, and methodical in your thinking."""


def get_cot_user_prompt(task: str) -> str:
    """
    Get the user prompt for a CoT task.

    Args:
        task: The task to solve

    Returns:
        Formatted user prompt
    """
    return f"""Task: {task}

Please solve this task using explicit Chain-of-Thought reasoning.
Break down your thinking into clear steps, explain your reasoning,
and assess your confidence at each stage."""


def extract_reasoning_steps(response: str) -> List[Dict[str, Any]]:
    """
    Extract reasoning steps from a CoT response.

    Args:
        response: The LLM response containing CoT reasoning

    Returns:
        List of extracted steps with thought, reasoning, confidence
    """
    steps = []
    lines = response.split("\n")

    current_step = None
    current_reasoning = None
    current_confidence = 1.0

    for line in lines:
        line = line.strip()

        # Detect step markers
        if line.startswith("Step "):
            # Save previous step if exists
            if current_step:
                steps.append({
                    "thought": current_step,
                    "reasoning": current_reasoning,
                    "confidence": current_confidence
                })

            # Start new step
            current_step = line
            current_reasoning = None
            current_confidence = 1.0

        elif line.startswith("Reasoning:"):
            current_reasoning = line.replace("Reasoning:", "").strip()

        elif line.startswith("Confidence:"):
            # Extract percentage or decimal
            conf_str = line.replace("Confidence:", "").strip()
            try:
                if "%" in conf_str:
                    current_confidence = float(conf_str.replace("%", "")) / 100.0
                else:
                    current_confidence = float(conf_str)
            except ValueError:
                current_confidence = 1.0

    # Save last step
    if current_step:
        steps.append({
            "thought": current_step,
            "reasoning": current_reasoning,
            "confidence": current_confidence
        })

    return steps


def validate_cot_response(response: str, min_steps: int = 2) -> bool:
    """
    Validate that a response contains proper CoT reasoning.

    Args:
        response: The response to validate
        min_steps: Minimum number of steps required

    Returns:
        True if valid CoT response, False otherwise
    """
    steps = extract_reasoning_steps(response)

    if len(steps) < min_steps:
        logger.warning(
            f"CoT validation failed: only {len(steps)} steps "
            f"(minimum {min_steps} required)"
        )
        return False

    # Check that steps have reasoning
    steps_with_reasoning = sum(
        1 for s in steps if s.get("reasoning")
    )

    if steps_with_reasoning < min_steps:
        logger.warning(
            f"CoT validation failed: only {steps_with_reasoning} steps "
            f"have explicit reasoning"
        )
        return False

    logger.info(f"CoT validation passed: {len(steps)} valid steps")
    return True
