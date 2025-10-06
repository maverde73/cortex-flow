"""
Tests for FASE 6: Advanced Reasoning Modes

Tests Chain-of-Thought (CoT), Tree-of-Thought (ToT), and Adaptive reasoning.
"""

import pytest
import time
from datetime import datetime

from utils.react_strategies import ReactStrategy, ReactConfig
from utils.react_strategies import get_cot_explicit_config, get_tree_of_thought_config, get_adaptive_config
from utils.react_cot import (
    ReasoningStep, ChainOfThought,
    get_cot_system_prompt, get_cot_user_prompt,
    extract_reasoning_steps, validate_cot_response
)
from utils.react_tot import (
    BranchStatus, ReasoningBranch, TreeOfThought,
    get_tot_system_prompt, get_tot_user_prompt,
    extract_branches
)
from utils.react_adaptive import (
    ComplexityLevel, PerformanceMetrics, StrategyTransition,
    AdaptiveReasoning, create_adaptive_session
)


# ============================================================================
# ReactStrategy Enum Tests (FASE 6 extensions)
# ============================================================================

class TestReactStrategyFase6:
    """Test FASE 6 strategy enum extensions."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_cot_explicit_strategy_exists(self):
        """Test COT_EXPLICIT strategy is available."""
        assert ReactStrategy.COT_EXPLICIT.value == "cot_explicit"

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_tree_of_thought_strategy_exists(self):
        """Test TREE_OF_THOUGHT strategy is available."""
        assert ReactStrategy.TREE_OF_THOUGHT.value == "tree_of_thought"

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_adaptive_strategy_exists(self):
        """Test ADAPTIVE strategy is available."""
        assert ReactStrategy.ADAPTIVE.value == "adaptive"

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_fase6_strategies_from_string(self):
        """Test all FASE 6 strategies can be created from strings."""
        assert ReactStrategy.from_string("cot_explicit") == ReactStrategy.COT_EXPLICIT
        assert ReactStrategy.from_string("tree_of_thought") == ReactStrategy.TREE_OF_THOUGHT
        assert ReactStrategy.from_string("adaptive") == ReactStrategy.ADAPTIVE


# ============================================================================
# ReactConfig Tests (FASE 6)
# ============================================================================

class TestReactConfigFase6:
    """Test FASE 6 strategy configurations."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_cot_explicit_config(self):
        """Test COT_EXPLICIT configuration."""
        config = get_cot_explicit_config()
        assert config.strategy == ReactStrategy.COT_EXPLICIT
        assert config.max_iterations == 15
        assert config.temperature == 0.5
        assert config.timeout_seconds == 240.0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_tree_of_thought_config(self):
        """Test TREE_OF_THOUGHT configuration."""
        config = get_tree_of_thought_config()
        assert config.strategy == ReactStrategy.TREE_OF_THOUGHT
        assert config.max_iterations == 25
        assert config.temperature == 0.6
        assert config.timeout_seconds == 360.0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_adaptive_config(self):
        """Test ADAPTIVE configuration."""
        config = get_adaptive_config()
        assert config.strategy == ReactStrategy.ADAPTIVE
        assert config.max_iterations == 30  # Higher ceiling for escalation
        assert config.temperature == 0.7
        assert config.timeout_seconds == 300.0


# ============================================================================
# Chain-of-Thought Tests
# ============================================================================

