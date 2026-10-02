# Interest groups: landholders, organised workers, firm owners and the rest are not modelled

**Status:** open

Complaint 110's first increment builds interest groups as actors (`sim/agents/group.py`) from two measured sources only: producers of a commodity whose sales the founder displaces (the market's `displaced_by_founder_tonnes`) and employers of a trade whose price the founder's and the firms' hiring pushed above the wage table (`labour_price_factor`). Every other body of people 110 names has no source yet:

- **Landholders whose rents fall.** Land rent is a static solver quantity (`sim/world/land.py`); nothing in the engine moves it year to year, so there is nothing for a landholder group to lose. It needs a rent that follows the crop price and the labour a farm can hire.
- **Workers of a trade the founder's machines displace.** The group built here speaks for the whole income of a displaced sector, owners and hands together, in wage-equivalents of a labourer. Splitting it into the owners' profit and the hands' wages needs a labour share per commodity; `sim/labour/labour_market.labour_hours_coefficients_per_unit_output` gives hours by trade per unit of output and is the natural source. Organised workers (a trade whose real wage falls, or whose members are numerous enough to riot) is the second half.
- **Owners of the firms in a sector** whose margin the founder or another firm erodes (`Firm.record.last_margin`, `exited_year`). Firms already exist as actors; they could be the members of a group and ask for protection or a monopoly.
- **Clergy, military, bureaucracy, urban poor, academics.** Each needs an income or a status that something in the economy moves.

The mechanism group actors use on the state (a budget line, a prohibition at the start gate, blame on the founder) is general; adding a kind is a new measuring method on `GroupView` (`sim/agents/world_groups.py`) returning `Sector`s, and a decision on whether `state_response` should let that kind demand a prohibition.

See also 110 and 312.

Related: 313.

Owner decision (2026-10-02): can be a mod; deferred.
