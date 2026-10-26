"""A reading of the nation's three age bands, handed to whoever asks."""
from sim.world.demography import CHILD_CALORIE_EQUIVALENT, ELDERLY_CALORIE_EQUIVALENT, Population


class People(Population):
    """The bands as they stood when asked: `total`, `nutrition_ratio` and the rest of a `Population`'s readings, with no
    random stream of its own. Changing one changes nothing; the module's own bands change only through its commands."""
    __slots__ = ()

    def __init__(self, children, working_age, elderly):
        self.children = children
        self.working_age = working_age
        self.elderly = elderly

    @property
    def adult_equivalents(self):
        """The food need in adult-equivalent units: a child counts as `CHILD_CALORIE_EQUIVALENT` of an adult, an elderly
        person as `ELDERLY_CALORIE_EQUIVALENT`."""
        return (self.children * CHILD_CALORIE_EQUIVALENT
                + self.working_age
                + self.elderly * ELDERLY_CALORIE_EQUIVALENT)
