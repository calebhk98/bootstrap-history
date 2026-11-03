"""Rules of `sim/projects/materials_wait.py`: what a project keeps on order, and what the clearing's results settle."""
QUICK_TOPIC = True

import unittest

from sim.projects import materials_wait


def order(material, tonnes, quoted, order_id=None):
    return {"material": material, "stock_key": "stock_" + material, "tonnes": tonnes, "quoted": quoted, "order_id": order_id}


def refused(material, tonnes, cause):
    return dict(order(material, tonnes, 0.0), refused=cause, refused_text="no")


class MaterialsWait(unittest.TestCase):
    def test_orders_all_refused_at_start_stay_on_order_as_unposted(self):
        record = {}
        materials_wait.record_orders(record, [refused("iron", 2.0, "cannot_pay")])
        self.assertEqual(record["materials_on_order"],
                         [{"material": "iron", "stock_key": "stock_iron", "tonnes": 2.0, "quoted": 0.0, "unposted": True,
                           "cause": "cannot_pay"}])
        self.assertEqual(record["awaiting_materials"], ["stock_iron"])
        self.assertEqual(record["materials_refused"][0]["cause"], "cannot_pay")

    def test_an_unposted_order_is_a_shortfall_with_its_cause(self):
        record = {}
        materials_wait.record_orders(record, [refused("iron", 2.0, "no_price")])
        add_back, shortfalls = materials_wait.reconcile(record["materials_on_order"], [])
        self.assertEqual(add_back, 0.0)
        self.assertEqual([(short["material"], short["tonnes"], short["cause"]) for short in shortfalls], [("iron", 2.0, "no_price")])

    def test_two_orders_for_one_material_are_each_settled_by_their_own_result(self):
        on_order = [order("iron", 1.0, 10.0, 7), order("iron", 3.0, 30.0, 9)]
        results = [{"material": "iron", "order_id": 7, "tonnes": 1.0, "bought_tonnes": 1.0, "paid": 10.0},
                   {"material": "iron", "order_id": 9, "tonnes": 3.0, "bought_tonnes": 1.0, "paid": 10.0}]
        add_back, shortfalls = materials_wait.reconcile(on_order, results)
        self.assertEqual(add_back, 20.0)
        self.assertEqual([short["tonnes"] for short in shortfalls], [2.0])

    def test_a_result_with_another_order_id_is_not_credited(self):
        add_back, shortfalls = materials_wait.reconcile(
            [order("iron", 2.0, 20.0, 4)], [{"material": "iron", "order_id": 5, "tonnes": 2.0, "bought_tonnes": 2.0, "paid": 25.0}])
        self.assertEqual(add_back, 20.0)
        self.assertEqual([short["tonnes"] for short in shortfalls], [2.0])


if __name__ == "__main__":
    unittest.main()
