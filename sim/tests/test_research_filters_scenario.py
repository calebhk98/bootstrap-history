"""`available` state filters and fog search through a running game: the command's startable and blocked lists agree with
`can_start` and `start_reason` on built nodes, and a search under fog leaks no hidden id. The filters themselves are
test_research_filters (the old whole-tree `can_start` sweep of Complaint 557 is not repeated here)."""
from .harness import *  # noqa: F401,F403


def _ask(test_sim, **cmd):
    return S._agent_dispatch(test_sim, NODES, {"cmd": "available", **cmd})


def _rows(out):
    return out.get("rows") if "rows" in out else out.get("available")


plain = sim(capital=1_000_000.0)
startable_out = _ask(plain, state="startable", limit=5)
startable_ids = [row["id"] for row in _rows(startable_out)]
check("state:startable lists nodes the game itself says can start",
      startable_ids and all(plain.can_start(node_id) for node_id in startable_ids), startable_out.get("error"))

blocked_out = _ask(plain, state="blocked", limit=5)
blocked_rows = _rows(blocked_out)
check("state:blocked lists nodes the game says cannot start, each with the reason the game gives",
      blocked_rows and all(not plain.can_start(row["id"]) and row["why_not"] == plain.start_reason(row["id"])[1]
                           for row in blocked_rows) and blocked_out["state"] == "blocked", blocked_out.get("error"))

fogged = sim(capital=1_000_000.0)
fogged.fog = True
fog_startable = [node_id for node_id in fogged.order if fogged.can_start(node_id)]
fog_heard = [node_id for node_id in fogged.order if node_id not in fog_startable and node_id not in fogged.done][:60]
fogged.revealed = set(fog_heard) | set(fog_startable)
hidden = [node_id for node_id in NODES if node_id not in fogged.revealed and node_id not in fogged.done
          and not fogged.is_visible(node_id) and len(NODES[node_id]["name"]) > 12]
hidden_query = NODES[hidden[0]]["name"].lower()
out_hidden = _ask(fogged, find=hidden_query, state="blocked", all=True)
out_nonsense = _ask(fogged, find="zzqxv wwkjh", state="blocked", all=True)
text = json.dumps(out_hidden).lower()
check("a fogged search for a hidden node's name looks exactly like nonsense and names no hidden id",
      set(out_hidden) == set(out_nonsense) and out_hidden["count"] == 0 and hidden[0].lower() not in text,
      (sorted(out_hidden), sorted(out_nonsense)))
