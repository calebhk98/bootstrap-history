# Research brief: how much grain prices should swing, and what damps them

An input report, written by a research agent during economy round four. Searches returned few numbers;
labels are **[read]** (abstract read), **[snippet]** and **[memory]** (unverified).

## How volatile
- Campbell & Ó Gráda, J. Econ. Hist. 2011 [read, abstract]: English yields 1268-1480 were highly
  variable, back-to-back shortfalls made the famines, and by about 1800 prices were less
  harvest-sensitive (ideas.repec.org/a/cup/jechis/v71y2011i04p859-886_00).
- Early modern European grain price variability, Econ. Rev. 2024 [read, abstract]: volatility fell
  over time, especially after about 1725 and at coastal sites; inland markets were more volatile
  (ideas.repec.org/a/eee/eecrev/v170y2024ics0014292124001818).
- [memory] The standard deviation of the yearly log change of wheat prices was roughly 0.15-0.30 in
  medieval and early modern England and inland Europe, and lower (0.10-0.15) on coasts and in the
  18th century. Bad years were +50-100%: fat-tailed and skewed upward.
- So a simulated 0.12-0.22 is plausible; 0.05-0.10 is probably low. Check the tail and the skew,
  and above all that the swings follow the harvest, not only their size.

## Mechanisms, ranked by the agent
1. **Storage carried between years** (Deaton & Laroque 1992; Williams & Wright 1991 [memory]).
   - Store when the expected next price covers spoilage, interest and storage.
   - Medieval carrying costs were high (McCloskey & Nash 1984 [memory]), so storage damped little.
   - Every parameter is physical or comes from the capital market.
2. **Planted area set in advance** (Nerlove).
   - Area responds to the expected price with a short-run elasticity of about 0.1-0.3 [snippet:
     modern estimates, ageconsearch 267010, mjard 339595].
   - Output is area times the weather yield. For grain the weather, not a cobweb, drives the price.
   - The elasticity is empirical, so label it a heuristic.
3. **Trade between regions** up to freight capacity, when the price gap exceeds the route cost.
   - Correlated weather limits it.

Before tuning: measure how much of the simulated grain volatility the weather alone and the demand
elasticity explain.
