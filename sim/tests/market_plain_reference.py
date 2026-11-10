"""`MarketState.to_plain` as it was before it read whole columns: through the dict views, a pair at a time."""
from sim.labour.market.state_fields import AreaMap, AsksField, HiredField, TraineesField, WagesField, WorkersField

_FIELDS = (("workers", WorkersField), ("trainees", TraineesField), ("wages", WagesField), ("hired_hours", HiredField), ("asks", AsksField))


def _plain_value(value):
    if isinstance(value, float):
        return value
    if hasattr(value, "items"):
        return dict(value.items())
    return [each.plain() if hasattr(each, "plain") else each for each in value]


def plain_state(state):
    return {name: {area: {trade: _plain_value(value) for trade, value in by_trade.items()}
                   for area, by_trade in AreaMap(state, field).items()} for name, field in _FIELDS}
