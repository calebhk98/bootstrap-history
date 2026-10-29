"""SMOKE: the Cash Shelter code mod in a whole game, allowed in a temporary mods directory. Coin lodged with a holder leaves the
founder's purse and reaches the holder's (a new actor of the cast), the mod's claim is kept in its saved memory, the exposure screen
reads the engine's hazard figures through the views the mod declared, a confiscation counts the claim and takes from it once the
purse is empty, and a withdrawal brings the coin home. The mod reads the game only through its declared access."""
import unittest

from sim.assembly.api import UndeclaredRead
from sim.tests.shipped_mod_games import ModGames
from sim.ui.proto.dispatch import _agent_dispatch_inner

MOD = "bh_cashshelter_z6f2"
HOLDER = MOD + ":holder_strongroom"
LODGED = 500.0


def command(game, word, text=""):
    return _agent_dispatch_inner(game, {}, {"cmd": "%s:%s" % (MOD, word), "text": text})


class CashShelterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.games = ModGames([MOD])
        cls.game = cls.games.unopened()
        cls.before = cls.game.view("acting_balance")()
        cls.deposit = command(cls.game, "deposit", "strongroom %d" % LODGED)

    @classmethod
    def tearDownClass(cls):
        cls.games.close()

    def test_the_mod_declared_what_it_reads_and_sends_and_the_assembly_gave_it_exactly_that(self):
        access = self.game.assembly.mod_access[MOD]
        self.assertIn("state_reach", access.reads)
        with self.assertRaises(UndeclaredRead):
            access.view("population")

    def test_lodged_coin_leaves_the_purse_and_reaches_the_holders_purse(self):
        self.assertTrue(self.deposit["ok"], self.deposit)
        holder = self.game.view("cast")().get(HOLDER)
        self.assertEqual(holder.money, LODGED)
        self.assertAlmostEqual(self.game.view("acting_balance")(), self.before - LODGED - self.deposit["carriage"], delta=0.06)   # the carriage is reported to a tenth

    def test_the_claim_is_kept_in_the_mods_saved_memory(self):
        seat = self.game.view("acting_seat")()
        claims = self.game.state.interface["mod_state"][MOD]["claims"]
        self.assertEqual(claims["strongroom"][seat]["amount"], LODGED)

    def test_the_exposure_screen_reads_the_hazard_figures_and_lists_the_claim(self):
        reply = command(self.game, "exposure")
        self.assertTrue(reply["ok"], reply)
        self.assertEqual([row["hazard"] for row in reply["hazards"]], ["fire", "banditry", "sack", "plague", "debasement", "treasury confiscation"])
        self.assertEqual(reply["sheltered_payable_today"], LODGED)
        self.assertGreater(reply["hazards"][0]["takes_cash"], 0.0)

    def test_a_confiscation_counts_the_claim_and_takes_from_it(self):
        game = self.games.unopened()
        command(game, "deposit", "strongroom %d" % LODGED)
        (owed, seize), = game.assembly.points["wealth_claims"]()
        self.assertEqual(owed(), LODGED)
        treasury = game.view("state_treasury")()
        held = treasury.money
        self.assertEqual(seize(100.0, treasury), 100.0)
        self.assertEqual(treasury.money, held + 100.0)
        self.assertEqual(game.view("cast")().get(HOLDER).money, LODGED - 100.0)
        self.assertEqual(owed(), LODGED - 100.0)   # the holder was solvent, so the claim fell by what was taken

    def test_a_withdrawal_brings_the_remaining_coin_home(self):
        game = self.games.unopened()
        command(game, "deposit", "strongroom %d" % LODGED)
        reply = command(game, "withdraw", "strongroom all")
        self.assertTrue(reply["ok"], reply)
        self.assertEqual(reply["paid"], LODGED)
        self.assertEqual(game.view("cast")().get(HOLDER).money, 0.0)


if __name__ == "__main__":
    unittest.main()
