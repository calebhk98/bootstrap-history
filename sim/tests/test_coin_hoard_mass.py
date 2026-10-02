"""Complaint 273: a treasury of coin has a mass from its coin metal, a guard-and-vault cost from that
mass, and it is shown on the money and state screens."""
from .harness import *  # noqa: F401,F403

rome, han = sim(civ="rome_100ad"), sim(civ="han_china_100ad")
for game in (rome, han):
    game.capital = 1.0e6
rome_hoard, han_hoard = rome.coin_hoard(), han.coin_hoard()
check("the hoard's mass is the coin held times the metal in one coin",
      abs(rome_hoard["tonnes"] - 1.0e6 * rome.civ["coin_standard"]["kg_per_unit"] / 1000.0) < 1e-9, rome_hoard)
check("the hoard names the civilisation's own coin metal",
      rome_hoard["metal"] == rome.civ["coin_standard"]["material"]
      and han_hoard["metal"] == han.civ["coin_standard"]["material"] and rome_hoard["metal"] != han_hoard["metal"],
      (rome_hoard["metal"], han_hoard["metal"]))
han.capital = -5.0
check("a purse in debt holds no coin", han.coin_hoard()["tonnes"] == 0.0, han.coin_hoard())
han.capital = 2.0e6
check("twice the money is twice the mass and twice the keeping cost",
      abs(han.coin_hoard()["tonnes"] - 2.0 * han_hoard["tonnes"]) < 1e-9
      and abs(han.coin_hoard()["keeping_cost_per_year"] - 2.0 * han_hoard["keeping_cost_per_year"]) < 1e-6,
      (han.coin_hoard(), han_hoard))
check("keeping it costs money a year, and the basis is stated",
      han_hoard["keeping_cost_per_year"] > 0.0 and han_hoard["basis"], han_hoard)
replies, _stdout, _code = proto([{"cmd": "money"}, {"cmd": "state"}], civ="han_china_100ad")
money_reply, state_reply = replies[-2], replies[-1]
opening = sim(civ="han_china_100ad").coin_hoard_report()
check("the money screen reports the hoard's mass",
      money_reply.get("coin_hoard", {}).get("tonnes") == opening["tonnes"], money_reply.get("coin_hoard"))
check("the state screen reports the hoard's mass",
      state_reply.get("coin_hoard", {}).get("tonnes") == opening["tonnes"], state_reply.get("coin_hoard"))
