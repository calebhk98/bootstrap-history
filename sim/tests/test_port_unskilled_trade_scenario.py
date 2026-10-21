"""Scenario (Complaint 446): the shipped data's economy-port setup carries the unskilled trade the registry names.
The rules are in test_port_unskilled_trade."""
from .harness import *  # noqa: F401,F403

from sim.engine import economy_port_setup

game = sim()
setup = economy_port_setup.build_setup(game)
check("the shipped data's setup carries the trade the registry names",
      setup.unskilled_trade == economy_port_setup.opening_values(game)["unskilled_trade"]
      and setup.unskilled_trade in setup.opening_wages, setup.unskilled_trade)
