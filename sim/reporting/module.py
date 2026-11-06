"""The reporting module: the log of what happened to each seat and the audit trail of what its automation did."""
from sim.assembly.api import Module

from .causes import Causes
from .log import Logging
from .output import Output
from .price_ratios import PriceRatios


class Reporting(Module):

    PARTS = {
        "logging": Logging,
        "causes": Causes,
        "output": Output,
        "price_ratios": PriceRatios,
    }
