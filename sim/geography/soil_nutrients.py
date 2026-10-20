"""A tile's soil nitrogen as a stock (Complaint 543): harvests draw it down; rest, legumes and manure restore it.

The stock is the share of the tile's native nitrogen pool left (one is untouched ground; a tile with no record is
native). Per hectare of holding and year the pool gains the natural input (what leaching and gas loss take from a
native soil, so a native soil holds still), a legume crop's net fixation and the share of applied manure that
settles into humus, and loses that loss, proportional to the pool, and the nitrogen in the harvest. A crop is fed
by the year's mineralisation of the pool, plus the nitrate that fallow hectares of the holding leave behind and
the manure's available share; its yield against the reference field follows that supply with diminishing return.
"""
from sim.constants import declare

NATIVE_POOL_KG_PER_HECTARE = declare(
    "NATIVE_POOL_KG_PER_HECTARE", 3000.0,
    kind="biological_parameter", unit="kg nitrogen per hectare in the rooting zone",
    source="Topsoil carries about 0.1 percent nitrogen (0.05 to 0.3), over about 3000 tonnes of soil to 25 cm "
           "(Brady and Weil, The Nature and Properties of Soils; recalled, not opened)",
    confidence="C", why="Size of the organic nitrogen pool a harvest draws on; the stock is kept as a share of it.")

LOSS_RATE_PER_YEAR = declare(
    "LOSS_RATE_PER_YEAR", 0.01,
    kind="engineering_estimate", unit="share of the pool per year",
    source="Leaching and denitrification take about a percent of soil organic nitrogen a year (order of magnitude "
           "from Brady and Weil, recalled)",
    confidence="D", why="Sets both the natural input that keeps native soil level and how fast a worn pool recovers.")

MINERALISATION_RATE_PER_YEAR = declare(
    "MINERALISATION_RATE_PER_YEAR", 0.02,
    kind="biological_parameter", unit="share of the pool made plant-available per year",
    source="One to three percent of soil organic nitrogen mineralises each year (Brady and Weil; recalled)",
    confidence="C", why="Nitrogen a crop can take from the pool in a year.")

GRAIN_NITROGEN_FRACTION = declare(
    "GRAIN_NITROGEN_FRACTION", 0.02,
    kind="biological_parameter", unit="kg nitrogen per kg of grain harvested",
    source="Wheat grain is about 1.8 to 2.4 percent nitrogen (feed and cereal composition tables; recalled). "
           "Straw is taken to stay on the field",
    confidence="B", why="What each harvest removes from the pool.")

LEGUME_NET_NITROGEN_KG_PER_HECTARE = declare(
    "LEGUME_NET_NITROGEN_KG_PER_HECTARE", 25.0,
    kind="engineering_estimate", unit="kg nitrogen per hectare of a grain legume crop, fixation less grain removal",
    source="Net nitrogen balance of harvested grain legumes runs from about -20 to +40 kg a hectare (Peoples and "
           "others 2009, Symbiosis 48; recalled, not opened)",
    confidence="D", why="Why a legume in the rotation holds the pool up.")

MANURE_AVAILABLE_FIRST_YEAR = declare(
    "MANURE_AVAILABLE_FIRST_YEAR", 0.3,
    kind="engineering_estimate", unit="share of applied manure nitrogen a crop can take that year",
    source="Farmyard manure gives a crop 10 to 30 percent of its nitrogen in the year of application (UK "
           "RB209 fertiliser manual; recalled)",
    confidence="C", why="Immediate yield effect of manure.")

MANURE_RETAINED_IN_POOL = declare(
    "MANURE_RETAINED_IN_POOL", 0.4,
    kind="engineering_estimate", unit="share of applied manure nitrogen that settles into the pool",
    source="Long-term manured plots (Rothamsted Broadbalk, Hoosfield) gain soil nitrogen from the organic fraction "
           "of manure; the share is recalled, conf D",
    confidence="D", why="Why repeated manuring builds a lasting stock rather than one good year.")

FALLOW_NITRATE_RETENTION = declare(
    "FALLOW_NITRATE_RETENTION", 0.5,
    kind="temporary_heuristic", unit="share of a fallow hectare's mineralised nitrogen left for the next crop",
    source="Bare fallow accumulates nitrate that the following crop uses, part of it leached; the share is invented",
    confidence="D", retire="a soil water and nitrate balance",
    why="Gives fallow its yield benefit beyond the pool: cropped hectares share the fallow hectares' mineral nitrogen.")

