"""SCENARIO (Complaint 230): the expected calendar years to succeed at a project are never below the earliest it can finish, and with no risk of
failure they are exactly that. `expected_calendar_years` and `earliest_completion_years` are called on a built (unopened) game's node;
the schedule arithmetic is test_readouts_timing_power_mines_road."""
from .harness import check, unopened_sim

NODE = "civ_sewer_separate"

game = unopened_sim(capital=1e12)
game.state.household.reputation = 80
earliest = game.earliest_completion_years(NODE)
risky = game.nodes[NODE]["risk"]
check("the node carries a risk of failure, so the test can tell a retry from none", risky > 0.0, risky)
check("the expectation counts the retries the dice force, so it is above the earliest finish", game.expected_calendar_years(NODE) > earliest,
      (game.expected_calendar_years(NODE), earliest))
game.nodes[NODE]["risk"] = 0.0
try:
    riskless = game.expected_calendar_years(NODE)
finally:
    game.nodes[NODE]["risk"] = risky    # the node table is shared with every other test
check("with no risk of failure the expectation is the earliest finish", abs(riskless - earliest) < 1e-9, (riskless, earliest))
