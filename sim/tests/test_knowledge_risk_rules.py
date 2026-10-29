"""knowledge_risk on the hazards module: the expected loss per sacking, the separate chance of any loss, what is
already lost and must be rebuilt, and the hedge named under fog."""

QUICK_TOPIC = True

import unittest

from sim.tests import hazards_host


def risk_module(at_risk=300, fog=False, forgotten=None, done=(), hedge="corpus_written", sack_ahead=True):
    """The hazards module over a civilisation with a sack ahead (or none) and the views the report reads."""
    module = hazards_host.build(
        civilisation={"hazards": [{"name": "test sack", "years": [200, 210], "sack_chance": 0.3}] if sack_ahead else []},
        losable_node_ids=lambda keep_dispersed=True: ["node%d" % i for i in range(at_risk)],
        corpus_hedge=(0.5, 0.22, hedge), techniques_forgotten=forgotten or {}, techniques_held=set(done),
        fog_of_war=fog, visibility=lambda node_id, memo=None: False, corpus_nodes=["corpus_dispersed"])
    module.hazard_figure = lambda kind, hazard, assume_running=(): hazard[kind]
    return module


class RiskGame:
    """The report's inputs, as the tests below state them."""

    def __init__(self, **inputs):
        self.module = risk_module(**inputs)

    def knowledge_risk(self, advice=True, chronology=True):
        return self.module.knowledge_risk(advice, chronology)


class KnowledgeRisk(unittest.TestCase):

    def test_the_expected_loss_per_sacking_is_not_discounted_by_the_chance_it_happens(self):
        risk = RiskGame().knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["technologies_at_risk"], 300)
        self.assertAlmostEqual(risk["expected_technologies_lost_per_sacking"], 300 * risk["fraction_lost_when_it_happens"], delta=0.6)

    def test_the_chance_a_sacking_costs_anything_is_reported_separately(self):
        risk = RiskGame().knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["and_the_chance_a_sacking_costs_you_anything"], risk["loss_chance_if_a_site_is_sacked"])

    def test_a_civilisation_with_no_sack_ahead_expects_no_loss(self):
        risk = RiskGame(sack_ahead=False).knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["expected_technologies_lost_per_sacking"], 0.0)

    def test_what_is_already_lost_is_listed_newest_first_and_never_what_is_known_again(self):
        game = RiskGame(forgotten={"a": 120, "b": 150, "c": 90}, done={"c"})
        risk = game.knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["you_have_already_lost"], 2)
        self.assertEqual(risk["and_have_to_build_again"], ["b", "a"])
        self.assertEqual(risk["the_most_recent_went_in"], 150)

    def test_nothing_lost_leaves_the_loss_fields_out(self):
        risk = RiskGame().knowledge_risk(advice=False, chronology=False)
        self.assertNotIn("you_have_already_lost", risk)

    def test_under_fog_an_unseen_hedge_is_not_named(self):
        risk = RiskGame(fog=True).knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["hedged_by"], "nothing yet")
        self.assertNotEqual(risk["better_hedge_available"], "corpus_dispersed")

    def test_without_fog_the_hedge_and_the_better_one_are_named(self):
        risk = RiskGame().knowledge_risk(advice=False, chronology=False)
        self.assertEqual(risk["hedged_by"], "corpus_written")
        self.assertEqual(risk["better_hedge_available"], "corpus_dispersed")


if __name__ == "__main__":
    unittest.main()
