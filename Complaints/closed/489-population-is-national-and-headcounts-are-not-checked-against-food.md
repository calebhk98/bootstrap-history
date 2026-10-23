# Population is one national figure, and soldiers, scholars and builders are not checked against food and people

**Status:** closed - umbrella; 602 and 604 are closed, the remaining work is 603

Children:

- 603: population, carrying capacity, famine and migration are national, not per region (people are now tracked per
  tile and migrate; urban share is still the fixed `urban_fraction`, `sim/labour/labour_population.py`)
- 602 (closed): the state's soldiers, officials, scholars and builders are checked against working-age people and food
- 604 (closed): literacy lives in three unlinked places and gates hiring, not research output

Why it mattered: a state reallocating tens of thousands to research and an army must be fed by real surplus, or
face famine and revolt (486); regional variation needs people per region (603).

The note that maize is absent from the crop table and irrigation is a stated non-goal (`sim/world/agriculture.py`) records a fact, not an ask.
