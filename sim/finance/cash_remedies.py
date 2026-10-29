"""The commands that raise cash or cut costs, each quoted with the amount the command itself uses, for refusals to list.

Needs: money_text, held_goods, goods_stock, material_commodity, sale_quote, techniques_held, techniques_granted, operating,
venture_real_upkeep, mine_capacity, mine_workings, mine_working_cost, staff."""
from typing import List

from sim.living_stock.api import stock_rates

from . import remedy_rules


class CashRemedies:

	def cash_remedies(self) -> List[str]:
		"""Lines like "sell iron 40 (brings 1,200 now)", largest amount first."""
		needs = self.needs
		money_text = needs.money_text
		found = []
		# living stock is the means of breeding more; it is not offered as cash
		breeding_stock = {needs.material_commodity[material] for material in stock_rates()}
		for material in sorted(needs.held_goods()):
			if material in breeding_stock:
				continue
			_key, tonnes, money = needs.sale_quote(material, needs.goods_stock[material])
			found.append(remedy_rules.sale_remedy(material, tonnes, money, money_text))
		held, granted = needs.techniques_held(), needs.techniques_granted()
		for node_id in sorted(needs.operating()):
			if node_id in held and node_id not in granted:
				found.append(remedy_rules.mothball_remedy(node_id, needs.venture_real_upkeep(node_id), money_text))
		workings = needs.mine_workings()
		for material in sorted(needs.mine_capacity()):
			saving = sum(needs.mine_working_cost(working) for working in workings if working.get("material") == material)
			found.append(remedy_rules.mine_closing_remedy(material, saving, money_text))
		for trade, people in sorted(needs.staff()["employees"].items()):
			found.append(remedy_rules.firing_remedy(trade, people, needs.labour_market().quote_annual(trade), money_text))
		return remedy_rules.top_remedies([remedy for remedy in found if remedy is not None])
