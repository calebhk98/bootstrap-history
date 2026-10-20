# A seller facing inelastic demand has an unbounded markup, and a sold-out seller's ask ratchets

**Status:** open

- `seller_offers.py` gives the markup a seller that moves the price asks as elasticity over elasticity minus one, and
  infinity when demand is inelastic (the `math.inf` branch). Floors such as food are inelastic, so a seller that moves
  the clearing price searches the whole book for its best reservation (`seller_pricing.py`) with no cost anchor.
- A seller that sold out raises its ask by `SOLD_OUT_ASK_RAISE_SHARE` a year (`ask_raise.py`), while an unsold seller
  cuts by search. A good whose supply cannot respond climbs year after year (511: copper; 558: bronze).

What the established models do (`Complaints/reports/research-agent-based-economy-design.md`): Lengnick 2013 keeps each
seller's price inside a band around its marginal cost and moves it by inventory against target; Caiani et al. 2016 set
price as a markup on expected unit cost, nudged by inventory; Peters et al. set a cost-covering minimum. None gives a
seller the buyers' whole demand curve; strategic pricing is for a real single owner (550).

What it would take: a seller's ask anchored on its own unit cost, moved by its stock against its target, bounded on both
sides; the book search kept only for a producer that is the whole market; within-year rounds where buyers can switch
sellers (Lengnick, Caiani). Tests call the ask functions with built inventories: a sold-out seller's ask rises within
the band and stops; an inelastic book does not give an unbounded ask.
