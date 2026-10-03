"""Complaints 170, 175, 145, 158: ventures paging, path blockers, foreman and net/payback on available."""
from .harness import *
from sim.ui.proto.render_screens_big import render_available
from sim.ui.proto.render_screens_economy import render_ventures
from sim.ui.proto.render_screens_status import render_path

# --- 174: ventures pages like available and log
many = sim(capital=1_000_000.0)
shut_ids = [node_id for node_id in NODES if many.is_venture(node_id)][:70]
many.done.update(shut_ids)
many._done_changed()


def shut_page(**paging):
    return S._agent_dispatch(many, NODES, dict(cmd="ventures", **paging))


first = shut_page()
shut_total = len(first["you_know_how_but_have_not_opened"]) + first["and_more_you_could_open"]
check("ventures default screen stays short and says how many more",
      len(first["you_know_how_but_have_not_opened"]) <= 20 and first["and_more_you_could_open"] > 0,
      first.get("and_more_you_could_open"))
seen = []
offset = 0
while offset < shut_total:
    page = shut_page(offset=offset, limit=15)
    rows = page["you_know_how_but_have_not_opened"]
    if not rows:
        break
    seen += [row["id"] for row in rows]
    offset += 15
check("paging ventures by offset/limit lists every shut concern exactly once",
      len(seen) == shut_total == len(set(seen)), (len(seen), shut_total))
last_page = shut_page(offset=shut_total - 3, limit=15)
check("the last page has no 'more' count",
      not last_page.get("and_more_you_could_open")
      and len(last_page["you_know_how_but_have_not_opened"]) == 3)
check("limit smaller than the default is honoured",
      len(shut_page(limit=5)["you_know_how_but_have_not_opened"]) == 5)
check("limit above the default shows more rows",
      len(shut_page(limit=40)["you_know_how_but_have_not_opened"]) == 40)
check("the rendered screen tells you the command for the next page",
      "ventures offset:20" in render_ventures(first), render_ventures(first)[-400:])
parsed, _ = _PT("ventures offset:20 limit:5")
check("typed 'ventures offset:20 limit:5' reaches the command",
      parsed == {"cmd": "ventures", "offset": 20, "limit": 5}, parsed)
parsed_plain, _ = _PT("ventures")
check("bare 'ventures' still parses", parsed_plain == {"cmd": "ventures"}, parsed_plain)

# --- 179: path prints the nearest blocker itself
blocked = sim(capital=1_000_000.0)
route = S._agent_dispatch(blocked, NODES, {"cmd": "path", "id": "ag2_botanic_garden"})
check("set-up: nothing on this route is startable", route["startable_today_count"] == 0, route)
blockers = route.get("nearest_blockers")
check("path carries the nearest blocker with its reason",
      isinstance(blockers, list) and blockers and blockers[0]["id"] == "ag2_botanic_garden"
      and "craftsmen" in blockers[0]["why"], blockers)
stuck_reason = blocked.start_reason("ag2_botanic_garden")[1]
check("...and it is the same text start_reason (and so stuck) gives",
      blockers[0]["why"] == stuck_reason)
path_text = render_path(route)
check("the path screen prints the blocker line",
      "ag2_botanic_garden" in path_text and "needs 3 trained craftsmen" in path_text, path_text)

# --- 149 and 162: available rows carry foreman, net and payback
rows_sim = sim(capital=1_000_000.0)
listing = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "all": True, "limit": 400})
by_id = {row["id"]: row for row in listing["available"]}
loom = by_id.get("tex_horizontal_loom")
check("set-up: the loom is on the list", loom is not None)
trade, fte = rows_sim.venture_foreman("tex_horizontal_loom")
check("available rows name the specialist foreman as `why` and `open` do",
      loom["specialist_foreman"] == {"trade": trade, "fte": round(fte, 2)} and trade, loom)
plain = next(row for row in listing["available"]
             if rows_sim.venture_foreman(row["id"])[0] is None)
check("a row with no specialist foreman omits the field",
      "specialist_foreman" not in plain, plain["id"])
check("net per year is earnings minus upkeep",
      abs(loom["net_per_year"] - (loom["earns_per_year"] - loom["costs_per_year_after"])) < 0.11, loom)
ramp_years = rows_sim.cfg["revenue_ramp_years"]
flat_years = loom["cost"] / loom["net_per_year"]
check("payback is slower than cost/net because revenue ramps up",
      loom["payback_years"] is not None and loom["payback_years"] > flat_years, (loom["payback_years"], flat_years))
check("payback is no worse than the flat figure plus the ramp's whole shortfall",
      loom["payback_years"] < flat_years + ramp_years, loom["payback_years"])
loser = next(row for row in listing["available"]
             if row["earns_per_year"] > 0 and row["net_per_year"] < 0)
check("a loss-maker has no payback", "payback_years" not in loser, loser)
check("a knowledge node has zero net and no payback",
      "payback_years" not in by_id["units_standards"])

by_net = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "net", "reverse": True, "limit": 30})
nets = [row["net_per_year"] for row in by_net["available"]]
check("sort:net reverse puts the biggest net first", nets == sorted(nets, reverse=True) and nets[0] > 0, nets[:5])
by_payback = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "payback", "limit": 400})
paybacks = [row.get("payback_years") for row in by_payback["available"]]
finite = [value for value in paybacks if value is not None]
check("sort:payback lists the quickest payback first and never-paying last",
      finite == sorted(finite) and paybacks[:len(finite)] == finite and finite, paybacks[:5])
parsed_sort, _ = _PT("available sort:net reverse")
check("typed sort:net parses", parsed_sort.get("sort") == "net", parsed_sort)
bad = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "nonsense"})
check("the sort error names the new sorts", "net" in bad["error"] and "payback" in bad["error"], bad)

text = render_available(by_net)
header_line = next(line for line in text.splitlines() if line.startswith("ID"))
check("the table has NET/YR, PAYBACK and FOREMAN columns",
      all(word in header_line for word in ("NET/YR", "PAYB", "FOREMAN")), header_line)
loom_line = next((line for line in render_available(listing).splitlines()
                  if line.startswith("tex_horizontal_loom")), "")
check("a foreman row prints the trade", trade[:7] in loom_line, loom_line)
check("the table stays within a sane width", len(header_line) <= 140, len(header_line))
path_rows = S._agent_dispatch(rows_sim, NODES, {"cmd": "path", "id": "tex_horizontal_loom"})
path_header = next(line for line in render_path(path_rows).splitlines() if line.startswith("ID"))
check("path's table header matches available's", path_header.split() == header_line.split(),
      (path_header, header_line))
