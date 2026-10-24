# Country literacy

`ActorRecord.literacy` on living strata is the current reading state. `CountryLiteracy`
calculates general literacy by weighting those shares by members. Elite literacy weights
the strata with a declared `property_share`; when none are declared it uses the whole
population. Exited and empty strata contribute nothing. Country profiles and civilisation
files supply opening conditions only.

Use `sim.literacy(field, country=None)` to read a country's share and
`sim.set_literacy(field, value, ceiling=1.0, country=None)` to teach its strata.
Omitting the country selects the home country. Actor worlds expose `literacy(field)`
for their own country. Schooling, technology effects, household education spending and
migration all change the same records. The live civilisation dictionary and `_civ_live`
save metadata do not hold literacy totals.

General schools teach non-propertied strata, and elite schools teach the propertied
strata. Their pupils' reading shares also contribute to the population-wide total.
The national ceiling likewise weights each group's own schooling limit by its members.

Scholar hiring and research productivity use the same provisional literacy ratio against
the labour package's reference initial condition and cap. Research productivity multiplies
the work scholar hours accomplish and the progress of another player's research, without
changing the purchased hours. The ratio remains a labour-model approximation rather than
an independently measured research productivity law.

Run `python3 -m sim.tests --only country_literacy_totals,country_literacy_wiring` for the
ownership, country isolation, migration, save round-trip and research regressions.
