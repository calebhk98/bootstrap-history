"""What interest groups can see of who is hurt: producers the founder's sales displace and
employers whose hands the founder's hiring bids up."""
from typing import Any, Dict, List, Optional

from sim.agents.api import CONCESSION_PREFIX, Sector, sector_key
from sim.polity.api import AddScandal
from sim.reporting.api import RecordEvent

from .rules import plain_number
from .world_memo import once


def founder_share_of_sellers(sellers, other_actors_concerns):
    """The founder's share of the concerns selling into a category: every seller's concerns (`sellers`, the
    founder's included) less the other actors' (`other_actors_concerns`), over every seller's, held to 0..1."""
    return min(1.0, max(0.0, 1.0 - other_actors_concerns / sellers))


def commodity_quote(needs: Any, commodity: str) -> Any:
	"""The quote for the first priced material the commodity is made of (its main product)."""
	material = needs.main_material_of[commodity]
	return None if material is None else needs.material_trade_quote[material]


class Groups:
	"""Read-only questions behind who organises and what it asks of the state. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._memo: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	@property
	def goods_category_names(self) -> Any:
		"""The goods categories: concerns in them share one market."""
		return self.needs.goods_categories()

	def _annual_labourer_wage(self) -> float:
		labour = self.world.labour
		return max(1e-9, labour.pay_per_person_year(labour.trade_of_role("unskilled")))

	def displaced_producers(self) -> List[Sector]:
		"""Producers of each commodity the founder sold into the market this year: what the
		society's own producers sell less at the price, and the people that income keeps."""
		needs = self.needs
		wage = self._annual_labourer_wage()
		sectors = []
		for commodity in needs.commodities_sold_by_acting_party():
			state = needs.market_state[commodity]
			quote = commodity_quote(needs, commodity)
			if state is None or quote is None:
				continue
			displaced = state["displaced_by_founder_tonnes"]
			if displaced <= 0.0:
				continue
			price = quote["buy_per_tonne"]
			lost = displaced * price
			base = (state["society_sales_tonnes"] + displaced) * price
			sectors.append(Sector(
				"displaced_producers", commodity, "producers of " + commodity,
				"your sales of %s take %s from their market" % (commodity, needs.mass_rate_text(displaced, grouped=True, short=False)),
				lost, base, lost / wage, 1.0))
		return sectors

	def goods_categories(self) -> Dict[str, Dict[str, Any]]:
		"""Each goods category the founder's and the firms' concerns sell into: how far the price of
		what it sells has fallen from its opening level, and the share of each trade's work that goes
		to it (TEMPORARY HEURISTIC, CLAUDE.md 4.4: the trade's hours in the category's techniques over
		its hours in every technique of the tree, until recipes give each trade's work by good)."""
		needs = self.needs
		nodes = needs.tree_nodes()
		hours: Dict[str, Dict[str, float]] = {}
		for category in sorted(self.goods_category_names):
			for node_id in needs.nodes_in_category[category]:
				for trade, trade_hours in (nodes[node_id].get("lab") or {}).items():
					hours.setdefault(category, {})[trade] = hours.get(category, {}).get(trade, 0.0) + trade_hours
		totals: Dict[str, float] = {}
		for node in nodes.values():
			for trade, trade_hours in (node.get("lab") or {}).items():
				totals[trade] = totals.get(trade, 0.0) + trade_hours
		categories = {}
		operating = set(needs.operating())
		for category in sorted(hours):
			founder_concerns = len(operating.intersection(needs.nodes_in_category[category]))
			actors_concerns = self.world.staff.actor_concerns_in(category)
			ratio = self._category_price_ratio(category) if founder_concerns + actors_concerns else None
			if ratio is None or ratio >= 1.0:
				continue
			categories[category] = {"price_depression": 1.0 - ratio, "trade_weights": {
				trade: trade_hours / totals[trade] for trade, trade_hours in hours[category].items()},
				"founder_share": founder_share_of_sellers(founder_concerns + actors_concerns, actors_concerns)}
		return categories

	def _category_price_ratio(self, category: str) -> Optional[float]:
		"""The economy's cleared prices for what the category's concerns sell over their long-run prices (the mean over the
		concerns whose takings are derived from output); None when none is."""
		needs = self.needs
		nodes = needs.tree_nodes()
		factors = [needs.node_output_market_factor(nodes[node_id]) for node_id in needs.nodes_in_category[category]
		           if needs.concern_baskets_now[node_id] is not None]
		return sum(factors) / len(factors) if factors else None

	def sectors(self) -> Dict[str, Sector]:
		"""Everyone hurt this year, by key."""
		def compute() -> Dict[str, Sector]:
			world = self.world
			registry = world.registry
			strata = registry.countries.home_actors("stratum")
			goods = Sector.of_goods(strata, self.goods_categories(), world) if strata else []
			caused = self.displaced_producers() + goods
			firms = registry.countries.home_actors("firm")
			foundations = [foundation for kind in ("church", "academy") for foundation in registry.countries.home_actors(kind)]
			governments = [government for government in registry.of_kind("government")
						   if government.record.country is None]
			servants = [sector for government in governments for sector in Sector.of_servants(government, world)]
			falling = Sector.of_strata(strata, world) + Sector.of_firms(firms, world) + Sector.of_foundations(foundations) + servants
			total_fall = sum(sector.lost_income for sector in falling)
			# what the founder is blamed for in a body's loss: the share of it his measured doing explains
			share = min(1.0, sum(sector.lost_income for sector in caused) / total_fall) if total_fall > 0.0 else 0.0
			for sector in falling:
				sector.blame_share = share
			Sector.remember_welfare(strata, world)
			Sector.remember_margins(firms)
			Sector.remember_foundations(foundations)
			for government in governments:
				Sector.remember_servants(government, world)
			return {sector_key(sector.kind, sector.subject): sector for sector in caused + falling}
		return once(self._memo, "sectors", compute)  # type: ignore[no-any-return]

	def group_claims(self) -> Dict[str, float]:
		"""What the state has undertaken to make good to each organised group, by budget line name."""
		return {CONCESSION_PREFIX + group.actor_id: group.record.claim
				for group in self.world.registry.countries.home_actors("interest_group") if group.organised()}

	def faction_backing(self) -> Dict[str, float]:
		"""The weight each organised group can put behind a claimant to the throne: its strength."""
		return {group.actor_id: group.record.strength
				for group in self.world.registry.countries.home_actors("interest_group")
				if group.organised() and group.record.strength > 0.0}

	def scope_revenue(self, scope: float) -> float:
		"""The state's yearly revenue from a territory holding `scope` of the whole."""
		return max(1e-9, self.world.revenue.state_revenue() * scope)

	def founder_protection(self) -> float:
		return float(self.needs.standing()["protection"])

	def lodge_blame(self, amount: float, text: str, year_gap: int, group_record: Any) -> None:
		"""A group's petition puts blame on the founder; the log says who and why, once in a while."""
		self.needs.send(AddScandal(amount))
		last = group_record.last_logged_year
		year = self.world.setting.year
		if last is None or year - last >= year_gap:
			group_record.last_logged_year = year
			self.needs.send(RecordEvent.from_line(text))  # the caller passes a LogLine (InterestGroup.words)

	def money_text(self, amount: float, grouped: bool = False, short: bool = False) -> str:
		return self.needs.money_text(amount, grouped=grouped, short=short)

	def plain_number(self, value: float) -> str:
		return plain_number(value)

	def say(self, text: str) -> None:
		"""A line in the founder's log, for a change in who is organised against him."""
		self.needs.send(RecordEvent.from_line(text))  # the caller passes a LogLine

	def state_in_deficit(self) -> bool:
		"""Whether the state could pay all it set out to last year."""
		record = self.world.setting.government().record
		return sum(record.unfunded.values()) > 1e-9

	def concession_paid(self, line_name: str) -> float:
		"""What the state paid last year on a named line of its budget."""
		record = self.world.setting.government().record
		return max(0.0, record.need.get(line_name, 0.0) - record.unfunded.get(line_name, 0.0))

