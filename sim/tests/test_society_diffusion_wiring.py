"""Complaint 287 and the diffusion wiring (from the craftsmen wording scenario): what the whole society has adopted of a built technology
(`civ_diffusion`), the category averages (`_category_diffusion_index`), the military share the government holds
(`state_military_diffusion`) and the report that stays absent until something spreads (`world_diffusion_report`). Each method runs on a
stand-in game holding the seats' finished nodes and the government's knowledge; the curve itself is test_diffusion_categories_rule."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.society_diffusion import DiffusionMixin

FOOD, WEAPON, WEAPON_TWO, PLAIN = "rotation", "cannon", "mortar", "workshop"
NODES = {FOOD: {"traits": ["food"]}, WEAPON: {"traits": ["military"]}, WEAPON_TWO: {"traits": ["military"]}, PLAIN: {"traits": ["craft"]}}


class Game(DiffusionMixin):
    """The founder's finished nodes by seat, the clock, and the government's knowledge."""

    def __init__(self, year=1000, seats=None, knowledge=()):
        self.nodes = NODES
        self.knowledge = set(knowledge)
        self.state = SimpleNamespace(scenario=SimpleNamespace(year=year), seats=seats if seats is not None else {})

    def state_treasury(self):
        return SimpleNamespace(knowledge=self.knowledge)

    def _diffusible_ids(self, category):
        return tuple(sorted(node_id for node_id, node in NODES.items() if category in node["traits"]))


def seat(done, years=None, granted=()):
    return SimpleNamespace(projects=SimpleNamespace(done=set(done), granted=set(granted), done_year=dict(years or {})))


HALF_LIFE = DiffusionMixin.DIFFUSION_HALF_LIFE_FOOD_YEARS

# ---- civ_diffusion
game = Game(seats={"founder": seat([])})
check("nothing spreads of a technology nobody has built", game.civ_diffusion(FOOD) == 0.0, None)
game = Game(year=1000, seats={"founder": seat([FOOD], {FOOD: 1000})})
check("nothing has spread the year it is built", game.civ_diffusion(FOOD) == 0.0, game.civ_diffusion(FOOD))
game = Game(year=1000 + HALF_LIFE, seats={"founder": seat([FOOD], {FOOD: 1000})})
check("half has spread after the category's half-life", abs(game.civ_diffusion(FOOD) - 0.5) < 1e-9, game.civ_diffusion(FOOD))
game = Game(year=1000 + 2 * HALF_LIFE, seats={"founder": seat([FOOD], {FOOD: 1000})})
check("three quarters have spread after two half-lives", abs(game.civ_diffusion(FOOD) - 0.75) < 1e-9, game.civ_diffusion(FOOD))
game = Game(year=1000 + HALF_LIFE, seats={"founder": seat([FOOD], {FOOD: 1000}), "second": seat([FOOD], {FOOD: 1000 + HALF_LIFE})})
check("the society copies from whichever seat finished it first", abs(game.civ_diffusion(FOOD) - 0.5) < 1e-9, game.civ_diffusion(FOOD))
game = Game(year=5000, seats={"founder": seat([PLAIN], {PLAIN: 1000})})
check("a technology with none of the four diffusible traits never diffuses", game.civ_diffusion(PLAIN) == 0.0, None)
game = Game(year=5000, seats={"founder": seat([FOOD], {FOOD: 1000})})
check("a node the tree does not hold has no diffusion", game.civ_diffusion("ghost") == 0.0, None)

# ---- military is the government's holding, not a curve
game = Game(year=1200, seats={"founder": seat([WEAPON], {WEAPON: 1000})})
check("military technology the founder built stays out of the state's hands however long it has had", game.civ_diffusion(WEAPON) == 0.0, None)
game.knowledge.add(WEAPON)
check("once the government holds it, it has fully spread", game.civ_diffusion(WEAPON) == 1.0, None)
check("the military share is the built weapons the government holds", Game(seats={"founder": seat([WEAPON, WEAPON_TWO])}, knowledge=[WEAPON]).state_military_diffusion() == 0.5, None)
check("with no weapon built the military share is nothing", Game(seats={"founder": seat([])}, knowledge=[WEAPON]).state_military_diffusion() == 0.0, None)
check("a weapon the starting society was granted is not the founder's to spread",
      Game(seats={"founder": seat([WEAPON], granted=[WEAPON])}, knowledge=[]).state_military_diffusion() == 0.0, None)

# ---- the category average is summed in sorted order
class Averaged(Game):
    NAMES = ["node_%02d" % number for number in range(24)]

    def __init__(self):
        super().__init__(seats={"founder": seat(self.NAMES)})
        self.asked = []

    def _diffusible_ids(self, category):
        return tuple(self.NAMES)

    def civ_diffusion(self, node_id):
        self.asked.append(node_id)
        return 0.5


averaged = Averaged()
check("a category average adds the nodes in sorted order, whatever order the set holds them in",
      averaged._category_diffusion_index("food") == 0.5 and averaged.asked == sorted(Averaged.NAMES), averaged.asked)
check("a category with nothing built averages nothing", Game(seats={"founder": seat([])})._category_diffusion_index("food") == 0.0, None)

# ---- the report stays absent until something spreads
class Reported(Game):
    def __init__(self, food=0.0, medical=0.0, military=0.0, information=0.0):
        super().__init__()
        self.figures = (food, medical, military, information)

    def food_diffusion_index(self):
        return self.figures[0]

    def medical_diffusion_index(self):
        return self.figures[1]

    def state_military_diffusion(self):
        return self.figures[2]

    def information_diffusion_index(self):
        return self.figures[3]

    def medical_diffusion_relief(self):
        return 0.25


check("while nothing has spread there is no report", Reported().world_diffusion_report() is None, None)
check("a spread below one per cent is no report", Reported(food=0.009).world_diffusion_report() is None, None)
report = Reported(food=0.4).world_diffusion_report()
check("once farming has spread the report names how much, and only that", report == {"food_and_farming_the_country_has_adopted": 0.4}, report)
report = Reported(medical=0.5, military=0.2, information=0.1).world_diffusion_report()
check("medicine carries the relief it gives, weapons and printing their shares",
      report["public_health_the_country_has_adopted"] == 0.5 and report["how_much_softer_the_next_epidemic_will_be"] == 0.25
      and report["military_technology_now_in_the_states_hands"] == 0.2 and report["printing_and_literacy_the_country_has_adopted"] == 0.1, report)
