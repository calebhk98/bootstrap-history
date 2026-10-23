"""The disease model's nation-level numbers, shared by every country that runs it (the home nation through
`sim/engine/disease_port.py`, each foreign country through `sim/agents/country_disease.py`)."""
from sim.constants import declare
from sim.world import demography

BANDS = ("children", "working_age", "elderly")
AGE_VULNERABILITY = {"children": demography.STARVATION_VULNERABILITY_CHILD,
                     "working_age": demography.STARVATION_VULNERABILITY_WORKING_AGE,
                     "elderly": demography.STARVATION_VULNERABILITY_ELDERLY}
AGEING = {"children": ("working_age", 1.0 / demography.CHILD_BAND_WIDTH_YEARS),
          "working_age": ("elderly", 1.0 / demography.WORKING_AGE_BAND_WIDTH_YEARS)}
INTRODUCTION_BAND = "working_age"
CAREGIVER_BANDS = ("working_age",)

DISEASE_TRAVELLER_ANNUAL_CHANCE = declare(
    "DISEASE_TRAVELLER_ANNUAL_CHANCE", 0.6, kind="temporary_heuristic",
    unit="dimensionless (chance per year, per pathogen, that an infected party sets out from a source where it is always present)",
    source=None, confidence="D", retire="Complaints/677: the outside world is simulated actors whose own people carry infection along the routes",
    why="Stands in for the outside world exporting infected travellers: while the pathogen is absent from the nation, "
        "one party with it reaches the nation with this chance each year, times the share of the source's contact "
        "that the routes let through (`DISEASE_TRAVEL_DECAY_DAYS`). Drawn from the disease package's own hash of the "
        "game's seed, never Sim.rng.")
DISEASE_EMERGENCE_ANNUAL_CHANCE = declare(
    "DISEASE_EMERGENCE_ANNUAL_CHANCE", 0.0015, kind="temporary_heuristic",
    unit="dimensionless (chance per year, per pathogen, that it starts to spread at a source where it is not always present)",
    source=None, confidence="D", retire="Complaints/677: the outside world is simulated actors whose own people carry infection along the routes",
    why="The outside world is not simulated, so a pathogen that is not always present at a source starts there at "
        "random: a spill-over from animals, a mutation, a long-dormant focus. Its arrival at the nation then follows "
        "the same contact rule as a pathogen that is always there. No dated outbreak is stated anywhere; the value "
        "is fitted so an ensemble of Rome runs holds a handful of pandemics in five centuries, never the same years "
        "(bounds asserted in `python3 -m sim.tests --slow --only plagues_from_contact`).")
DISEASE_TRAVEL_DECAY_DAYS = declare(
    "DISEASE_TRAVEL_DECAY_DAYS", 150.0, kind="temporary_heuristic",
    unit="days of travel (the distance at which a source's contact falls to a third)",
    source=None, confidence="D", retire="Complaints/677: the outside world is simulated actors, so contact comes from their traffic and not from distance",
    why="Contact between a source and the nation falls off with the fewest days of travel between them over the "
        "routes the nation's technologies and the outsiders' carriers open (geography's reach), as exp(-days / this). "
        "Inside the nation the contact between tiles is read from the traffic on each edge; the outside world has no "
        "actors yet, so its contact is only this distance rule.")
DISEASE_CONTACT_INFECTED_PEOPLE = declare(
    "DISEASE_CONTACT_INFECTED_PEOPLE", 10, kind="temporary_heuristic", unit="people",
    source=None, confidence="D", retire="Complaints/677: the outside world's own travellers set how many arrive",
    why="Infected working-age people an introduction brings to the tile it enters at. Stands in for the outside "
        "world's traveller flux; an arrival of a few people dies out by chance in a small share of draws, which the chain-binomial "
        "step produces by itself.")
AGE_FATALITY_FROM_STARVATION_VULNERABILITY = declare(
    "AGE_FATALITY_FROM_STARVATION_VULNERABILITY", 1.0, kind="temporary_heuristic",
    unit="dimensionless (exponent of the band's starvation vulnerability in its relative case fatality)",
    source=None, confidence="D",
    why="A pathogen's case fatality is one number for the whole population. Its split across bands reuses the "
        "demography module's relative vulnerability of children, working-age adults and the elderly (sourced for "
        "famine, direction supported for epidemic disease, magnitude borrowed), rescaled so the population-weighted "
        "mean stays the pathogen's own figure. The nutrition shortfall multiplies it by the same curve baseline "
        "mortality uses. Replaced by per-band fatality in the pathogen files when sourced.")
DISEASE_CARE_COLLAPSE_SENSITIVITY = declare(
    "DISEASE_CARE_COLLAPSE_SENSITIVITY", 1.0, kind="temporary_heuristic",
    unit="dimensionless (extra case fatality, as a multiple of the base, when every caregiving adult is ill at once)",
    source=None, confidence="D",
    why="When most adults fall ill together nobody fetches water, feeds the sick or tends the harvest, so fatality "
        "rises (the sociocultural account of virgin-soil epidemics, Neel 1970 on the Yanomami measles epidemic, "
        "controversial; no figure read). The multiplier is one plus this times the ill share of the caregiving "
        "band, so a small outbreak is unchanged and the figure is only the direction. Vary across the ensemble; "
        "replaced by a sourced curve or by a nursing-capacity mechanism once households exist in the model.")
DISEASE_URBAN_DENSITY_RATIO = declare(
    "DISEASE_URBAN_DENSITY_RATIO", 4.0, kind="temporary_heuristic",
    unit="dimensionless (density of an urban resident's neighbourhood over a rural resident's)",
    source=None, confidence="D",
    why="A country's crowding index is the person-weighted density: rural people at one, urban people at this ratio, "
        "weighted by the civilisation's urban share. Pathogen transmissibilities are stated for the rural index of one. "
        "At home it fixes the mean of the tiles' crowding (each tile's own comes from its density); a foreign country, "
        "still one patch, uses it whole.")
SURVIVING_SHARE_FLOOR = declare(
    "SURVIVING_SHARE_FLOOR", 0.05, kind="engineering_estimate", unit="share of a party that is still alive after a year",
    source=None, confidence="D",
    why="Numerical floor under 1 minus a place's disease loss, so a place where nearly everyone dies makes a party "
        "cost many times more rather than infinitely more. Not an outcome: only the divisor's lower bound.")
