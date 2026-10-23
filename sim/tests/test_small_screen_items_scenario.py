"""Scenarios for the small screen items in a whole game: the replies carry the timing of the hedges (Complaint 92), the
funding parts that add up to what the engine says you could fund (93), the living stock a node rests on beside the
knowledge (86), and the opening state reads situation, goal, risks, then the detail (97). The rules and the screens are
in test_small_screen_items; the funding arithmetic is in test_affordability_warning."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_screen_state import render_state

# --- 92: the risk reply carries the timing the rule works out for each hedge with a calendar floor
england = unopened_sim(civ="england_1300", capital=1e6)
risk = S._agent_dispatch(england, NODES, {"cmd": "risk"})
timed = []
for hazard in risk["knowledge_risk"]["known_hazards_ahead"]:
    for advice in (hazard.get("what_you_can_do") or {}).values():
        for step in advice.get("you_could_begin_now_toward_it") or []:
            if step.get("years_even_if_you_start_today") is not None:
                timed.append((hazard, step))
check("every hedge with a calendar floor carries its timing against the window it answers",
      bool(timed) and all((step.get("timing") or {}).get("earliest_finish_year") is not None
                          and step["timing"]["window_opens_year"] == hazard["years"][0] for hazard, step in timed),
      [step.get("timing") for _hazard, step in timed][:2])

# --- 93: the money reply carries the four funding figures, and the capacity shown is the engine's
funded = unopened_sim(civ="rome_100ad", capital=1e5)
money = S._agent_dispatch(funded, NODES, {"cmd": "money"})
funding = money.get("funding") or {}
check("money carries the four funding figures apart, and the capacity shown is the engine's",
      {"cash_on_hand", "credit_available_now", "surplus_allowance_over_years", "sustainable_annual_surplus",
       "already_committed"} <= set(funding)
      and abs(money["you_could_actually_fund_up_to"] - funded.funding_capacity()) < 0.2
      and abs(funding.get("already_committed", -1) - funded.committed_spend()) < 0.2, funding)

# --- 86: why lists the living stock a node rests on, held beside needed, and a herd not held is a supply blocker
mexica = unopened_sim(civ="mexica_1500", capital=1e6)
treadmill = S._agent_dispatch(mexica, NODES, {"cmd": "why", "id": "pwr_animal_treadmill"})
gate = (treadmill.get("living_stock") or [{}])[0]
check("why lists the living stock a node rests on, held beside needed, brought by its node, as a supply blocker",
      gate.get("material") == "draught_animal_kg" and gate.get("held") == 0.0 and gate.get("needed") == 1000
      and gate.get("brought_by") == "exp_import_draught_animals"
      and any(blocker["kind"] == "supply" and "draught animal" in blocker["text"] for blocker in treadmill["blockers"])
      and "knowledge" not in {blocker["kind"] for blocker in treadmill["blockers"] if "draught animal" in blocker["text"]},
      (treadmill.get("living_stock"), treadmill["blockers"]))
mexica.grant_stock("draught_animal_kg", 1000)
herd_held = S._agent_dispatch(mexica, NODES, {"cmd": "why", "id": "pwr_animal_treadmill"})
check("once the animals are held the same line shows them held and no supply blocker remains",
      (herd_held["living_stock"][0]["held"] or 0) >= 1000
      and not any(blocker["kind"] == "supply" for blocker in herd_held["blockers"]),
      (herd_held["living_stock"], herd_held["blockers"]))

# --- 97: the opening state reads situation, goal, risks, then the detail
opening = unopened_sim(civ="rome_100ad")
opening_text = render_state(S._agent_dispatch(opening, NODES, {"cmd": "state", "full": True})).splitlines()


def first_line_starting(prefix):
    return next((position for position, line in enumerate(opening_text) if line.startswith(prefix)), None)


order = [first_line_starting(prefix) for prefix in ("Money:", "You:", "Goal:", "AHEAD:", "EMPLOY:", "STANDING:")]
# presentation: the order of the state screen's blocks
check("the opening state shows money, hours, goal, looming risks, then staff and standing",
      None not in order and order == sorted(order), order)
