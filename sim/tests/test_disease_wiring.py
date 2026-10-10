"""The disease model wired to the engine's side (Complaint 386, stage 2): the yearly step over age bands, deaths handed
to `Population`, the saved state, the contact heuristic and technology scales. No game is built; the stand-in
carries only what `DiseasePortMixin` reads."""

QUICK_TOPIC = True

import json
import types
import unittest

from sim.disease import api as disease
from sim.engine import disease_port, state, validate_disease_data
from sim.world import demography

BANDS = disease_port.BANDS


def pathogen_plain(case_fatality=0.3, permanent=True, immunity_days=None):
    return {"id": "test_pathogen", "name": "Test pathogen",
            "stages": [{"id": "exposed", "infectiousness": 0.0, "mean_duration_in_days": 10.0, "shape": 3},
                       {"id": "infectious", "infectiousness": 1.0, "mean_duration_in_days": 14.0, "shape": 2}],
            "transmissibility_per_day": 4.0 / 14.0, "case_fatality": case_fatality,
            "immunity": {"permanent": permanent, "duration_in_days": immunity_days}}


def pathogens(**options):
    return {"test_pathogen": disease.Pathogen.from_plain(pathogen_plain(**options))}


PEOPLE = {"children": 30000.0, "working_age": 60000.0, "elderly": 10000.0}


def year_with(records, fatality_scale=None, introductions=("test_pathogen",), people=PEOPLE, **options):
    return disease.advance_year(pathogens(**options), records, people, "wiring-test", introductions=introductions,
                                introduction_band="working_age", introduction_size=20, fatality_scale=fatality_scale)


class StandIn(disease_port.DiseasePortMixin):
    def __init__(self, civ=None, effects=(), diffusion=1.0, children=3e4, working_age=6e4, elderly=1e4):
        self.civ = civ or {"id": "stand_in"}
        self.year = 1500
        self.state = types.SimpleNamespace(disease=state.DiseaseState())
        self.population = demography.Population(children, working_age, elderly)
        self._effects, self._diffusion = effects, diffusion

    def _farm_year_weather_seed(self, year, region=None):
        return 12345 + year

    def _effect_terms(self, channel):
        return list(self._effects) if channel == "disease_effects" else []

    def civ_diffusion(self, node_id):
        return self._diffusion


class PopulationHandbackTest(unittest.TestCase):
    def test_epidemic_deaths_are_deaths_and_the_accounting_identity_holds(self):
        population = demography.Population(3e4, 6e4, 1e4)
        plain = demography.Population(3e4, 6e4, 1e4)
        flows = population.step(1e12, epidemic_deaths={"children": 2000.0, "elderly": 500.0})
        base = plain.step(1e12)
        self.assertAlmostEqual(flows.deaths - base.deaths, 2500.0)
        self.assertAlmostEqual(flows.deaths_children - base.deaths_children, 2000.0)
        self.assertAlmostEqual(flows.start_total + flows.births - flows.deaths, flows.end_total)

    def test_a_band_cannot_lose_more_than_it_holds(self):
        population = demography.Population(100.0, 6e4, 1e4)
        population.step(1e12, epidemic_deaths={"children": 1e9})
        self.assertGreaterEqual(population.children, 0.0)


class AgeBandsAndFoodTest(unittest.TestCase):
    def test_children_and_the_old_die_more_than_working_age_and_the_mean_stays_the_pathogens(self):
        scale = disease_port.DiseaseWorld(StandIn()).fatality_scale_by_band(1.0)
        self.assertGreater(scale["children"], scale["working_age"])
        self.assertGreater(scale["elderly"], scale["working_age"])
        people = PEOPLE
        mean = sum(scale[band] * people[band] for band in BANDS) / sum(people.values())
        self.assertAlmostEqual(mean, 1.0)

    def test_hunger_raises_every_bands_fatality(self):
        world = disease_port.DiseaseWorld(StandIn())
        fed, hungry = world.fatality_scale_by_band(1.0), world.fatality_scale_by_band(0.7)
        for band in BANDS:
            self.assertGreater(hungry[band], fed[band])

    def test_a_larger_fatality_scale_kills_more_in_the_same_year(self):
        low, high = {}, {}
        killed_low = year_with(low, fatality_scale={band: 0.2 for band in BANDS}).deaths_by_band
        killed_high = year_with(high, fatality_scale={band: 2.0 for band in BANDS}).deaths_by_band
        self.assertGreater(sum(killed_high.values()), sum(killed_low.values()))

    def test_no_fatality_scale_no_deaths(self):
        result = year_with({}, fatality_scale={band: 0.0 for band in BANDS})
        self.assertEqual(sum(result.deaths_by_band.values()), 0)


