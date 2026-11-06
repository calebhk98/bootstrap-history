"""The seats module: who plays, joining and handing over, goals and win conditions, dealings between seats, and sight.

The seat registry is the assembly's: the module reads the ids through `registered_seats`, switches seats with `act_as`, and
changes the registry by the assembly's commands `AddSeat` and `MoveSeat`."""
from sim.assembly.api import Module

from .dealings import Dealings
from .founder import Founder
from .goals import Goals
from .handover import Handover
from .holders import Holders
from .run import Run
from .sight import Sight


class Seats(Module):

    PARTS = {
        "holders": Holders,
        "run": Run,
        "handover": Handover,
        "sight": Sight,
        "dealings": Dealings,
        "goals": Goals,
        "founder": Founder,
    }
