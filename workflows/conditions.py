"""
Conditional Routing Logic for Workflows

Evaluates conditions on workflow state to determine next node routing.
Supports multiple operators and state field access.
"""

import logging
import re
from typing import Optional, Any, Dict
from schemas.workflow_schemas import (
    ConditionalEdge,
    WorkflowCondition,
    ConditionOperator,
    WorkflowState
)

logger = logging.getLogger(__name__)


class ConditionEvaluator:
    """Evaluates conditional routing rules"""

    def evaluate_edge(
        self,
        conditional_edge: ConditionalEdge,
        state: WorkflowState
    ) -> str:
        """
        Evaluate conditional edge and return next node.

        Args:
            conditional_edge: Conditional edge definition
            state: Current workflow state

        Returns:
            Node ID to route to
        """
        for condition in conditional_edge.conditions:
            if self._evaluate_condition(condition, state):
                logger.info(
                    f"Condition matched: {condition.field} {condition.operator} {condition.value} "
                    f"→ routing to '{condition.next_node}'"
                )
                return condition.next_node

        logger.info(f"No condition matched, using default: '{conditional_edge.default}'")
        return conditional_edge.default

    def _evaluate_condition(
        self,
        condition: WorkflowCondition,
        state: WorkflowState
    ) -> bool:
        """
        Evaluate a single condition.

        Args:
            condition: Condition to evaluate
            state: Current workflow state

        Returns:
            True if condition passes
        """
        # Get field value from state
        field_value = self._get_field_value(condition.field, state)

        if field_value is None:
            logger.warning(f"Field '{condition.field}' not found in state")
            return False

        # Evaluate based on operator
        try:
            result = self._apply_operator(
                field_value,
                condition.operator,
                condition.value
            )
            logger.debug(
                f"Condition evaluation: {condition.field}={field_value} "
                f"{condition.operator} {condition.value} → {result}"
            )
            return result

        except Exception as e:
            logger.error(f"Error evaluating condition: {e}")
            return False

    def _get_field_value(self, field: str, state: WorkflowState) -> Optional[Any]:
        """
        Get field value from state, supporting nested access.

        Examples:
            "sentiment_score" → state.sentiment_score
            "custom_metadata.quality" → state.custom_metadata["quality"]
            "node_outputs.analyze" → state.node_outputs["analyze"]
        """
        # Direct attribute access
        if hasattr(state, field):
            return getattr(state, field)

        # Nested access (e.g., "custom_metadata.quality")
        if "." in field:
            parts = field.split(".")
            value = state
            for part in parts:
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value

        # Dict access in custom_metadata
        if field in state.custom_metadata:
            return state.custom_metadata[field]

        return None

    def _apply_operator(
        self,
        field_value: Any,
        operator: ConditionOperator,
        comparison_value: Any
    ) -> bool:
        """Apply comparison operator"""

        if operator == ConditionOperator.EQUALS:
            return field_value == comparison_value

        elif operator == ConditionOperator.NOT_EQUALS:
            return field_value != comparison_value

        elif operator == ConditionOperator.GREATER_THAN:
            return float(field_value) > float(comparison_value)

        elif operator == ConditionOperator.LESS_THAN:
            return float(field_value) < float(comparison_value)

        elif operator == ConditionOperator.GREATER_EQUAL:
            return float(field_value) >= float(comparison_value)

        elif operator == ConditionOperator.LESS_EQUAL:
            return float(field_value) <= float(comparison_value)

        elif operator == ConditionOperator.CONTAINS:
            return str(comparison_value).lower() in str(field_value).lower()

        elif operator == ConditionOperator.NOT_CONTAINS:
            return str(comparison_value).lower() not in str(field_value).lower()

        elif operator == ConditionOperator.IN:
            if isinstance(comparison_value, (list, tuple, set)):
                return field_value in comparison_value
            return False

        elif operator == ConditionOperator.NOT_IN:
            if isinstance(comparison_value, (list, tuple, set)):
                return field_value not in comparison_value
            return True

        else:
            logger.warning(f"Unknown operator: {operator}")
            return False


def extract_sentiment_score(text: str) -> float:
    """
    Extract sentiment score from text.

    Simple heuristic: count positive vs negative keywords.
    For production, use proper sentiment analysis model.

    Returns:
        Score between 0.0 (negative) and 1.0 (positive)
    """
    positive_keywords = [
        "good", "great", "excellent", "positive", "success", "win",
        "benefit", "advantage", "strong", "growth", "improve"
    ]
    negative_keywords = [
        "bad", "poor", "negative", "fail", "loss", "risk",
        "weak", "decline", "problem", "issue", "concern"
    ]

    text_lower = text.lower()

    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)

    total = positive_count + negative_count
    if total == 0:
        return 0.5  # Neutral

    return positive_count / total


def extract_keywords(text: str, keywords: list[str]) -> list[str]:
    """
    Extract matching keywords from text.

    Args:
        text: Text to search
        keywords: Keywords to find

    Returns:
        List of found keywords
    """
    found = []
    text_lower = text.lower()

    for keyword in keywords:
        if keyword.lower() in text_lower:
            found.append(keyword)

    return found
