"""Complaints 170, 175, 145, 158: `ventures` paging, `path` blockers, and the foreman, net and payback of an `available`
row. Each rule runs on a stand-in game or a built reply (no game): the paging, the row economics (net, payback,
foreman, sort keys), the nearest blockers of a route, and the tables that print them. The commands through a game are
test_screens_ventures_path_available_scenario."""
from types import SimpleNamespace

from .harness import check, NODES, _PT

from sim.ui.proto import available_economics, venture_paging
from sim.ui.proto.render_screen_available import render_available
from sim.ui.proto.render_screens_economy import render_ventures
from sim.ui.proto.render_screens_status import render_path
from sim.ui.proto.route_blockers import route_blockers
from sim.ui.proto.techtree import _SORT_KEYS, _SORT_KEY_NAMES
from sim.tests.ui_stand_in import Game

QUICK_TOPIC = True

# --- 174: ventures pages like available and log
check("a bare ventures command asks for the first default page", venture_paging.page_request({}, 20) == (0, 20))
check("an offset and a limit are read, a limit smaller or larger than the default honoured",
      venture_paging.page_request({"offset": 20, "limit": 5}, 20) == (20, 5)
      and venture_paging.page_request({"limit": 40}, 20) == (0, 40))
check("a negative offset, a zero or negative limit and text that is not a number fall back safely",
      venture_paging.page_request({"offset": -4}, 20) == (0, 20) and venture_paging.page_request({"limit": 0}, 20) == (0, 20)
      and venture_paging.page_request({"limit": -3}, 20) == (0, 1)
      and venture_paging.page_request({"offset": "x", "limit": "y"}, 20) == (0, 20))

first = venture_paging.page_fields(70, 0, 20)
check("the default screen stays short and says how many more there are and the command for the next page",
      first["and_more_you_could_open"] == 50 and first["next_page"] == "ventures offset:20 limit:20" and first["showing_from"] == 0
      and first["shut_concerns_in_all"] == 70, first)
seen = 0
offset, pages = 0, 0
while offset < 70:
    fields = venture_paging.page_fields(70, offset, 15)
    seen += min(15, 70 - offset)
    offset += 15
    pages += 1
check("paging by offset and limit reaches every shut concern exactly once and ends", seen == 70 and pages == 5)
check("the last page has no 'more' count", "and_more_you_could_open" not in venture_paging.page_fields(70, 67, 15))
check("a list that exactly fills the page has no 'more' either", "and_more_you_could_open" not in venture_paging.page_fields(20, 0, 20))
# presentation: the screen tells you the command for the next page
check("the rendered screen tells you the command for the next page",
      "ventures offset:20" in render_ventures(dict(first, ok=True, running="nothing", note="")), None)
parsed, _ = _PT("ventures offset:20 limit:5")
check("typed 'ventures offset:20 limit:5' reaches the command", parsed == {"cmd": "ventures", "offset": 20, "limit": 5}, parsed)
check("bare 'ventures' still parses", _PT("ventures")[0] == {"cmd": "ventures"})


# --- 149 and 162: available rows carry foreman, net and payback
def _venture(earnings, upkeep, foreman=None, stock=None, ramp_years=4):
    return Game(
        cfg={"revenue_ramp_years": ramp_years}, venture_real_earnings=lambda node_id: earnings,
        venture_real_upkeep=lambda node_id: upkeep, venture_foreman=lambda node_id: foreman or (None, 0.0),
        project_cost=lambda node_id: 1000.0, stock_needed_by=lambda node_id: stock)


earner = _venture(earnings=300.0, upkeep=100.0)
fields = available_economics.row_fields(earner, "loom", {})
check("net per year is earnings minus upkeep", fields["net_per_year"] == 200.0, fields)
flat_years = 1000.0 / 200.0
check("payback is slower than cost over net because revenue ramps up, and no worse than the flat figure plus the ramp",
      flat_years < fields["payback_years"] < flat_years + 4, (fields["payback_years"], flat_years))
check("payback is found year by year: upkeep is paid in full from the first year while takings ramp, so year one loses 25, "
      "year two nets 50, and an outlay of 10 is earned back 1.7 years in",
      available_economics.payback_years(earner, "loom", 10.0) == 1.7, available_economics.payback_years(earner, "loom", 10.0))
check("a loss-maker has no payback and a negative net",
      available_economics.payback_years(_venture(earnings=100.0, upkeep=300.0), "loom", 1000.0) is None
      and available_economics.net_per_year(_venture(earnings=100.0, upkeep=300.0), "loom") == -200.0)
check("a concern whose takings only just match its upkeep never pays back",
      available_economics.payback_years(_venture(earnings=100.0, upkeep=100.0), "loom", 1000.0) is None)
check("a payback beyond the horizon is none", available_economics.payback_years(_venture(earnings=101.0, upkeep=100.0), "loom", 1.0e6) is None)
knowledge = available_economics.row_fields(_venture(earnings=0.0, upkeep=0.0), "theory", {})
check("a knowledge node has zero net and no payback", knowledge == {"net_per_year": 0.0}, knowledge)

foreman = available_economics.row_fields(_venture(200.0, 50.0, foreman=("chemist", 0.456)), "lab", {})
check("a row names the specialist foreman as `why` and `open` do (trade and the share of a person's year)",
      foreman["specialist_foreman"] == {"trade": "chemist", "fte": 0.46}, foreman)
