"""What a trade's wage screen says about where the wage comes from. Shared by the labour and economy screens."""


def wage_origin(sim, trade):
    """The fields that explain `a_year_of_one` for a trade. Before the economy opens the wage is the opening schedule scaled by the
    cost-of-living factors, which are shown as `wage_foundation`. After it opens the wage is the economy's: last year's clearing of
    the trade's labour markets, so the factors do not apply and are not shown."""
    if sim.view("agent_economy_opened")():
        return {"wage_from": "the labour market's clearing last year (hours hired and offered in the trade's markets); a trade no market has paid is priced by the fallback rule: its opening wage at today's price level, else the unskilled wage plus the trade's training premium"}
    return {"wage_foundation": {
        "base_for_skill_and_difficulty": round(sim.view("base_annual_wage")[trade], 2),
        **{factor_key: round(value, 3) for factor_key, value in sim.view("labour_market")().cost_factors(trade).items()}}}
