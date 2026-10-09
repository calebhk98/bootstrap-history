"""`validate` rejects a pathogen file (data/disease/) with a missing source tag, a bad stage or an out-of-range reproduction number."""
from typing import List

from sim.disease import api as disease


def check_disease_data() -> List[str]:
    return disease.check_pathogen_data()
