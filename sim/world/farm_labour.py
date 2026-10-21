"""Labour of a cropped hectare of wheat, built from its sub-tasks (data/world/farm_labour.json).

Pure: reads the data file and the model's working day; imports nothing else from sim/."""
import json
import os
from functools import lru_cache
from typing import Any, Dict

from sim.constants import declare
from sim.unit_conversions import HOURS_PER_PERSON_YEAR, WORKING_DAYS_PER_YEAR

FARM_LABOUR_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "data", "world", "farm_labour.json")


@lru_cache(maxsize=1)
def load_farm_labour() -> Dict[str, Any]:
    with open(FARM_LABOUR_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def hours_per_working_day() -> float:
    return HOURS_PER_PERSON_YEAR / WORKING_DAYS_PER_YEAR


def wheat_task_person_days(data: Dict[str, Any]) -> Dict[str, float]:
    """Person-days a hectare takes by sub-task (cultivation cycle, reaping, threshing)."""
    tasks = data["wheat"]["tasks"]
    reaping = float(tasks["reaping"]["person_days"])
    return {"cultivation_cycle": float(tasks["cultivation_cycle"]["person_days"]),
            "reaping": reaping,
            "threshing": reaping * float(tasks["threshing"]["person_days_as_share_of_reaping"])}


def wheat_hours_per_hectare(data: Dict[str, Any], working_day_hours: float) -> float:
    """Hours of labour per hectare with a plough team."""
    return sum(wheat_task_person_days(data).values()) * working_day_hours


def wheat_hand_tilling_extra_hours(data: Dict[str, Any]) -> float:
    """Extra hours per hectare when the tilling is done with hand tools instead of by a yoke of oxen."""
    tilling = data["wheat"]["hand_tilling"]
    return float(tilling["hours_per_hectare_by_hand_tools"]) - float(tilling["hours_per_hectare_with_oxen"])


def wheat_hoe_hours_per_hectare(data: Dict[str, Any], working_day_hours: float) -> float:
    return wheat_hours_per_hectare(data, working_day_hours) + wheat_hand_tilling_extra_hours(data)


def wheat_reaping_hectares_per_person_day(data: Dict[str, Any]) -> float:
    """Hectares one person reaps in a day, the inverse of the reaping sub-task."""
    return 1.0 / wheat_task_person_days(data)["reaping"]


WHEAT_HOURS_PER_HECTARE = wheat_hours_per_hectare(load_farm_labour(), hours_per_working_day())
WHEAT_HOE_HOURS_PER_HECTARE = wheat_hoe_hours_per_hectare(load_farm_labour(), hours_per_working_day())
WHEAT_REAPED_HECTARES_PER_PERSON_DAY = wheat_reaping_hectares_per_person_day(load_farm_labour())


REFERENCE_LABOUR_HOURS_PER_HECTARE = declare(
    "REFERENCE_LABOUR_HOURS_PER_HECTARE", WHEAT_HOURS_PER_HECTARE,
    kind="engineering_estimate",
    unit="labourer-hours/hectare/season, at the reference (quality-1.0, "
         "fold-return-4.5) wheat yield",
    source="Built from sub-tasks in data/world/farm_labour.json by this module: Shukurov et al., "
           "arXiv 1505.05121 section 8.1 (secondary), White (1965) on Columella, 44 person-days/ha for the "
           "cultivation cycle excluding harvest and 5.7 for reaping; Halstead and Jones (1989), threshing "
           "about the same as reaping; person-days at the model's working day. Equals data/production/"
           "40_organics.json wheat_kg labour_hours (tested). sim/world/agriculture.py, sim/world/land.py (as "
           "LAND_REFERENCE_LABOUR_HOURS_PER_HECTARE) and sim/engine/colonies.py import this declaration.",
    confidence="C",
    why="The labour intensity the reference yield is quoted at, and the "
        "anchor every Cobb-Douglas yield curve in either consuming module "
        "is calibrated to reproduce exactly at that one point.")
