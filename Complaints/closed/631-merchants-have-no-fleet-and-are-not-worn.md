# Merchants have no fleet: dispatch is limited by cash, not by carriers

**Status:** closed - each merchant holds carriers in its carrier account (`carriage_wear.account`); dispatch carries no more tonnes than the wear a year its held carriers bear (held over service life) plus idle capacity hired from other merchants allows (`carriage_fleet.py`, `merchants.dispatch(fleet=)`); the fleet its routes call for is bid for in the goods market (`carriage_fleet_book.bids`); carriers with a life age by it with the other durables (`year_close.wear_and_spoilage`), the per-haul tonne-km wear remaining only for feed; merchants open with fleets sized to their capital's trade (`carriage_fleet_book.endow`, goods from `EDGE_PRODUCTION` as the opening durables are). Tests: `sim/tests/test_merchant_fleet.py`.

Left: a real-game trace is not run here. PR #60 found the carrier trades near empty and plant wages unstable; 644 and 659 are meant to answer that. The opening fleet size is a derived estimate (capital over the value of a tonne of the opening's goods, times the wear of an average haul), not a measured trade volume.

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 629 and 630.

**What is wrong.** A merchant's dispatch is cut by hours hired but not by carts, ships or animals it owns. Merchants are not worn.

**Evidence.** `inventory.wear_moves` wears cohort holdings only; `sim/economy/merchants.py`.

**Why it matters.** Trade can be paid for and still be physically impossible.

**What it would take.** A per-merchant fleet whose yearly capacity follows from its carriers and the route's days, bids or hire for more, wear booked from the service life, and an opening endowment of fleets.

**Test.** A test: a merchant without a fleet ships only what its hired capacity allows; wear reduces the fleet.
