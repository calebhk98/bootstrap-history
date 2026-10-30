"""The quantities a dated event's cause can name (Complaints/266), each read from the views of the module that owns the fact.

A reader takes `needs` (the module's reads) and the cause's `node`, and answers a number or None when unmeasured."""
from typing import Any, Callable, Dict, NamedTuple, Optional

from . import cause_rules


class Quantity(NamedTuple):
    read: Callable[[Any, Optional[str]], Optional[float]]
    start_field: Optional[str] = None     # civilisation field holding the start value, when there is one
    needs_node: bool = False
    meaning: str = ""


def _population(needs: Any, node: Optional[str]) -> Optional[float]:
    return needs.population_total()


def _literacy(field: str) -> Callable[[Any, Optional[str]], Optional[float]]:
    def read(needs: Any, node: Optional[str]) -> Optional[float]:
        figure = needs.literacy(field, None)
        return None if figure is None else float(figure)
    return read


def _output_hours_per_head(needs: Any, node: Optional[str]) -> Optional[float]:
    return cause_rules.output_hours_per_head(needs.real_output_hours(None), needs.population_total())


def _funded_share(needs: Any, node: Optional[str]) -> float:
    budget = needs.state_budget_figures()
    return cause_rules.funded_share(budget["need"], budget["unfunded"])


def _army_share(needs: Any, node: Optional[str]) -> float:
    army = needs.army_figures()
    return cause_rules.army_share_of_wanted(army["wanted"], army["under_arms"])


def _state_holds(needs: Any, node: Optional[str]) -> float:
    return 1.0 if needs.state_knows(node) else 0.0


def _territory_share(needs: Any, node: Optional[str]) -> float:
    return cause_rules.territory_share(needs.tiles_listed_by(needs.civilisation()),
                                       needs.tiles_listed_by(needs.opening_civilisation()))


def _food_supply_ratio(needs: Any, node: Optional[str]) -> Optional[float]:
    return needs.nutrition_ratio_last_year()


def _coin_metal_kept(needs: Any, node: Optional[str]) -> float:
    return needs.state_budget_figures()["coin_metal_kept"]


def _from_strata(rule: Callable[[Any], Optional[float]]) -> Callable[[Any, Optional[str]], Optional[float]]:
    return lambda needs, node: rule(needs.home_strata_rows())


QUANTITIES: Dict[str, Quantity] = {
    "population": Quantity(_population, "population", meaning="people in the society"),
    "output_hours_per_head": Quantity(_output_hours_per_head, meaning="hours of real output a year per person"),
    "state_funded_share": Quantity(_funded_share, meaning="share of what the state needs that its revenue covers"),
    "army_share_of_wanted": Quantity(_army_share, meaning="soldiers kept over the force the state's threat calls for"),
    "literacy_general": Quantity(_literacy("literacy_general"), "literacy_general", meaning="general literacy"),
    "literacy_elite": Quantity(_literacy("literacy_elite"), "literacy_elite", meaning="elite literacy"),
    "state_holds": Quantity(_state_holds, needs_node=True, meaning="1 when the state holds the technology `node`, else 0"),
    "territory_share_of_start": Quantity(_territory_share, meaning="share of the tiles held at the start still held"),
    "food_supply_ratio": Quantity(_food_supply_ratio, meaning="calories available over calories needed last year"),
    "lowest_stratum_welfare": Quantity(_from_strata(cause_rules.lowest_stratum_welfare),
                                       meaning="welfare ratio of the worst-off free body of people"),
    "stratum_welfare_spread": Quantity(_from_strata(cause_rules.stratum_welfare_spread),
                                       meaning="best-off over worst-off welfare among free bodies of people"),
    "coin_metal_kept": Quantity(_coin_metal_kept, meaning="share of the opening metal the state's coin still holds"),
    "elite_share_vs_opening": Quantity(_from_strata(cause_rules.elite_share_vs_opening),
                                       meaning="propertied share of the people over its opening share"),
}
