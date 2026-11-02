# Economy and labour audit: the prompt to re-run

Run by an orchestrating session after a cleanup round, to check what is left of Complaint 964 and find what the
cleanup exposed. The orchestrator spawns the six reviewers below as Sonnet agents in parallel (CLAUDE.md section 1),
read-only, then opens at least one citation from each report itself before believing it.

## Rules every reviewer gets

- Read `CLAUDE.md` first. Do not edit files. No whole games, no slow suite, no traces; greps, reads and commands
  under a minute. A reviewer may call one pure function with hand-written inputs from a scratch file to confirm a
  bug.
- Docs, docstrings, comments, design notes and complaint files have described this code wrongly before. Treat every
  one as a hypothesis. Every claim in the report cites code that was opened (file:line). A docstring that
  contradicts its code is a finding.
- Classify each finding CONFIRMED (both sides read, or a snippet run) or SUSPECTED, and say whether it can produce
  wrong numbers or is maintainability only.
- Report under about 1800 words, ranked by impact, plus what was not covered.

## The six reviewers

1. **Labour single owner.** For each labour fact (people by trade and area, hours offered, hours hired, wages,
   trainees, staff, army and levy, bonded labour) list every place it is stored and every place it is computed,
   with how copies are kept in step. Trace the wage a household sees, an employer pays and the UI reports; people by
   trade across the core, the engine and demography; hours hired across the core, the ledger and the staff book.
   Check supply against the offers households actually make. Packages: `sim/economy/` labour files and `year_labour`,
   `sim/labour/`, `sim/labour/market/`, `sim/workforce/`.
2. **Goods and prices single owner.** For price, traded volume, unsold, unmet and cost of making, list every writer
   and reader. Trace one good's price from ask to clearing to memory to next year's plan, households and the UI. Find
   missing values read as zero. Check respend rounds against the first round's records. Packages: `sim/economy/`
   goods and memory files, `sim/markets/`, `sim/prices/`. Run
   `grep -rn "solved_prices(\|_price_tables()" sim --include=*.py | grep -v tests` and report every reader.
3. **Architecture.** Count writers and readers per field of `EconomyRecord` and `EconomySetup`; find state on
   `Economy` or the port that is not saved but read across years; caches kept in another object's `__dict__`;
   `getattr`/`hasattr` on fields that always exist; package-wall violations; duplicate implementations of one rule;
   whether `tools/done_check.sh` and `tools/check_module_reads.py` can actually fail on what they claim to measure.
4. **Correctness.** Walk `Economy._run_year` and check units (runs against quantity, hours against people, yield
   factors), budgets and their respend, income and property income, the own plot, money conservation, divisions
   guarded to a wrong value, and order dependence.
5. **Reports against code.** For `Complaints/reports/` (newest first) and `docs/architecture/STATE_OF_THE_PROJECT.md`,
   `ECONOMY_AGENTS.md` and `sim/ARCHITECTURE.md`, check every named file, function, constant and figure against the
   code; classify each MATCHES, STALE or NEVER TRUE.
6. **External models against their source.** For the reports on other simulations
   (`research-reference-economy-models.md`, `research-alternative-economic-models.md`,
   `research-agent-based-economy-design.md`, `docs/architecture/ECONOMY_MODEL_SURVEY.md`, the `model-run-*.md` files)
   and for the code that cites another model (`grep -rnE "Eurace|JMAB|Caiani|Lengnick|BAM|Mark-0" sim --include=*.py`),
   obtain the real source (Eurace@Unibi from ETACE on GitHub, S120/jmab and S120/benchmark, the BAM, Lengnick and
   Mark-0 implementations the run reports name), read it without running it, and say for each claim whether the
   source matches, differs (how) or could not be obtained.

## What the orchestrator does with the reports

Open a citation from each. Add the confirmed findings to Complaint 964 (or close the items fixed), and say in it which
reviewer found what was new.
