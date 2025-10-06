#!/usr/bin/env python3
"""
Demo script per FASE 6 - Advanced Reasoning Modes con LangSmith Tracing

Questo script dimostra le 3 nuove modalità di ragionamento avanzato:
1. Chain-of-Thought (CoT) - Ragionamento step-by-step esplicito
2. Tree-of-Thought (ToT) - Esplorazione percorsi multipli
3. Adaptive Reasoning - Switching dinamico di strategia

I trace saranno visibili in LangSmith dashboard.
"""

import asyncio
import logging
from datetime import datetime

from utils.react_cot import (
    ChainOfThought,
    get_cot_system_prompt,
    get_cot_user_prompt,
    validate_cot_response
)
from utils.react_tot import (
    TreeOfThought,
    get_tot_system_prompt,
    get_tot_user_prompt
)
from utils.react_adaptive import (
    create_adaptive_session,
    ComplexityLevel
)
from utils.react_strategies import ReactStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_chain_of_thought():
    """
    Demo Chain-of-Thought reasoning.

    Simula un processo di ragionamento step-by-step per un problema matematico.
    """
    print("\n" + "="*80)
    print("DEMO 1: Chain-of-Thought (CoT) Reasoning")
    print("="*80 + "\n")

    task = "Calculate the area of a circle with radius 5 cm"
    logger.info(f"Task: {task}")

    # Create CoT chain
    chain = ChainOfThought(task_description=task)

    # Simulate reasoning steps
    chain.add_step(
        thought="I need to recall the formula for the area of a circle",
        confidence=0.95
    )

    chain.add_step(
        thought="The formula is A = π * r²",
        action="recall_formula",
        observation="Formula: A = π * r²",
        confidence=1.0
    )

    chain.add_step(
        thought="Now I substitute r = 5 cm into the formula",
        action="substitute_values",
        observation="A = π * 5² = π * 25",
        confidence=0.98
    )

    chain.add_step(
        thought="Calculate the final result using π ≈ 3.14159",
        action="calculate",
        observation="A ≈ 78.54 cm²",
        confidence=0.99
    )

    chain.complete()

    # Display summary
    print(chain.get_summary())
    print(f"\n✅ CoT demonstration complete with {len(chain.steps)} reasoning steps")

    return chain


def demo_tree_of_thought():
    """
    Demo Tree-of-Thought reasoning.

    Simula esplorazione di approcci alternativi per risolvere un problema.
    """
    print("\n" + "="*80)
    print("DEMO 2: Tree-of-Thought (ToT) Reasoning")
    print("="*80 + "\n")

    task = "Optimize a sorting algorithm for large datasets"
    logger.info(f"Task: {task}")

    # Create ToT tree
    tree = TreeOfThought(
        task_description=task,
        max_branches=5,
        max_depth=3
    )

    # Root level: Different algorithmic approaches
    branch1 = tree.create_branch("Approach 1: QuickSort with random pivot")
    branch1.add_action("analyze_complexity", "O(n log n) average, O(n²) worst")
    branch1.evaluate(0.75)

    branch2 = tree.create_branch("Approach 2: MergeSort with parallel execution")
    branch2.add_action("analyze_complexity", "O(n log n) guaranteed, parallelizable")
    branch2.evaluate(0.85)

    branch3 = tree.create_branch("Approach 3: RadixSort for integer keys")
    branch3.add_action("analyze_complexity", "O(nk) where k is key size")
    branch3.evaluate(0.70)

    # Second level: Refine best approach
    branch4 = tree.create_branch(
        "Refine MergeSort: Use hybrid with insertion sort for small arrays",
        parent_id=branch2.branch_id
    )
    branch4.add_action("optimize", "Reduces overhead for small partitions")
    branch4.evaluate(0.90)

    branch5 = tree.create_branch(
        "Refine MergeSort: Implement in-place variant",
        parent_id=branch2.branch_id
    )
    branch5.add_action("optimize", "Reduces memory usage")
    branch5.evaluate(0.88)

    # Select best branch
    best = tree.select_best_branch()
    tree.complete()

    # Display summary
    print(tree.get_summary())
    print(f"\n✅ ToT demonstration complete")
    print(f"   Best approach selected: {best.thought}")
    print(f"   Score: {best.score:.2f}")

    return tree


def demo_adaptive_reasoning():
    """
    Demo Adaptive Reasoning.

    Simula switching dinamico di strategia basato su performance.
    """
    print("\n" + "="*80)
    print("DEMO 3: Adaptive Reasoning")
    print("="*80 + "\n")

    # Test 1: Simple task (should stay FAST)
    print("\n--- Test 1: Simple Task ---")
    task1 = "What is 2 + 2?"
    session1 = create_adaptive_session(task1)
    print(f"Task: {task1}")
    print(f"Detected complexity: {session1.complexity_estimate.value}")
    print(f"Initial strategy: {session1.initial_strategy.value}")

    # Simulate good progress
    session1.update_metrics(
        iterations_used=1,
        time_elapsed=2.0,
        errors_encountered=0,
        progress_score=1.0,
        confidence_score=1.0
    )
    print(f"Final strategy: {session1.current_strategy.value}")
    print(f"Escalations: {session1.escalation_count}")

    # Test 2: Complex task with escalations
    print("\n--- Test 2: Complex Task with Escalation ---")
    task2 = "Analyze and evaluate comprehensive market research data for strategic planning"
    session2 = create_adaptive_session(task2)
    print(f"Task: {task2}")
    print(f"Detected complexity: {session2.complexity_estimate.value}")
    print(f"Initial strategy: {session2.initial_strategy.value}")

    # Simulate poor initial progress → triggers escalation
    session2.update_metrics(
        iterations_used=5,
        time_elapsed=30.0,
        errors_encountered=2,
        progress_score=0.2,
        confidence_score=0.4
    )
    print(f"After 5 iterations with poor progress:")
    print(f"  Current strategy: {session2.current_strategy.value}")
    print(f"  Escalations: {session2.escalation_count}")

    # Still poor progress → another escalation
    session2.update_metrics(
        iterations_used=15,
        time_elapsed=90.0,
        errors_encountered=3,
        progress_score=0.4,
        confidence_score=0.5
    )
    print(f"After 15 iterations:")
    print(f"  Current strategy: {session2.current_strategy.value}")
    print(f"  Escalations: {session2.escalation_count}")

    print(f"\n{session2.get_summary()}")
    print(f"\n✅ Adaptive demonstration complete")

    return session1, session2


def main():
    """Run all FASE 6 demonstrations."""
    print("\n" + "🚀"*40)
    print("FASE 6: Advanced Reasoning Modes - LangSmith Demo")
    print("🚀"*40 + "\n")

    print("ℹ️  LangSmith tracing is enabled.")
    print("   View traces at: https://smith.langchain.com/")
    print("   Project: cortex-flow")

    # Run demonstrations
    cot_chain = demo_chain_of_thought()
    tot_tree = demo_tree_of_thought()
    adaptive_sessions = demo_adaptive_reasoning()

    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80 + "\n")

    print(f"✅ Chain-of-Thought: {len(cot_chain.steps)} reasoning steps")
    print(f"✅ Tree-of-Thought: {len(tot_tree.branches)} branches explored")
    print(f"✅ Adaptive Reasoning: 2 sessions with dynamic strategy switching")

    print("\n📊 Check LangSmith dashboard for detailed traces!")
    print("   All reasoning steps, branches, and escalations are tracked.\n")


if __name__ == "__main__":
    main()
