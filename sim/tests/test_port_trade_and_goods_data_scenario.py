"""Scenario (Complaints 443, 444): the economy port hands the economy each trade's fatality risk and each durable good's
service life, built from the shipped data. The rules are in test_port_trade_and_goods_data."""
import json
import os

from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "world")
trades_file = json.load(open(os.path.join(DATA, "trades.json")))["trades"]
lives = json.load(open(os.path.join(DATA, "service_lives.json")))["years"]

game = unopened_sim()
setup = economy_port_setup.build_setup(game)
check("the port passes each trade's risk into the economy",
      all(setup.trades[name].fatality_risk_per_year == trades_file[name]["fatality_risk_per_year"] for name in trades_file))
durable = [good for good in lives if good in setup.specs]
check("some stated durable goods are in the economy's goods", len(durable) > 0, sorted(setup.specs)[:5])
check("the economy's good specs carry the stated service life",
      all(setup.specs[good].service_life_years == lives[good]["years"] for good in durable))
check("a good with no stated life is still used up within the year", setup.specs["wheat_kg"].service_life_years == 0.0)
