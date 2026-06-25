"""Bandwidth budget management for network replication."""

from __future__ import annotations

from dataclasses import dataclass

from yuna.types.identifiers import EntityID


@dataclass
class BudgetUsage:
    """Bandwidth usage statistics for an observer."""

    bytes_used: int
    bytes_budget: int
    bytes_remaining: int
    is_over_budget: bool
    overage: int


class BandwidthBudget:
    """Manage bandwidth budgets for network replication.

    Responsibilities:
    - Track bytes sent per observer per tick
    - Enforce hard limits (max bytes per tick)
    - Track soft limits (target bytes per tick)
    - Calculate overage and throttling
    - Reset budgets per tick

    Usage:
        budget = BandwidthBudget(
            hard_limit=10000,
            soft_limit=8000,
        )
        budget.allocate_budget(observer_id=player1)
        can_send = budget.can_afford(observer_id=player1, bytes_needed=500)
        budget.spend(observer_id=player1, bytes_spent=500)
        usage = budget.get_usage(observer_id=player1)
    """

    def __init__(
        self,
        hard_limit: int,
        soft_limit: int | None = None,
    ) -> None:
        """Initialize bandwidth budget manager.

        Args:
            hard_limit: Maximum bytes per tick (never exceed)
            soft_limit: Target bytes per tick (prefer to stay under)
        """
        self.hard_limit = hard_limit
        self.soft_limit = soft_limit if soft_limit is not None else hard_limit
        self._budgets: dict[EntityID, int] = {}
        self._spent: dict[EntityID, int] = {}

    def allocate_budget(self, observer_id: EntityID) -> None:
        """Allocate budget for observer.

        Args:
            observer_id: Observer to allocate budget for
        """
        self._budgets[observer_id] = self.hard_limit
        self._spent[observer_id] = 0

    def can_afford(self, observer_id: EntityID, bytes_needed: int) -> bool:
        """Check if observer can afford bytes.

        Args:
            observer_id: Observer to check
            bytes_needed: Bytes needed

        Returns:
            True if observer has budget remaining
        """
        if observer_id not in self._budgets:
            return False

        spent = self._spent.get(observer_id, 0)
        budget = self._budgets[observer_id]
        return spent + bytes_needed <= budget

    def spend(self, observer_id: EntityID, bytes_spent: int) -> None:
        """Spend bytes from observer budget.

        Args:
            observer_id: Observer to spend from
            bytes_spent: Bytes to spend
        """
        if observer_id not in self._spent:
            self._spent[observer_id] = 0

        self._spent[observer_id] += bytes_spent

    def get_remaining(self, observer_id: EntityID) -> int:
        """Get remaining budget for observer.

        Args:
            observer_id: Observer to get remaining budget for

        Returns:
            Bytes remaining in budget
        """
        if observer_id not in self._budgets:
            return 0

        spent = self._spent.get(observer_id, 0)
        budget = self._budgets[observer_id]
        return max(0, budget - spent)

    def get_usage(self, observer_id: EntityID) -> BudgetUsage:
        """Get usage statistics for observer.

        Args:
            observer_id: Observer to get usage for

        Returns:
            Budget usage statistics
        """
        budget = self._budgets.get(observer_id, 0)
        spent = self._spent.get(observer_id, 0)
        remaining = max(0, budget - spent)
        is_over = spent > budget
        overage = max(0, spent - budget)

        return BudgetUsage(
            bytes_used=spent,
            bytes_budget=budget,
            bytes_remaining=remaining,
            is_over_budget=is_over,
            overage=overage,
        )

    def is_over_soft_limit(self, observer_id: EntityID) -> bool:
        """Check if observer is over soft limit.

        Args:
            observer_id: Observer to check

        Returns:
            True if over soft limit
        """
        spent = self._spent.get(observer_id, 0)
        return spent > self.soft_limit

    def is_over_hard_limit(self, observer_id: EntityID) -> bool:
        """Check if observer is over hard limit.

        Args:
            observer_id: Observer to check

        Returns:
            True if over hard limit
        """
        spent = self._spent.get(observer_id, 0)
        return spent > self.hard_limit

    def reset(self) -> None:
        """Reset all budgets for new tick."""
        for observer_id in self._budgets:
            self._spent[observer_id] = 0

    def reset_observer(self, observer_id: EntityID) -> None:
        """Reset budget for specific observer.

        Args:
            observer_id: Observer to reset
        """
        if observer_id in self._spent:
            self._spent[observer_id] = 0

    def remove_observer(self, observer_id: EntityID) -> None:
        """Remove observer from budget tracking.

        Args:
            observer_id: Observer to remove
        """
        self._budgets.pop(observer_id, None)
        self._spent.pop(observer_id, None)
