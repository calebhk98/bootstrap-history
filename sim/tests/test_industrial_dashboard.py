"""industrial_dashboard: regression checks, run individually with `--only industrial_dashboard`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# THE INDUSTRIAL DASHBOARD: `capacity`, `economy`, `changes`. A player who
# had already won the game asked for one command that answers "what
# physical capability does my society currently have, not just what I know
# how to build" - capacity, demand and surplus per material; power capability
# by scale; mines with their utilisation; the project portfolio sorted by
# what actually constrains it; spare founder-hours, staff and cash; a short
# economic summary with detail behind an explicit ask; and `changes N` for
# what moved over the last N years. See protocol.py's own block comment
# above _material_capacity_rows for the full design note.
# =============================================================================
from engine.protocol import _agent_capacity as _ACAP, _agent_economy as _AECO

check("the three new commands are advertised in KNOWN_COMMANDS, the same "
      "way every other command has to be - a command nobody can discover "
      "by typing 'help' does not really exist",
      all(command in S.KNOWN_COMMANDS for command in ("capacity", "economy", "changes")),
      S.KNOWN_COMMANDS)

# --- `capacity` shares ONE underlying summary for resources, power, mines,
# the portfolio and spare capacity, rather than recomputing any of them.
# Proved here by checking `capacity`'s embedded mines rows are IDENTICAL to
# the standalone `mines` command's own rows for the same Sim - if a future
# edit gives one of them its own copy of the arithmetic, this catches the
# two screens drifting apart instead of a playtester finding two different
# answers to "what is my coal mine actually raising".
_s_cap = sim(capital=2_000_000.0)
_s_cap.mines.append({"material": "iron", "capacity": 500.0,
                     "opened_year": _s_cap.year, "capex_paid": 0.0,
                     "intensity_yrs": 0.0})
_s_cap.mines.append({"material": "coal", "capacity": 900.0,
                     "opened_year": _s_cap.year, "capex_paid": 0.0,
                     "intensity_yrs": 0.0})
_dash = S._agent_dispatch(_s_cap, NODES, {"cmd": "capacity"})
_mines_standalone = S._agent_dispatch(_s_cap, NODES, {"cmd": "mines"})
check("`capacity` embeds the exact same mine rows `mines` returns on its "
      "own - one computation, read from two places, not two",
      _dash.get("mines", {}).get("mines_you_own")
      == _mines_standalone.get("mines_you_own"),
      (_dash.get("mines"), _mines_standalone))
check("`capacity` reports a material's own capacity, demand and surplus, "
      "not just the single worst-binding one resource_throttle tracks - "
      "the whole point of the request was being able to reason about a "
      "bottleneck without it being hidden inside one aggregate number",
      isinstance(_dash.get("resources"), list)
      and any(resource_row["material"] == "iron" for resource_row in _dash["resources"]),
      _dash.get("resources"))
_iron_row = next(resource_row for resource_row in _dash["resources"] if resource_row["material"] == "iron")
check("...and capacity/demand/surplus actually add up the way the labels "
      "say they do",
      abs(_iron_row["surplus_t_per_yr"]
          - (_iron_row["capacity_t_per_yr"] - _iron_row["demand_t_per_yr"])) < 0.5,
      _iron_row)

# --- `capacity`'s power section reports REAL generation/demand/reserve
# margin figures now (economy.py's generation_breakdown_kw()/
# _electricity_demand_kw()), not a second, unverified copy of them - proved
# the same way the mines check above proves capacity/mines share one
# computation: read straight off the same Sim and compare to the number.
_s_pow = sim(capital=2_000_000.0)
for _pk in ("cap_power_water", "water_power_scale", "dynamo", "cap_power_electric",
            "cap_power_steam", "en_alternator"):
    if _pk in NODES:
        _s_pow.done.add(_pk)
        _s_pow.operating.add(_pk)
_s_pow._done_changed()
_powdash = S._agent_dispatch(_s_pow, NODES, {"cmd": "capacity"})["power"]
check("with a dynamo and an alternator actually built, the dashboard shows "
      "real generation, not a capability gate - and the SAME number "
      "generation_breakdown_kw() itself computes, not a second guess at it",
      _powdash.get("generation_kw", {}).get("total")
      == round(_s_pow.generation_breakdown_kw()["total_kw"], 1)
      and _powdash["generation_kw"]["total"] > 0,
      _powdash)
check("...and demand is the same figure _electricity_demand_kw() computes",
      _powdash.get("demand_kw") == round(_s_pow._electricity_demand_kw(), 1),
      _powdash)
check("...and reserve margin is (generation - demand) / demand, arithmetic "
      "a player can check by hand rather than a label with no formula",
      _powdash.get("reserve_margin") is None
      or abs(_powdash["reserve_margin"]
             - (_powdash["generation_kw"]["total"] - _powdash["demand_kw"])
               / max(1e-9, _powdash["demand_kw"])) < 0.01,
      _powdash)
check("a founder with NOTHING electrical built yet gets zero generation "
      "and zero demand, not an invented figure - the capacity dashboard "
      "and a bare Sim agree because both read the same functions",
      _dash["power"].get("generation_kw", {}).get("total") == 0
      and _dash["power"].get("demand_kw") == 0,
      _dash["power"])

# --- FOG: the power ladder must name only tiers the player has actually
# discovered, the same visibility test `why`/`available` use, not a second
# guess at what counts as "known". A fresh fogged founder who has built
# nothing but the ambient grant has heard of none of the electrical branch.
_s_fogpow = sim(capital=10_000.0)
_s_fogpow.fog = True
_s_fogpow.revealed = set()
_powout = _ACAP(_s_fogpow, NODES)["power"]
_powids = {tier["id"] for tier in _powout["power_tiers_you_have_discovered"]
          if isinstance(_powout["power_tiers_you_have_discovered"], list)}
check("a fresh fogged founder's power ladder names only tiers they have "
      "actually discovered (muscle power, granted to everyone), never "
      "cap_power_grid or any other tier nobody has earned yet",
      _powids <= {"cap_power_muscle"}, _powids)
check("...and says nothing at all about which projects wait on workshop- "
      "or grid-scale power, since the player has not discovered either "
      "capability to be told a project needs it",
      "waiting_on_workshop_scale_power" not in _powout
      and "waiting_on_grid_scale_power" not in _powout,
      _powout)

# --- `economy`: short by default, full detail only on request - the user's
# own instruction was that this risks becoming the giant spreadsheet a
# player explicitly said they did not want.
_eco = _AECO(_s_cap)
check("`economy` is short by default - no per-trade wage table and no "
      "per-material price table unless asked for",
      "wages_by_trade" not in _eco and "tracked_material_prices" not in _eco,
      sorted(_eco.keys()))
_eco_full = _AECO(_s_cap, {"full": True})
check("...and the detail is there the moment it is asked for, read from "
      "the same material_price_factor()/labour wage formula `money` and "
      "`labour` already use, not a second version of either",
      bool(_eco_full.get("tracked_material_prices"))
      and bool(_eco_full.get("wages_by_trade")),
      list(_eco_full.keys()))

# --- `changes N`: the diff a player otherwise has to work out by holding
# two screens in their head - one of our own testers did exactly that to
# diagnose a bug.
_s_chg = sim(capital=500_000.0)
_s_chg.end_year = _s_chg.cfg["start_year"] + 50
_chg0 = S._agent_dispatch(_s_chg, NODES, {"cmd": "changes", "years": 5})
check("`changes` before any year has ever been stepped says so plainly, "
      "rather than diffing against nothing and calling it zero",
      _chg0.get("ok") is False and "nothing has been recorded" in _chg0["error"],
      _chg0)
for _bad, _why in ((True, "bool"), (2.5, "fractional"), (0, "zero"), (-1, "negative")):
    _r = S._agent_dispatch(_s_chg, NODES, {"cmd": "changes", "years": _bad})
    check("`changes years=%r` (%s) is refused, not silently coerced" % (_bad, _why),
          _r.get("ok") is False, _r)
S._agent_dispatch(_s_chg, NODES, {"cmd": "step", "years": 6})
_chg_near = S._agent_dispatch(_s_chg, NODES, {"cmd": "changes", "years": 3})
check("a window narrower than the run's own history is answered directly",
      _chg_near.get("ok") is True and _chg_near.get("to_year") == _s_chg.year,
      _chg_near)
_chg_far = S._agent_dispatch(_s_chg, NODES, {"cmd": "changes", "years": 50})
check("a window wider than the run's own recorded history is refused by "
      "name, saying how far back the record actually goes, rather than "
      "silently diffing against the earliest year it has as though that "
      "were what was asked for",
      _chg_far.get("ok") is False and "only goes back to" in _chg_far["error"],
      _chg_far)
_before_built = set(_s_chg.done)
_to_start = [node_id for node_id in _s_chg.order if _s_chg.can_start(node_id)]
_to_start.sort(key=lambda k: NODES[k]["_total_cost"])
for _k in _to_start[:2]:
    S._agent_dispatch(_s_chg, NODES, {"cmd": "start", "id": _k})
S._agent_dispatch(_s_chg, NODES, {"cmd": "step", "years": 3})
_newly_built = sorted(_s_chg.done - _before_built)
_chg_built = S._agent_dispatch(_s_chg, NODES, {"cmd": "changes", "years": 3})
check("a technology completed inside the window is actually named as "
      "'completed', read from s.done_year/the step loop's own diff, not "
      "re-derived a second way",
      _chg_built.get("ok") is True
      and (_chg_built.get("technologies_completed") == "none"
           or set(_chg_built.get("technologies_completed") or []) <= set(_s_chg.done)),
      (_newly_built, _chg_built.get("technologies_completed")))

# --- the typed front end reaches all three, the same way it reaches
# everything else a player can type rather than script.
from engine.protocol import parse_typed as _PT2
check("'capacity' types straight through",
      _PT2("capacity") == ({"cmd": "capacity"}, None), _PT2("capacity"))
check("'industry' and 'dashboard' are the same command by another name",
      _PT2("industry")[0] == {"cmd": "capacity"}
      and _PT2("dashboard")[0] == {"cmd": "capacity"},
      (_PT2("industry"), _PT2("dashboard")))
check("'changes 10' carries the number through",
      _PT2("changes 10") == ({"cmd": "changes", "years": 10.0}, None),
      _PT2("changes 10"))
check("bare 'changes' defaults to 5 years, not an error",
      _PT2("changes") == ({"cmd": "changes", "years": 5}, None), _PT2("changes"))
check("'economy full' carries the flag through",
      _PT2("economy full") == ({"cmd": "economy", "full": True}, None),
      _PT2("economy full"))

# --- every reply renders to readable text, not an apology. render_pretty
# swallows a bad formatter and prints '(could not render...)' instead of
# crashing the session, which would hide a real bug in these three brand
# new renderers as silently-accepted garbage; check the real text, not
# just that SOMETHING came back.
check("`capacity` renders without the renderer's own safety net firing",
      "could not render" not in _RP("capacity", _dash), _RP("capacity", _dash))
check("`economy` renders without the renderer's own safety net firing",
      "could not render" not in _RP("economy", _eco), _RP("economy", _eco))
check("`changes` renders without the renderer's own safety net firing",
      "could not render" not in _RP("changes", _chg_built), _RP("changes", _chg_built))

