"""Regression coverage for Complaint 192: labour needs shown as uncertain
estimates while something is unknown (option `fuzzy_estimates`, off by default).

Only the display is fuzzy; the start check, hiring, supervision and bills use
the real numbers.
"""
from .harness import *
from sim.engine.proto.render import render_pretty
from sim.engine.proto import saveload as _saveload

NODE = "fin_lottery"          # a going concern with staff, a foreman-free crew and two hired trades


def fuzzy_sim(capital=1_000_000):
    fuzzy = sim(capital=capital)
    fuzzy.fuzzy_estimates = True
    return fuzzy


def why_of(sim_state, node_id=NODE):
    return S._agent_dispatch(sim_state, NODES, {"cmd": "why", "id": node_id})


def figures(out):
    """Every fuzzy-able labour, money and time figure of a `why` reply."""
    flat = {
        "founder_hours": out["founder_hours"],
        "calendar_floor_years": out["calendar_floor_years"],
        "cost_total": out["cost"]["total"],
        "scholars": out["staff_needed"]["scholars"],
        "artisans": out["staff_needed"]["artisans"],
        "keep_scholars": out["staff_to_keep_it_open"]["scholars"],
        "keep_artisans": out["staff_to_keep_it_open"]["artisans"],
    }
    for trade, hours in out["hired_labour"].items():
        flat["hired:" + trade] = hours
    return flat


REAL = {
    "founder_hours": NODES[NODE]["ph"],
    "scholars": NODES[NODE]["sch"],
    "artisans": NODES[NODE]["art"],
}
real_lab = dict(NODES[NODE]["lab"])

# ---- option off: exactly the real figures, and no estimate markers -----------
plain = sim(capital=1_000_000)
out_off = why_of(plain)
check("option off: staff needed is the real figure",
      out_off["staff_needed"] == {"scholars": REAL["scholars"], "artisans": REAL["artisans"]},
      out_off["staff_needed"])
check("option off: hired labour is exactly the node's trades and hours",
      out_off["hired_labour"] == real_lab, out_off["hired_labour"])
check("option off: no estimate marker and no '(est.)' text",
      not out_off.get("figures_are_estimates") and "(est.)" not in render_pretty("why", out_off))

# ---- option on: fuzzy, stable, in range, labelled -----------------------------
fuzzy = fuzzy_sim()
first = why_of(fuzzy)
second = why_of(fuzzy)
check("fuzzy: repeated why shows identical figures (drawn once, never re-rolled)",
      figures(first) == figures(second), (figures(first), figures(second)))
check("fuzzy: figures are marked as estimates in the JSON",
      bool(first.get("figures_are_estimates")), sorted(first))
check("fuzzy: the rendered screen labels estimates",
      "(est.)" in render_pretty("why", first), render_pretty("why", first)[:2000])

shown = figures(first)
differs = [key for key, value in (
    ("founder_hours", REAL["founder_hours"]), ("scholars", REAL["scholars"]),
    ("artisans", REAL["artisans"])) if shown[key] != value]
check("fuzzy: at least one real figure is displayed inexactly", bool(differs), shown)
in_range = all(0 <= shown[key] <= 2 * REAL[key] + 1e-9 for key in REAL)
check("fuzzy: each shown value lies in [0, 2 x real]", in_range, shown)
for trade, hours in real_lab.items():
    check("fuzzy: hired hours for %s lie in [0, 2 x real]" % trade,
          0 <= shown["hired:" + trade] <= 2 * hours + 1e-9, shown)

# Different actors see different draws for the same node.
first_actor_total = sum(shown[key] for key in REAL)
other = fuzzy_sim()
other.viewer_actor_id = "another_player"
check("fuzzy: another actor draws its own estimates",
      figures(why_of(other)) != shown, figures(why_of(other)))

# ---- decoys: trades the node does not use, stable, gone after start -----------
decoys = sorted(set(first["hired_labour"]) - set(real_lab))
check("fuzzy: one to three decoy trades are listed before starting",
      1 <= len(decoys) <= 3, first["hired_labour"])
check("fuzzy: the real trades are all still listed",
      set(real_lab) <= set(first["hired_labour"]), first["hired_labour"])
check("fuzzy: decoys are the same on every look",
      sorted(set(second["hired_labour"]) - set(real_lab)) == decoys)

