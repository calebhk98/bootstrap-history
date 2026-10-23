"""The bill a `start` reply states: what was paid for materials at the start and what is still owed in instalments, to a tenth."""


def bill_parts(instalments_owed, materials_paid_now):
    """(the whole bill, materials paid now, instalments still owed), each rounded to a tenth; the whole is the sum of the two
    rounded parts, so the figures printed add up."""
    instalments = round(instalments_owed, 1)
    materials = round(materials_paid_now, 1)
    return round(instalments + materials, 1), materials, instalments