class TestReasoningStep:
    """Test ReasoningStep dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_reasoning_step_creation(self):
        """Test creating a reasoning step."""
        step = ReasoningStep(
            step_number=1,
            thought="I need to analyze the problem",
            confidence=0.9
        )
        assert step.step_number == 1
        assert step.thought == "I need to analyze the problem"
        assert step.confidence == 0.9
        assert step.action is None
        assert step.observation is None

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_reasoning_step_with_action(self):
        """Test reasoning step with action and observation."""
        step = ReasoningStep(
            step_number=2,
            thought="Search for information",
            action="tavily_search",
            observation="Found 5 results",
            confidence=0.8
        )
        assert step.action == "tavily_search"
        assert step.observation == "Found 5 results"

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_reasoning_step_to_dict(self):
        """Test serialization to dictionary."""
        step = ReasoningStep(
            step_number=1,
            thought="Test thought",
            confidence=0.95
        )
        data = step.to_dict()
        assert data["step_number"] == 1
        assert data["thought"] == "Test thought"
        assert data["confidence"] == 0.95
        assert "timestamp" in data


class TestChainOfThought:
    """Test ChainOfThought manager."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_chain_creation(self):
        """Test creating a chain-of-thought."""
        chain = ChainOfThought(task_description="Solve math problem")
        assert chain.task_description == "Solve math problem"
        assert len(chain.steps) == 0
        assert chain.completed_at is None

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_add_steps(self):
        """Test adding reasoning steps."""
        chain = ChainOfThought(task_description="Test task")

        step1 = chain.add_step("First thought", confidence=0.9)
        assert step1.step_number == 1
        assert len(chain.steps) == 1

        step2 = chain.add_step("Second thought", action="search", confidence=0.8)
        assert step2.step_number == 2
        assert len(chain.steps) == 2

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_chain_completion(self):
        """Test completing a chain."""
        chain = ChainOfThought(task_description="Test task")
        chain.add_step("Step 1")
        chain.add_step("Step 2")

        chain.complete()
        assert chain.completed_at is not None
        assert chain.completed_at > chain.started_at

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_chain_summary(self):
        """Test generating chain summary."""
        chain = ChainOfThought(task_description="Analyze data")
        chain.add_step("Load data", confidence=1.0)
        chain.add_step("Process data", confidence=0.9)
        chain.add_step("Generate insights", confidence=0.8)
        chain.complete()

        summary = chain.get_summary()
        assert "Analyze data" in summary
        assert "3" in summary  # 3 steps
        assert "Steps:" in summary

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_chain_serialization(self):
        """Test chain serialization."""
        chain = ChainOfThought(task_description="Test")
        chain.add_step("Step 1")
        chain.complete()

        data = chain.to_dict()
        assert data["task_description"] == "Test"
        assert data["total_steps"] == 1
        assert len(data["steps"]) == 1


class TestCoTPrompts:
    """Test Chain-of-Thought prompts."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_cot_system_prompt(self):
        """Test CoT system prompt generation."""
        prompt = get_cot_system_prompt()
        assert "Chain-of-Thought" in prompt
        assert "step-by-step" in prompt
        assert "reasoning" in prompt.lower()

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_cot_user_prompt(self):
        """Test CoT user prompt generation."""
        task = "Calculate 15% of 250"
        prompt = get_cot_user_prompt(task)
        assert task in prompt
        assert "Chain-of-Thought" in prompt


class TestCoTExtraction:
    """Test extracting CoT from responses."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_extract_reasoning_steps(self):
        """Test extracting steps from CoT response."""
        response = """
Step 1: Identify the problem type
Reasoning: This is a percentage calculation
Confidence: 95%

Step 2: Calculate 15% of 250
Reasoning: 15/100 * 250 = 37.5
Confidence: 100%

Final Answer: 37.5
"""
        steps = extract_reasoning_steps(response)
        assert len(steps) == 2
        assert steps[0]["confidence"] == 0.95
        assert steps[1]["confidence"] == 1.0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_validate_cot_response_valid(self):
        """Test validation passes for valid CoT response."""
        response = """
Step 1: First step
Reasoning: Why we do this
Confidence: 80%

Step 2: Second step
Reasoning: Next logical step
Confidence: 90%
"""
        assert validate_cot_response(response, min_steps=2) is True

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_validate_cot_response_invalid(self):
        """Test validation fails for insufficient steps."""
        response = """
Step 1: Only one step
Reasoning: Not enough
"""
        assert validate_cot_response(response, min_steps=2) is False


# ============================================================================
# Tree-of-Thought Tests
# ============================================================================

