"""The materials module: the supply and demand of raw materials, the resource throttle, electricity, how a material reaches
the seat, and what a project pays for its materials."""
from sim.assembly.api import Module

from .availability import Availability
from .demand import Demand
from .electricity import Electricity
from .project_bill import ProjectBill
from .readings import Readings
from .supply import Supply
from .throttle import Throttle


class Materials(Module):

    PARTS = {
        "readings": Readings,
        "supply": Supply,
        "demand": Demand,
        "electricity": Electricity,
        "throttle": Throttle,
        "project_bill": ProjectBill,
        "availability": Availability,
    }
