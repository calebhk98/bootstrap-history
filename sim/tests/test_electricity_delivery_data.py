"""Electricity's delivery entries in the production data: generators make the generated good, only a delivery entry makes
the meter carrier, its draw is grossed up by the loss a conductor's resistance sets, and its line plant's copper follows
from the stated current density. Data and physics only, no solve; the prices are test_electricity_delivery."""
QUICK_TOPIC = True
import math
import unittest

from sim.labour.labour_market import production_data

CIRCULAR_MIL_SQUARE_METRES = 5.0671e-10
TWO_WIRE = "electrical_mj_main_two_wire"
THREE_WIRE = "electrical_mj_main_three_wire"
DELIVERY_KEYS = (TWO_WIRE, THREE_WIRE)


def loss_ratio(basis):
    """Watts lost per watt delivered: resistivity times circuit length times current density over voltage."""
    current_density = 1.0 / (basis["circular_mils_per_ampere"] * CIRCULAR_MIL_SQUARE_METRES)
    return (basis["resistivity_ohm_m"] * basis["circuit_length_m"] * current_density
            / basis["delivered_voltage_v"])


def copper_mass_kg(basis):
    current_density = 1.0 / (basis["circular_mils_per_ampere"] * CIRCULAR_MIL_SQUARE_METRES)
    section = basis["rated_power_w"] / basis["delivered_voltage_v"] / current_density
    return basis["conductors"] * section * basis["route_length_m"] * basis["copper_density_kg_m3"]


class DeliveryData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.production = production_data()

    def test_generators_make_the_generated_good_not_the_carrier(self):
        for key in ("electrical_mj_dynamo", "electrical_mj_photovoltaic"):
            self.assertEqual(list(self.production[key]["outputs"]), ["electricity_generated_mj"], key)


    def test_only_a_delivery_entry_makes_the_meter_carrier(self):
        makers = {key for key, entry in self.production.items() if "electrical_mj" in entry["outputs"]}
        self.assertEqual(makers, set(DELIVERY_KEYS))


    def test_a_delivery_entry_draws_the_generated_good_grossed_up_for_its_stated_loss(self):
        for key in DELIVERY_KEYS:
            entry = self.production[key]
            basis = entry["loss_basis"]
            drawn = entry["inputs"]["electricity_generated_mj"]
            self.assertAlmostEqual(drawn, entry["outputs"]["electrical_mj"] * (1.0 + loss_ratio(basis)),
                                   delta=0.001 * drawn, msg=key)


    def test_the_line_plant_copper_follows_from_its_stated_current_density(self):
        for key in DELIVERY_KEYS:
            unit = self.production[key]["capital"][0]["build_materials"]
            (unit_key,) = unit
            copper = self.production[unit_key]["inputs"]["copper_wire_kg"]
            self.assertAlmostEqual(copper, copper_mass_kg(self.production[key]["loss_basis"]),
                                   delta=0.002 * copper, msg=key)


    def test_the_loss_ratio_rises_with_distance_and_falls_with_voltage(self):
        basis = dict(self.production[TWO_WIRE]["loss_basis"])
        far = dict(basis, circuit_length_m=basis["circuit_length_m"] * 2.0)
        high = dict(basis, delivered_voltage_v=basis["delivered_voltage_v"] * 2.0)
        self.assertAlmostEqual(loss_ratio(far), 2.0 * loss_ratio(basis))
        self.assertAlmostEqual(loss_ratio(high), 0.5 * loss_ratio(basis))


    def test_the_three_wire_main_loses_less_and_uses_less_copper_than_the_two_wire(self):
        two, three = self.production[TWO_WIRE]["loss_basis"], self.production[THREE_WIRE]["loss_basis"]
        self.assertLess(loss_ratio(three), loss_ratio(two))
        self.assertLess(copper_mass_kg(three), copper_mass_kg(two))
        # equal current density, doubled voltage, a neutral of the outer wires' section
        self.assertAlmostEqual(copper_mass_kg(three) / copper_mass_kg(two), 0.75, places=6)


    def test_a_delivery_entry_states_the_plant_its_output_is_bounded_by(self):
        for key in DELIVERY_KEYS:
            capital = self.production[key]["capital"][0]
            self.assertGreater(capital["annual_output_at_basis"], 0.0, key)
            self.assertTrue(math.isfinite(capital["annual_output_at_basis"]), key)



if __name__ == "__main__":
    unittest.main()
