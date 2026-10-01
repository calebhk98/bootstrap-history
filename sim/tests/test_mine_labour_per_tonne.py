"""Labour per tonne of rock and per tonne of mineral in the deposit model
agrees with the sourced hand-mining figures (Complaints/610)."""
import unittest

from sim.world import deposits, mine_fire_setting, mine_works
from sim.unit_conversions import KILOGRAMS_PER_TONNE

# Bettenay 2022 (Metalla 26.2, Tables 1-2): Kongsberg fire-set drive, 37.5
# man-days per fathom of a 6.5 ft by 5 ft drive (Timberlake 1990 quoting
# Collins 1883); Melle all-in rate 25-250 kg of rock per miner per day.
KONGSBERG_MAN_DAYS_PER_FATHOM = 37.5
KONGSBERG_FATHOM_METRES = 1.8288
KONGSBERG_DRIVE_AREA_SQUARE_METRES = 6.5 * 0.3048 * 5.0 * 0.3048
GRANITE_DENSITY = 2.65
MELLE_ALL_IN_MAXIMUM_KILOGRAMS_PER_MINER_DAY = 250.0


def _vein_deposits():
    return [deposit for metal in deposits.METALS
            for deposit in deposits.load_deposits(metal)
            if deposit.depth_class in ("shallow_vein", "deep_vein")]


def _hours_per_tonne_of_ore(deposit):
    return (deposits.extraction_cost_labour_hours_per_kg(deposit)
            * deposit.ore_grade_kg_per_tonne)


def _hours_per_tonne_of_rock(deposit):
    return (_hours_per_tonne_of_ore(deposit)
            / mine_works.rock_broken_tonnes_per_tonne_ore(deposit.depth_class))


class MineLabourPerTonne(unittest.TestCase):

    def test_hours_per_tonne_of_mineral_is_ore_hours_times_ore_per_tonne(self):
        for metal in deposits.METALS:
            for deposit in deposits.load_deposits(metal):
                hours_per_tonne_mineral = (
                    deposits.extraction_cost_labour_hours_per_kg(deposit)
                    * KILOGRAMS_PER_TONNE)
                ore_per_tonne_mineral = (
                    KILOGRAMS_PER_TONNE / deposit.ore_grade_kg_per_tonne)
                self.assertAlmostEqual(
                    hours_per_tonne_mineral,
                    _hours_per_tonne_of_ore(deposit) * ore_per_tonne_mineral,
                    delta=1e-6 * hours_per_tonne_mineral, msg=deposit.name)

    def test_hard_rock_face_breaking_matches_the_kongsberg_drive(self):
        tonnes = (KONGSBERG_DRIVE_AREA_SQUARE_METRES * KONGSBERG_FATHOM_METRES
                  * GRANITE_DENSITY)
        hours = (KONGSBERG_MAN_DAYS_PER_FATHOM * mine_fire_setting.MINING_SHIFT_HOURS
                 / tonnes)
        self.assertAlmostEqual(
            deposits.BREAKING_HOURS_PER_TONNE_HARD / hours, 1.0, delta=0.15)

    def test_hard_rock_pays_for_its_fire_setting_wood(self):
        self.assertEqual(mine_fire_setting.fire_setting_labour_hours_per_tonne_rock("soft"), 0.0)
        wood_hours = mine_fire_setting.fire_setting_labour_hours_per_tonne_rock("hard")
        self.assertGreater(wood_hours, 5.0)
        deposit = next(d for d in deposits.load_deposits("copper") if d.hardness_class == "hard")
        rock_per_ore = mine_works.rock_broken_tonnes_per_tonne_ore(deposit.depth_class)
        works = sum(mine_works.works_hours_per_tonne_ore(
            deposit.depth_class, deposit.hardness_class,
            deposits._lift_hours_per_tonne_metre(),
            deposits.shaft_depth_metres(deposit),
            mine_fire_setting.MINING_SHIFT_HOURS).values())
        self.assertAlmostEqual(
            _hours_per_tonne_of_ore(deposit),
            (deposits.BREAKING_HOURS_PER_TONNE_HARD + wood_hours) * rock_per_ore + works,
            places=6)

    def test_deep_hard_rock_stays_inside_the_all_in_rate_of_a_hand_mine(self):
        # Bettenay's all-in 25-250 kg of rock per miner per day counts the
        # face and its support; it excludes forest and processing workers.
        for deposit in _vein_deposits():
            if deposit.depth_class != "deep_vein" or deposit.hardness_class != "hard":
                continue
            kilograms_per_shift = (KILOGRAMS_PER_TONNE * mine_fire_setting.MINING_SHIFT_HOURS
                                   / _hours_per_tonne_of_rock(deposit))
            self.assertLessEqual(
                kilograms_per_shift, MELLE_ALL_IN_MAXIMUM_KILOGRAMS_PER_MINER_DAY * 1.5,
                deposit.name)


if __name__ == "__main__":
    unittest.main()
