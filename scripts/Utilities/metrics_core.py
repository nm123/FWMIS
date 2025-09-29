"""
Core Metrics Classes

Basic metric classes for collecting and storing metrics data.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Counter:
    """Simple counter metric."""

    name: str
    description: str
    value: int = 0
    labels: Dict[str, str] = field(default_factory=dict)

    def increment(self, amount: int = 1) -> None:
        """Increment the counter."""
        self.value += amount

    def reset(self) -> None:
        """Reset the counter."""
        self.value = 0


@dataclass
class Gauge:
    """Gauge metric for values that can go up and down."""

    name: str
    description: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        """Set the gauge value."""
        self.value = value

    def increment(self, amount: float = 1.0) -> None:
        """Increment the gauge."""
        self.value += amount

    def decrement(self, amount: float = 1.0) -> None:
        """Decrement the gauge."""
        self.value -= amount


@dataclass
class Histogram:
    """Histogram metric for measuring distributions."""

    name: str
    description: str
    buckets: list = field(default_factory=lambda: [0.1, 0.5, 1.0, 2.5, 5.0, 10.0])
    observations: list = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)

    def observe(self, value: float) -> None:
        """Add an observation."""
        self.observations.append(value)

    def get_percentile(self, percentile: float) -> float:
        """Get percentile value."""
        if not self.observations:
            return 0.0
        sorted_obs = sorted(self.observations)
        index = int(len(sorted_obs) * percentile / 100)
        return sorted_obs[min(index, len(sorted_obs) - 1)]

    def count(self) -> int:
        """Get total count of observations."""
        return len(self.observations)

    def sum(self) -> float:
        """Get sum of all observations."""
        return sum(self.observations)
