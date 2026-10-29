#!/usr/bin/env bash
# Print one labelled line per done-criteria count for the module registry migration.
# Run from the repository root.
set -u

echo "sim direct bases, MRO length, callable names:" \
  "$(python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len(Sim.__bases__), len(Sim.__mro__), sum(callable(getattr(Sim,n,None)) for n in dir(Sim)))")"

echo "mixin classes in MRO:" \
  "$(python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(sum(k.__name__.endswith('Mixin') for k in Sim.__mro__))")"

coupling_output="$(python3 tools/measure/coupling.py)"
echo "inheritance left on Sim, cross-class references: $(printf '%s\n' "$coupling_output" | head -1)"

echo "module graph (tools/measure/module_graph.py):"
python3 tools/measure/module_graph.py | sed 's/^/  /'

# Owners of money: the ledger (the seats' purses), the actors (sim/agents, each actor's own purse) and markets (sim/economy, the
# agent economy's book). The household facade in sim/agents/household*.py writes the seat's purse, which is the ledger's, so it counts.
outside_money_owners() { grep -v '^sim/tests/' | grep -vE '^sim/(ledger|economy)/' | grep -vE '^sim/agents/[^h]|^sim/agents/h[^o]'; }

echo "direct capital/money writes outside owners:" \
  "$(grep -rnE '\.capital *=[^=]|\.money *=[^=]' sim --include=*.py | outside_money_owners | wc -l)"

echo "book/ledger transfer calls outside owners:" \
  "$(grep -rn 'book\.transfer\|ledger\.transfer' sim --include=*.py | outside_money_owners | wc -l)"

echo "pay_edge calls outside owners:" \
  "$(grep -rn 'pay_edge(' sim --include=*.py | outside_money_owners | wc -l)"

echo "register globals:" \
  "$(grep -rn '^def register\|^    def register' sim --include=*.py | grep -v tests | wc -l)"

echo "test files mentioning Mixin:" \
  "$(grep -rl --include=*.py Mixin sim/tests | wc -l)"

echo "test files importing sim.engine:" \
  "$(grep -rlE --include=*.py 'from sim\.engine|import sim\.engine' sim/tests | wc -l)"

echo "mods importing sim.engine outside mod_code:" \
  "$(grep -rn 'from sim\.engine\|import sim\.engine' mods --include=*.py | grep -v 'mod_code' | wc -l)"
