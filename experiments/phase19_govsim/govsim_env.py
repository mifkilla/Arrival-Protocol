# ARRIVAL Protocol -- AI-to-AI Coordination Through Structured Semantic Atoms
# Copyright (C) 2025-2026 Mefodiy Kelevra
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Phase 19: Fish Pond Game Environment
=====================================
Pure game logic for GovSim-inspired harvest negotiation.
No API calls — just math and state management.

Replenishment formula (Piatti et al. 2024):
  remaining = stock - sum(harvests)
  new_stock = min(2 * remaining, max_capacity)

Collapse: stock < collapse_threshold → game over.

Copyright (C) 2026 Mefodiy Kelevra (AGPL-3.0)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import math


@dataclass
class PondState:
    """Immutable snapshot of the pond at a given month."""
    month: int
    stock_before: float
    harvests: Dict[str, int]
    stock_after_harvest: float
    stock_after_replenish: float
    fair_share: float
    collapsed: bool
    gini: float = 0.0


class FishPondEnv:
    """
    Fish pond commons simulation (GovSim-inspired).

    Usage:
        env = FishPondEnv()
        for month in range(1, 13):
            harvests = {"alpha": 10, "beta": 12, ...}
            state = env.step(harvests)
            if state.collapsed:
                break
    """

    def __init__(
        self,
        initial_stock: int = 100,
        max_capacity: int = 100,
        collapse_threshold: int = 5,
        n_months: int = 12,
        agent_names: Optional[List[str]] = None,
    ):
        self.initial_stock = initial_stock
        self.max_capacity = max_capacity
        self.collapse_threshold = collapse_threshold
        self.n_months = n_months
        self.agent_names = agent_names or ["alpha", "beta", "gamma", "delta", "epsilon"]
        self.n_agents = len(self.agent_names)

        # State
        self.stock = float(initial_stock)
        self.current_month = 0
        self.collapsed = False
        self.history: List[PondState] = []
        self.cumulative_harvests: Dict[str, int] = {a: 0 for a in self.agent_names}

    def get_fair_share(self) -> float:
        """
        Fair share = (stock - collapse_threshold) / n_agents.
        This is the maximum each agent can take if all take equal amounts
        while keeping the pond above collapse threshold.
        """
        available = max(0, self.stock - self.collapse_threshold)
        return available / self.n_agents

    def get_max_safe_harvest(self) -> float:
        """Maximum total harvest that keeps pond above collapse threshold."""
        return max(0, self.stock - self.collapse_threshold)

    def step(self, harvests: Dict[str, int]) -> PondState:
        """
        Execute one month of the game.

        Args:
            harvests: {agent_name: fish_count} for each agent

        Returns:
            PondState snapshot of this month

        Raises:
            ValueError: if game already collapsed or month exceeded
        """
        if self.collapsed:
            raise ValueError("Game already collapsed")
        if self.current_month >= self.n_months:
            raise ValueError(f"Game over: reached month {self.n_months}")

        self.current_month += 1
        stock_before = self.stock
        fair_share = self.get_fair_share()

        # Clamp harvests: non-negative, can't take more than exists
        clamped = {}
        remaining = self.stock
        for agent in self.agent_names:
            proposed = max(0, harvests.get(agent, 0))
            actual = min(proposed, int(remaining))
            clamped[agent] = actual
            remaining -= actual
            self.cumulative_harvests[agent] += actual

        total_harvested = sum(clamped.values())
        stock_after_harvest = stock_before - total_harvested

        # Check collapse
        if stock_after_harvest < self.collapse_threshold:
            self.collapsed = True
            self.stock = stock_after_harvest
            state = PondState(
                month=self.current_month,
                stock_before=stock_before,
                harvests=clamped,
                stock_after_harvest=stock_after_harvest,
                stock_after_replenish=stock_after_harvest,
                fair_share=fair_share,
                collapsed=True,
                gini=self._compute_gini(list(clamped.values())),
            )
            self.history.append(state)
            return state

        # Replenishment: doubling, capped at max_capacity
        stock_after_replenish = min(2.0 * stock_after_harvest, self.max_capacity)
        self.stock = stock_after_replenish

        state = PondState(
            month=self.current_month,
            stock_before=stock_before,
            harvests=clamped,
            stock_after_harvest=stock_after_harvest,
            stock_after_replenish=stock_after_replenish,
            fair_share=fair_share,
            collapsed=False,
            gini=self._compute_gini(list(clamped.values())),
        )
        self.history.append(state)
        return state

    def format_history_for_prompt(self, last_n: int = 3) -> str:
        """Format recent history for inclusion in LLM prompts."""
        if not self.history:
            return "No previous rounds."

        recent = self.history[-last_n:]
        lines = ["RECENT HISTORY:"]
        for s in recent:
            harvest_parts = [f"{a}={s.harvests.get(a, 0)}" for a in self.agent_names]
            lines.append(
                f"  Month {s.month}: stock={s.stock_before:.0f}, "
                f"harvests=[{', '.join(harvest_parts)}], "
                f"after={s.stock_after_replenish:.0f}"
            )
        return "\n".join(lines)

    def get_resource_trajectory(self) -> List[float]:
        """Return stock values over time (before harvest each month)."""
        trajectory = [float(self.initial_stock)]
        for s in self.history:
            trajectory.append(s.stock_after_replenish)
        return trajectory

    def get_months_survived(self) -> int:
        """How many months did the game last?"""
        if self.collapsed:
            return self.current_month - 1  # Last month was collapse
        return self.current_month

    def is_survived(self) -> bool:
        """Did the game reach month 12 without collapse?"""
        return self.current_month >= self.n_months and not self.collapsed

    def compute_gini_coefficient(self) -> float:
        """Gini coefficient of cumulative harvests (0=equal, 1=one takes all)."""
        values = list(self.cumulative_harvests.values())
        return self._compute_gini(values)

    @staticmethod
    def _compute_gini(values: List[int]) -> float:
        """Compute Gini coefficient for a list of values."""
        if not values or all(v == 0 for v in values):
            return 0.0
        n = len(values)
        values_sorted = sorted(values)
        total = sum(values_sorted)
        if total == 0:
            return 0.0
        cumsum = 0.0
        gini_sum = 0.0
        for i, v in enumerate(values_sorted):
            cumsum += v
            gini_sum += (2 * (i + 1) - n - 1) * v
        return gini_sum / (n * total)

    def to_dict(self) -> Dict[str, Any]:
        """Full JSON-serializable state."""
        return {
            "initial_stock": self.initial_stock,
            "max_capacity": self.max_capacity,
            "collapse_threshold": self.collapse_threshold,
            "n_months": self.n_months,
            "n_agents": self.n_agents,
            "agent_names": self.agent_names,
            "current_month": self.current_month,
            "final_stock": self.stock,
            "collapsed": self.collapsed,
            "months_survived": self.get_months_survived(),
            "survived": self.is_survived(),
            "cumulative_harvests": self.cumulative_harvests,
            "gini_coefficient": self.compute_gini_coefficient(),
            "resource_trajectory": self.get_resource_trajectory(),
            "history": [
                {
                    "month": s.month,
                    "stock_before": s.stock_before,
                    "harvests": s.harvests,
                    "stock_after_harvest": s.stock_after_harvest,
                    "stock_after_replenish": s.stock_after_replenish,
                    "fair_share": round(s.fair_share, 1),
                    "collapsed": s.collapsed,
                    "gini": round(s.gini, 4),
                }
                for s in self.history
            ],
        }
