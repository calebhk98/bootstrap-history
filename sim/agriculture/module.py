"""The agriculture module: farmland, the growing-season weather, soil nitrogen, the wild stock and the food the held land
gives. It owns the wild stock, the soil nitrogen stock and the weather salt; the farm holding is read and written through
the engine's household state until demography and the farm workforce move."""
from sim.assembly.api import Module

from .farm import Farm
from .farm_state import FarmState
from .food import Food
from .soil import Soil
from .weather import Weather


class Agriculture(Weather, Food, Soil, Farm, FarmState, Module):
    def setup(self):
        self.setup_weather()