class TestReasoningBranch:
    """Test ReasoningBranch dataclass."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_creation(self):
        """Test creating a reasoning branch."""
        branch = ReasoningBranch(
            branch_id="branch_1",
            parent_id=None,
            thought="First approach: use method A"
        )
        assert branch.branch_id == "branch_1"
        assert branch.parent_id is None
        assert branch.status == BranchStatus.EXPLORING
        assert branch.score == 0.0
        assert branch.depth == 0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_add_action(self):
        """Test adding actions to branch."""
        branch = ReasoningBranch(
            branch_id="branch_1",
            parent_id=None,
            thought="Test approach"
        )
        branch.add_action("search", "Found data")
        branch.add_action("analyze", "Processed data")

        assert len(branch.actions) == 2
        assert len(branch.observations) == 2
        assert branch.actions[0] == "search"
        assert branch.observations[1] == "Processed data"

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_evaluation(self):
        """Test evaluating a branch."""
        branch = ReasoningBranch(
            branch_id="branch_1",
            parent_id=None,
            thought="Test"
        )
        branch.evaluate(0.85)

        assert branch.score == 0.85
        assert branch.status == BranchStatus.EVALUATED

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_status_transitions(self):
        """Test branch status transitions."""
        branch = ReasoningBranch(branch_id="b1", parent_id=None, thought="Test")

        assert branch.status == BranchStatus.EXPLORING

        branch.evaluate(0.7)
        assert branch.status == BranchStatus.EVALUATED

        branch.select()
        assert branch.status == BranchStatus.SELECTED

        # Test rejection
        branch2 = ReasoningBranch(branch_id="b2", parent_id=None, thought="Test")
        branch2.reject()
        assert branch2.status == BranchStatus.REJECTED

        # Test failure
        branch3 = ReasoningBranch(branch_id="b3", parent_id=None, thought="Test")
        branch3.fail()
        assert branch3.status == BranchStatus.FAILED


class TestTreeOfThought:
    """Test TreeOfThought manager."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_tree_creation(self):
        """Test creating a tree-of-thought."""
        tree = TreeOfThought(
            task_description="Optimize algorithm",
            max_branches=5,
            max_depth=3
        )
        assert tree.task_description == "Optimize algorithm"
        assert tree.max_branches == 5
        assert tree.max_depth == 3
        assert len(tree.branches) == 0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_create_branches(self):
        """Test creating branches."""
        tree = TreeOfThought(task_description="Test task", max_branches=3)

        branch1 = tree.create_branch("Approach 1: Greedy algorithm")
        assert branch1.branch_id == "branch_1"
        assert branch1.depth == 0

        branch2 = tree.create_branch("Approach 2: Dynamic programming")
        assert branch2.branch_id == "branch_2"

        assert len(tree.branches) == 2

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_depth_limit(self):
        """Test max depth enforcement."""
        tree = TreeOfThought(task_description="Test", max_depth=2)

        b1 = tree.create_branch("Level 0")
        b2 = tree.create_branch("Level 1", parent_id=b1.branch_id)
        b3 = tree.create_branch("Level 2", parent_id=b2.branch_id)  # Should be None (exceeds depth)

        assert b1.depth == 0
        assert b2.depth == 1
        assert b3 is None  # Exceeded max depth

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_branch_count_limit(self):
        """Test max branches enforcement."""
        tree = TreeOfThought(task_description="Test", max_branches=2)

        b1 = tree.create_branch("Branch 1")
        b2 = tree.create_branch("Branch 2")
        b3 = tree.create_branch("Branch 3")  # Should be None (exceeds count)

        assert len(tree.branches) == 2
        assert b3 is None

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_get_children(self):
        """Test retrieving child branches."""
        tree = TreeOfThought(task_description="Test")

        parent = tree.create_branch("Parent")
        child1 = tree.create_branch("Child 1", parent_id=parent.branch_id)
        child2 = tree.create_branch("Child 2", parent_id=parent.branch_id)

        children = tree.get_children(parent.branch_id)
        assert len(children) == 2
        assert child1 in children
        assert child2 in children

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_select_best_branch(self):
        """Test selecting best branch by score."""
        tree = TreeOfThought(task_description="Test")

        b1 = tree.create_branch("Approach 1")
        b1.evaluate(0.6)

        b2 = tree.create_branch("Approach 2")
        b2.evaluate(0.9)  # Best

        b3 = tree.create_branch("Approach 3")
        b3.evaluate(0.7)

        best = tree.select_best_branch()
        assert best.branch_id == b2.branch_id
        assert best.status == BranchStatus.SELECTED
        assert b1.status == BranchStatus.REJECTED
        assert b3.status == BranchStatus.REJECTED

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_get_selected_path(self):
        """Test retrieving selected path from root to leaf."""
        tree = TreeOfThought(task_description="Test")

        b1 = tree.create_branch("Root")
        b1.evaluate(0.8)

        b2 = tree.create_branch("Child", parent_id=b1.branch_id)
        b2.evaluate(0.9)

        tree.selected_branch_id = b2.branch_id
        b2.select()

        path = tree.get_selected_path()
        assert len(path) == 2
        assert path[0].branch_id == b1.branch_id
        assert path[1].branch_id == b2.branch_id


# ============================================================================
# Adaptive Reasoning Tests
# ============================================================================