class YearStepTest(unittest.TestCase):
    def test_people_plus_deaths_are_conserved(self):
        records = {}
        result = year_with(records)
        for band in BANDS:
            living = sum(disease.Patch.from_plain(records["test_pathogen"][band]).counts.values())
            self.assertEqual(living + result.deaths_by_band[band], PEOPLE[band])

    def test_the_dead_leave_the_contact_denominator(self):
        pathogen = pathogens()["test_pathogen"]
        patch = disease.Patch.naive(pathogen, 5000, seed=3)
        patch.seed_infection(pathogen, 50)
        started = patch.living()
        for _ in range(60):
            disease.step_patch(pathogen, patch)
        self.assertGreater(patch.deaths_from_disease, 0)
        self.assertEqual(patch.living(), started - patch.deaths_from_disease)

    def test_a_nation_without_exposure_pays_nothing_and_stores_nothing(self):
        sim = StandIn()
        self.assertEqual(sim.disease_year(1e12), {})
        self.assertEqual(sim.state.disease.records, {})

    def test_immunity_ages_with_the_people_who_carry_it(self):
        records = {}
        year_with(records)
        for band in BANDS:
            self.assertIn("recovered", records["test_pathogen"][band]["counts"])
        immune_children = records["test_pathogen"]["children"]["counts"]["recovered"]
        ageing = {"children": ("working_age", 0.25)}
        later = {"test_pathogen": records["test_pathogen"]}
        before = later["test_pathogen"]["working_age"]["counts"]["recovered"]
        disease.advance_year(pathogens(), later, PEOPLE, "wiring-test", ageing=ageing)
        self.assertGreater(later["test_pathogen"]["working_age"]["counts"]["recovered"], before + 0.2 * immune_children)

    def test_births_arrive_susceptible(self):
        records = {}
        year_with(records)
        grown = dict(PEOPLE, children=PEOPLE["children"] + 5000.0)
        susceptible_before = records["test_pathogen"]["children"]["counts"]["susceptible"]
        disease.advance_year(pathogens(), records, grown, "wiring-test")
        self.assertGreaterEqual(records["test_pathogen"]["children"]["counts"]["susceptible"], susceptible_before)

    def test_lost_immunity_returns_people_to_susceptible_without_a_circulating_case(self):
        records = {}
        year_with(records, permanent=False, immunity_days=365.0)
        counts = lambda: {name: sum(records["test_pathogen"][band]["counts"][name] for band in BANDS)
                          for name in ("susceptible", "recovered")}
        for _ in range(40):
            if not disease.is_circulating(records, "test_pathogen"):
                break
            disease.advance_year(pathogens(permanent=False, immunity_days=365.0), records, PEOPLE, "wiring-test")
        immune = counts()["recovered"]
        disease.advance_year(pathogens(permanent=False, immunity_days=365.0), records,
                             {band: sum(records["test_pathogen"][band]["counts"].values()) for band in BANDS}, "wiring-test")
        self.assertLess(counts()["recovered"], immune)


class SavedStateTest(unittest.TestCase):
    def test_the_state_is_a_save_field_and_round_trips_through_json(self):
        self.assertIn("records", state.SAVE_FIELDS)
        straight, resumed = {}, {}
        year_with(straight)
        year_with(resumed)
        disease_state = state.DiseaseState(records=resumed, introduced={"test_pathogen": [1500]}, deaths={"test_pathogen": 7})
        blob = json.loads(json.dumps(state.serialize_state(disease_state)))
        loaded = state.deserialize_state(blob, state.DiseaseState)
        self.assertEqual(loaded.introduced, {"test_pathogen": [1500]})
        for _ in range(3):
            year_with(straight, introductions=())
            year_with(loaded.records, introductions=())
        self.assertEqual(straight, loaded.records)

    def test_a_game_without_epidemics_saves_an_empty_record(self):
        self.assertEqual(state.serialize_state(state.DiseaseState())["records"], {})


