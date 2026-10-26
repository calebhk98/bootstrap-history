"""The commodity catalogue and the memos for answers that hold while what is built, run and produced does not change."""
from typing import Any, Callable, Dict, Hashable, Optional

from . import commodities, rules

# the catalogue file does not change mid-run and loading it involves a JSON load, so one is kept for every game
_LEDGER: Dict[str, Any] = {}
_COMMODITY_OF_MATERIAL: Dict[str, Any] = {}


def shared_ledger() -> Any:
    """The curated commodities from commodities.json, as a CommodityLedger."""
    if "ledger" not in _LEDGER:
        _LEDGER["ledger"] = commodities.CommodityLedger()
    return _LEDGER["ledger"]


class Memos:

    def commodity_record(self, commodity: str) -> Dict[str, Any]:
        """The curated commodity's record (its material keys, its price ceiling factor), or an empty one."""
        return shared_ledger().commodities.get(commodity) or {}

    def material_commodity_map(self) -> Dict[str, str]:
        """material key -> curated commodity id, from commodities.json's own material_keys lists."""
        if "map" not in _COMMODITY_OF_MATERIAL:
            _COMMODITY_OF_MATERIAL["map"] = rules.commodity_map(shared_ledger().commodities)
        return _COMMODITY_OF_MATERIAL["map"]

    def commodity_country_output(self, commodity: str) -> float:
        """Tonnes a year the society brings to market of a catalogued commodity, which knows what built works raise it."""
        return shared_ledger().country_output(commodity, built=self.needs.legacy_projects().done)

    def done_memo(self, name: str, key: Hashable, compute: Callable[[], Any]) -> Any:
        """`compute()` remembered per (name, key) while the done set, the techniques in use and the economy's producers (they
        change as its year closes) are unchanged; for answers that depend only on what is built and run."""
        done = self.needs.legacy_projects().done
        stamp = (self.needs.price_epoch(), len(done), self.needs.producers_stamp())
        memo = self._done_store
        if memo is None or memo[0] != stamp or memo[1] is not done:
            memo = self._done_store = (stamp, done, {})
        table = memo[2]
        entry = (name, key)
        if entry not in table:
            table[entry] = compute()
        return table[entry]

    def producers_memo(self, name: str, key: Hashable, compute: Callable[[], Any]) -> Optional[Any]:
        """`compute()` remembered per (name, key) while the economy's producers are unchanged (they change only as its year
        closes); for answers that read nothing but the producers. An answer of None is not kept."""
        stamp = self.needs.producers_stamp()
        memo = self._producers_store
        if memo is None or memo[0] != stamp:
            memo = self._producers_store = (stamp, {})
        entry = (name, key)
        if entry not in memo[1]:
            answer = compute()
            if answer is None:      # not yet known (the economy is opening): ask again
                return None
            memo[1][entry] = answer
        return memo[1][entry]
