# Trade only covers goods both economies can make; foreign economies stand still

**Status:** partly - goods only one side makes now cross when value per tonne pays the freight; foreign technology and population are still frozen

`_foreign_price_pair` in `sim/engine/foreign_economies.py` trades a good only
when the home society and the partner can both make it with the technologies
they hold. A partner that cannot make a good but would buy it (foreign
consumer demand for what only the home society makes) is not modelled, nor is
a home society that imports what it cannot make. The partner's technology and
population are frozen at its civilisation file's opening, so a founder's
technology never reaches it and it never grows.

## What it would take

Foreign demand from the partner's own population and income for goods it
cannot make, priced from the importer's side; foreign technology that advances
through its own society actors (`docs/architecture/ACTORS_NEXT.md` increment
7). Tariffs, embargoes, exchange rates between coins other than by metal
content, and foreign competitors as firm actors remain `Complaints/109`.

## Progress

A good only this society makes flows to a partner whose households want it
(the partner has demand and no capacity); a good only the partner makes flows
in against this society's own household demand, with no home capacity. Which
goods cross is decided by value per tonne against the route's freight, not by
name. Open: the partner's technology and population stay at its civilisation
file's opening (`docs/architecture/ACTORS_NEXT.md` increment 7), and tariffs,
embargoes and exchange rates (`Complaints/109`).

Related: 324, 338, 339, 346, 347, 350, 351, 353.

Owner decision (2026-10-02): can wait. A foreign economy should be another country object sharing every method the home civilisation has.
