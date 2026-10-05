"""Complaint 446: the economy port takes the unskilled trade from the trade registry, not from a name in code."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup

registry = {"hand": {"family": "labour", "training_years": 0},
            "wright": {"family": "craft", "training_years": 4}}
check("the unskilled trade is the one the registry says anyone can take up",
      economy_port_setup.unskilled_trade(registry) == "hand")

opening = {"unskilled_trade": "hand", "wages": {"hand": 2.0, "wright": 6.0}, "prices": {"grain": 4.0},
           "carriage": {"cart": 1.0}}
check("a society whose unskilled trade has another name counts money in that trade's hour",
      economy_port_setup.coin_per_unit(opening) == 2.0)
counted = economy_port_setup.in_units(opening)
check("its wages are counted against that trade's wage",
      counted["wages"] == {"hand": 1.0, "wright": 3.0}, counted["wages"])

game = sim()
setup = economy_port_setup.build_setup(game)
check("the shipped data's setup carries the trade the registry names",
      setup.unskilled_trade == economy_port_setup.opening_values(game)["unskilled_trade"]
      and setup.unskilled_trade in setup.opening_wages, setup.unskilled_trade)
