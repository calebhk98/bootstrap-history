# Resolution audit: combined tech-tree realism review, part 03

**Scope:** only `COMBINED_TECH_TREE_REALISM_REVIEW_part_03.md`: Roman rows
200–209, the complete Later Han section, and the Norse inherited-state rows
present before the file boundary.

**Result:** the concrete defects in this part are fixed. The Roman tail required
five inherited grants, six graph or scope repairs, and one new inherited circus
venue. The Han and Norse baseline-contamination findings had already been
resolved by the explicit, civilization-specific opening states introduced with
the part 02 work; this audit adds regression coverage so they cannot return.

## Roman rows 200–209

- Inns, larger commercial lodging houses, basic gold amalgamation, and large
  market-oriented estates are explicit Roman starting knowledge.
- A Roman circus/racecourse is now a distinct inherited venue. Pari-mutuel
  betting depends on that venue rather than an amphitheatre.
- Commercial theatre depends on the theatre tradition and contract law, not an
  amphitheatre.
- Marine insurance now depends on bankers, maritime lending, and enforceable
  contracts, and its scope is underwriting practice, records, reserves, and
  claims rather than the abstract discovery of risk.
- Paid post now adapts the existing Roman courier network and inns into a public
  relay with custody contracts, schedules, route agents, and delivery records.
- Ancient soft soldering remains inherited. `mt2_solder_lead_tin` now represents
  later composition control and correctly identifies the eutectic as about
  61.9% tin and 38.1% lead at 183 °C.
- A watch case now requires a pocket watch and describes the fitted housing
  around an existing portable movement.

## Later Han opening state

The review was generated before starting knowledge became fully explicit by
civilization. The present Han state no longer receives Roman glass windows,
marble facing, hypocausts, lead plumbing, thermae, Mediterranean writing media,
Roman entertainment, Mediterranean hull forms, murex dyeing, the mature
water-stamped rag-paper recipe, the bundled crank/flywheel/cam package, the
bundled later horse collar, or a navigational compass.

Han retains the historically appropriate underlying capabilities explicitly:
paper as a material and lodestone/directional knowledge. The practical compass,
mature rag-paper production, sternpost rudder, and other later or differently
scoped implementations remain projects rather than inherited gifts. All 34
`GENERIC MISSING GATE` rows in the Han opening-project table are the same graph
defects audited and repaired in part 02; the single `BASELINE CONTAMINATED` row
is no longer exposed by an invalid inherited hull grant.

The report's `PLAUSIBLE TO ATTEMPT / NEEDS NODE-SPECIFIC CHECK` label is a
triage category, not a defect finding. Those 222 rows therefore do not call for
222 automatic removals or historical date locks.

## Norse rows contained in this file

The part ends during the Norse inherited-state table. All definite foreign
baseline grants visible in this portion—Roman glass windows and marble facing,
a standing bureaucracy and tax farming, flush plumbing, hypocausts, thermae,
and enfleurage—are absent from the explicit Norse opening state. Nodes which
were merely flagged for local-form verification are likewise not silently
inherited unless the current scenario data deliberately supplies the applicable
local capability.

## Follow-up boundary

This audit does not claim to resolve the remainder of the Norse review, England,
or the Mexica sections: those occur in parts 04 and 05. Broader decomposition of
`crank_conrod` and additional civilization-localized variants would improve the
tree, but part 03's concrete opening-state defect is fixed by not granting that
overbundled node to Han. Such broader refactoring should not be confused with an
unfixed Han opening grant.

## Regression protection

`sim/tests/test_realism_part03.py` locks the Roman grants and repaired causal
edges, the corrected solder chemistry, the separation of circus, theatre, and
amphitheatre, and the exclusion of the definite Han and Norse contaminants.
