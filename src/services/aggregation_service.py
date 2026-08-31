"""
Aggregation service for Mentor API.

Thin subclass so shared GET route factories dispatch through the local
service module. Aggregation is consume-only here; Mentee owns hit/completion
writes.
"""

from api_utils.services import AggregationService as SharedAggregationService


class AggregationService(SharedAggregationService):
    """Local AggregationService subclass for factory wiring."""


__all__ = ["AggregationService"]