class ContactHeuristicTest(unittest.TestCase):
    CIV = {"id": "stand_in", "disease_exposure": {"outside_contact": [{"pathogens": ["smallpox"], "years": [1520, 1600]}]}}

    def arrivals(self, sim, years, records=None):
        world = disease_port.DiseaseWorld(sim)
        return [year for year in years if world.introductions(records or {}, year)]

    def test_nothing_arrives_outside_the_window_or_without_a_listing(self):
        self.assertEqual(self.arrivals(StandIn(self.CIV), range(1400, 1520)), [])
        self.assertEqual(self.arrivals(StandIn(self.CIV), range(1601, 1700)), [])
        self.assertEqual(self.arrivals(StandIn(), range(1400, 1700)), [])

    def test_arrivals_are_a_repeatable_draw_near_the_declared_chance(self):
        sim = StandIn(self.CIV)
        years = list(range(1520, 1601))
        first = self.arrivals(sim, years)
        self.assertEqual(first, self.arrivals(StandIn(self.CIV), years))
        share = len(first) / len(years)
        self.assertGreater(share, disease_port.DISEASE_CONTACT_ANNUAL_CHANCE / 3)
        self.assertLess(share, disease_port.DISEASE_CONTACT_ANNUAL_CHANCE * 2)

    def test_a_pathogen_already_circulating_is_not_introduced_again(self):
        records = {"smallpox": {"working_age": {"counts": {"susceptible": 5, "infectious.0": 3}}}}
        self.assertEqual(self.arrivals(StandIn(self.CIV), range(1520, 1601), records), [])

    def test_the_scenario_files_name_real_pathogens(self):
        civ = json.load(open("data/civilizations/mexica_1500.json", encoding="utf-8"))
        self.assertEqual(validate_disease_data.check_disease_data({}, {"mexica_1500": civ}), [])
        self.assertNotIn("Old World epidemics on contact", [hazard.get("name") for hazard in civ["hazards"]])
        for hazard in civ["hazards"]:
            first, last = hazard.get("years", [0, 0])
            if "staff_loss" in hazard:
                self.assertFalse(first <= 1520 <= last or first <= 1600 <= last, hazard.get("name"))

    def test_the_validator_rejects_an_unknown_pathogen_and_a_bad_effect(self):
        bad_civ = {"c": {"disease_exposure": {"outside_contact": [{"pathogens": ["no_such"], "years": [1, 2]}]}}}
        bad_node = {"n": {"mechanics": {"disease_effects": {"acts_on": "luck", "factor": 2, "pathogens": ["no_such"]}}}}
        problems = validate_disease_data.check_disease_data(bad_node, bad_civ)
        self.assertEqual(len(problems), 4)


class TechnologyScaleTest(unittest.TestCase):
    def spec(self, acts_on, factor, pathogen_ids=None):
        spec = {"acts_on": acts_on, "factor": factor}
        if pathogen_ids:
            spec["pathogens"] = pathogen_ids
        return spec

    def test_effects_multiply_by_how_far_the_country_has_taken_them_up(self):
        effects = [("quarantine", self.spec("transmission", 0.5)), ("nursing", self.spec("case_fatality", 0.8))]
        fatality, transmission = disease_port.DiseaseWorld(StandIn(effects=effects, diffusion=1.0)).technology_scales(["a", "b"])
        self.assertEqual((fatality["a"], transmission["a"]), (0.8, 0.5))
        fatality, transmission = disease_port.DiseaseWorld(StandIn(effects=effects, diffusion=0.5)).technology_scales(["a"])
        self.assertAlmostEqual(transmission["a"], 0.75)
        self.assertAlmostEqual(fatality["a"], 0.9)

    def test_an_effect_that_names_a_pathogen_leaves_the_others_alone(self):
        effects = [("vaccine", self.spec("transmission", 0.4, ["a"]))]
        _fatality, transmission = disease_port.DiseaseWorld(StandIn(effects=effects)).technology_scales(["a", "b"])
        self.assertEqual((transmission["a"], transmission["b"]), (0.4, 1.0))

    def test_technology_nobody_has_taken_up_does_nothing(self):
        effects = [("quarantine", self.spec("transmission", 0.5))]
        _fatality, transmission = disease_port.DiseaseWorld(StandIn(effects=effects, diffusion=0.0)).technology_scales(["a"])
        self.assertEqual(transmission["a"], 1.0)

    def test_a_vaccine_in_force_means_fewer_infected_in_the_same_year(self):
        bare, covered = {}, {}
        disease.advance_year(pathogens(), bare, PEOPLE, "wiring-test", introductions=("test_pathogen",),
                             introduction_band="working_age", introduction_size=20)
        disease.advance_year(pathogens(), covered, PEOPLE, "wiring-test", introductions=("test_pathogen",),
                             introduction_band="working_age", introduction_size=20,
                             transmission_scale={"test_pathogen": 0.2})
        immune = lambda records: sum(records["test_pathogen"][band]["counts"]["recovered"] for band in BANDS)
        self.assertLess(immune(covered), immune(bare))


