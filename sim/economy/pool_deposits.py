"""The economy's lenders and the actors' pool: what the pool pays a lender or loses of its deposit reaches the books the
economy keeps for lenders (property income, credit losses). The deposit itself is the lender's asset
(`Contracts.deposit_value`, read by banks.assets_of and CreditView.claims)."""
from .types import AgentId


def note_pool_posting(record, lender: AgentId, units: float) -> None:
    """The pool paid `lender` interest (`units` above nothing) or the lender lost `units` of its deposit to a default
    (below nothing); in the economy's unit. Interest is property income; a loss is a lender's credit loss, which ages
    into the ask it makes."""
    if units > 0.0:
        record.capital_markets.note_pool_income(lender, units)
    elif units < 0.0:
        record.credit.add_loss(lender, -units)
