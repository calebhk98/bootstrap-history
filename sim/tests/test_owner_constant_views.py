"""The views that hand a declared number to the modules that read it: each owner answers with its own constant."""
QUICK_TOPIC = True

import unittest

from sim.markets import categories
from sim.markets.goods_views import GoodsViews
from sim.polity import constants as polity_constants
from sim.production import constants as production_constants
from sim.projects import constants as projects_constants
from sim.tests import polity_host, production_host, projects_host


class OwnerConstantViews(unittest.TestCase):
    def test_markets_answer_the_goods_categories(self):
        self.assertIs(GoodsViews().goods_categories(), categories.GOODS_CATEGORIES)

    def test_projects_answer_the_substitute_quality_discount(self):
        self.assertEqual(projects_host.build().substitute_quality_discount(), projects_constants.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT)

    def test_production_answers_the_institution_expansion_convexity(self):
        self.assertEqual(production_host.build().institution_expansion_convexity(), production_constants.INSTITUTION_EXPANSION_CONVEXITY)

    def test_polity_answers_the_terms_a_state_funds_a_client_on(self):
        self.assertEqual(polity_host.build().state_funding_terms(), {
            "base_hours": polity_constants.STATE_FUNDING_BASE_LABOUR_HOURS,
            "exponent": polity_constants.STATE_FUNDING_POP_SCALE_EXPONENT,
            "governance_scale": polity_constants.STATE_FUNDING_GOV_QUALITY_SCALE})


if __name__ == "__main__":
    unittest.main()
