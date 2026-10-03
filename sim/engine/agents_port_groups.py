"""What interest groups can see of who is hurt: producers the founder's sales displace and
employers whose hands the founder's hiring bids up. Mixed into `SimWorld`."""
from typing import Any, Dict, List

from sim.agents.api import CONCESSION_PREFIX, Sector, sector_key

from .goods_market_api import FOUNDER


class GroupView:
	"""Read-only questions behind who organises and what it asks of the state."""

	_sim: Any

	def _annual_labourer_wage(self) -> float:
		return max(1e-9, self.pay_per_person_year("labourer"))

	def _commodity_quote(self, commodity: str) -> Any:
		"""The quote for the first priced material the commodity is made of (its main product)."""
		sim = self._sim
		made_of = sim.economy.materials_in(commodity)
		for material in made_of + [commodity]:
			quote = sim.economy.trade_quote(material)
			if quote is not None:
				return quote
		return None

	def displaced_producers(self) -> List[Sector]:
		"""Producers of each commodity the founder sold into the market this year: what the
		society's own producers sell less at the price, and the people that income keeps."""
		sim = self._sim
		wage = self._annual_labourer_wage()
		sectors = []
		for commodity in sim.economy.goods.commodities_sold_by(FOUNDER):
			state = sim.market_state(commodity)
			quote = self._commodity_quote(commodity)
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
				"your sales of %s take %s tonnes a year from their market" % (commodity, "{:,.0f}".format(displaced)),
				lost, base, lost / wage, 1.0))
		return sectors

	def squeezed_employers(self) -> List[Sector]:
		"""Employers of each trade whose price the hiring of the founder and the firms has pushed
		above the wage table. With a fixed budget they can no longer afford the share of the town's
		hands that the premium prices out, and the hands the founder and the firms keep are hands
		they cannot hire; the value lost is those hands at the going wage."""
		sim = self._sim
		sectors = []
		for trade in sim.economy.labour.pressured_trades():
			factor = sim.economy.labour.price_factor(trade)
			if factor <= 1.0 + 1e-9:
				continue
			pool = sim.labour.market_supply(trade) / sim.HOURS_PER_PERSON_YEAR
			priced_out = pool * (1.0 - 1.0 / factor)
			wage = sim.economy.labour.unscarce_annual(trade)
			sectors.append(Sector(
				"squeezed_employers", trade, "employers of %s in the founder's town" % trade,
				"hiring by you and the firms has raised the going price of %s by %d%% and priced out about %s hands"
				% (trade, round((factor - 1.0) * 100), "{:,.0f}".format(priced_out)),
				priced_out * wage, pool * wage * factor, priced_out * wage / self._annual_labourer_wage(),
				sim.labour.local_market_share()))
		return sectors

	def sectors(self) -> Dict[str, Sector]:
		"""Everyone hurt this year, by key."""
		def compute() -> Dict[str, Sector]:
			return {sector_key(sector.kind, sector.subject): sector
					for sector in self.displaced_producers() + self.squeezed_employers()}
		return self._once("sectors", compute)  # type: ignore[attr-defined,no-any-return]

	def group_claims(self) -> Dict[str, float]:
		"""What the state has undertaken to make good to each organised group, by budget line name."""
		return {CONCESSION_PREFIX + group.actor_id: group.record.claim
				for group in self._sim.actors.of_kind("interest_group") if group.organised()}  # type: ignore[attr-defined]

	def scope_revenue(self, scope: float) -> float:
		"""The state's yearly revenue from a territory holding `scope` of the whole."""
		return max(1e-9, self.state_revenue() * scope)  # type: ignore[attr-defined,no-any-return]

	def founder_protection(self) -> float:
		return float(self._sim.state.household.protection)

	def lodge_blame(self, amount: float, text: str, year_gap: int, group_record: Any) -> None:
		"""A group's petition puts blame on the founder; the log says who and why, once in a while."""
		sim = self._sim
		household = sim.state.household
		household.scandal += amount
		last = group_record.last_logged_year
		if last is None or self.year - last >= year_gap:  # type: ignore[attr-defined]
			group_record.last_logged_year = self.year  # type: ignore[attr-defined]
			household.log.append((self.year, text))  # type: ignore[attr-defined]

	def say(self, text: str) -> None:
		"""A line in the founder's log, for a change in who is organised against him."""
		self._sim.state.household.log.append((self.year, text))  # type: ignore[attr-defined]

	def state_in_deficit(self) -> bool:
		"""Whether the state could pay all it set out to last year."""
		record = self.government().record
		return sum(record.unfunded.values()) > 1e-9

	def concession_paid(self, line_name: str) -> float:
		"""What the state paid last year on a named line of its budget."""
		record = self.government().record
		return max(0.0, record.need.get(line_name, 0.0) - record.unfunded.get(line_name, 0.0))

