"""The reporting module: the log of what happened to each seat and the audit trail of what its automation did."""
from sim.assembly.api import Module

from .log import Logging


class Reporting(Logging, Module):
    pass
