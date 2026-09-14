# CONTRACT v2 for tech-tree branch authors

Read this INSTEAD of CONTRACT.md. It supersedes it. Also read `VOCABULARY.md`
for the ids you may reference, and `../world/geography.json` for where distant
materials are.

## What changed, and why

**1. NOTHING IS UNOBTAINABLE.** The old tree had a "tier 9 unobtainable" for
rubber, quinine, New World crops and so on. That was wrong. You know where those
things are. Rubber grows on Landolphia vines in West Africa, which is coastal
sailing that Hanno did around 500 BC. Saltpetre effloresces on the Gangetic
plain, on a route Rome already sails annually. Potatoes need one successful
voyage and then you grow them. If your technology needs a distant material,
depend on the relevant `exp_*` expedition node and say what it costs. Never
write "unobtainable, so use a substitute" without first stating what it would
take to go and get the real thing.

**2. RESEARCH IS FREE. BUILDING IS NOT.** The founder carries the blueprints.
He does not need to invent the flyer, the lockstitch, the p-n junction or the
three-plate method; he can draw them on the first day. So:
- `ph` (founder hours) is for TEACHING, SPECIFYING and DEBUGGING A FIRST
  ARTICLE, not for discovery. Most nodes should be 20 to 300. Above 600 only
  when the founder must personally sit with a process until it works.
- `build_yrs` is how long it physically takes to construct and commission the
  thing once you have everything in `pre`. Weeks to a couple of years, usually.
- `adopt_yrs` is how long the ECONOMY takes to absorb it, and is only nonzero
  for things that must spread to be useful: a rail network, a grid, a currency,
  interchangeable manufacture. Money cannot buy this down.
- **Never encode a historical delay that was caused by not knowing the answer.**
  If a thing took 300 years historically because a plague killed the people who
  knew, that is not a cost you pay. Put the honest figure in `dev_years` and
  `dev_people` as a REFERENCE ONLY, meaning "from the moment all prerequisites
  existed, N people took M years to work it out", and leave `build_yrs` as the
  actual construction time.

**3. SUBSTITUTION. Prerequisites are not all AND.** A steam engine does not
require coal: charcoal, wood or oil all work, worse. It does not require steel:
bronze, copper or wrought iron all work, worse. Encode that:

```json
"pre": ["cap_tol_10um", "boring_mill"],
"req_any": [
  {"group": "fuel",
   "options": {"coal_coke": 1.0, "mat_charcoal": 0.75, "wood_kg": 0.45, "mat_petroleum_refined": 0.95}},
  {"group": "pressure_vessel",
   "options": {"mat_bulk_steel": 1.0, "mat_wrought_iron": 0.6, "mat_bronze": 0.45, "mat_copper": 0.35}}
]
```
`pre` is AND. Each `req_any` group is OR, and the number is a QUALITY factor:
1.0 is the best option, and a worse one still works but costs more, breaks more
and produces less. Use this wherever a real substitution exists. It is the
single most important schema change in v2.

**4. `gov` AND `sus` ARE GONE. Use `traits` instead.** How a society reacts is a
property of the SOCIETY, not the technology. A printing press is subversive
where a scribal elite controls literacy and unremarkable where it does not. So
tag the technology and let the civilization file decide:

`traits`: any of `military`, `labour_saving`, `information`, `spectacle`,
`inexplicable`, `medical`, `food`, `infrastructure`, `luxury`, `commerce`,
`religious_adjacent`, `weapon_democratising`, `status_threatening`.

Most nodes have one to three. A water-driven trip hammer is
`["labour_saving","infrastructure"]`. A telegraph is
`["information","military","infrastructure"]`. An arc lamp is
`["spectacle","inexplicable","infrastructure"]`.

## Node schema v2

```json
{
  "id": "dom_thing",
  "name": "Plain name",
  "tier": 2,
  "cat": "category",
  "pre": ["id", "id"],
  "req_any": [{"group":"fuel","options":{"a":1.0,"b":0.6}}],
  "traits": ["labour_saving"],
  "kb": "",
  "ph": 80,
  "lab": {"smith": 400},
  "mat": {"iron_bar_kg": 60},
  "cap": 300, "up": 60,
  "build_yrs": 0.5, "adopt_yrs": 0,
  "dev_years": 12, "dev_people": 3,
  "risk": 0.15,
  "rev": 400, "sch": 0, "art": 2,
  "conf": "C",
  "note": "..."
}
```

`yrs` is still accepted and is treated as `build_yrs` if you omit the new
fields, but prefer the new ones.

Allowed trades: labourer, artisan, master, glassblower, smith, carpenter, miner,
scribe, scholar, furnaceman, potter, chemist, machinist, mason, millwright,
plumber, merchant, sailor, engraver, optician, engineer, electrician.

Materials: any key in `../prices.json`. If you need one that is not there, use
the closest and say so in the note. Do not invent a key.

## Quality bar

- **Granularity.** The target is EVERY DISTINCT THING INVENTED BEFORE 1950.
  Do not write one node called "the automobile". Write the frame, the axle, the
  differential, the clutch, the gearbox, the carburettor, the magneto, the
  radiator, the shock absorber, the windscreen wiper, the electric starter.
  A tree with 300 nodes for a domain is closer to right than one with 40.
- **The `note` is the most valuable field.** State the non-obvious kernel: what
  the actual invention is, as opposed to the general idea. "Sewing machine:
  sews cloth" is worthless. "Sewing machine: two inventions, the lockstitch and
  the eye-pointed needle, and either alone is useless" is worth having.
- **No em dashes.** Commas or plain hyphens.
- Output a JSON array and nothing else. It must parse.
