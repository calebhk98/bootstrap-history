"""Sizes of the remedies a shortage screen suggests: plain arithmetic on the shortfall, no game state."""
import math


def automatic_policy_on(policy, name, manual):
    """Whether the automatic policy `name` runs: what the actor set, else on for an automatic game and off for a manual one."""
    return policy.get(name, not manual)


def nitre_bed_square_metres(deficit_tonnes, safety_buffer, yield_tonnes_per_square_metre):
    """Nitre bed to lay so the deficit, with headroom, is covered, in whole hundreds of square metres (never under one hundred)."""
    return max(100, int(math.ceil(deficit_tonnes * safety_buffer / max(yield_tonnes_per_square_metre, 1e-12) / 100.0)) * 100)


def nitre_deficit_tonnes(shortfall_tonnes, demand_tonnes, bed_square_metres, yield_tonnes_per_square_metre, market_tonnes, stock_tonnes):
    """Tonnes a year of saltpetre still to cover: the larger of the reported shortfall and the demand left after the
    beds' yield, the market and the stock."""
    available = bed_square_metres * yield_tonnes_per_square_metre + market_tonnes + stock_tonnes
    return max(shortfall_tonnes, demand_tonnes - available, 0.0)


def mine_shortfall_after_sinking(material, shortfall_tonnes, mine_tranches):
    """(tonnes being sunk, year the earliest is ready, shortfall left) once the tranches of `material` already being sunk count."""
    sinking = [tranche for tranche in (mine_tranches or []) if tranche[0] == material]
    sinking_tonnes = sum(tranche[1] for tranche in sinking)
    if sinking_tonnes <= 0.0:
        return 0.0, None, shortfall_tonnes
    return sinking_tonnes, int(min(tranche[2] for tranche in sinking)), max(0.0, shortfall_tonnes - sinking_tonnes)


def mine_size_tonnes(shortfall_tonnes):
    """Tonnes a year of new working to quote and buy: the shortfall rounded up, at least one."""
    return max(1, math.ceil(shortfall_tonnes - 1e-9))


NITRE_SPEND_SHARE_OF_CAPITAL = 0.05     # of capital a year; automatic nitre beds are held to a flat ceiling, never sized to the gap


def nitre_bed_yearly_spend(capital, ceiling):
    """Money the automatic remedy lays into nitre beds in a year: a share of capital, never past a flat ceiling."""
    return min(capital * NITRE_SPEND_SHARE_OF_CAPITAL, ceiling)


AUTO_MINE_SPEND_SHARE_OF_CAPITAL = 0.25     # of capital the automatic mining policy commits to one order


def auto_mine_affordable_tonnes(capital, capex_per_tonne):
    """Tonnes a year of new working a share of the purse sinks at the mine's capital cost per tonne."""
    return capital * AUTO_MINE_SPEND_SHARE_OF_CAPITAL / max(1.0, capex_per_tonne)


def auto_mine_order_tonnes(demand_tonnes, active_tonnes, pending_tonnes, capital, capex_per_tonne):
    """Tonnes a year the automatic policy orders: the demand left once working mines and shafts still being
    sunk count (so a tranche about to commission is not ordered twice), never more than the purse affords."""
    want = max(0.0, demand_tonnes - active_tonnes - pending_tonnes)
    return min(want, auto_mine_affordable_tonnes(capital, capex_per_tonne))
