"""What the capital markets beyond lending keep from year to year: hazard records, insurers and their policies, the
exposure each holder has to a hazard, and the funds.

One field of the economy's record (`record.capital`), so a new institution adds its state here and not to the record's
own list of fields. Each part is a plain dataclass; the save is `plain(...)` and `from_plain` builds them back.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .record_plain import plain


@dataclass
class Hazard:
    """What has been seen of one hazard: the years watched and the share of the value exposed that it took each year."""
    years: int = 0
    loss_share_total: float = 0.0       # summed over the years, each the share of insured value lost that year
    worst: float = 0.0                  # the largest share any year took


@dataclass
class Insurer:
    agent_id: str
    founder: str
    founded_year: int
    mutual: bool = False                # members share the year's claims after the fact; no premium is paid in advance
    failed_year: int = -1               # the year it could not pay its claims in full; below zero while it stands
    paid_in: float = 0.0                # the capital its founder put in, which no dividend returns


@dataclass
class Policy:
    insurer: str
    holder: str
    hazard: str
    insured_value: float                # what the holder is paid if the hazard takes all of it


@dataclass
class Fund:
    """A pool of shares and loans that households hold units in: its holdings are the fund's own agent's, the units
    are what each holder owns of the whole."""
    agent_id: str
    manager: str
    founded_year: int
    units: Dict[str, float] = field(default_factory=dict)       # holder -> units held
    closed_year: int = -1


@dataclass
class CapitalState:
    hazards: Dict[str, Hazard] = field(default_factory=dict)
    insurers: Dict[str, Insurer] = field(default_factory=dict)
    policies: List[Policy] = field(default_factory=list)
    exposure: Dict[str, Dict[str, float]] = field(default_factory=dict)    # holder -> hazard -> value exposed
    funds: Dict[str, Fund] = field(default_factory=dict)

    def to_plain(self) -> Dict[str, Any]:
        return {"hazards": {key: plain(value) for key, value in sorted(self.hazards.items())},
                "insurers": {key: plain(value) for key, value in sorted(self.insurers.items())},
                "policies": [plain(value) for value in self.policies],
                "exposure": {holder: dict(sorted(held.items())) for holder, held in sorted(self.exposure.items())},
                "funds": {key: plain(value) for key, value in sorted(self.funds.items())}}

    @classmethod
    def from_plain(cls, record: Dict[str, Any]) -> "CapitalState":
        return cls(hazards={key: Hazard(**value) for key, value in record.get("hazards", {}).items()},
                   insurers={key: Insurer(**value) for key, value in record.get("insurers", {}).items()},
                   policies=[Policy(**value) for value in record.get("policies", [])],
                   exposure={holder: dict(held) for holder, held in record.get("exposure", {}).items()},
                   funds={key: Fund(**value) for key, value in record.get("funds", {}).items()})
