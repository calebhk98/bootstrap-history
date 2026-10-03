"""Complaint 110: the economy makes interest groups. People whose income the founder's doing takes
organise in proportion to what they lost, press the state, and the state answers by its capacity and
its purse. Every effect names its group and its cause."""
from .harness import *

from sim.agents.api import SimWorld, supply
from sim.engine.goods_market_api import FOUNDER
from sim.agents.group import state_response
from sim.engine.saveload import load_state, save_state


def grievance_game(civ="rome_100ad", share=0.6, capacity=None, purse=1.0e12):
    """A game whose founder has sold `share` of the opening iron market this year."""
    game = sim(civ=civ, agent_economy=False)   # the displaced-sales market is the engine's own
    if capacity is not None:
        game.state_capacity = capacity
    game._open_market_book()
    game.goods_market.note_sale(FOUNDER, "iron", game._market_entry("iron")["reference_tonnes"] * share)
    game.state_treasury().money = purse
    return game


def a_year(game):
    game.advance_actors(game.state.scenario.year)


def the_group(game):
    rows = game.interest_groups()
    return rows[0] if rows else None


# ---- nobody is organised until someone has lost something ------------------------------------
quiet = sim()
a_year(quiet)
check("a founder who has hurt nobody has no interest groups", quiet.interest_groups() == [], quiet.interest_groups())
check("the groups screen says so",
      quiet.interest_groups_report()["groups"] == [] and "note" in quiet.interest_groups_report())

# ---- selling into a market organises the producers it displaces ------------------------------
big = grievance_game()
a_year(big)
group = the_group(big)
check("selling into a market organises the producers it displaces",
      group is not None and group["name"] == "producers of iron" and group["kind"] == "displaced_producers", group)
check("the group's size and loss come from the market's displaced sales",
      group["people"] > 0 and group["income_lost_per_year"] > 0 and 0.0 < group["grievance_share"] < 1.0, group)
check("the group names its cause",
      "your sales of iron" in group["cause"], group["cause"])
petition = [text for _year, text in big.state.household.log if "INTEREST GROUP" in text]
check("the log names the group and its cause when it petitions",
      petition and "producers of iron" in petition[0] and "your sales of iron" in petition[0], petition)
check("a petition puts blame on the founder", big.state.household.scandal > 0.0, big.state.household.scandal)

small = grievance_game(share=0.003)
a_year(small)
check("a loss too small to organise over forms no group", small.interest_groups() == [], small.interest_groups())
middling = grievance_game(share=0.2)
a_year(middling)
check("a bigger loss organises more people with a stronger pull",
      the_group(middling) is not None and the_group(middling)["people"] < group["people"]
      and the_group(middling)["pull_on_the_state"] < group["pull_on_the_state"],
      (the_group(middling), group))

# ---- the state's answer is decided by its capacity and its purse -----------------------------
weak = state_response(0.8, 0.2, False, "displaced_producers", 1.0e6)
strong = state_response(0.8, 0.9, False, "displaced_producers", 1.0e6)
check("a state with more capacity makes more good and lets more blame fall",
      strong["claim"] > weak["claim"] and strong["blame"] > weak["blame"], (weak, strong))
check("a state that can act forbids the technique when the pull is strong enough", strong["ban"] and not weak["ban"],
      (weak, strong))
check("a state in deficit compensates instead of forbidding",
      not state_response(0.8, 0.9, True, "displaced_producers", 1.0e6)["ban"]
      and state_response(0.8, 0.9, True, "displaced_producers", 1.0e6)["claim"] > 0.0)
check("employers are compensated, never given a prohibition",
      not state_response(0.9, 0.9, False, "squeezed_employers", 1.0e6)["ban"])
weak_game = grievance_game(capacity=0.2)
a_year(weak_game)
check("the same loss earns a weak state's group a smaller claim than a strong state's",
      the_group(weak_game)["state_undertakes_to_make_good"] < group["state_undertakes_to_make_good"],
      (the_group(weak_game), group))

# ---- the state's budget carries what it undertakes -------------------------------------------
flush = grievance_game()
a_year(flush)
name = "concession: group:displaced_producers:iron"
a_year(flush)
record = flush.state_treasury().record
check("the state's budget carries a line for the group's claim", record.need.get(name, 0.0) > 0.0, record.need)
check("a purse that covers it pays the group and the founder is not levied for it",
      record.unfunded.get(name, 1.0) == 0.0 and flush.group_levy_reasons() == [], (record.unfunded, flush.group_levy_reasons()))
check("what the state paid arrives in the group's purse",
      flush.actors.get("group:displaced_producers:iron").money > 0.0)

broke = sim()
broke.civ["standing_army"] = 1.0e8
broke._open_market_book()
broke.goods_market.note_sale(FOUNDER, "iron", broke._market_entry("iron")["reference_tonnes"] * 0.6)
broke.state_treasury().money = 0.0
a_year(broke)
a_year(broke)
record = broke.state_treasury().record
check("a state that cannot pay leaves the group's claim unfunded",
      record.unfunded.get(name, 0.0) > 0.0, (record.need, record.unfunded))
