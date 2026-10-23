"""Complaint 485: raising, ordering, recalling and disbanding an army (CampaignActorsMixin) on a stand-in game that holds
a force, three tiles and a record of armies. The rules it calls are in test_campaign_rules."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.campaign_actors import CampaignActorsMixin
from sim.world.army_record import Army

OWNER, RIVAL = "rome", "han"
HOME, BORDER, THEIRS = "t_home", "t_border", "t_theirs"


class _Game(CampaignActorsMixin):
    """What the army methods read of a Sim: a force, who owns which tile, and the economy's record of armies."""

    def __init__(self, force=1000.0):
        self.force = {OWNER: force, RIVAL: 400.0}
        self.owners = {HOME: OWNER, BORDER: OWNER, THEIRS: RIVAL}
        self.world_map = types.SimpleNamespace(tiles={HOME: object(), BORDER: object(), THEIRS: object(), "t_unowned": object()})
        self.state = types.SimpleNamespace(economy=types.SimpleNamespace(campaigns={}), scenario=types.SimpleNamespace(year=100))
        self.civ = {"id": OWNER}
        self.actors = types.SimpleNamespace(state=types.SimpleNamespace(countries={RIVAL: object()}))

    def tiles_owned_by(self, owner):
        return sorted(tile for tile, holder in self.owners.items() if holder == owner)

    def tile_owner(self, tile):
        return self.owners.get(tile)

    def owner_world(self, owner):
        government = types.SimpleNamespace(record=types.SimpleNamespace(army=self.force[owner]))
        return types.SimpleNamespace(equipment_kg_per_soldier=lambda: 12.5, soldiers_under_arms=lambda: self.force[owner],
                                     government=lambda: government)


def place_army(game, soldiers=300.0, owner=OWNER, tile=HOME, army_id="army_1", target=None):
    """Put an army straight into the game's record of armies."""
    army = Army(army_id, owner, tile, soldiers, 12.5, home_tile=tile)
    army.target = target
    game.army_records()[army_id] = army.to_dict()
    return army


class RaisingAnArmy(unittest.TestCase):

    def test_a_raised_army_is_recorded_with_its_owner_tile_soldiers_and_equipment(self):
        game = _Game()
        army = game.raise_army(OWNER, 300.0, HOME)
        self.assertEqual((army.owner, army.tile, army.soldiers, army.equipment_kg), (OWNER, HOME, 300.0, 12.5))
        self.assertEqual(game.army_records(), {army.army_id: army.to_dict()})

    def test_free_soldiers_are_the_force_less_the_armies_in_the_field(self):
        game = _Game()
        place_army(game, soldiers=300.0)
        self.assertEqual(game.free_soldiers(OWNER), 700.0)

    def test_the_army_gets_the_next_id_and_the_counter_moves_on(self):
        game = _Game()
        game.campaign_store()["next_id"] = 7
        army = game.raise_army(OWNER, 100.0, HOME)
        self.assertEqual((army.army_id, game.campaign_store()["next_id"]), ("army_7", 8))

    def test_more_than_the_free_soldiers_is_refused_with_a_cause_and_changes_nothing(self):
        game = _Game()
        place_army(game, soldiers=600.0)
        refused = game.raise_army(OWNER, 401.0, HOME)
        self.assertEqual(refused.cause, "not_enough_soldiers")
        self.assertEqual(len(game.army_records()), 1)

    def test_a_tile_that_is_not_the_owners_or_not_on_the_map_is_refused(self):
        game = _Game()
        self.assertEqual(game.raise_army(OWNER, 100.0, THEIRS).cause, "tile_not_yours")
        self.assertEqual(game.raise_army(OWNER, 100.0, "nowhere").cause, "unknown_tile")
        self.assertEqual(game.army_records(), {})

    def test_with_no_tile_named_the_army_is_raised_on_a_tile_the_owner_holds(self):
        game = _Game()
        self.assertIn(game.raise_army(OWNER, 100.0).tile, (HOME, BORDER))

    def test_a_bare_owner_with_no_state_keeps_no_soldiers(self):
        self.assertEqual(_Game().owner_force("nobody"), 0.0)

    def test_soldiers_who_die_in_the_field_come_off_the_owners_army_line(self):
        game = _Game()
        government = game.owner_government(OWNER)
        game.owner_government = lambda owner: government
        game.strike_from_force(OWNER, 120.0)
        self.assertEqual(government.record.army, 880.0)
        game.strike_from_force("nobody", 50.0)
        game.strike_from_force(OWNER, -5.0)
        self.assertEqual(government.record.army, 880.0)


class OrdersAndStandingDown(unittest.TestCase):

    def setUp(self):
        self.game = _Game()
        self.army = place_army(self.game)

    def test_an_order_sets_the_target_and_clears_progress(self):
        self.game.army_records()[self.army.army_id]["progress_days"] = 3.0
        ordered = self.game.order_army(OWNER, self.army.army_id, THEIRS)
        self.assertEqual((ordered.target, ordered.progress_days), (THEIRS, 0.0))
        self.assertEqual(self.game.army_of(self.army.army_id).target, THEIRS)

    def test_an_order_to_where_it_stands_clears_the_target(self):
        place_army(self.game, target=THEIRS)
        self.assertIsNone(self.game.order_army(OWNER, self.army.army_id, HOME).target)

    def test_an_order_to_a_tile_off_the_map_is_refused(self):
        self.assertEqual(self.game.order_army(OWNER, self.army.army_id, "nowhere").cause, "unknown_tile")

    def test_another_actor_cannot_give_the_army_orders_or_disband_it(self):
        self.assertEqual(self.game.order_army(RIVAL, self.army.army_id, THEIRS).cause, "not_your_army")
        self.assertEqual(self.game.disband_army(RIVAL, self.army.army_id).cause, "not_your_army")
        self.assertEqual(len(self.game.army_records()), 1)

    def test_an_unknown_army_is_refused_with_the_owners_armies_as_choices(self):
        refused = self.game.order_army(OWNER, "army_99", THEIRS)
        self.assertEqual(refused.cause, "unknown_army")

    def test_recall_sends_the_army_back_to_the_tile_it_was_raised_on(self):
        place_army(self.game, tile=BORDER)
        self.game.army_records()["army_1"]["home_tile"] = HOME
        self.assertEqual(self.game.recall_army(OWNER, "army_1").target, HOME)

    def test_a_recall_to_a_lost_home_tile_goes_to_a_tile_the_owner_still_holds(self):
        place_army(self.game, tile=THEIRS)
        self.game.army_records()["army_1"]["home_tile"] = HOME
        self.game.owners[HOME] = RIVAL
        self.assertEqual(self.game.recall_army(OWNER, "army_1").target, BORDER)

    def test_disbanding_removes_the_armys_record_and_hands_it_back(self):
        disbanded = self.game.disband_army(OWNER, self.army.army_id)
        self.assertEqual(self.game.army_records(), {})
        self.assertEqual(disbanded.army_id, self.army.army_id)


if __name__ == "__main__":
    unittest.main()
