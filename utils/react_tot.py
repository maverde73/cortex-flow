"""
Tree-of-Thought (ToT) Reasoning Support (FASE 6)

Implements tree-based reasoning where multiple paths are explored
and the best one is selected.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BranchStatus(str, Enum):
    """Status of a reasoning branch."""
    EXPLORING = "exploring"  # Currently being developed
    EVALUATED = "evaluated"  # Has been scored
    SELECTED = "selected"  # Chosen as best path
    REJECTED = "rejected"  # Discarded as suboptimal
    FAILED = "failed"  # Led to dead end


@dataclass
class ReasoningBranch:
    """
    Represents a single branch in the tree of thought.

    Each branch is a potential reasoning path that can be explored,
    evaluated, and compared with alternatives.
    """
    branch_id: str
    parent_id: Optional[str]
    thought: str
    actions: List[str] = field(default_factory=list)
    observations: List[str] = field(default_factory=list)
    status: BranchStatus = BranchStatus.EXPLORING
    score: float = 0.0  # Quality score (0.0-1.0)
    depth: int = 0  # How many steps from root
    created_at: datetime = field(default_factory=datetime.now)

    def add_action(self, action: str, observation: str):
        """Add an action-observation pair to this branch."""
        self.actions.append(action)
        self.observations.append(observation)

    def evaluate(self, score: float):
        """Evaluate this branch with a quality score."""
        self.score = max(0.0, min(1.0, score))  # Clamp to [0,1]
        self.status = BranchStatus.EVALUATED
        logger.debug(f"Branch {self.branch_id} evaluated with score {self.score:.2f}")

    def select(self):
        """Mark this branch as selected."""
        self.status = BranchStatus.SELECTED
        logger.info(f"Branch {self.branch_id} selected (score: {self.score:.2f})")

    def reject(self):
        """Mark this branch as rejected."""
        self.status = BranchStatus.REJECTED

    def fail(self):
        """Mark this branch as failed."""
        self.status = BranchStatus.FAILED
        logger.warning(f"Branch {self.branch_id} failed")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "branch_id": self.branch_id,
            "parent_id": self.parent_id,
            "thought": self.thought,
            "actions": self.actions,
            "observations": self.observations,
            "status": self.status.value,
            "score": self.score,
            "depth": self.depth,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TreeOfThought:
    """
    Manages a tree of thought reasoning process.

    Explores multiple reasoning paths in parallel and selects
    the most promising one based on evaluation scores.
    """
    task_description: str
    max_branches: int = 5  # Maximum branches to explore
    max_depth: int = 4  # Maximum depth to explore
    branches: List[ReasoningBranch] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    selected_branch_id: Optional[str] = None

    def create_branch(
        self,
        thought: str,
        parent_id: Optional[str] = None
    ) -> ReasoningBranch:
        """
        Create a new reasoning branch.

        Args:
            thought: The reasoning for this branch
            parent_id: Optional parent branch ID

        Returns:
            The created branch
        """
        # Check branch limit
        if len(self.branches) >= self.max_branches:
            logger.warning(
                f"Branch limit reached ({self.max_branches}), "
                "not creating new branch"
            )
            return None

        # Calculate depth
        depth = 0
        if parent_id:
            parent = self.get_branch(parent_id)
            if parent:
                depth = parent.depth + 1

                # Check depth limit
                if depth >= self.max_depth:
                    logger.warning(
                        f"Max depth reached ({self.max_depth}), "
                        "not creating deeper branch"
                    )
                    return None

        branch_id = f"branch_{len(self.branches) + 1}"
        branch = ReasoningBranch(
            branch_id=branch_id,
            parent_id=parent_id,
            thought=thought,
            depth=depth
        )

        self.branches.append(branch)
        logger.debug(
            f"Created branch {branch_id} at depth {depth} "
            f"(parent: {parent_id or 'root'})"
        )

        return branch

    def get_branch(self, branch_id: str) -> Optional[ReasoningBranch]:
        """Get a branch by ID."""
        for branch in self.branches:
            if branch.branch_id == branch_id:
                return branch
        return None

    def get_children(self, parent_id: str) -> List[ReasoningBranch]:
        """Get all child branches of a parent."""
        return [
            b for b in self.branches
            if b.parent_id == parent_id
        ]

    def evaluate_branches(self):
        """
        Evaluate all unexplored branches.

        This should be called after exploring branches to score them.
        """
        for branch in self.branches:
            if branch.status == BranchStatus.EXPLORING:
                # Simple heuristic: score based on depth and actions
                # In real implementation, this would use LLM evaluation
                score = self._heuristic_score(branch)
                branch.evaluate(score)

    def _heuristic_score(self, branch: ReasoningBranch) -> float:
        """
        Simple heuristic scoring for branches.

        In production, this would be replaced with LLM-based evaluation.
        """
        # Deeper branches with more actions get slightly higher scores
        depth_bonus = branch.depth * 0.1
        action_bonus = len(branch.actions) * 0.05

        # Base score starts at 0.5
        score = 0.5 + depth_bonus + action_bonus

        # Penalize failed branches
        if branch.status == BranchStatus.FAILED:
            score = 0.0

        return min(1.0, score)

    def select_best_branch(self) -> Optional[ReasoningBranch]:
        """
        Select the best branch based on scores.

        Returns:
            The selected branch, or None if no branches
        """
        # Ensure all branches are evaluated
        self.evaluate_branches()

        # Find branch with highest score
        evaluated_branches = [
            b for b in self.branches
            if b.status == BranchStatus.EVALUATED
        ]

        if not evaluated_branches:
            logger.warning("No evaluated branches to select from")
            return None

        best_branch = max(evaluated_branches, key=lambda b: b.score)
        best_branch.select()
        self.selected_branch_id = best_branch.branch_id

        # Reject others
        for branch in evaluated_branches:
            if branch.branch_id != best_branch.branch_id:
                branch.reject()

        logger.info(
            f"Selected branch {best_branch.branch_id} with score {best_branch.score:.2f}"
        )

        return best_branch

    def get_selected_path(self) -> List[ReasoningBranch]:
        """
        Get the complete path from root to selected branch.

        Returns:
            List of branches forming the selected path
        """
        if not self.selected_branch_id:
            return []

        path = []
        current_id = self.selected_branch_id

        # Walk backwards from selected branch to root
        while current_id:
            branch = self.get_branch(current_id)
            if not branch:
                break

            path.insert(0, branch)  # Insert at front to maintain order
            current_id = branch.parent_id

        return path

    def complete(self):
        """Mark the tree exploration as completed."""
        self.completed_at = datetime.now()
        logger.info(
            f"ToT completed: {len(self.branches)} branches explored in "
            f"{(self.completed_at - self.started_at).total_seconds():.1f}s"
        )

    def get_summary(self) -> str:
        """
        Generate a summary of the tree exploration.

        Returns:
            Human-readable summary
        """
        if not self.branches:
            return "No branches explored"

        duration = (
            (self.completed_at or datetime.now()) - self.started_at
        ).total_seconds()

        selected_path = self.get_selected_path()

        summary = [
            f"Tree-of-Thought Summary:",
            f"- Task: {self.task_description}",
            f"- Branches Explored: {len(self.branches)}",
            f"- Max Depth Reached: {max(b.depth for b in self.branches)}",
            f"- Duration: {duration:.1f}s",
            f"",
            "Selected Path:"
        ]

        if selected_path:
            for branch in selected_path:
                summary.append(
                    f"  {branch.branch_id} (depth {branch.depth}, "
                    f"score {branch.score:.2f}): {branch.thought[:60]}..."
                )
        else:
            summary.append("  (No path selected)")

        return "\n".join(summary)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "task_description": self.task_description,
            "max_branches": self.max_branches,
            "max_depth": self.max_depth,
            "branches": [b.to_dict() for b in self.branches],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "selected_branch_id": self.selected_branch_id,
            "total_branches": len(self.branches)
        }


def get_tot_system_prompt() -> str:
    """
    Get the system prompt for Tree-of-Thought reasoning.

    Returns:
        System prompt that encourages exploring multiple paths
    """
    return """You are an expert problem solver that uses Tree-of-Thought reasoning.

