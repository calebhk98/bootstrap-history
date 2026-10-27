"""The kinds, founding rules, policies and commands the game ships; the actors module provides them to its own extension points.

The order of the spawners is the order they run in each year."""
from typing import Any, Callable, Dict, List, Tuple

from .extensions import ActorExtensions, Spawner


def shipped_kinds() -> Dict[str, Any]:
	from .firm import Firm
	from .foundation import Academy, Church
	from .government import Government
	from .group import InterestGroup
	from .player import Player
	from .stratum import Stratum
	from .trader import Trader
	return {"firm": Firm, "government": Government, "interest_group": InterestGroup, "player": Player, "stratum": Stratum,
	        "church": Church, "academy": Academy, "trader": Trader}


def shipped_spawners() -> List[Tuple[str, Spawner]]:
	from .demand_year import settle_all
	from .equity_round import equity_rounds
	from .exchange_commands import exchange_answers, patent_enforcement
	from .group_servants import run_servants
	from .joint_stock import dividends
	from .spinoff import consider_spinoffs
	from .strata_seed import strata_spawner
	from .trader_entry import trader_entry
	return [("firm_entry", lambda registry, world: registry.consider_entry(world)),
	        ("interest_groups", lambda registry, world: registry.consider_groups(world)),
	        ("dividends", dividends), ("strata", strata_spawner), ("equity_rounds", equity_rounds), ("spinoffs", consider_spinoffs),
	        ("exchange_answers", exchange_answers), ("patent_enforcement", patent_enforcement), ("state_servants", run_servants),
	        ("demand_year", settle_all), ("trader_entry", trader_entry)]


def shipped_world_scope() -> Callable[[Any, Any, Any], Any]:
	from .country_view import CountryWorld
	return lambda world, profile, holder: CountryWorld(world, profile, holder)


def shipped_policies() -> Dict[str, Callable[[], Any]]:
	from .fiscal_response import fiscal_policy_factories
	from .policy import BASE_POLICIES
	return {**BASE_POLICIES, **fiscal_policy_factories()}


def shipped_commands() -> Dict[str, Callable[[Any, Dict[str, Any], Any], str]]:
	from .demand_commands import answer_demand
	from .exchange_commands import accept, decline, offer
	from .patent import patent_command
	from .player_commands import base_commands
	return {**base_commands(), "patent": patent_command, "offer": offer, "accept": accept, "decline": decline,
	        "answer_demand": answer_demand}


def shipped_extensions() -> ActorExtensions:
	"""Everything the game ships, for a registry built with no assembly around it."""
	return ActorExtensions(shipped_kinds(), shipped_spawners(), shipped_world_scope(), shipped_policies(), shipped_commands())
