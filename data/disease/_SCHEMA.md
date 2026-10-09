# data/disease/ - one file per pathogen

Read by `sim/disease/loader.py`; `python3 sim/simulator.py validate` checks every file here. Design:
`Complaints/reports/epidemic-model-research.md` sections 3 and 11. The file name is the pathogen id.

A pathogen is a chain of stages. A stage with `shape` k is k equal exponential substages, so a bell-shaped
duration needs no engine code. People leave the last stage dead with probability `case_fatality`, else
immune. Never store the size of an epidemic: it falls out of transmissibility, durations and who is immune.

| Field | Meaning |
|---|---|
| `id`, `name`, `tags` | Free tags such as respiratory, waterborne, crowd |
| `stages` | Ordered list of `{id, infectiousness, mean_duration_in_days, shape}`; infectiousness is the share of a full infectious person's contacts |
| `transmissibility_per_day` | Transmissions per fully infectious person per day in a fully mixed, fully susceptible group |
| `case_fatality` | Share of those who finish the last stage who die |
| `immunity` | `{permanent, duration_in_days}`; a finite duration returns people to susceptible |
| `reproduction_number_range` | Sourced range; validate fails a file whose stages and transmissibility imply a number outside it |
| `sources` | One entry per numeric field (`transmissibility_per_day`, `case_fatality`, `immunity`, `reproduction_number_range`, and `stage.<id>` for each stage): `{confidence, source}` |

Confidence tags follow the research report: `read` (figure seen in a source that was opened), `summary`
(seen only in a search summary or second hand), `snippet`, `recalled` (standard literature, not re-checked),
`disputed` (sources disagree), plus `derived` (computed from other fields, say how) and `unsourced`
(placeholder; do not use the file in a scenario until it is replaced). Anything but `read` must be
re-checked before a scenario relies on it.

Not yet expressed: branching stages, routes other than person to person, reservoirs, per-band severity.
