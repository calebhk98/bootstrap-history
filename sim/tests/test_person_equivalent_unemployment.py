"""`person_equivalent_unemployment` from written-out markets: people weighted, not hours weighted; markets that
offered nothing are outside the labour force."""

QUICK_TOPIC = True

from .harness import check

from sim.economy.diagnostics import person_equivalent_unemployment

# 100 people sell 10 hours each and 75% are hired; 300 people sell 1000 hours each and 5% are hired
rate = person_equivalent_unemployment([(100.0, 1000.0, 750.0), (300.0, 300000.0, 15000.0)])
check("people weighted, not hours weighted", abs(rate - (100 * 0.25 + 300 * 0.95) / 400) < 1e-12, rate)

rate = person_equivalent_unemployment([(100.0, 0.0, 0.0), (50.0, 10.0, 10.0)])
check("a market that offered no hours is outside the labour force", rate == 0.0, rate)

check("no hours offered anywhere is None, not zero", person_equivalent_unemployment([(100.0, 0.0, 0.0)]) is None)

# equal hours per person: the people rate is the hours rate of the same rows (weighting is not a source of divergence)
rows = [(10.0, 20000.0, 10000.0), (30.0, 60000.0, 54000.0)]
hours_rate = 1.0 - (10000.0 + 54000.0) / (20000.0 + 60000.0)
check("equal hours per person gives the hours rate", abs(person_equivalent_unemployment(rows) - hours_rate) < 1e-12)

# the plot trade's rows (most people, little unemployment) dilute a rate that includes them: scope, not weighting
wage_rows = [(10.0, 20000.0, 15000.0)]
with_plot = wage_rows + [(990.0, 1980000.0, 1980000.0)]
check("adding a fully hired plot trade lowers the rate",
      person_equivalent_unemployment(with_plot) < person_equivalent_unemployment(wage_rows) / 50.0)