# ---- save / load round trip ---------------------------------------------------
import tempfile as _tempfile
_path = os.path.join(_tempfile.mkdtemp(), "fuzzy192.json")
_saveload.save_state(fuzzy, _path)
reloaded = sim(capital=1_000_000)
_saveload.load_state(reloaded, _path)
check("fuzzy: the option survives save and load", bool(getattr(reloaded, "fuzzy_estimates", False)))
check("fuzzy: the same figures are shown after save and load",
      figures(why_of(reloaded)) == shown, (figures(why_of(reloaded)), shown))

# ---- start: spread halves, decoys drop out, start uses the real values --------
started = S._agent_dispatch(fuzzy, NODES, {"cmd": "start", "id": NODE})
check("fuzzy: start succeeds on the real check", started.get("ok") is True, started)
after = why_of(fuzzy)
check("fuzzy: decoys drop out at start",
      set(after["hired_labour"]) == set(real_lab), after["hired_labour"])
sample = "founder_hours"
deviation_before = shown[sample] / REAL[sample] - 1
deviation_after = figures(after)[sample] / REAL[sample] - 1
check("fuzzy: the founder-hours spread halves at start",
      abs(deviation_before) > 0.02
      and abs(deviation_after - deviation_before / 2) < 0.02,
      (deviation_before, deviation_after))
big_trade = max(real_lab, key=real_lab.get)
hired_before = shown["hired:" + big_trade] / real_lab[big_trade] - 1
hired_after = figures(after)["hired:" + big_trade] / real_lab[big_trade] - 1
check("fuzzy: the hired-hours spread halves at start",
      abs(hired_after - hired_before / 2) < 0.02, (hired_before, hired_after))
check("fuzzy: start's own reply shows the same estimate as why, not the exact hours",
      started["founder_hours_needed"] == figures(after)["founder_hours"]
      and started["founder_hours_needed"] != REAL["founder_hours"], started)

# ---- narrowing with progress; exact at completion -----------------------------
active = fuzzy.active[NODE]
active["ph_left"] = NODES[NODE]["ph"] * 0.5          # half the founder hours spent
halfway = figures(why_of(fuzzy))[sample] / REAL[sample] - 1
check("fuzzy: the spread narrows in proportion to work done",
      abs(halfway - deviation_after / 2) < 0.02, (deviation_after, halfway))
active["ph_left"] = NODES[NODE]["ph"] * 0.1
nearly = figures(why_of(fuzzy))[sample] / REAL[sample] - 1
check("fuzzy: the spread keeps narrowing",
      abs(nearly) < abs(halfway) + 1e-9, (halfway, nearly))
del fuzzy.active[NODE]
fuzzy.done.add(NODE)
fuzzy._done_changed()
complete = why_of(fuzzy)
check("fuzzy: completion shows the exact figures",
      complete["staff_needed"] == {"scholars": REAL["scholars"], "artisans": REAL["artisans"]}
      and complete["hired_labour"] == real_lab
      and complete["founder_hours"] == REAL["founder_hours"], complete["staff_needed"])

# ---- other screens: available rows and the compact variant --------------------
fuzzy2 = fuzzy_sim()
rows = S._agent_dispatch(fuzzy2, NODES, {"cmd": "available", "limit": 200})["available"]
row = next((r for r in rows if r["id"] == NODE), None)
check("fuzzy: available lists the node", row is not None)
if row is not None:
    check("fuzzy: available row hours are an estimate within [0, 2 x real]",
          0 <= row["founder_hours"] <= 2 * REAL["founder_hours"] + 1e-9, row)
    check("fuzzy: available row hours match what why shows",
          row["founder_hours"] == why_of(fuzzy2)["founder_hours"], row)

# ---- the real need is what start/refusal states ---------------------------------
refused_sim = fuzzy_sim()
refused = S._agent_dispatch(refused_sim, NODES, {"cmd": "start", "id": "ag2_botanic_garden"})
real_art = NODES["ag2_botanic_garden"]["art"]
check("fuzzy: a refusal at start states the real need",
      refused.get("ok") is False and ("needs %d trained craftsmen" % real_art) in refused.get("error", ""),
      refused)
refused_why = why_of(refused_sim, "ag2_botanic_garden")
check("fuzzy: why does not print the exact refusal need",
      ("needs %d trained craftsmen" % real_art) not in json.dumps(refused_why), refused_why.get("start_blocked_reason"))
compact = S._agent_dispatch(refused_sim, NODES,
                            {"cmd": "why", "id": "ag2_botanic_garden", "compact": True})
check("fuzzy: the compact why does not print the exact refusal need",
      ("needs %d trained craftsmen" % real_art) not in json.dumps(compact), compact)