For each task, you must:
1. Generate multiple possible approaches to solve the problem
2. For each approach, think through the steps involved
3. Evaluate the pros and cons of each approach
4. Select the most promising approach to pursue

Format your thinking as:

Approach 1: [Describe first approach]
Steps: [List key steps]
Pros: [Advantages]
Cons: [Disadvantages]
Score: [Rate 0-100 based on viability]

Approach 2: [Describe second approach]
Steps: [List key steps]
Pros: [Advantages]
Cons: [Disadvantages]
Score: [Rate 0-100 based on viability]

... generate 3-5 approaches ...

Best Approach: [Select the approach with highest score]
Rationale: [Explain why this is best]

Final Answer: [Execute the best approach and provide result]

Think creatively and explore different angles."""


def get_tot_user_prompt(task: str) -> str:
    """
    Get the user prompt for a ToT task.

    Args:
        task: The task to solve

    Returns:
        Formatted user prompt
    """
    return f"""Task: {task}

Please solve this task using Tree-of-Thought reasoning.
Generate multiple approaches, evaluate each one, and select
the best path forward. Be thorough in your exploration."""


def extract_branches(response: str) -> List[Dict[str, Any]]:
    """
    Extract reasoning branches from a ToT response.

    Args:
        response: The LLM response containing ToT reasoning

    Returns:
        List of extracted branches with approach, steps, score
    """
    branches = []
    lines = response.split("\n")

    current_approach = None
    current_steps = None
    current_pros = None
    current_cons = None
    current_score = 0.5

    for line in lines:
        line = line.strip()

        # Detect approach markers
        if line.startswith("Approach "):
            # Save previous approach if exists
            if current_approach:
                branches.append({
                    "thought": current_approach,
                    "steps": current_steps,
                    "pros": current_pros,
                    "cons": current_cons,
                    "score": current_score
                })

            # Start new approach
            current_approach = line
            current_steps = None
            current_pros = None
            current_cons = None
            current_score = 0.5

        elif line.startswith("Steps:"):
            current_steps = line.replace("Steps:", "").strip()

        elif line.startswith("Pros:"):
            current_pros = line.replace("Pros:", "").strip()

        elif line.startswith("Cons:"):
            current_cons = line.replace("Cons:", "").strip()

        elif line.startswith("Score:"):
            # Extract score
            score_str = line.replace("Score:", "").strip()
            try:
                if "/" in score_str:
                    # Handle "85/100" format
                    num, denom = score_str.split("/")
                    current_score = float(num) / float(denom)
                else:
                    current_score = float(score_str) / 100.0
            except ValueError:
                current_score = 0.5

    # Save last approach
    if current_approach:
        branches.append({
            "thought": current_approach,
            "steps": current_steps,
            "pros": current_pros,
            "cons": current_cons,
            "score": current_score
        })

    return branches
