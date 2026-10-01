# Trade only covers goods both economies can make; foreign economies stand still

**Status:** open

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
content, and foreign competitors as firm actors remain `Complaints/113`.
