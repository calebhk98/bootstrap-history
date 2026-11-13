"""Complaint 106: a firm picks equity over debt when the shares cost it less than the lenders' rate and an investor is
there; a state's bonds held by the pool's depositors are marked to the yield the market asks today, beside household
lenders' claims. Plain functions called with their inputs written out."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import bonds, capital_structure

# ---- the choice between equity and debt ---------------------------------------------------------------------
check("the cost of equity is the dividend over the whole equity's worth",
	  abs(capital_structure.cost_of_equity(5.0, 100.0) - 0.05) < 1e-12)
check("equity worth nothing has no cost, not a free one", capital_structure.cost_of_equity(5.0, 0.0) is None)
check("a firm takes equity when it costs less than the lenders ask", capital_structure.prefers_equity(0.09, 0.05, True))
check("it borrows when the lenders ask less", not capital_structure.prefers_equity(0.04, 0.05, True))
check("it borrows at a tie", not capital_structure.prefers_equity(0.05, 0.05, True))
check("it borrows when no investor will take the shares", not capital_structure.prefers_equity(0.09, 0.05, False))
check("it borrows when the equity has no cost to compare", not capital_structure.prefers_equity(0.09, None, True))

# ---- the pool's bond holders are marked to the market ------------------------------------------------------
book = bonds.BondBook()
book.set_terms("state:a", 0.05, 0.05)
book.sell("state:a", 100.0)
holders = {"household:a": 60.0, "merchant:b": 40.0}
at_par = book.marked_worth("state:a", holders, 0.05)
check("at the coupon yield each holder's bonds are worth what it paid",
	  abs(at_par["household:a"] - 60.0) < 1e-6 and abs(at_par["merchant:b"] - 40.0) < 1e-6, at_par)
dearer = book.marked_worth("state:a", holders, 0.10)
check("a higher yield cuts every holder's mark in proportion to its holding",
	  dearer["household:a"] < 60.0 and abs(dearer["household:a"] / dearer["merchant:b"] - 1.5) < 1e-9, dearer)
check("the marks sum to the bonds' value at the new yield",
	  abs(sum(dearer.values()) - bonds.bond_price(book.debt("state:a"), 0.05, bonds.BOND_TERM_YEARS, 0.10)) < 1e-6, dearer)
check("an issuer with no bonds out leaves its holders marked at nothing, not at what they paid",
	  book.marked_worth("state:none", holders, 0.05) == {"household:a": 0.0, "merchant:b": 0.0})
