"""
Cost tracking for OpenAI API calls with tiktoken token counting.

This module provides budget monitoring and cost estimation for LLM extraction calls.
It uses tiktoken to count tokens BEFORE API calls and aborts if budget exceeded.

Features:
- Token counting with tiktoken (o200k_base encoding for gpt-4o-mini)
- 10% safety buffer on cost estimates (spike validated <1% variance for long texts)
- Hard abort at $1.00 threshold
- Per-call and cumulative cost tracking
- Detailed cost reporting

Usage:
    tracker = CostTracker(budget_limit=1.00)

    # Before each API call
    tracker.check_budget(text_to_process)

    # After each API call
    tracker.track_call(input_tokens=150, output_tokens=50)

    # Get summary
    summary = tracker.get_summary()
"""

import tiktoken
from typing import Optional


class CostLimitExceeded(Exception):
    """Raised when cumulative cost exceeds budget limit.

    This exception triggers immediate pipeline abort to prevent cost overruns.

    Attributes:
        cumulative_cost: Total cost incurred so far
        budget_limit: Maximum allowed budget
        estimated_next_cost: Cost of the call that would exceed budget
    """

    def __init__(self, cumulative_cost: float, budget_limit: float, estimated_next_cost: float):
        self.cumulative_cost = cumulative_cost
        self.budget_limit = budget_limit
        self.estimated_next_cost = estimated_next_cost
        super().__init__(
            f"Cost limit exceeded: ${cumulative_cost:.4f} + ${estimated_next_cost:.4f} "
            f"would exceed budget of ${budget_limit:.2f}"
        )


class CostTracker:
    """Track OpenAI API costs with token counting and budget enforcement.

    Uses tiktoken to estimate costs BEFORE making API calls. Aborts pipeline
    if cumulative cost would exceed budget limit.

    Pricing (gpt-4o-mini as of 2024-11):
    - Input: $0.15 per 1M tokens
    - Output: $0.60 per 1M tokens

    Attributes:
        budget_limit: Maximum allowed cost in USD (default: $1.00)
        cumulative_cost: Total cost incurred so far
        call_count: Number of API calls tracked
        total_input_tokens: Sum of input tokens across all calls
        total_output_tokens: Sum of output tokens across all calls
    """

    # OpenAI gpt-4o-mini pricing (per 1M tokens)
    INPUT_COST_PER_1M = 0.15  # $0.15 per 1M input tokens
    OUTPUT_COST_PER_1M = 0.60  # $0.60 per 1M output tokens

    # Safety buffer (10% added to estimates - spike showed <1% variance for long texts)
    BUFFER_MULTIPLIER = 1.10

    # Encoding for gpt-4o-mini
    ENCODING_NAME = "o200k_base"

    def __init__(self, budget_limit: float = 1.00):
        """Initialize cost tracker with budget limit.

        Args:
            budget_limit: Maximum allowed cost in USD (default: $1.00)

        Raises:
            ValueError: If budget_limit is not positive
        """
        if budget_limit <= 0:
            raise ValueError(f"Budget limit must be positive, got {budget_limit}")

        self.budget_limit = budget_limit
        self.cumulative_cost = 0.0
        self.call_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

        # Initialize tiktoken encoder
        self._encoding = tiktoken.get_encoding(self.ENCODING_NAME)

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self._encoding.encode(text))

    def estimate_cost(self, input_text: str, estimated_output_tokens: int = 300) -> float:
        """Estimate cost for an API call BEFORE making it.

        Counts input tokens with tiktoken and estimates output tokens.
        Applies 10% safety buffer to account for variance.

        Args:
            input_text: Text to send to OpenAI (prompt + website content)
            estimated_output_tokens: Expected output size (default: 300 for typical extraction)

        Returns:
            Estimated cost in USD with 10% safety buffer
        """
        input_tokens = self.count_tokens(input_text)

        # Calculate base cost
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (estimated_output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        base_cost = input_cost + output_cost

        # Apply safety buffer (10%)
        return base_cost * self.BUFFER_MULTIPLIER

    def check_budget(self, input_text: str, estimated_output_tokens: int = 300) -> None:
        """Check if next API call would exceed budget.

        Call this BEFORE making OpenAI API call. Raises exception if budget
        would be exceeded.

        Args:
            input_text: Text to send to OpenAI
            estimated_output_tokens: Expected output size (default: 300)

        Raises:
            CostLimitExceeded: If cumulative cost + estimated cost > budget_limit
        """
        estimated_cost = self.estimate_cost(input_text, estimated_output_tokens)
        projected_total = self.cumulative_cost + estimated_cost

        if projected_total > self.budget_limit:
            raise CostLimitExceeded(
                cumulative_cost=self.cumulative_cost,
                budget_limit=self.budget_limit,
                estimated_next_cost=estimated_cost
            )

    def track_call(self, input_tokens: int, output_tokens: int) -> float:
        """Track actual cost of a completed API call.

        Call this AFTER OpenAI API call completes. Uses actual token counts
        from response.usage.

        Args:
            input_tokens: Actual input tokens from response.usage.prompt_tokens
            output_tokens: Actual output tokens from response.usage.completion_tokens

        Returns:
            Actual cost of this call in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        call_cost = input_cost + output_cost

        self.cumulative_cost += call_cost
        self.call_count += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        return call_cost

    def get_remaining_budget(self) -> float:
        """Get remaining budget.

        Returns:
            Remaining budget in USD (budget_limit - cumulative_cost)
        """
        return max(0.0, self.budget_limit - self.cumulative_cost)

    def get_summary(self) -> dict:
        """Get cost tracking summary.

        Returns:
            Dictionary with cost tracking statistics:
            - budget_limit: Maximum allowed cost
            - cumulative_cost: Total cost incurred
            - remaining_budget: Budget left
            - call_count: Number of API calls tracked
            - total_input_tokens: Sum of input tokens
            - total_output_tokens: Sum of output tokens
            - average_cost_per_call: Mean cost per call (if calls > 0)
            - budget_utilization_pct: Percentage of budget used
        """
        avg_cost = self.cumulative_cost / self.call_count if self.call_count > 0 else 0.0
        utilization_pct = (self.cumulative_cost / self.budget_limit) * 100

        return {
            "budget_limit": self.budget_limit,
            "cumulative_cost": self.cumulative_cost,
            "remaining_budget": self.get_remaining_budget(),
            "call_count": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "average_cost_per_call": avg_cost,
            "budget_utilization_pct": utilization_pct
        }

    def __str__(self) -> str:
        """String representation of cost tracker status."""
        summary = self.get_summary()
        return (
            f"CostTracker(calls={summary['call_count']}, "
            f"cost=${summary['cumulative_cost']:.4f}/${summary['budget_limit']:.2f}, "
            f"remaining=${summary['remaining_budget']:.4f})"
        )
