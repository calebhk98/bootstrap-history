"""The goods market's plain rules: functions of their inputs, with no game behind them."""
from sim.constants import declare


def tonnes_sold(asked, held, market_room):
	"""An order is cut to what is held and to what the market will still take this year."""
	return min(asked, held, market_room)


WORKSHOP_CATEGORY = "your own workshop"
CONCERNS_NAMED_PER_CATEGORY = declare(
	"CONCERNS_NAMED_PER_CATEGORY", 6, kind="temporary_heuristic", unit="concerns", source=None, confidence="D",
	retire="no complaint covers it; a report-layout bound, retired when the market-ceiling report pages through every concern of a category",
	why="The report of what the market ceiling took names this many of a category's biggest concerns; more would not fit "
	    "a line, and the rows' amounts do not depend on it.")
WORKSHOP_TAKINGS_FLOOR = declare(
	"WORKSHOP_TAKINGS_FLOOR", 0.5, kind="temporary_heuristic", unit="money a year", source=None, confidence="D",
	retire="no complaint covers it; a report-rounding bound, retired when the market-ceiling report pages through every concern of a category",
	why="A workshop whose yearly takings are below this is left out of the ceiling report as a row of its own: it would "
	    "show as nothing at the report's one-decimal rounding.")


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
	if workshop_nominal > WORKSHOP_TAKINGS_FLOOR:
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
