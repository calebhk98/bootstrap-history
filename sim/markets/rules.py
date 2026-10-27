"""The goods market's plain rules: functions of their inputs, with no game behind them."""
from . import categories

HOME_SELLER = "home"   # the seller id of the home society's own producers, as opposed to a trading partner's id

MINIMUM_FLOOR_RATIO = 0.01   # the clearing searches between floor and ceiling in logs, so the floor stays above nothing


def tonnes_sold(asked, held, market_room):
	"""An order is cut to what is held and to what the market will still take this year."""
	return min(asked, held, market_room)


def seller_revenue_factor(price_ratio, quantity_ratio, active_sellers, income_factor=1.0):
	"""One seller's revenue relative to day one: the category's price ratio times quantity ratio shared among the
	active sellers, times `income_factor` (one for an essential category)."""
	return price_ratio * quantity_ratio / active_sellers * income_factor


def reach_factor(reach):
	"""How much further than a purely local market goods can travel, capped so several reach flags do not multiply into an
	implausible number."""
	return min(reach, categories.REACH_CEILING)


def category_ratios(config, sellers, extra, world_age, pop_scale, reach):
	"""(price ratio, quantity ratio, sellers counted) of a whole goods category: `sellers` already in it and `extra` more
	sharing its total supply, the oldest of them `world_age` years old. The time constant grows with the civilisation's
	size and shrinks with its reach."""
	sellers += extra
	tau = max(1.0, config["tau"] * (pop_scale ** categories.GOODS_TAU_POP_SCALE_EXPONENT) / reach)
	world_supply = 1.0 + world_age / tau
	total_supply = world_supply * sellers
	elasticity = config["eta"]
	price_ratio = max(config["floor"], min(1.0, total_supply ** (-1.0 / elasticity)))
	quantity_ratio = min(total_supply, price_ratio ** (-elasticity))
	return (price_ratio, quantity_ratio, sellers)


def essential_price_ratio(category_ratios_of_essentials, farm_hectares):
	"""The cost of living stand-in: the mean of the essential categories' price ratios that exist (one when none does), or
	what household farmland makes staples cost if that is lower."""
	ratios = [ratio for ratio in category_ratios_of_essentials if ratio is not None]
	market_ratio = sum(ratios) / len(ratios) if ratios else 1.0
	farm_ha = max(0.0, farm_hectares or 0.0)
	farm_ratio = max(categories.HOUSEHOLD_FARM_PRICE_RATIO_FLOOR,
	                 1.0 / (1.0 + farm_ha / categories.HOUSEHOLD_FARM_HECTARES_HALF_EFFECT))
	return min(market_ratio, farm_ratio)


def income_factor(essential_ratio):
	"""How much extra a population has to spend on everything that is not a staple, from how cheap staples are."""
	return max(categories.INCOME_FACTOR_FLOOR, min(categories.INCOME_FACTOR_CEILING,
	                                                1.0 + categories.INCOME_ELASTICITY * (1.0 - essential_ratio)))


def category_factor(ratios, is_essential, income_factor_of_staples):
	"""One seller's revenue in a category relative to day one; one when the category has no seller."""
	if ratios is None:
		return 1.0
	return seller_revenue_factor(*ratios, 1.0 if is_essential else income_factor_of_staples)


def floor_ratio(running_share, unsplit_floor_ratio):
	"""The lowest price over the incumbents' cost their producers sell at: the running share of the cost where it is split,
	the whole cost (`unsplit_floor_ratio`) where it is not."""
	return unsplit_floor_ratio if running_share is None else max(MINIMUM_FLOOR_RATIO, running_share)


WORKSHOP_CATEGORY = "your own workshop"
CONCERNS_NAMED_PER_CATEGORY = 6


def absorption_by_category(deduction, concern_rows, category_of, workshop_nominal):
	"""Rows {category, nominal, absorbed, lost, concerns} whose `lost` values add up to `deduction`, the figure the ledger
	deducts when the market ceiling cuts every earner by the same share. `concern_rows` is {node id: yearly takings},
	`category_of(node id)` its goods category (or None), `workshop_nominal` the workshop's takings."""
	if deduction <= 0:
		return []
	groups = {}
	for node_id, amount in concern_rows.items():
		category = category_of(node_id) or "other"
		group = groups.setdefault(category, {"nominal": 0.0, "members": []})
		group["nominal"] += amount
		group["members"].append((amount, node_id))
	if workshop_nominal > 0.5:
		groups[WORKSHOP_CATEGORY] = {"nominal": workshop_nominal, "members": []}
	squeezed_total = sum(group["nominal"] for group in groups.values())
	if squeezed_total <= 0:
		return []
	out = []
	for category, group in groups.items():
		lost = round(deduction * group["nominal"] / squeezed_total, 1)
		members = sorted(group["members"], key=lambda member: (-member[0], member[1]))
		out.append({"category": category, "nominal": round(group["nominal"], 1),
		            "lost": lost,
		            "concerns": [node_id for _amount, node_id in members[:CONCERNS_NAMED_PER_CATEGORY]]})
	out.sort(key=lambda row: (-row["lost"], row["category"]))
	# Rounding residue goes to the largest row, so the rows sum exactly.
	residue = round(deduction - sum(row["lost"] for row in out), 1)
	out[0]["lost"] = round(out[0]["lost"] + residue, 1)
	for row in out:
		row["absorbed"] = round(row["nominal"] - row["lost"], 1)
	return out
