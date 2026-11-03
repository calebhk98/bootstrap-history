"""The disease module: epidemics and endemic disease in the nation.

The nation is a metapopulation: one patch of three age bands per tile held, infection passing between tiles by the
traffic between them (`metapopulation.py`). A pathogen reaches it from the outside sources the civilisation's
`disease_exposure.outside_contact` names (map tiles where it lives, initial conditions only): the chance falls with the
fewest days of travel between the source's tiles and the tiles the nation holds, over the routes its technologies and the
outsiders' carriers open, and it enters at the held tile those routes reach first. Pathogens `disease_exposure.endemic`
names are already in the people at the start. Technology acts through `disease_effects` on node mechanics. Nothing here
names a pathogen, a year or a technology. The module owns the infection records and tells demography nothing but the deaths
by band; the disease burden and the endemic rates it publishes are what the population step reads."""
from sim.assembly.api import Module

from .burden import Burden
from .contact import Contact
from .epidemics import Epidemics
from .forecast import Forecast
from .people import People
from .seats_hit import SeatsHit


class Disease(Module):

    PARTS = {
        "burden": Burden,
        "forecast": Forecast,
        "epidemics": Epidemics,
        "seats_hit": SeatsHit,
        "contact": Contact,
        "people": People,
    }
