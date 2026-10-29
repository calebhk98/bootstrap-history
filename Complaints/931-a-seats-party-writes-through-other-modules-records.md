# A seat's party in an exchange writes through the seats module's dealings and the ventures module's business

**Status:** open

The actors module builds a seat's party for an exchange (`sim/actors/seat_parties.py`). Its money, staff and know-how come through the
owners' views and commands, but two records are shared: the party's patents, shares held, shares issued and offers are the seats
module's stored dealings (`SeatsSeat`, the view `seat_dealings`), and the plants it opens, closes and hands over are the ventures
module's business (the view `seat_business`). The exchange (sim/agents) writes to both in place, so the owners publish a live record,
uncached, that a command of theirs did not change. A reader that holds a stale copy or a mod that replaces the record is not told.

Evidence: `grep -rn "seat_dealings\|seat_business" sim --include=*.py`; the exchange's writes are `patent.hand_over`, `joint_stock.hand_over`
and `exchange_sale` in sim/agents.

Fix: the exchange asks the owners to change their records (a seats command to grant a patent, move shares and keep an offer; a ventures
command to hand a plant over), so no module hands a live record to another. The party then holds views only.
