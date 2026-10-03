"""The geography file: regions, located materials and the land-tile grid (data/world/geography.json)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOFILE = os.path.join(ROOT, "data", "world", "geography.json")


def load_geography():
    """Where things are, not just what they cost.

    Reach must be computed per civilization from real geography, never a
    single hard-coded value measured from Italy: Han China's own distance
    to Malaya, which Chinese and Malay traders already sail to routinely,
    is not the same as its distance to Italy, a place that civilization has
    never seen. See Geography.region_reach and Geography.material_reach for where reach
    is actually computed; this loader just hands back the raw data.
    """
    return json.load(open(GEOFILE))
