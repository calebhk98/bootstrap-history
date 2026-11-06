"""A `LabourRecord` holding the last clearing's hours by labour market key, for tests that stand in an economy."""
from sim.economy.labour_record import LabourRecord
from sim.economy.market_memory import KEY_SEPARATOR
from sim.labour.api import MarketState


def labour_record(hired_by_market=None, idle_by_market=None, **fields) -> LabourRecord:
    """Hours hired (one employer, "employer") and idle by market key (trade|area); other fields pass through."""
    hired_hours = {}
    for key, hours in (hired_by_market or {}).items():
        trade, area = key.split(KEY_SEPARATOR, 1)
        hired_hours.setdefault(area, {})[trade] = {"employer": hours}
    workforce = fields.pop("workforce", None) or MarketState()
    workforce.hired_hours.update(hired_hours)
    return LabourRecord(workforce=workforce, hours_idle=dict(idle_by_market or {}), **fields)