HALF_SATURATION_SUPPLY_KG_PER_HECTARE = declare(
    "HALF_SATURATION_SUPPLY_KG_PER_HECTARE", 30.0,
    kind="temporary_heuristic", unit="kg nitrogen per hectare",
    source="Order of a cereal crop's nitrogen uptake; the saturating form (Mitscherlich) is standard, this "
           "constant is invented",
    confidence="D", retire="a crop growth model against nitrogen supply and demand",
    why="Supply at which a crop reaches half its nitrogen-saturated yield.")

HERD_EXCRETA_KG_PER_LIVE_WEIGHT_KG_YEAR = declare(
    "HERD_EXCRETA_KG_PER_LIVE_WEIGHT_KG_YEAR", 29.0,
    kind="biological_parameter", unit="kg fresh dung and urine per kg live weight per year",
    source="A cow of 500 kg voids about 40 kg of dung and urine a day, 8 percent of live weight (farm manure "
           "handbooks; recalled)",
    confidence="C", why="Manure the society's draught herd drops.")

MANURE_NITROGEN_FRACTION = declare(
    "MANURE_NITROGEN_FRACTION", 0.005,
    kind="biological_parameter", unit="kg nitrogen per kg fresh dung and urine",
    source="Fresh cattle manure with urine is about half a percent nitrogen (RB209; recalled)",
    confidence="C", why="Nitrogen in the herd's excreta.")

MANURE_COLLECTED_SHARE = declare(
    "MANURE_COLLECTED_SHARE", 0.3,
    kind="temporary_heuristic", unit="share of the herd's excreta carried to the fields",
    source="Share dropped in byre, fold and yard rather than on pasture; invented",
    confidence="D", retire="farmers buying manure goods through the economy (Complaints/544)",
    why="Transitional rule: the society's draught herd manures its cropland for free until farm producers buy the "
        "manure goods.")

NATURAL_INPUT_KG_PER_HECTARE = NATIVE_POOL_KG_PER_HECTARE * LOSS_RATE_PER_YEAR   # keeps a native soil level


def _supply(pool_share, cropped_share, manure_nitrogen_kg_per_hectare):
    """Plant-available nitrogen a cropped hectare gets in a year, kg."""
    fallow_hectares_per_cropped = (1.0 - cropped_share) / cropped_share
    mineral = MINERALISATION_RATE_PER_YEAR * NATIVE_POOL_KG_PER_HECTARE * pool_share
    manure = MANURE_AVAILABLE_FIRST_YEAR * manure_nitrogen_kg_per_hectare / cropped_share
    return mineral * (1.0 + FALLOW_NITRATE_RETENTION * fallow_hectares_per_cropped) + manure


def _saturation(supply):
    return supply / (supply + HALF_SATURATION_SUPPLY_KG_PER_HECTARE)


def yield_response(pool_share, cropped_share, reference_cropped_share, manure_nitrogen_kg_per_hectare=0.0):
    """Yield of a cropped hectare against the reference field (native soil under the reference rotation).
    `manure_nitrogen_kg_per_hectare` is spread over the holding."""
    if cropped_share <= 0.0:
        return 0.0
    reference = _saturation(_supply(1.0, reference_cropped_share, 0.0))
    return _saturation(_supply(pool_share, cropped_share, manure_nitrogen_kg_per_hectare)) / reference


def next_share(pool_share, cropped_share, harvest_kg_per_cropped_hectare, legume_share=0.0,
               manure_nitrogen_kg_per_hectare=0.0, reference_cropped_share=0.5):
    """The pool share after one year. `harvest_kg_per_cropped_hectare` is the reference field's harvest; the
    tile's own response scales it. `legume_share` is the share of the holding in grain legumes."""
    pool = pool_share * NATIVE_POOL_KG_PER_HECTARE
    harvest_kg = harvest_kg_per_cropped_hectare * yield_response(
        pool_share, cropped_share, reference_cropped_share, manure_nitrogen_kg_per_hectare)
    removal = cropped_share * harvest_kg * GRAIN_NITROGEN_FRACTION
    gain = (NATURAL_INPUT_KG_PER_HECTARE + legume_share * LEGUME_NET_NITROGEN_KG_PER_HECTARE
            + MANURE_RETAINED_IN_POOL * manure_nitrogen_kg_per_hectare)
    pool = max(0.0, pool + gain - removal - LOSS_RATE_PER_YEAR * pool)
    return pool / NATIVE_POOL_KG_PER_HECTARE


def herd_manure_nitrogen_kg(herd_live_weight_kg):
    """Nitrogen a herd's collected excreta carries to the fields in a year."""
    return (herd_live_weight_kg * HERD_EXCRETA_KG_PER_LIVE_WEIGHT_KG_YEAR * MANURE_NITROGEN_FRACTION
            * MANURE_COLLECTED_SHARE)
