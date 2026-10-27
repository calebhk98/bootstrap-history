"""`EconomyPort.open_agent` opens the agent economy and, only when the game's money was still counted at the opening's figure,
reprices it to the economy's wage (`opening_money.reprice_opening_money`) from the figure that stood before. Called on a stand-in
port; the repricing itself is in test_one_money_per_labour_hour."""
import types
import unittest
from unittest import mock

from sim.engine import opening_money
from sim.markets.port import EconomyPort

QUICK_TOPIC = True
UNDER_TEST = {"open_agent"}

OPENING_FIGURE = 0.7


class Agent:
    def __init__(self, opened):
        self._opened, self.during_opening = opened, []

    def opened(self):
        return self._opened

    def economy(self):
        self.during_opening.append(self.port._opening)
        self._opened = True


def port_over(agent, priced):
    sim = types.SimpleNamespace(
        view=lambda name: lambda: priced,
        labour=types.SimpleNamespace(money_per_labour_hour=lambda: OPENING_FIGURE))
    port = types.SimpleNamespace(agent=agent, _sim=sim, _opening=False)
    if agent is not None:
        agent.port = port
    return port


class OpenAgentTests(unittest.TestCase):
    def open_it(self, agent, priced):
        port = port_over(agent, priced)
        with mock.patch.object(opening_money, "reprice_opening_money") as reprice:
            EconomyPort.open_agent(port)
        return port, reprice

    def test_opening_the_economy_reprices_the_money_counted_at_the_opening_figure(self):
        agent = Agent(opened=False)
        port, reprice = self.open_it(agent, priced=False)
        self.assertTrue(agent.opened())
        reprice.assert_called_once_with(port._sim, OPENING_FIGURE)

    def test_the_economy_opens_with_the_opening_flag_set_and_clear_after(self):
        agent = Agent(opened=False)
        port, _reprice = self.open_it(agent, priced=False)
        self.assertEqual(agent.during_opening, [True])
        self.assertFalse(port._opening)

    def test_money_already_counted_at_the_economys_wage_is_not_repriced_again(self):
        agent = Agent(opened=True)
        _port, reprice = self.open_it(agent, priced=True)
        reprice.assert_not_called()
        self.assertEqual(agent.during_opening, [])

    def test_an_economy_priced_but_not_yet_opened_opens_without_repricing(self):
        agent = Agent(opened=False)
        _port, reprice = self.open_it(agent, priced=True)
        self.assertTrue(agent.opened())
        reprice.assert_not_called()

    def test_a_game_with_no_agent_economy_does_nothing(self):
        _port, reprice = self.open_it(None, priced=False)
        reprice.assert_not_called()


if __name__ == "__main__":
    unittest.main()