class CareCollapseAndDensityTest(unittest.TestCase):
    """Complaint 471: fatality rises with the share of caregivers ill at once; contact scales with crowding."""

    def run_year(self, pathogen_extra=None, introduction_size=20, **options):
        plain = pathogen_plain()
        plain.update(pathogen_extra or {})
        records = {}
        result = disease.advance_year({"test_pathogen": disease.Pathogen.from_plain(plain)}, records, PEOPLE,
                                      "wiring-test", introductions=("test_pathogen",), introduction_band="working_age",
                                      introduction_size=introduction_size, **options)
        return records, result

    def test_the_multiplier_is_one_for_no_sensitivity_and_grows_with_the_ill_share(self):
        from sim.disease.step import care_collapse_multiplier
        pathogen = pathogens()["test_pathogen"]
        patch = disease.Patch.naive(pathogen, 1000, seed=1)
        self.assertEqual(care_collapse_multiplier({"a": patch}, None), 1.0)
        self.assertEqual(care_collapse_multiplier({"a": patch}, (("a",), 2.0)), 1.0)
        patch.seed_infection(pathogen, 250)
        self.assertAlmostEqual(care_collapse_multiplier({"a": patch}, (("a",), 2.0)), 1.5)
        self.assertEqual(care_collapse_multiplier({"a": patch}, (("elsewhere",), 2.0)), 1.0)

    def test_a_mass_epidemic_kills_more_with_care_collapse_than_without(self):
        _, bare = self.run_year()
        _, collapsing = self.run_year(care_collapse=(("working_age",), 3.0))
        self.assertGreater(sum(collapsing.deaths_by_band.values()), sum(bare.deaths_by_band.values()))

    def test_zero_density_exponent_ignores_crowding_and_a_positive_one_speeds_spread(self):
        flat, _ = self.run_year({"density_exponent": 0.0}, crowding=1.0)
        flat_crowded, _ = self.run_year({"density_exponent": 0.0}, crowding=4.0)
        self.assertEqual(flat, flat_crowded)
        immune = lambda records: sum(records["test_pathogen"][band]["counts"]["recovered"] for band in BANDS)
        sparse, _ = self.run_year({"density_exponent": 0.5}, crowding=1.0, introduction_size=2)
        crowded, _ = self.run_year({"density_exponent": 0.5}, crowding=4.0, introduction_size=2)
        self.assertGreater(immune(crowded), immune(sparse))

    def test_crowding_rises_with_the_urban_share_and_is_one_when_rural(self):
        index = lambda urban: disease_port.DiseaseWorld(StandIn(civ={"id": "x", "urban_fraction": urban})).crowding_index()
        self.assertEqual(index(0.0), 1.0)
        self.assertLess(index(0.1), index(0.3))
        self.assertEqual(disease_port.DiseaseWorld(StandIn()).crowding_index(), 1.0)

    def test_every_pathogen_file_declares_a_density_exponent_between_the_poles(self):
        for pathogen in disease.load_pathogens().values():
            self.assertTrue(0.0 <= pathogen.density_exponent <= 1.0, pathogen.id)


if __name__ == "__main__":
    unittest.main()
