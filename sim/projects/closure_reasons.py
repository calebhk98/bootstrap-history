"""Why a work is shut: the reasons a closure record carries."""
from sim.agents.api import business_review

CLOSED_FOR_STAFF = business_review.STAFF_SHORT
CLOSED_BY_CHOICE = "manual"
CLOSED_LOSS_MAKING = business_review.LOSS_MAKING
CLOSED_CREDITOR_SEIZURE = business_review.CREDITOR_SEIZURE
CLOSED_GATE_LAPSED = "gate_lapsed"
