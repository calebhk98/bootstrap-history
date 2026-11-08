"""The producer table (`record.producers`) is written only here; the modules that found, change or close a producer call these.

The table is a `ProducerStore` (producer_store.py): each call writes the producer's row of columns. A plain mapping (a test's) is
written as a dict."""
from typing import Dict, Iterable, Tuple

from .producer_store import ProducerStore
from .producers import Producer
from .types import AgentId


def put_producer(producers: Dict[AgentId, Producer], producer: Producer) -> None:
    """`producer` is the table's row for its id, new or replacing."""
    if isinstance(producers, ProducerStore):
        producers.put(producer)
    else:
        producers[producer.agent_id] = producer


def put_producers(producers: Dict[AgentId, Producer], rows: Iterable[Tuple[AgentId, Producer]]) -> None:
    """Each (id, producer) is the table's row for the id, replacing one."""
    for _producer_id, producer in rows:
        put_producer(producers, producer)


def remove_producer(producers: Dict[AgentId, Producer], producer_id: AgentId) -> None:
    """The producer has closed."""
    del producers[producer_id]


def set_fields(producers: ProducerStore, producer_id: AgentId, **changes) -> None:
    """The named scalar fields of one producer take the values (None for a field that may be absent)."""
    producers.set_fields(producer_id, **changes)


def set_column(producers: ProducerStore, name: str, producer_ids: Iterable[AgentId], values: Iterable[float]) -> None:
    """One scalar field of the producers named takes the values; an id the table does not hold is skipped."""
    producers.set_column(name, producer_ids, values)


def set_rows(producers: ProducerStore, name: str, rows, values) -> None:
    """One scalar field of the table's rows takes the values (a block write for the rows of `ProducerStore.order`)."""
    producers.set_rows(name, rows, values)
