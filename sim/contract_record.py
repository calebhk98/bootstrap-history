"""One contract as a plain record: lender, borrower, currency, principal and the terms of its kind. The registry (`sim/contracts.py`)
holds facilities and deposits as these objects; the term loans live in the loan table (`sim/loans/`) and are made into one of these
only on demand."""
from dataclasses import dataclass

FACILITY = "facility"
TERM_LOAN = "term_loan"
DEPOSIT = "deposit"


@dataclass
class Contract:
    contract_id: str
    lender: str
    borrower: str
    currency: str
    principal: float
    rate: float = 0.0
    years_left: float = 0.0
    collateral_value: float = 0.0
    arrears: float = 0.0
    issued_year: int = 0
    arrears_interest: float = 0.0     # the part of arrears that is unpaid interest
    kind: str = TERM_LOAN
    collateral_tile: str = ""         # the tile whose land title the loan pledges (empty: none)
    collateral_share: float = 0.0     # the share of that tile's land pledged
    unit_value: float = 1.0           # a deposit placed across the exchange: what one coin of its principal is worth in the lender's own unit

    @property
    def loan_id(self) -> str:
        return self.contract_id