rates_with = broke.state_levy_rates()
calm = sim()
calm.civ["standing_army"] = 1.0e8
calm.state_treasury().money = 0.0
a_year(calm)
a_year(calm)
check("the unpaid claim raises the rate the state takes from taxpayers it sees",
      rates_with[0] > calm.state_levy_rates()[0], (rates_with, calm.state_levy_rates()))
reasons = broke.group_levy_reasons()
check("the levy names the group it is for and the cause",
      reasons and "producers of iron" in reasons[0] and "your sales of iron" in reasons[0], reasons)
broke.employees["artisan"] = 2000.0
broke.labour._resync_pools()
broke.capital = 60000000.0
broke.eminence = 25.0
broke.update_protection()
check("the requisition screen lists the group among the reasons for the levy",
      any("producers of iron" in why for why in broke.requisition_report()[1]), broke.requisition_report())

def clean_start_ok(node_id):
    return sim().start_reason(node_id)[0]


# ---- a ban the state can afford stops the founder building what hurts the group --------------
banner = grievance_game()
a_year(banner)
a_year(banner)
group = the_group(banner)
check("a strong group with a state that can afford it demands a prohibition",
      group["demands"] and "iron" in group["demands"][0], group)
making = [node_id for node_id in sorted(banner.nodes) if "iron" in
          {banner._material_tag(material)[0] for material in supply.materials_made_by(node_id)}
          and banner.state_interest(banner.nodes[node_id]) <= 0.0]
check("there are techniques that make the commodity", bool(making), making[:3])
banner.state.household.protection = 0.0
from sim.engine.interest_groups import check_group_prohibition
verdict = check_group_prohibition(banner, making[0], banner.nodes[making[0]], False, None, True)
check("the start gate refuses a forbidden technique and says whose petition and why",
      verdict and verdict[0] is False and "producers of iron" in verdict[1] and "forbidden" in verdict[1], verdict)
check("the prohibition is one of the start gate's own checks", check_group_prohibition in banner._START_REASON_CHECKS)
reachable = [node_id for node_id in making if clean_start_ok(node_id)]
if reachable:
    ok, why = banner.start_reason(reachable[0])
    check("a forbidden technique the founder could otherwise start is refused by start_reason, naming the group",
          not ok and "producers of iron" in (why or ""), (reachable[0], why))
clean = sim()
check("without a group nothing is forbidden", clean.group_prohibition_of(making[0]) is None)
banner.state.household.protection = 0.9
check("protection above the state-opposition line lets the founder build regardless",
      check_group_prohibition(banner, making[0], banner.nodes[making[0]], False, None, True) is None)

# ---- a grievance that stops being renewed fades and the group disbands -----------------------
fading = grievance_game()
a_year(fading)
fading.state.scenario.year += 1
for _year in range(60):
    fading.state.scenario.year += 1
    a_year(fading)
    if the_group(fading) is None:
        break
check("when the cause stops, the group's loss fades and it disbands", the_group(fading) is None, fading.interest_groups())
check("the log says the group is no longer organised",
      any("no longer organised" in text and "producers of iron" in text for _year, text in fading.state.household.log))
fading.goods_market.note_sale(FOUNDER, "iron", fading._market_entry("iron")["reference_tonnes"] * 0.6)
a_year(fading)
check("the same group organises again when the cause returns", the_group(fading) is not None)

# ---- the rule is not about any civilisation --------------------------------------------------
for civ_id in ("england_1300", "han_china_100ad", "norse_900ad"):
    other = grievance_game(civ=civ_id)
    a_year(other)
    check("%s: the same sale organises the same kind of group" % civ_id,
          the_group(other) is not None and the_group(other)["kind"] == "displaced_producers", other.interest_groups())

# ---- employers squeezed by the founder's hiring ----------------------------------------------
squeezed = sim()
squeezed.labour.market.press("artisan", squeezed.labour.market_supply("artisan") * 3.0)
squeezed.state_treasury().money = 1.0e12
world = SimWorld(squeezed)
sectors = {sector.subject: sector for sector in world.squeezed_employers()}
check("hiring that raises a trade's price squeezes the employers of that trade",
      "artisan" in sectors and sectors["artisan"].lost_income > 0.0 and "raised the going price" in sectors["artisan"].cause,
      sectors)
check("a trade nobody pressed squeezes no one", "labourer" not in sectors)

# ---- groups persist through a save ------------------------------------------------------------
saved = grievance_game()
a_year(saved)
a_year(saved)
before = saved.interest_groups()
path = _rel("interest_groups_roundtrip.json")
save_state(saved, path)
loaded = sim()
load_state(loaded, path)
check("organised groups survive a save and load", loaded.interest_groups() == before, (before, loaded.interest_groups()))

# ---- the screen -------------------------------------------------------------------------------
replies, _out, _code = proto([{"cmd": "groups"}])
check("the groups command exists and answers", replies and replies[-1].get("ok"), replies[-1:] if replies else None)
report = banner.interest_groups_report()
check("the report says what the state is doing about the group",
      report["groups"] and "state_in_deficit" in report and "note" in report, report)
