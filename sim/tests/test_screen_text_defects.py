"""Screen text that read wrongly or said too little: Complaints/195 (score change line), 204 (sack chance wording),
280 (option ids). Each rule is called on a built hazard, a stand-in game for the score, or the tree's data."""
from .harness import check, NODES, S

from sim.tests.score_game import ScoreGame
from sim.ui import cli
from sim.ui.proto.hazard_words import advice_header
from sim.ui.proto.render_screens_status import render_score
from sim.ui.proto.score import score_report
from sim.ui.proto.score_change import attach_change_since_last_score

QUICK_TOPIC = True

# --- 204: the sack chance line prints the figure with nothing built, not a dash
with_total = advice_header("sack_chance", {}, {"sack_chance_after_what_you_have_built": 0.4,
                                                "sack_chance_per_year": 0.9})
# presentation: the line names the chance with what the founder has built against what stands with nothing built
check("the sack chance line gives the after-defences chance and the chance with nothing built, in figures",
      "(- with nothing built)" not in with_total and "40%" in with_total and "90% with nothing built" in with_total,
      with_total)
bare = advice_header("sack_chance", {}, {"sack_chance": 0.9, "sack_chance_after_what_you_have_built": 0.9})
# presentation: the same wording when only the plain figure is held
check("with only the plain figure held, the line still prints it rather than a dash",
      "90% with nothing built" in bare and "(- with" not in bare, bare)

# --- 195: a second `score` says what moved since the first
game = ScoreGame(NODES)
first = attach_change_since_last_score(game, score_report(game, NODES))
check("the first score has no change line to show",
      all("since_last_score" not in component for component in first["components"].values()))
game.reputation = game.reputation + 20
second = attach_change_since_last_score(game, score_report(game, NODES))
standing_change = second["components"]["standing"].get("since_last_score")
check("a second score reports the standing change since the first",
      standing_change is not None and abs(standing_change["normalized_change"] - 0.2) < 1e-9, standing_change)
check("...and only the component that moved reports a movement",
      all(component.get("since_last_score", {}).get("normalized_change") == 0
          for name, component in second["components"].items() if name != "standing"))
# presentation: the score screen prints the change line
check("the score screen prints the change line", "since your last score" in render_score(second),
      render_score(second)[-600:])
third = attach_change_since_last_score(game, score_report(game, NODES))
check("an unchanged score reports no movement",
      (third["components"]["standing"].get("since_last_score") or {}).get("normalized_change") == 0)

# --- 280: no option names the tail of a node id under another prefix without the validator saying so
check("the control option of load dispatch names the real telephone node",
      "telephone_exchange" not in {option for group in NODES["el2_load_dispatch_and_scheduling"].get("req_any") or []
                                   for option in group.get("options") or {}})
loose_warning = [warning for warning in cli._validate_nodes(*[
    NODES, set(cli.load()[4]), cli.load()[3]])[1] if "purchasable commodities" in warning]
# presentation: the validator's warning says how many options are the tail of one node id
check("validate says how many commodity-style options are the tail of one node id",
      loose_warning and "also the tail of one node id" in loose_warning[0], loose_warning)
