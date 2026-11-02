#!/usr/bin/env bash
# Print one labelled line per done-criteria count for the module registry migration.
# Run from the repository root.
set -u

echo "sim direct bases, MRO length, callable names:" \
  "$(python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(len(Sim.__bases__), len(Sim.__mro__), sum(callable(getattr(Sim,n,None)) for n in dir(Sim)))")"

mixin_count="$(python3 -c "import sys; sys.path.insert(0,'.'); from sim.engine.core import Sim; print(sum(k.__name__.endswith('Mixin') for k in Sim.__mro__))")"
echo "mixin classes in MRO: $mixin_count"

coupling_output="$(python3 tools/measure/coupling.py)"
echo "inheritance left on Sim, cross-class references: $(printf '%s\n' "$coupling_output" | head -1)"

echo "module graph (tools/measure/module_graph.py):"
python3 tools/measure/module_graph.py | sed 's/^/  /'

module_read_count="$(python3 tools/check_module_reads.py | wc -l | tr -d ' ')"
echo "module reads and sends not declared in their spec: $module_read_count"

# Owners of money: the ledger (the seats' purses), the actors (sim/agents, each actor's own purse) and markets (sim/economy, the
# agent economy's book). The seat's party in sim/agents/household*.py reaches the seat's purse, which is the ledger's, so it counts.
outside_money_owners() { grep -v '^sim/tests/' | grep -vE '^sim/(ledger|economy)/' | grep -vE '^sim/agents/[^h]|^sim/agents/h[^o]'; }

# Files that own a balance (the actor's `money` property, the purses, the seat accounts and the ledger that writes them).
# Any other file that writes `.capital` or `.money` is counted, with its file:line.
money_owner_files='^sim/(agents/base|agents/purses|ledger/ledger|ledger/seat_account)\.py:'
# Files that define a book transfer (`Book`, `Purses.transfer`, the agents' `ledger.transfer`) or the ledger that calls them.
book_owner_files='^sim/(book|agents/purses|agents/ledger|ledger/ledger)\.py:'
outside_owner_files() { grep -v '^sim/tests/' | grep -vE "$1" | cut -d: -f1,2; }

money_writes="$(grep -rnE '\.capital *=[^=]|\.money *=[^=]' sim --include=*.py | outside_owner_files "$money_owner_files")"
money_count="$(printf '%s\n' "$money_writes" | grep -c .)"
echo "direct capital/money writes outside owners: $money_count"
printf '%s\n' "$money_writes" | grep . | sed 's/^/  /'

book_calls="$(grep -rnE '\b(book|ledger|purses)\.(transfer|transfer_many|move_many)\(' sim --include=*.py | outside_owner_files "$book_owner_files")"
echo "book/ledger transfer calls outside owners: $(printf '%s\n' "$book_calls" | grep -c .)"
printf '%s\n' "$book_calls" | grep . | sed 's/^/  /'

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

echo "mods importing sim beyond sim.mod_api:" \
  "$(grep -rn 'from sim\.\|import sim\.' mods --include=*.py | grep -v 'sim\.mod_api' | wc -l)"

legacy_reads="$(grep -rnE '\bview\([[:space:]]*["'"'"']legacy_' sim --include=*.py | grep -v '^sim/tests/' | cut -d: -f1,2)"
legacy_count="$(printf '%s\n' "$legacy_reads" | grep -c .)"
echo "string reads of legacy_* views outside tests: $legacy_count"
printf '%s\n' "$legacy_reads" | grep . | sed 's/^/  /'

wall_output="$(python3 tools/check_package_walls.py)"
wall_status=$?
wall_count="$(printf '%s\n' "$wall_output" | grep -c 'imports sim\.')"
echo "imports of a walled package's submodule from outside it: $wall_count"
printf '%s\n' "$wall_output" | grep . | sed 's/^/  /'

port_reach="$(grep -rnE '(\beconomy|_economy)\.(record|setup)\b' sim/markets --include='port*.py' | cut -d: -f1,2)"
echo "economy record/setup reach-through from sim/markets/port*.py: $(printf '%s\n' "$port_reach" | grep -c .)"
printf '%s\n' "$port_reach" | grep . | sed 's/^/  /'

# Checks that fail the run when above zero; the other counts above are a backlog and stay informational.
failed_checks=()
[ "$mixin_count" -gt 0 ] && failed_checks+=("mixin classes in MRO")
[ "$module_read_count" -gt 0 ] && failed_checks+=("module reads and sends not declared in their spec")
[ "$money_count" -gt 0 ] && failed_checks+=("direct capital/money writes outside owners")
[ "$legacy_count" -gt 0 ] && failed_checks+=("string reads of legacy_* views outside tests")
[ "$wall_status" -ne 0 ] && failed_checks+=("package walls (tools/check_package_walls.py)")

if [ "${#failed_checks[@]}" -eq 0 ]; then
  echo "failing checks: none"
  exit 0
fi
echo "failing checks: $(IFS=';'; printf '%s' "${failed_checks[*]}" | sed 's/;/; /g')"
exit 1
