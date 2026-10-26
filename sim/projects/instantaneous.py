"""Whether a capability is a state transition rather than a one-year undertaking."""

NEGLIGIBLE_PRICE = 0.5


def is_instantaneous(founder_hours, calendar_floor_years, price, labour_hours_by_trade, effective_risk):
    """A capability with no founder hours, no calendar floor, no money, no labour and no risk completes when it is
    started. Anything with money, labour, risk or a calendar floor stays a project even when founder hours are zero."""
    return (founder_hours <= 0 and calendar_floor_years <= 0 and price <= NEGLIGIBLE_PRICE
            and not labour_hours_by_trade and effective_risk <= 0)
