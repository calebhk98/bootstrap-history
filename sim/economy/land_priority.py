"""Who gets a tile's scarce land: the higher rent bid first (Complaint 961). Every claim on a tile (a producer's
hectares asked, the hectares households work as their own plots) carries what it would pay a hectare, and land goes down
that order; claims that bid the same share what is left in proportion to the hectares they ask. Plain functions."""
import math
from typing import Dict, Hashable, Sequence, Tuple

Claim = Tuple[Hashable, float, float]      # (claimant, bid per hectare, hectares asked)


def allocate_by_bid(supply: float, claims: Sequence[Claim]) -> Dict[Hashable, float]:
    """Hectares each claimant is granted out of `supply`: the highest bid is served in full before the next, and claims
    of equal bid are cut by one factor. No claimant gets more than it asked."""
    granted = {claimant: 0.0 for claimant, _bid, _hectares in claims}
    left = max(0.0, supply)
    ordered = sorted(claims, key=lambda claim: -claim[1])
    start = 0
    while start < len(ordered) and left > 0.0:
        end = start + 1
        while end < len(ordered) and math.isclose(ordered[end][1], ordered[start][1], rel_tol=1e-9, abs_tol=1e-12):
            end += 1
        tier = ordered[start:end]
        asked = sum(max(0.0, hectares) for _claimant, _bid, hectares in tier)
        scale = min(1.0, left / asked) if asked > 0.0 else 0.0
        for claimant, _bid, hectares in tier:
            granted[claimant] = max(0.0, hectares) * scale
        left -= asked * scale
        start = end
    return granted
