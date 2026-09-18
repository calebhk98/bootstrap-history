# Sim instance-state inventory

**Status:** measured, input to `HOUSEHOLD_EXTRACTION.md`. Every number below
was produced by the scripts described in "Method", run against this checkout
of `sim/engine/`; nothing here is copied from `sim/ARCHITECTURE.md`'s "~157
attributes" figure, and it does not match it exactly (see §0).

## 0. Headline count

**165 distinct instance attributes** exist on a `Sim` object, once every
lazily-created field and every field hidden behind `self.__dict__[...]`
(rather than `self.name`) is counted. `sim/ARCHITECTURE.md`'s "~157" is in the
right neighbourhood but is not this number; the difference is almost entirely
the attributes that a naive grep for `self.name = ...` alone would miss -
because they are only ever touched from `sim/engine/proto/` (via the `s`
parameter, not `self`), or hidden behind `self.__dict__[...]` entirely (see
§1).

## 1. Method

- **Assignment sites**: every file was parsed with `ast` (not regexed), and
  every `Attribute` target of an `Assign`/`AugAssign`/`AnnAssign` was
  collected, scoped to `self` inside `Sim` and its six mixins
  (`EconomyMixin`, `FogMixin`, `GeographyMixin`, `LabourMixin`,
  `ProjectsMixin`, `SocietyMixin`) in `sim/engine/{core,economy,fog,geography,
  labour,projects,society}.py`, and separately to the parameter conventionally
  named `s` (occasionally `sim`/`s0`) that every file under
  `sim/engine/proto/` and `sim/engine/cli.py` uses for the `Sim` instance
  passed in. This second half matters: several `SAVE_FIELDS` members
  (`_dashboard_history`, `_founder_death_aged`, `_founder_death_year`,
  `_said_command_index`, `_said_parallelism`) are never assigned inside the
  six mixin files at all - they are only ever set from `sim/engine/proto/
  dispatch.py` and `state.py` via `s.name = ...`. A scan of `self.` alone
  would have missed them.
- **Scoping check**: `economy.py` defines a second class, `_InvalidatingSet`,
  above `EconomyMixin` in the same file, with its own unrelated `self`
  (`self._on_change`). Class-scoping the AST walk (not just file-scoping it)
  excludes that attribute from this inventory, correctly.
- **`getattr(self, "name", default)` sites**: collected the same way, giving
  the lazy-creation call sites the brief describes.
- **`SAVE_FIELDS`**: read directly out of the `SAVE_FIELDS` tuple in
  `sim/engine/proto/saveload.py` by parsing that one assignment with `ast`,
  not by eyeballing it. **Finding, in passing**: the tuple's source lists
  `"teaching_hours_this_year"` twice (once after `"commissioned"`, again
  after `"wage_hours_this_year"`); it is 99 string literals naming 98 distinct
  fields. Harmless (`save_state`/`load_state` just iterate it), but worth a
  one-line fix.
- **Hidden attributes via `self.__dict__[...]`**: three attributes are never
  written as `self.name = ...` or read as `self.name` at all, so the two
  passes above cannot see them by construction. They were found by grepping
  `\.__dict__` across `sim/engine/`: `revealed` (`sim/engine/fog.py`) is a
  `@property` whose real backing field is `self.__dict__["_revealed"]`,
  written that way specifically so the property can enforce ratchet
  (union-only) semantics without recursing into its own setter; and
  `_foreign_institution_cache` / `_foreign_only_cache` (`sim/engine/
  society.py`) use `self.__dict__.setdefault(...)` as a shorthand lazy-cache
  idiom. All three are included in the 165 and in the table below, with
  `_revealed` given its own row distinct from the public `revealed` property
  it backs. A repo-wide check also ruled out `vars(self)`, `__setattr__`, and
  dynamic (non-constant-string) `setattr`/`getattr` names as further hiding
  places - the only dynamic `setattr` in the package is `saveload.py`'s
  `load_state` looping over `SAVE_FIELDS`, which is already fully enumerated.
- **"First set" (column 2)**: `__init__` (`sim/engine/core.py`) if any
  assignment to the name appears there; otherwise the earliest
  `getattr(self/s, "name", default)` call site, labelled "lazy via getattr";
  a residual handful (`_agri_mechanisation_ids`, `_diffusible_ids_cache`,
  `_stock_throttle_cache`, `done_year`) are set unconditionally outside
  `__init__` with **no** getattr guard anywhere - three are
  `self.__dict__.get(...)`-guarded caches (an equivalent lazy idiom spelled
  differently) and the fourth, `done_year`, is (re)initialised in `run()`,
  which means **`__init__` does not fully initialise a `Sim`** -
  `run()` does additional setup (`self.goal`, `self.done_year = {}`) before
  the year loop starts. `_revealed`/`_foreign_institution_cache`/
  `_foreign_only_cache` are marked "special" and cited by their `__dict__`
  line instead, since neither mode applies literally.
- **Column 4/5 (files / sites)**: every `self.name`, `s.name` (proto/cli),
  read or write, plus every `getattr`/`setattr`/`hasattr`/`del` call naming
  it, across the 23 files of `sim/engine/` (the 7 above plus the 16 files
  under `sim/engine/proto/`) and `sim/engine/cli.py`. `sim/engine/protocol.py`
  is a pure re-export shim (confirmed by reading it) and contributes nothing;
  `commodities.py`, `data.py`, and `settings.py` were checked and confirmed to
  never reference a `Sim` instance directly, so they are correctly absent
  from every file-count in this table.
- **Category**: assigned by reading each attribute's defining comment (most
  household fields carry one - this codebase's comments are load-bearing per
  `CLAUDE.md` §7) plus its actual call sites, not by name-guessing.