class TestPerformanceMetrics:
    """Test PerformanceMetrics tracking."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_metrics_creation(self):
        """Test creating metrics."""
        metrics = PerformanceMetrics()
        assert metrics.iterations_used == 0
        assert metrics.time_elapsed == 0.0
        assert metrics.errors_encountered == 0
        assert metrics.progress_score == 0.0
        assert metrics.confidence_score == 1.0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_is_stuck_detection(self):
        """Test stuck detection."""
        metrics = PerformanceMetrics()

        # Not stuck initially
        assert metrics.is_stuck() is False

        # Stuck due to errors
        metrics.errors_encountered = 3
        assert metrics.is_stuck() is True

        # Stuck due to low progress
        metrics2 = PerformanceMetrics(iterations_used=10, progress_score=0.1)
        assert metrics2.is_stuck() is True

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_is_progressing_well(self):
        """Test good progress detection."""
        metrics = PerformanceMetrics(
            progress_score=0.8,
            confidence_score=0.9,
            errors_encountered=0
        )
        assert metrics.is_progressing_well() is True

        # Low progress
        metrics2 = PerformanceMetrics(progress_score=0.3)
        assert metrics2.is_progressing_well() is False


class TestAdaptiveReasoning:
    """Test AdaptiveReasoning manager."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_adaptive_session_creation(self):
        """Test creating adaptive session."""
        session = AdaptiveReasoning(
            task_description="Solve complex problem",
            initial_strategy=ReactStrategy.FAST
        )
        assert session.task_description == "Solve complex problem"
        assert session.current_strategy == ReactStrategy.FAST
        assert session.escalation_count == 0

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_complexity_estimation(self):
        """Test task complexity estimation."""
        session = AdaptiveReasoning(task_description="Test")

        # Simple task
        simple = session.estimate_complexity("What is the capital of France?")
        assert simple == ComplexityLevel.SIMPLE

        # Complex task
        complex_task = session.estimate_complexity(
            "Analyze and evaluate the comprehensive implications of climate change"
        )
        assert complex_task == ComplexityLevel.COMPLEX

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_initial_strategy_for_complexity(self):
        """Test getting initial strategy based on complexity."""
        session = AdaptiveReasoning(task_description="Test")

        assert session.get_initial_strategy_for_complexity(ComplexityLevel.SIMPLE) == ReactStrategy.FAST
        assert session.get_initial_strategy_for_complexity(ComplexityLevel.MODERATE) == ReactStrategy.BALANCED
        assert session.get_initial_strategy_for_complexity(ComplexityLevel.COMPLEX) == ReactStrategy.DEEP

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_escalation(self):
        """Test strategy escalation."""
        session = AdaptiveReasoning(
            task_description="Test",
            initial_strategy=ReactStrategy.FAST
        )

        # Escalate from FAST to BALANCED
        new_strategy = session.escalate_strategy("Test escalation")
        assert new_strategy == ReactStrategy.BALANCED
        assert session.current_strategy == ReactStrategy.BALANCED
        assert session.escalation_count == 1
        assert len(session.transitions) == 1

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_max_escalations_limit(self):
        """Test max escalations enforcement."""
        session = AdaptiveReasoning(
            task_description="Test",
            max_escalations=2
        )

        # Force metrics to trigger escalation
        session.metrics.errors_encountered = 3

        # First escalation should work
        assert session.should_escalate() is True
        session.escalate_strategy("First")

        # Second escalation should work
        session.metrics.errors_encountered = 3
        assert session.should_escalate() is True
        session.escalate_strategy("Second")

        # Third escalation should be blocked
        session.metrics.errors_encountered = 3
        assert session.should_escalate() is False

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_update_metrics_triggers_escalation(self):
        """Test that updating metrics can trigger escalation."""
        session = AdaptiveReasoning(
            task_description="Test",
            initial_strategy=ReactStrategy.FAST
        )

        # Update with poor metrics
        session.update_metrics(
            iterations_used=10,
            time_elapsed=30.0,
            errors_encountered=3,
            progress_score=0.1,
            confidence_score=0.3
        )

        # Should have escalated
        assert session.current_strategy != ReactStrategy.FAST
        assert len(session.transitions) > 0


class TestCreateAdaptiveSession:
    """Test adaptive session factory function."""

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_create_session_simple_task(self):
        """Test creating session for simple task."""
        session = create_adaptive_session("What is 2+2?")
        assert session.complexity_estimate == ComplexityLevel.SIMPLE
        assert session.initial_strategy == ReactStrategy.FAST

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_create_session_complex_task(self):
        """Test creating session for complex task."""
        session = create_adaptive_session(
            "Analyze the comprehensive market research data and evaluate trends"
        )
        assert session.complexity_estimate == ComplexityLevel.COMPLEX
        assert session.initial_strategy == ReactStrategy.DEEP

    @pytest.mark.unit
    @pytest.mark.fase6
    def test_create_session_with_escalation_limit(self):
        """Test creating session with custom escalation limit."""
        session = create_adaptive_session("Test task", max_escalations=5)
        assert session.max_escalations == 5