check("a row with no specialist foreman omits the field", "specialist_foreman" not in fields)
check("held living stock rides on the row when the node needs some",
      available_economics.row_fields(_venture(200.0, 50.0, stock=[{"material": "ox"}]), "farm", {})["living_stock"] == [{"material": "ox"}])

# the sort keys
ids = {"slow": _venture(300.0, 250.0), "quick": _venture(900.0, 100.0), "never": _venture(100.0, 300.0)}
game = Game(
    venture_real_earnings=lambda node_id: ids[node_id].venture_real_earnings(node_id),
    venture_real_upkeep=lambda node_id: ids[node_id].venture_real_upkeep(node_id),
    cfg={"revenue_ramp_years": 4}, project_cost=lambda node_id: 1000.0)
by_net = sorted(ids, key=lambda node_id: _SORT_KEYS["net"](game, {}, node_id), reverse=True)
check("sort:net reverse puts the biggest net first", by_net == ["quick", "slow", "never"], by_net)
by_payback = sorted(ids, key=lambda node_id: (_SORT_KEYS["payback"](game, {}, node_id), node_id))
check("sort:payback lists the quickest payback first and never-paying last", by_payback == ["quick", "slow", "never"], by_payback)
check("the advertised sort names include the new sorts, each with a key", {"net", "payback"} <= set(_SORT_KEY_NAMES)
      and all(name in _SORT_KEYS for name in _SORT_KEY_NAMES))
check("typed sort:net parses", _PT("available sort:net reverse")[0].get("sort") == "net")

# the table
rows = [{"id": "loom", "name": "Horizontal loom", "cost": 900.0, "founder_hours": 50, "calendar_floor_years": 1.0, "risk": 0.1,
         "earns_per_year": 300.0, "costs_per_year_after": 100.0, "net_per_year": 200.0, "payback_years": 6.0,
         "specialist_foreman": {"trade": "chemistry", "fte": 0.5}, "downstream_count": 3}]
listing = {"count": 1, "available": rows}
text = render_available(listing)
header_line = next(line for line in text.splitlines() if line.startswith("ID"))
check("the table has NET/YR, PAYBACK and FOREMAN columns", all(word in header_line for word in ("NET/YR", "PAYB", "FOREMAN")), header_line)
loom_line = next(line for line in text.splitlines() if line.startswith("loom"))
check("a foreman row prints the first seven letters of the trade, its net and its payback",
      "chemist" in loom_line and "200" in loom_line and "6" in loom_line, loom_line)
check("the table stays within a sane width", len(header_line) <= 140, len(header_line))
path_header = next(line for line in render_path({"name": "Goal", "id": "goal", "remaining_count": 2, "startable_today_count": 1,
                                                 "still_waiting_on_something_else": 1,
                                                 "startable_today_toward_this": rows}).splitlines() if line.startswith("ID"))
check("path's table header matches available's", path_header.split() == header_line.split(), (path_header, header_line))


# --- 179: path prints the nearest blocker itself
class _Route(SimpleNamespace):
    def start_blockers(self, node_id):
        return self.blockers.get(node_id, [])

    def start_reason(self, node_id):
        return False, "reason of " + node_id


tree = {"far": {"pre": ["mid"]}, "mid": {"pre": ["near"]}, "near": {"pre": []}, "other": {"pre": []}}
route_game = _Route(done=set(), blockers={"near": [{"text": "needs 3 trained craftsmen", "kind": "staff"},
                                                  {"text": "also money", "kind": "money"},
                                                  {"text": "and more money", "kind": "money"}]})
blockers = route_blockers(route_game, tree, ["far", "mid", "near", "other"], 3)
check("the nodes of an unstartable route come nearest to startable first (fewest unbuilt prerequisites)",
      [row["id"] for row in blockers] == ["near", "other", "mid"], blockers)
check("each carries the reason start_blockers gives, its kind, and the distinct kinds in order",
      blockers[0]["why"] == "needs 3 trained craftsmen" and blockers[0]["kind"] == "staff" and blockers[0]["kinds"] == ["staff", "money"],
      blockers[0])
check("a node with no blocker listed falls back to start_reason's text", blockers[1]["why"] == "reason of other" and blockers[1]["kind"] is None)
route_game.done = {"near"}
check("what is built no longer counts against a node's nearness",
      [row["id"] for row in route_blockers(route_game, tree, ["far", "mid"], 2)] == ["mid", "far"])
check("only `count` blockers are returned", len(route_blockers(route_game, tree, ["far", "mid", "other"], 1)) == 1)
shown = render_path({"name": "Goal", "id": "goal", "remaining_count": 1, "startable_today_count": 0,
                     "still_waiting_on_something_else": 1, "startable_today_toward_this": "nothing yet",
                     "nearest_blockers": [{"id": "ag2_botanic_garden", "why": "needs 3 trained craftsmen"}]})
# presentation: the path screen prints the blocker line
check("the path screen prints the blocker line", "ag2_botanic_garden" in shown and "needs 3 trained craftsmen" in shown, shown)
check("the botanic garden is a node of the tree for the scenario", "ag2_botanic_garden" in NODES)
