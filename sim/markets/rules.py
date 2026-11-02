"""The goods market's plain rules: functions of their inputs, with no game behind them."""

HOME_SELLER = "home"   # the seller id of the home society's own producers, as opposed to a trading partner's id

MINIMUM_FLOOR_RATIO = 0.01   # the clearing searches between floor and ceiling in logs, so the floor stays above nothing


def tonnes_sold(asked, held, market_room):
	"""An order is cut to what is held and to what the market will still take this year."""
	return min(asked, held, market_room)


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
