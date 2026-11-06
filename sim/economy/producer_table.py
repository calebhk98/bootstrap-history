"""The producer table (`record.producers`) is written only here; the modules that found, change or close a producer call these."""
from typing import Dict

from .producers import Producer
from .types import AgentId


def put_producer(producers: Dict[AgentId, Producer], producer: Producer) -> None:
    """`producer` is the table's row for its id, new or replacing."""
    producers[producer.agent_id] = producer


def remove_producer(producers: Dict[AgentId, Producer], producer_id: AgentId) -> None:
    """The producer has closed."""
    del producers[producer_id]