Precisely: **152** names get a plain `self.name = ...`/`self.name += ...`
somewhere in the seven mixin/core files (this excludes `_InvalidatingSet`'s
own unrelated `self._on_change`, defined above `EconomyMixin` in the same
file - see the scoping check above); **2** more (`end_year`, `fog`) appear in
those same seven files only via `getattr(self, ...)`, never a plain
assignment. That is **154** names visible from `self`-scope alone. A further
**8** names (`_dashboard_history`, `_founder_death_aged`,
`_founder_death_cache`, `_founder_death_year`, `_goal_critical_floor`,
`_said_command_index`, `_said_parallelism`, `_said_stack_caution`) are never
touched via `self` anywhere in the six mixins or `core.py` at all - they only
exist via `s.name = ...` / `getattr(s, ...)` in `sim/engine/proto/`. That is
**162** names from static+dynamic scanning of ordinary attribute syntax
across every file in the package. The remaining **3**
(`_revealed`/`_foreign_institution_cache`/`_foreign_only_cache`) are the
`self.__dict__[...]`-hidden ones from the bullet above, invisible to both of
the scans above by construction. **154 + 8 + 3 = 165**, the de-duplicated
total every count below is built from.

## 2. The full table

| Name | First set | In `SAVE_FIELDS`? | Files | Sites | Category | Notes / non-person-owner flag |
|---|---|---|---|---|---|---|
| `_agri_mechanisation_ids` | set outside `__init__`, no getattr guard (sim/engine/society.py:875, in `agrarian_slack`) | no | 1 | 1 | INTERNAL (keyed off world/scenario (nodes only)) | fixed set of agri-mechanisation node ids, derived only from the static tree |
| `_cap_factor` | `__init__` (sim/engine/core.py:92) | no | 2 | 5 | INTERNAL (keyed off household (done/granted/practice/operating)) | capability_factor() memo |
| `_dashboard_history` | lazy via getattr (sim/engine/proto/dispatch.py:2295) | yes | 2 | 4 | INTERNAL (keyed off household (snapshots of household portfolio)) | one portfolio snapshot per year, for `changes`/`economy` |
| `_demand_by_emp_key_cache` | lazy via getattr (sim/engine/economy.py:3391) | no | 1 | 2 | INTERNAL (keyed off household) | material demand grouped by employment key |
| `_demand_by_tag_cache` | lazy via getattr (sim/engine/economy.py:3320) | no | 1 | 2 | INTERNAL (keyed off household) | material demand grouped by supply tag |
| `_diffusible_ids_cache` | set outside `__init__`, no getattr guard (sim/engine/society.py:1314, in `_diffusible_ids`) | no | 1 | 1 | INTERNAL (keyed off world/scenario (nodes only)) | fixed set of diffusible-tech node ids, derived only from the static tree |
| `_done_seq` | `__init__` (sim/engine/core.py:91) | no | 2 | 4 | INTERNAL (keyed off household (tracks `done`)) | version counter that invalidates caches when `done` changes |
| `_electricity_load_ids_cache` | lazy via getattr (sim/engine/economy.py:3060) | no | 1 | 2 | INTERNAL (keyed off world/scenario (nodes only)) | fixed set of electricity-gated node ids, derived only from the static tree |
| `_food_diffusion_said` | `__init__` (sim/engine/core.py:250) | no | 2 | 3 | INTERNAL (keyed off world (population-wide)) | last year a food-diffusion note fired |
| `_food_pop_bonus_applied` | lazy via getattr (sim/engine/society.py:1443) | yes | 1 | 3 | INTERNAL (keyed off world (population-wide bonus, but the flag itself lives on the Sim instance)) | whether this year's food-diffusion population bonus has already been applied |
| `_foreign_institution_cache` | special (see note) (sim/engine/society.py:1561) | no | 1 | 1 | INTERNAL (keyed off world/scenario (civ+nodes only)) | per-node memo of a string match against civ id + node name |
| `_foreign_only_cache` | special (see note) (sim/engine/society.py:1577) | no | 1 | 1 | INTERNAL (keyed off world/scenario (civ+nodes only)) | per-node memo of a string match against civ id + node name |
| `_founder_death_aged` | lazy via getattr (sim/engine/proto/state.py:279) | yes | 2 | 2 | INTERNAL (keyed off household (and person-specific, see summary)) | founder's age at death, cached for --session resume |
| `_founder_death_cache` | lazy via getattr (sim/engine/proto/state.py:282) | no | 1 | 2 | INTERNAL (keyed off household (and person-specific, see summary)) | fallback: founder's death year/age recovered by scanning the log |
| `_founder_death_year` | lazy via getattr (sim/engine/proto/state.py:281) | yes | 2 | 2 | INTERNAL (keyed off household (and person-specific, see summary)) | year the founder died, cached for --session resume |
| `_goal_closure` | lazy via getattr (sim/engine/labour.py:1850) | no | 4 | 11 | INTERNAL (keyed off household (via the chosen goal)) | prerequisite closure of self.goal, cached |
| `_goal_critical_floor` | lazy via getattr (sim/engine/proto/score.py:94) | no | 1 | 2 | INTERNAL (keyed off household (via the chosen goal)) | cached critical-path floor for self.goal |
| `_goods_cat_state_cache` | lazy via getattr (sim/engine/economy.py:1249) | no | 1 | 2 | INTERNAL (keyed off household) | cache keyed on (year, _operating_ver) |
| `_home_centroid` | `__init__` (sim/engine/core.py:304) | no | 2 | 2 | INTERNAL (keyed off world/scenario) | this civilisation's home coordinate, fixed for the run |
| `_labour_pressure` | lazy via getattr (sim/engine/labour.py:253) | no | 1 | 3 | INTERNAL (keyed off household) | per-trade record of how hard THIS household has recently bid up a trade's wage |
| `_last_buy_refusal` | lazy via getattr (sim/engine/proto/dispatch.py:817) | no | 2 | 4 | INTERNAL (keyed off household (this household's last buy attempt)) | reason the last `buy slaves` call refused, for the next error message |
| `_last_subst_gap` | lazy via getattr (sim/engine/projects.py:1657) | no | 1 | 3 | INTERNAL (keyed off household (this household's own project explanation)) | cached substitution-gap explanation for `why` |
| `_literacy_said` | `__init__` (sim/engine/core.py:249) | no | 2 | 3 | INTERNAL (keyed off world (civ literacy)) | last year a literacy-census note fired |
| `_mat_unlock` | `__init__` (sim/engine/core.py:309) | no | 2 | 3 | INTERNAL (keyed off world/scenario) | node id -> located_materials key index |
| `_material_demand_cache` | lazy via getattr (sim/engine/economy.py:3298) | no | 1 | 3 | INTERNAL (keyed off household (from operating/employees)) | this year's material-demand snapshot, set by resource_throttle() |
| `_material_stock_ledger` | lazy via getattr (sim/engine/economy.py:2684) | yes | 1 | 3 | INTERNAL (keyed off household (owned inventory - this one arguably belongs in HOUSEHOLD outright, see summary)) | tonnes on hand, by material |
| `_mineral_scale` | `__init__` (sim/engine/core.py:323) | no | 2 | 2 | INTERNAL (keyed off world/scenario (geo+civ only, same for every actor of this civ)) | per-material market-access scale from home_regions/reach, fixed for the run |
| `_nodes_by_cat_cache` | lazy via getattr (sim/engine/economy.py:1291) | no | 1 | 2 | INTERNAL (keyed off world/scenario (nodes only)) | node-id-by-category index, derived only from the static tree |
| `_operating_ver` | lazy via getattr (sim/engine/economy.py:936) | no | 1 | 4 | INTERNAL (keyed off household (tracks `operating`)) | version counter that invalidates caches when `operating` changes |
| `_pop_recovery_years` | `__init__` (sim/engine/core.py:72) | no | 2 | 5 | WORLD | time-constant for the whole society's demographic recovery from the worst shock endured |
| `_pop_scale_base` | `__init__` (sim/engine/core.py:70) | no | 3 | 8 | WORLD | pop_scale's steady-state baseline before the current deficit is applied |
| `_pop_tech_pending` | `__init__` (sim/engine/core.py:79) | no | 2 | 5 | WORLD | queued population-raising effects of technologies, applied to the whole society's population |
| `_practice_cache` | lazy via getattr (sim/engine/economy.py:2052) | no | 1 | 2 | INTERNAL (keyed off household, but see `granted` ambiguity) | cache of which granted nodes are 'practisable', keyed on len(granted) |
| `_regions` | `__init__` (sim/engine/core.py:302) | no | 2 | 10 | INTERNAL (keyed off world/scenario) | geography.json's regions, minus '_'-prefixed keys |
| `_rev_up_candidates_cache` | lazy via getattr (sim/engine/economy.py:2111) | no | 1 | 2 | INTERNAL (keyed off household) | candidate nodes for revenue/upkeep, keyed on operating/practice |
| `_revealed` | special (see note) (sim/engine/fog.py:112) | no | 1 | 3 | INTERNAL (keyed off household (fog-of-war visibility)) | the real backing set for the `revealed` property; only ever touched via self.__dict__, never self._revealed |
| `_said_autoopen` | lazy via getattr (sim/engine/projects.py:1194) | yes | 1 | 2 | INTERNAL (keyed off household (operating/done)) | which nodes auto-open has already announced, per node |
| `_said_command_index` | lazy via getattr (sim/engine/proto/state.py:312) | yes | 1 | 2 | INTERNAL (keyed off session (command count, not economic)) | whether the 'you have now typed N commands' note has fired |
| `_said_condition` | `__init__` (sim/engine/core.py:251) | no | 2 | 2 | INTERNAL (keyed off world (society-wide hazards, mostly)) | hazard-condition messages already printed once |
| `_said_confiscation_band` | `__init__` (sim/engine/core.py:248) | no | 2 | 4 | INTERNAL (keyed off household (confiscation_risk scales with household wealth/eminence)) | last confiscation-risk band warned about for this household |
| `_said_debasement` | lazy via getattr (sim/engine/society.py:2499) | yes | 1 | 3 | INTERNAL (keyed off world (money_real)) | last year a debasement note fired |
| `_said_deputies` | lazy via getattr (sim/engine/core.py:801) | yes | 1 | 2 | INTERNAL (keyed off household (directors_extra)) | last deputies/directors band already warned about |
| `_said_eminence` | `__init__` (sim/engine/core.py:243) | no | 1 | 3 | INTERNAL (keyed off household (eminence)) | last eminence band already warned about |
| `_said_near_limit` | lazy via getattr (sim/engine/economy.py:462) | yes | 1 | 5 | INTERNAL (keyed off household (credit_limit)) | whether 'near credit limit' was already warned about |
| `_said_notice_approach` | `__init__` (sim/engine/core.py:246) | no | 2 | 3 | INTERNAL (keyed off household (state_notice scales with household size)) | last state-notice band warned about for this household |
| `_said_output` | lazy via getattr (sim/engine/society.py:2475) | yes | 1 | 2 | INTERNAL (keyed off world (output_factor)) | which output-factor drops have already been announced |
| `_said_parallelism` | lazy via getattr (sim/engine/proto/dispatch.py:357) | yes | 1 | 2 | INTERNAL (keyed off household (this household's own active projects)) | whether the >=2-year-project parallelism note has fired |
| `_said_requisition` | `__init__` (sim/engine/core.py:245) | no | 2 | 3 | INTERNAL (keyed off household (state_notice/requisition scale with household wealth)) | last year a state-requisition note fired for this household |
| `_said_scandal` | lazy via getattr (sim/engine/core.py:2110) | yes | 1 | 3 | INTERNAL (keyed off household (scandal)) | last scandal band already warned about |
| `_said_stack_caution` | lazy via getattr (sim/engine/proto/techtree.py:611) | no | 1 | 2 | INTERNAL (keyed off household (this household's own portfolio)) | whether a tech-stacking leverage caution has fired |
| `_said_wage_cascade` | `__init__` (sim/engine/core.py:244) | no | 1 | 3 | INTERNAL (keyed off world (wage_index)) | last year a wage-cascade note fired |
| `_spend_this_year` | `__init__` (sim/engine/core.py:242) | no | 1 | 5 | INTERNAL (keyed off household) | running tally this year, promoted to spend_last_year at year end |
| `_staff_scale` | `__init__` (sim/engine/core.py:241) | no | 2 | 3 | INTERNAL (keyed off household) | pre-first-step default for staff_capacity(); overwritten every step |
| `_stock_throttle_cache` | set outside `__init__`, no getattr guard (sim/engine/economy.py:3261, in `resource_throttle`) | no | 1 | 2 | INTERNAL (keyed off household) | memoised (throttle, binding) result for that signature |
| `_stock_throttle_sig` | lazy via getattr (sim/engine/economy.py:3208) | no | 1 | 4 | INTERNAL (keyed off household (industrial/lab need, mines, forest_ha, nitre_bed_m2, stock)) | signature of the inputs the last throttle computation used |
| `_wage_index_base` | `__init__` (sim/engine/core.py:57) | no | 1 | 3 | WORLD | wage_index's pre-shock baseline; same civ-wide scope as wage_index |
| `_win_condition_keys` | `__init__` (sim/engine/core.py:36) | no | 1 | 2 | INTERNAL (keyed off world/scenario) | sorted node ids that carry a win_condition, fixed for the run |
| `active` | `__init__` (sim/engine/core.py:95) | yes | 9 | 67 | HOUSEHOLD | the household's in-progress projects (ph_left, years_elapsed, spent) |
| `artisans` | `__init__` (sim/engine/core.py:104) | yes | 9 | 33 | HOUSEHOLD | owned staff pool |
| `atrocity` | `__init__` (sim/engine/core.py:288) | yes | 1 | 1 | HOUSEHOLD | count of atrocities committed (never scored as a benefit) |
| `binding` | `__init__` (sim/engine/core.py:340) | yes | 5 | 25 | HOUSEHOLD | what is currently binding the household's output (material name or None) |
| `bondage_debt` | `__init__` (sim/engine/core.py:163) | yes | 3 | 7 | HOUSEHOLD | outstanding bondage debt |
| `bondage_years_left` | `__init__` (sim/engine/core.py:162) | yes | 4 | 12 | HOUSEHOLD | years of bondage service still owed by/for the household |
| `bountied` | `__init__` (sim/engine/core.py:265) | yes | 4 | 9 | HOUSEHOLD | which bounty node ids the household has already collected |
| `bounties_paid` | `__init__` (sim/engine/core.py:264) | yes | 2 | 2 | HOUSEHOLD | count of bounties the household has been paid |
| `bounty_set` | `__init__` (sim/engine/core.py:43) | no | 1 | 2 | SCENARIO | which node ids are being tracked for bounty scoring, chosen at setup and never mutated |
| `bribes_ytd` | `__init__` (sim/engine/core.py:283) | yes | 3 | 10 | HOUSEHOLD | money spent on bribes this year |
| `capital` | `__init__` (sim/engine/core.py:89) | yes | 10 | 172 | HOUSEHOLD | money on hand |
| `cfg` | `__init__` (sim/engine/core.py:41) | no | 11 | 63 | SCENARIO | run configuration dict (merged DEFAULTS + overrides) |
| `civ` | `__init__` (sim/engine/core.py:44) | no | 15 | 82 | SCENARIO | loaded civilisation record (starting techs, weights, geography ids) |
| `commissioned` | `__init__` (sim/engine/core.py:122) | yes | 2 | 3 | HOUSEHOLD | cumulative hours bought by the job, by trade |
| `contract_hours` | `__init__` (sim/engine/core.py:121) | yes | 2 | 9 | HOUSEHOLD | hours bought by the job this year, by trade |
| `contract_projects` | `__init__` (sim/engine/core.py:119) | no | 1 | 1 | HOUSEHOLD | projects the household staffs by the job rather than with employees |
| `credit_frozen_until` | `__init__` (sim/engine/core.py:164) | yes | 4 | 14 | HOUSEHOLD | year until which nobody will fund new work for this household |
| `dead_reason` | `__init__` (sim/engine/core.py:255) | yes | 4 | 8 | HOUSEHOLD | why the run ended -- **mostly generic (bankruptcy, denunciation, catastrophe) but one value ('the founder died without training successors') is person-specific and needs a non-person equivalent or removal** |
| `director_hours_spent_founder` | `__init__` (sim/engine/core.py:261) | yes | 1 | 2 | HOUSEHOLD | hours the founder personally spent directing -- **FLAG: named for a single director/founder; a firm/government has no one person whose hours this is** |
| `directors_extra` | `__init__` (sim/engine/core.py:105) | yes | 5 | 18 | HOUSEHOLD | owned staff pool (management capacity) |
| `done` | `__init__` (sim/engine/core.py:90) | yes | 11 | 106 | HOUSEHOLD | tech/institutions this household possesses (own work + granted) |
| `done_year` | set outside `__init__`, no getattr guard (sim/engine/cli.py:916, in `cmd_play`) | yes | 7 | 11 | HOUSEHOLD | year each of the household's done nodes was completed |
| `economy` | `__init__` (sim/engine/core.py:259) | yes | 3 | 10 | WORLD | size of the imperial economy relative to 100 AD |
| `eminence` | `__init__` (sim/engine/core.py:280) | yes | 5 | 21 | HOUSEHOLD | standing: how conspicuous the household has become |
| `employees` | `__init__` (sim/engine/core.py:107) | yes | 8 | 62 | HOUSEHOLD | owned staff by trade |
| `end_year` | lazy via getattr (sim/engine/cli.py:1244) | no | 5 | 12 | SCENARIO | computed horizon (start_year+horizon), a session parameter set by cli.py, not saved |
| `events` | `__init__` (sim/engine/core.py:40) | no | 2 | 7 | SCENARIO | whether random events fire this run, set at construction |
| `failed_attempts` | `__init__` (sim/engine/core.py:96) | yes | 5 | 14 | HOUSEHOLD | count of failed attempts per node, for this household's retry-risk math |
| `familiarity` | `__init__` (sim/engine/core.py:281) | yes | 3 | 5 | HOUSEHOLD | standing: how used to this actor the world has become |
| `farm_hectares` | lazy via getattr (sim/engine/economy.py:1373) | yes | 2 | 4 | HOUSEHOLD | owned farmland |
| `fog` | lazy via getattr (sim/engine/cli.py:1253) | no | 10 | 43 | SCENARIO | fog-of-war on/off, a menu choice for the whole playthrough (see also 'revealed' which IS household state) |
| `forest_ha` | `__init__` (sim/engine/core.py:326) | yes | 4 | 12 | HOUSEHOLD | owned coppice, hectares |
| `forgotten` | `__init__` (sim/engine/core.py:147) | yes | 5 | 8 | HOUSEHOLD | household nodes destroyed by a sacking, with the year |
| `founder_alive` | `__init__` (sim/engine/core.py:252) | yes | 10 | 23 | HOUSEHOLD | whether the founder is alive -- **FLAG: literally a single mortal person's vital status; meaningless for a firm or government as written** |
| `freedmen` | `__init__` (sim/engine/core.py:285) | yes | 5 | 16 | HOUSEHOLD | former slaves the household has freed |
| `geo` | `__init__` (sim/engine/core.py:301) | no | 2 | 4 | SCENARIO | geography.json, loaded once |
| `goal` | lazy via getattr (sim/engine/proto/dispatch.py:79) | no | 12 | 33 | SCENARIO | the chosen win-condition node id for this playthrough (AMBIGUOUS - see summary: a multi-actor world would want this per-actor) |
| `goal_year` | `__init__` (sim/engine/core.py:256) | yes | 6 | 24 | HOUSEHOLD | the year THIS household reached its goal |
| `gov` | `__init__` (sim/engine/core.py:253) | yes | 3 | 3 | HOUSEHOLD | standing/political capital with the state, accrued via state_interest() from institutions the household runs |
| `granted` | `__init__` (sim/engine/core.py:94) | yes | 10 | 36 | HOUSEHOLD | starting techs this civilisation already had for free (AMBIGUOUS - see summary: this is a civ fact mirrored per-Sim, not really per-actor) |
| `granted_staff` | lazy via getattr (sim/engine/labour.py:1979) | yes | 1 | 3 | HOUSEHOLD | staff granted outright by an institution (kept separate from scholars/artisans totals) |
| `hour_allocations` | `__init__` (sim/engine/core.py:139) | yes | 3 | 12 | HOUSEHOLD | the household's standing per-project hour directives |
| `hours_this_year` | lazy via getattr (sim/engine/proto/state.py:612) | yes | 2 | 2 | HOUSEHOLD | last year's founder-hours accounting -- **FLAG: 'founder-hours' - needs a generalised 'owner labour hours' framing for a non-person owner** |
| `insolvent_years` | lazy via getattr (sim/engine/core.py:882) | yes | 4 | 16 | HOUSEHOLD | consecutive years the household has run at a loss |
| `inst_units` | lazy via getattr (sim/engine/projects.py:203) | yes | 1 | 6 | HOUSEHOLD | how many units of each scalable institution the household has founded |
| `interest_paid` | lazy via getattr (sim/engine/economy.py:428) | yes | 4 | 5 | HOUSEHOLD | interest the household has paid on debt |
| `last_military_demand` | `__init__` (sim/engine/core.py:247) | no | 2 | 3 | HOUSEHOLD | last year the household itself was subject to a military levy |
| `last_patron_death` | lazy via getattr (sim/engine/society.py:2574) | yes | 1 | 2 | HOUSEHOLD | last time a patron of the household died -- **mild flag: 'patron' is a Roman social-network concept a firm/government could still have (a backer/sponsor), so this generalises with only a naming question** |
| `last_settlement` | `__init__` (sim/engine/core.py:263) | yes | 2 | 3 | HOUSEHOLD | last year the household's debts were settled |
| `last_taught` | `__init__` (sim/engine/core.py:150) | yes | 1 | 2 | HOUSEHOLD | year auto_train last taught a trade, per trade |
| `last_withdrawal` | lazy via getattr (sim/engine/society.py:159) | yes | 1 | 3 | HOUSEHOLD | last time the household withdrew money (context: cli.py `withdraw` command) |
| `life_left` | `__init__` (sim/engine/core.py:268) | yes | 2 | 6 | HOUSEHOLD | founder's remaining lifespan -- **FLAG: elite-male-aged-35 mortality draw; only meaningful for a single mortal person** |
| `living_cost_paid` | `__init__` (sim/engine/core.py:287) | yes | 1 | 2 | HOUSEHOLD | subsistence cost paid this year -- **'living cost' is written as a person's subsistence; a firm/government has overhead, not personal upkeep - needs a decision** |
| `log` | `__init__` (sim/engine/core.py:254) | yes | 8 | 83 | HOUSEHOLD | the household's own narrative event log, read back by `log`/`state` |
| `manual` | `__init__` (sim/engine/core.py:50) | no | 4 | 18 | SCENARIO | constructor flag selecting player vs optimizer default policy; changes what policy defaults to, is not itself economic state |
| `manumitted_total` | `__init__` (sim/engine/core.py:286) | yes | 3 | 4 | HOUSEHOLD | lifetime count of manumissions |
| `market_pressure` | `__init__` (sim/engine/core.py:328) | yes | 2 | 6 | HOUSEHOLD | how hard THIS household has recently leaned on the slave market |
| `mine_cost_paid` | `__init__` (sim/engine/core.py:337) | yes | 1 | 2 | HOUSEHOLD | cumulative capital sunk into mines |
| `mine_pending` | `__init__` (sim/engine/core.py:335) | yes | 2 | 9 | HOUSEHOLD | capital sunk into mines not yet producing |
| `mine_ready` | `__init__` (sim/engine/core.py:336) | yes | 1 | 1 | HOUSEHOLD | year each pending mine comes on stream |
| `mine_tranches` | lazy via getattr (sim/engine/economy.py:3961) | yes | 3 | 10 | HOUSEHOLD | mine construction tranches in progress (paired with mine_pending/mines) |
| `mines` | `__init__` (sim/engine/core.py:334) | yes | 3 | 13 | HOUSEHOLD | the household's own mine workings |
| `money_real` | `__init__` (sim/engine/core.py:257) | yes | 3 | 4 | WORLD | purchasing power of a denarius (currency debasement), a monetary fact of the whole civilisation |
| `mothballed` | `__init__` (sim/engine/core.py:146) | yes | 6 | 17 | HOUSEHOLD | household's completed works shut down on purpose |
| `nitre_bed_m2` | `__init__` (sim/engine/core.py:327) | yes | 3 | 9 | HOUSEHOLD | owned saltpetre beds, m^2 |
| `nodes` | `__init__` (sim/engine/core.py:22) | no | 11 | 180 | SCENARIO | the tech tree itself, loaded once, shared by every actor |
| `opened_year` | `__init__` (sim/engine/core.py:148) | yes | 4 | 6 | HOUSEHOLD | year each of the household's ventures first opened |
| `operating` | `__init__` (sim/engine/core.py:161) | yes | 10 | 63 | HOUSEHOLD | the set of ventures the household actually runs (revenue/upkeep follow this) |
| `order` | `__init__` (sim/engine/core.py:38) | no | 6 | 13 | SCENARIO | topological build order of nodes, static |
| `output_factor` | `__init__` (sim/engine/core.py:260) | yes | 4 | 15 | WORLD | real output factor, crushed by war/plague for the whole society |
| `paid_towards` | `__init__` (sim/engine/core.py:149) | yes | 4 | 10 | HOUSEHOLD | denarii sunk into a household project before it stalled |
| `policy` | `__init__` (sim/engine/core.py:174) | yes | 5 | 27 | HOUSEHOLD | the household's own automation switches (auto_hire, auto_mine, ...) -- **one sub-key, auto_court_heir ('court a dead patron's successor'), is written for a mortal successor; needs a decision for a non-person owner** |
| `pop_deficit` | `__init__` (sim/engine/core.py:71) | no | 2 | 9 | WORLD | how far below trend the WHOLE society's population currently sits (explicitly: 'a hit to the whole labour market, not only to you') |
| `pop_scale` | `__init__` (sim/engine/core.py:59) | no | 5 | 19 | WORLD | population of the whole civilisation relative to its 65M reference, drives every wage/market calc economy-wide |
| `price_index` | `__init__` (sim/engine/core.py:55) | no | 8 | 48 | WORLD | this civilisation's price level relative to Rome 100 AD |
| `protection` | `__init__` (sim/engine/core.py:282) | yes | 5 | 20 | HOUSEHOLD | standing: patrons, office, citizenship, priesthood |
| `reputation` | `__init__` (sim/engine/core.py:274) | yes | 10 | 35 | HOUSEHOLD | standing: ability to be believed and followed |
| `res` | `__init__` (sim/engine/core.py:293) | no | 2 | 2 | SCENARIO | resources.json, loaded once |
| `revealed` | lazy via getattr (sim/engine/fog.py:126) | yes | 4 | 11 | HOUSEHOLD | fog-of-war: which nodes are visible to this household (ratchet property; real store is _revealed, see note) |
| `rng` | `__init__` (sim/engine/core.py:39) | no | 6 | 16 | SCENARIO | the shared random generator; mutable state but an engine resource, not economic-actor state |
| `scandal` | `__init__` (sim/engine/core.py:279) | yes | 7 | 33 | HOUSEHOLD | standing: accumulated unexplained/alarming behaviour |
| `scandal_last_year` | lazy via getattr (sim/engine/proto/state.py:759) | no | 2 | 6 | HOUSEHOLD | last year's scandal reading, used to report this year's delta |
| `scholars` | `__init__` (sim/engine/core.py:103) | yes | 5 | 20 | HOUSEHOLD | owned staff pool |
| `shortages` | `__init__` (sim/engine/core.py:338) | yes | 3 | 4 | HOUSEHOLD | tally of which material bound in which year for this household (diagnostic, but per-household - see summary) |
| `shut_for_staff` | lazy via getattr (sim/engine/projects.py:564) | yes | 3 | 9 | HOUSEHOLD | household ventures currently shut for lack of staff |
| `slaves` | `__init__` (sim/engine/core.py:284) | yes | 6 | 21 | HOUSEHOLD | owned slaves |
| `spend_last_year` | lazy via getattr (sim/engine/proto/dispatch.py:1065) | yes | 3 | 5 | HOUSEHOLD | last year's spend (spend_this_year, promoted at year end) |
| `stalled` | `__init__` (sim/engine/core.py:262) | yes | 1 | 7 | HOUSEHOLD | count of stalled years |
| `state_capacity` | `__init__` (sim/engine/core.py:58) | no | 4 | 7 | WORLD | the state's own administrative/fiscal capacity, explicitly named in the WORLD example set |
| `teaching_hours_this_year` | `__init__` (sim/engine/core.py:123) | yes | 3 | 7 | HOUSEHOLD | hours the household spent teaching this year |
| `throttle` | `__init__` (sim/engine/core.py:339) | yes | 4 | 7 | HOUSEHOLD | this year's output throttle from the household's own material/labour binding |
| `total_spend` | `__init__` (sim/engine/core.py:266) | yes | 2 | 3 | HOUSEHOLD | lifetime spend |
| `trade_hours_used` | `__init__` (sim/engine/core.py:145) | yes | 3 | 7 | HOUSEHOLD | hours consumed by the household's projects this year, by trade |
| `trade_introduced_year` | `__init__` (sim/engine/core.py:117) | yes | 2 | 3 | HOUSEHOLD | when the household first taught a trade (companion to trades_created) |
| `trade_schools` | lazy via getattr (sim/engine/labour.py:1060) | yes | 2 | 5 | HOUSEHOLD | owned trade-school capacity |
| `trades_created` | `__init__` (sim/engine/core.py:109) | yes | 5 | 11 | HOUSEHOLD | trades the household has taught into existence (AMBIGUOUS - see summary: becomes a society-wide fact once taught) |
| `trades_endemic` | `__init__` (sim/engine/core.py:118) | yes | 3 | 4 | HOUSEHOLD | which taught trades the society has since supplied on its own (companion to trades_created) |
| `training` | `__init__` (sim/engine/core.py:93) | yes | 4 | 15 | HOUSEHOLD | [artisan_capacity, year_matures] pairs the household has queued |
| `verbose` | `__init__` (sim/engine/core.py:42) | no | 1 | 1 | SCENARIO | CLI verbosity flag, set at construction |
| `w` | `__init__` (sim/engine/core.py:51) | no | 5 | 23 | SCENARIO | alias for civ['values'], the scoring/weights table |
| `wage_hours_this_year` | lazy via getattr (sim/engine/core.py:1185) | yes | 5 | 13 | HOUSEHOLD | hours the household has sold as wages this year (prevents double-selling) |
| `wage_index` | `__init__` (sim/engine/core.py:56) | no | 6 | 16 | WORLD | this civilisation's wage level, moved by demography/scarcity, applies to every hire in the world, not just the household |
| `wages_earned` | lazy via getattr (sim/engine/labour.py:907) | yes | 1 | 2 | HOUSEHOLD | wages the household earned selling its own hours |
| `wages_paid` | `__init__` (sim/engine/core.py:120) | yes | 1 | 1 | HOUSEHOLD | wages paid out this year |
| `wages_prepaid` | `__init__` (sim/engine/core.py:151) | yes | 4 | 10 | HOUSEHOLD | first-year wages already advanced by `hire` |
| `work_trade` | `__init__` (sim/engine/core.py:144) | yes | 2 | 8 | HOUSEHOLD | which trade the household's 'work' allocation sells hours as |
| `worker_housing_places` | lazy via getattr (sim/engine/economy.py:1398) | yes | 3 | 4 | HOUSEHOLD | owned worker housing capacity |
| `year` | `__init__` (sim/engine/core.py:80) | yes | 12 | 106 | WORLD | the calendar year, shared by the whole simulation |


## 3. Counts per category

| Category | Count |
|---|---|
| HOUSEHOLD | 84 |
| INTERNAL | 53 |
| SCENARIO | 15 |
| WORLD | 13 |
| **Total** | **165** |

98 of the 165 (the 98 distinct names in `SAVE_FIELDS`) persist across a save;
67 do not. Of the 67 that don't: most of the SCENARIO/WORLD group is either
reloaded from the civ/geo/resource files on construction or reconstituted by
`load_state`'s own post-loop fixups (`_reset_operating()`, the `_civ_live`
patch, `w.update`, `rng.setstate`), and almost the entire INTERNAL group is
caches that are cheap to rebuild and are never round-tripped on purpose.

By first-set mode: **108** attributes are given a real value in `__init__`;
**50** are created lazily via `getattr(self/s, "name", default)` at first
read, exactly the pattern `CLAUDE.md`/`core.py` describe, where **absence is
meaningful** (a save file missing the field means "this has never happened
yet", not "zero"); **4** are set unconditionally outside `__init__` with no
getattr guard (see §1); and **3** are the `self.__dict__[...]`-hidden ones.

## 4. The 10 attributes touched by the most different files

| Rank | Name | Files | Sites | Category |
|---|---|---|---|---|
| 1 | `civ` | 15 | 82 | SCENARIO |
| 2 | `year` | 12 | 106 | WORLD |
| 2 | `goal` | 12 | 33 | SCENARIO |
| 4 | `nodes` | 11 | 180 | SCENARIO |
| 4 | `done` | 11 | 106 | HOUSEHOLD |
| 4 | `cfg` | 11 | 63 | SCENARIO |
| 7 | `capital` | 10 | 172 | HOUSEHOLD |
| 7 | `operating` | 10 | 63 | HOUSEHOLD |
| 7 | `fog` | 10 | 43 | SCENARIO |
| 7 | `granted` | 10 | 36 | HOUSEHOLD |

Six of the ten are SCENARIO/config-shaped, not HOUSEHOLD - unsurprising,
since `nodes`/`civ`/`cfg`/`goal`/`fog` are read defensively (often via
`getattr` with a fallback) from almost every command handler in
`sim/engine/proto/`, simply to know what game is being played, before any
household-specific logic runs. `nodes` has the single most read/write
**sites** (180) of anything in the object, though it never changes after
construction - it is looked up constantly, not mutated. Among genuinely
HOUSEHOLD fields, `capital` has the most sites of any attribute at all (172),
which matches its role: nearly every economic method in the engine either
checks it or moves it.

## 5. Attributes flagged genuinely ambiguous (need a decision, not a move)

- **`granted`** - the set of technologies this *civilisation* already had for
  free at 100 AD (or on arrival), seeded once from `civ["starting_techs"]`
  and read everywhere `done`/`capability_factor`/`_practice_cache` are. It is
  stored per-`Sim`, but its *content* is a fact about the civilisation, not
  about which actor is asking: two households in the same civilisation would
  have an identical `granted` set on day one. If a second actor (a
  government, a rival household) is ever added, either `granted` moves to a
  shared WORLD/civ object and each actor's `done` is compared against it, or
  every actor keeps its own (correct today, but duplicated data that must be
  kept in sync by construction alone, never by an explicit update path).
  `_practice_cache` inherits this ambiguity, since it is keyed on
  `len(self.granted)`.
- **`goal`** (and, more weakly, `goal_year`, `end_year`, `fog`) - `goal` is
  read from `sim/engine/proto/dispatch.py` and `cli.py` as a single,
  session-wide choice ("the one thing you were told the name of on arrival"),
  which reads as SCENARIO/session-config today. But a win condition is
  naturally a property of *whoever is playing*, not of the world: a
  government pursuing "gunpowder" and a rival household pursuing "printing"
  in the same run is a completely reasonable extension, and would need `goal`
  to be per-actor (HOUSEHOLD), with `goal_year` (already HOUSEHOLD, this
  actor's own achievement year) as its natural companion. I left it in
  SCENARIO for this table because that is what today's single-actor code
  does with it, but this is a real fork, not a formality.
- **`trades_created` / `trade_introduced_year` / `trades_endemic`** - a trade
  the household teaches into existence starts as a HOUSEHOLD fact (only this
  actor can hire it) but the whole point of `trades_endemic` is to record
  when the *society* has gone on to supply it on its own, at which point it
  is no longer specific to the household that taught it. These three fields
  currently live entirely on the household's side of that transition and
  never move to a world-level "who else can now hire this" fact - worth
  deciding whether a second actor should inherit a trade the first actor
  taught, or have to re-teach it.
- **`shortages`** - `SAVE_FIELDS` and its own comment call it "a diagnostic
  tally... read by `run`/`compare`'s cross-seed summary and by nothing that
  decides anything" - i.e. it is INTERNAL by function (nothing reads it to
  make a decision) but it is keyed to *this household's* material binds, and
  it is deliberately saved, which INTERNAL fields elsewhere in this table
  mostly are not. Filed as HOUSEHOLD here on the "it's about this actor's
  history" argument, but it reads equally well as an INTERNAL diagnostic
  that should move with the household regardless.
- **`_material_stock_ledger`** - filed as INTERNAL (it is a cache/ledger, not
  a field anyone sets by choice), but its content - tonnes of each material
  the household currently holds - is exactly the shape of an inventory,
  which is explicitly named as HOUSEHOLD subject matter in the brief. It
  would not be wrong to file it as HOUSEHOLD outright; I kept it INTERNAL
  only because the code frames it as a stock-throttling cache rather than as
  a first-class inventory anyone queries directly.

## 6. HOUSEHOLD fields flagged for a non-person owner

Per the brief, HOUSEHOLD fields whose *name or content* is written for a
single mortal person, not a household/firm/government in general:

| Name | Why it does not generalise as written |
|---|---|
| `founder_alive` | Literally a person's vital status. A firm or a government does not die of age. |
| `life_left` | A random draw from "elite male already aged 35" mortality. Meaningless for a non-person owner; the whole mortality subsystem this feeds (see `founder_life_mean`/`founder_life_sd` in `cfg`) is founder-specific. |
| `director_hours_spent_founder` | Named for one person's personal working hours. A firm/government has no single body whose hours this is - it would need to become something like "owner-supplied labour hours" with no implied headcount of one. |
| `hours_this_year` | Documented as "the founder's own hours accounting" (see `_founder_death_info` and the SAVE_FIELDS comment). Same fix as the row above. |
| `dead_reason` | Mostly generic run-ending reasons (bankruptcy, denunciation, a catastrophe), but one literal value produced by `core.py` is `"the founder died without training successors"` - a person-specific failure mode with no non-person equivalent yet. |
| `policy` | The dict itself generalises fine (`auto_hire`, `auto_mine`, ...), but one key, `auto_court_heir` ("court a dead patron's successor"), is written for succession after a mortal owner's death. |
| `living_cost_paid` | Framed throughout as personal subsistence ("a few months' subsistence"), priced at household living costs. A firm/government has overhead, not personal upkeep in the same sense - conceptually adjacent but not the same mechanism. |
| `last_patron_death` | Milder: "patron" is a Roman patronage-network concept, not an anatomical one, so a firm/government having a patron (a backer, a sponsor) is a small stretch, not a redesign - flagged for the naming decision, not because the mechanism is unsound. |

`_founder_death_aged` / `_founder_death_year` / `_founder_death_cache` are the
INTERNAL caches behind the same person-specific facts and are noted in the
table rather than repeated here, since they follow `founder_alive`/`life_left`
by construction - they exist only to remember when/how old the founder was
when they died, and have nothing to remember for an owner that cannot die of
age.

## 7. INTERNAL fields, by what they are keyed off

Of the 53 INTERNAL entries: roughly two-thirds are keyed off HOUSEHOLD state
(directly, like `_cap_factor` on `done`/`granted`/`operating`, or
transitively, like the `_said_*` warn-once throttles that fire on a household
metric crossing a band) and must move with the household if it is extracted,
or the cache invalidation they exist for silently stops matching what
changed. The rest are keyed off WORLD state (`_said_wage_cascade`,
`_said_debasement`, `_said_output`, `_literacy_said`, `_food_diffusion_said`,
`_said_condition`) or off SCENARIO data alone (`_nodes_by_cat_cache`,
`_electricity_load_ids_cache`, `_agri_mechanisation_ids`,
`_diffusible_ids_cache`, `_foreign_institution_cache`, `_foreign_only_cache`,
`_mineral_scale`, `_regions`, `_mat_unlock`, `_home_centroid`,
`_win_condition_keys`) and should stay on `Sim`/a future World object
regardless of how many households exist. One, `_said_command_index`, is keyed
off neither - it throttles a "you have now typed N commands" onboarding note,
which is a UI/session concern, not economic state of any kind. The "keyed
off" column in the table above gives the specific reason for every one of the
53, not just the bucket.
