"""`ventures` paging, `path` blockers and the economics columns of `available`, through running games (the rules are
test_screens_ventures_path_available): (1) paging a game's seventy shut concerns lists each exactly once; (2) `path` to
a goal nothing on which is startable carries the same blocker text `start_reason` gives; (3) the `available` rows carry
the fields the economics module computes, and the sorts order them."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto import available_economics

# --- (1) ventures pages through a game's shut concerns
many = sim(capital=1_000_000.0)
shut_ids = [node_id for node_id in NODES if many.is_venture(node_id)][:70]
many.done.update(shut_ids)
many._done_changed()


def shut_page(**paging):
    return S._agent_dispatch(many, NODES, dict(cmd="ventures", **paging))


first = shut_page()
shut_total = len(first["you_know_how_but_have_not_opened"]) + first["and_more_you_could_open"]
seen, offset = [], 0
while offset < shut_total:
    rows = shut_page(offset=offset, limit=15)["you_know_how_but_have_not_opened"]
    if not rows:
        break
    seen += [row["id"] for row in rows]
    offset += 15
check("ventures' default screen stays short; paging lists every shut concern exactly once; the last page has no 'more'; "
      "the limit is honoured",
      len(first["you_know_how_but_have_not_opened"]) <= 20 and first["and_more_you_could_open"] > 0
      and len(seen) == shut_total == len(set(seen))
      and not shut_page(offset=shut_total - 3, limit=15).get("and_more_you_could_open")
      and len(shut_page(limit=5)["you_know_how_but_have_not_opened"]) == 5
      and len(shut_page(limit=40)["you_know_how_but_have_not_opened"]) == 40,
      (len(seen), shut_total))

# --- (2) path prints the nearest blocker itself
blocked = sim(capital=1_000_000.0)
route = S._agent_dispatch(blocked, NODES, {"cmd": "path", "id": "ag2_botanic_garden"})
blockers = route.get("nearest_blockers")
check("nothing on this route is startable, and path carries the nearest blocker with the same text start_reason (and so stuck) gives",
      route["startable_today_count"] == 0 and isinstance(blockers, list) and blockers
      and blockers[0]["id"] == "ag2_botanic_garden" and "craftsmen" in blockers[0]["why"]
      and blockers[0]["why"] == blocked.start_reason("ag2_botanic_garden")[1], blockers)

# --- (3) available rows carry foreman, net and payback; the sorts order them
rows_sim = sim(capital=1_000_000.0)
_foreman_node = min((node_id for node_id in sorted(NODES)
                     if rows_sim.is_venture(node_id) and rows_sim.venture_foreman(node_id)[0] is not None
                     and rows_sim.venture_real_earnings(node_id, fully_ramped=True) > 0),
                    key=lambda node_id: len(S.closure(NODES, node_id)))
_earner = min((node_id for node_id in sorted(NODES)
               if rows_sim.is_venture(node_id) and rows_sim.venture_foreman(node_id)[0] is None
               and rows_sim.concern_takings(node_id, 1.0) > 0
               and rows_sim.venture_real_earnings(node_id, fully_ramped=True) > rows_sim.venture_real_upkeep(node_id)),
              key=lambda node_id: len(S.closure(NODES, node_id)))
rows_sim.done.update((S.closure(NODES, _foreman_node) - {_foreman_node}) | (S.closure(NODES, _earner) - {_earner}))
rows_sim.artisans = rows_sim.scholars = 20.0
rows_sim._done_changed()
listing = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "all": True, "limit": 5000})
by_id = {row["id"]: row for row in listing["available"]}
foreman_row, earner_row = by_id.get(_foreman_node), by_id.get(_earner)
check("the rows of `available` carry the fields the economics module computes: the specialist foreman as `why` and "
      "`open` name it, the net and the payback",
      foreman_row is not None and earner_row is not None
      and foreman_row["specialist_foreman"] == available_economics.specialist_foreman(rows_sim, _foreman_node)
      and earner_row["net_per_year"] == available_economics.row_fields(rows_sim, _earner, NODES[_earner])["net_per_year"]
      and earner_row.get("payback_years") == available_economics.payback_years(rows_sim, _earner, earner_row["cost"]),
      (foreman_row, earner_row))
by_net = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "net", "reverse": True, "limit": 30})
nets = [row["net_per_year"] for row in by_net["available"]]
by_payback = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "payback", "limit": 400})
paybacks = [row.get("payback_years") for row in by_payback["available"]]
finite = [value for value in paybacks if value is not None]
check("sort:net reverse puts the biggest net first; sort:payback lists the quickest first and never-paying last",
      nets == sorted(nets, reverse=True) and nets[0] > 0 and finite == sorted(finite) and paybacks[:len(finite)] == finite and finite,
      (nets[:5], paybacks[:5]))
bad = S._agent_dispatch(rows_sim, NODES, {"cmd": "available", "sort": "nonsense"})
check("an unknown sort is refused, naming the net and payback sorts", "net" in bad["error"] and "payback" in bad["error"], bad)
