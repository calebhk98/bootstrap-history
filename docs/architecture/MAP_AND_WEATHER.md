# The map is two systems, and weather is the reason the second one cannot grow

Covers stakeholder maintainability items 6 and 7. Every number below carries
the command that produced it. Where I contradict the investigation this task
started from, I say so and give the evidence; several of its claims were
right, one was stale by the time this was written (the weather fix it
describes as pending has since shipped), and the exact region count was off
by one.

---

## 0. Verdict in one paragraph

There are genuinely two systems, but the split is narrower and further along
than the starting brief describes: the weather mechanism it treats as still
pooling naively by region already migrated to `land_tiles`, with a real
spatial-correlation model, in a commit made the same day this document was
written. What has NOT moved is land rent, mineral deposits, and the
Ricardian price mechanism they feed - three consumers still keyed on the 21
hand-drawn regions, with the same 86x size-disparity defect Complaints/46 and
50 documented. The weather cost problem is real, confirmed cubic by both the
loop structure and direct timing, and it is not close: at a 10,000-tile
world, one default Monte Carlo run for Rome (`--mc 200`, the shipped
default) would spend about twelve minutes on matrix factorisation alone,
against about 1.4 seconds today. The fix is not numpy - this project ships
zero third-party dependencies and numpy is not even installed in this
environment - it is decoupling how many weather cells a civilisation pools
over from how many tiles the map uses to store area, because the two
questions (how finely is land subdivided, and how many independent climate
draws does a harvest need) have different right answers. Recommended order
is in section 7.

---

## 1. The two systems, precisely, and who reads what

### 1.1 What exists in `data/world/geography.json`

Both live under one file, as two independent top-level keys: `regions` and
`land_tiles`. Confirmed:

```
python3 -c "import json; g=json.load(open('data/world/geography.json')); print(list(g.keys()))"
-> ['_doc', 'regions', 'reach_levels', 'located_materials', 'land_tiles']
```

**`regions`: 22 keys, 21 of them real.** One key is `_note` (a metadata
string, not a region record):

```
python3 -c "import json; g=json.load(open('data/world/geography.json'));
print(len(g['regions']), sorted(g['regions'].keys()))"
-> 22 keys; '_note' is one of them; the other 21 are region ids
  (americas_carib, americas_north, americas_south, arabia_horn,
  australia_pacific, britannia, china, east_africa_south, gaul_germania,
  greece_anatolia, greenland_arctic, hispania, india, italia,
  levant_mesopotamia, north_africa, persia_centralasia, scandinavia,
  siberia_urals, southeast_asia, west_africa)
```

This corrects the starting brief's "about 22 hand-drawn records" - it is 21
records plus one documentation string that happens to share the dict.
`sim/world/land.py` and the Complaints agree with 21, not 22.

Sizes, read from each region's own `land.land_area_km2`:

```
python3 -c "
import json
g = json.load(open('data/world/geography.json'))
areas = {k: v['land']['land_area_km2'] for k, v in g['regions'].items() if k != '_note'}
print(min(areas.values()), max(areas.values()), max(areas.values())/min(areas.values()))
"
-> 230000 19800000 86.08695652173913
```

britannia at 230,000 km2 to americas_north at 19,800,000 km2, an 86.09x
spread, exactly as the starting brief said. Confirmed, not merely repeated.

**`land_tiles`: 1,139 tiles, not "about 1,139".** Exact:

```
python3 -c "import json; g=json.load(open('data/world/geography.json'));
lt=g['land_tiles']; print(lt['tile_count'], lt['target_tile_area_km2'])"
-> 1139 150000.0
```

`target_tile_area_km2` is a target, not a guarantee - tiles are clipped to
Natural Earth's coastline, and a coastal tile gets whatever land actually
falls inside its cell:

```
python3 -c "
import json, statistics
g = json.load(open('data/world/geography.json'))
areas = [t['land_area_km2'] for t in g['land_tiles']['tiles'].values()]
print(min(areas), max(areas), statistics.mean(areas), statistics.median(areas))
"
-> min 15028.6, max 150000.0, mean 117057.4, median 149792.5
```

So "about 150,000 km2 each" is true for the median tile and false for a
coastal one; interior tiles hit the cap almost exactly (median 149,792.5 is
99.9% of the 150,000 target), coastal ones can be a tenth of that. This is
not a bug - it is what "clip an equal-area grid to a coastline" produces -
but it means the tile system's own internal size spread (max/min = 9.98x)
is real, just an order of magnitude smaller than the region system's 86x.

`land_tiles` also carries `region_to_tiles` (which tiles fall inside each of
the 21 hand-drawn regions) and `unmapped_tile_count`:

```
python3 -c "
import json
g = json.load(open('data/world/geography.json'))
lt = g['land_tiles']
mapped = sum(len(v) for v in lt['region_to_tiles'].values())
print(mapped, lt['unmapped_tile_count'], mapped + lt['unmapped_tile_count'])
"
-> 943 196 1139
```

943 of the 1,139 tiles fall inside one of the 21 regions; 196 do not (land
outside any territory a shipped civilisation currently holds - the deep
interior of Africa, Australia, the far Americas). This matters for section 5:
any future civilisation whose `home_regions` names ground outside the 21
drawn boxes has no tile coverage to fall back on yet.

Generated by `tools/generate_geography_tiles.py`: an equal-area 150,000 km2
grid (module constant `TARGET_TILE_AREA_KM2`, no command-line flag to change
it), clipped to Natural Earth 1:50m land polygons, classified by
Koppen-Geiger climate class via the `kgcpy` package. Regenerating it needs
network access and three packages (`shapely`, `geopandas`, `kgcpy`) the test
suite does not otherwise depend on - confirmed from that generator's own
module docstring and `sim/tests/test_geography_tiles.py`'s docstring, which
tests the COMMITTED OUTPUT rather than re-running the pipeline for exactly
that reason.

### 1.2 Who reads which system - verified by grep, not assumed

```
grep -rn "land_tiles" sim/ --include=*.py | grep -v test
-> only sim/engine/core.py (comments and the weather-cell builder)

grep -n "land_tiles" sim/world/land.py sim/solve_prices.py
-> no matches in either file
```

| Mechanism | File | Reads | Confirmed by |
|---|---|---|---|
| Land rent (extensive + intensive margin) | `sim/world/land.py` | `regions` only | grep, zero `land_tiles` hits |
| Price solver's land-rent wiring | `sim/solve_prices.py` | `regions`, via `land.py` | grep for `land_tiles` (none), `from sim.world import land` at line 779 |
| Mineral deposit locations and rent | `sim/world/deposits.py` | `regions` (`geography["regions"].get(region)`, lines 825, 957) | direct read |
| Forest/coppice land ceiling | `sim/engine/economy_mining.py` `home_land_area_km2`/`forest_land_ceiling` | `regions`, summed by `land_area_km2` (NOT region count) | direct read, see 1.3 |
| Home centroid, region-name lookups | `sim/engine/geography.py` | `regions` (`self._regions`) | direct read |
| Freight distance between civilisations | `sim/engine/economy_freight.py` | `regions` centroids (`self._regions[region_id]["lat"/"lon"]`) | direct read |
| Growing-season weather pooling | `sim/engine/core.py` `_compute_farm_weather_cells` | `land_tiles` directly (falls back to a region's own centroid only for an unmapped region) | direct read, quoted in 1.3 |

One line in the table needs a caveat: `sim/engine/economy_mining.py`'s
`home_land_area_km2` sums `land_area_km2` across a civilisation's held
regions - it does NOT count regions the way the old weather code and the old
forest-ceiling code once did. Its own docstring says so explicitly ("not
counted by how many region labels that ground happens to be filed under").
That means the specific "China gets one weather system because it is one
label" defect Complaints/50 found was **already fixed in this file** before
this task started; it is not a live bug here, only in the sense that the
underlying region SIZES are still capricious, not in the sense that anything
here mis-measures them.

### 1.3 The starting brief's biggest miss: weather already migrated

The starting brief states "Only the weather pooling in sim/engine/core.py
reads `land_tiles`" as if it were still the simple per-region pooling
Complaints/47 and 50 describe. That undersells what is actually there.
`git log --oneline -3 -- sim/engine/core.py` shows the current mechanism was
committed as `a59f803`, "Weather correlates over distance, and crops
finally pay for their land", **committed today (2026-09-18, per `git log -1
--format="%ci" a59f803`)**, on this same branch. The working tree is clean
(`git status --short` returns nothing for this file), so this is shipped
code, not someone's half-finished edit I happened to catch mid-save.

What it actually does, read from `sim/engine/core.py` (function names, not
line numbers - another agent is actively restructuring this file; the same
functions moved from around line 1885 to around line 920 between two reads
minutes apart, same text, different offset, confirmed by diffing the
docstrings, which is why every citation here is by name):

- `_compute_farm_weather_cells`: breaks each of a civilisation's
  `home_regions` into its `land_tiles.region_to_tiles` cells (943 of 1,139
  tiles are mapped this way), falling back to one cell at a region's own
  centroid only for a region absent from that mapping (should not happen for
  any of the 21 shipped regions - all 21 appear there).
- `_compute_farm_weather_correlation_cholesky(cells)`: builds an n-by-n
  spatial correlation matrix, `correlation(cell_a, cell_b) =
  exp(-chordal_distance_km(cell_a, cell_b) / decorrelation_length_km)`, and
  Cholesky-factorises it. `decorrelation_length_km` is
  `GROWING_SEASON_WEATHER_DECORRELATION_LENGTH_KM`, declared in
  `sim/world/shared_constants.py` at 600.0 km, confidence `D`, sourced by
  chaining three different published correlation-length figures (daily
  precipitation, seasonal precipitation totals, synoptic-scale weather
  systems) rather than one direct measurement - the module says so itself
  and calls for "a sensitivity sweep across the roughly 150-1,500 km range
  this docstring's own chain of reasoning spans". I could not find that
  sweep recorded anywhere in `docs/` or `Complaints/`; it is promised, not
  done.
- `_pooled_farm_weather_multiplier(yr)`: draws one independent standard
  normal per cell, correlates them through the Cholesky factor (a
  lower-triangular matrix-vector product), clips each cell's multiplier the
  same way the old single-draw mechanism did, and takes the arable-land-
  weighted average.

This is a materially different, and materially better, mechanism than the
one the starting brief and Complaints/47/50 describe as current: it answers
Complaints/50's own question - "over what distance does growing-season
weather stop agreeing with itself?" - with an actual number, instead of the
two hardcoded answers ("one region is one weather system, perfectly
correlated with itself and independent of every other region") that
complaint measured as both wrong. `Complaints/50` is still an open file (not
in `Complaints/closed/`) despite this; `Complaints/47`, the complaint it
superseded, is closed. I did not move either file - not my brief - but flag
this for whoever owns that queue: the fix Complaints/50 called for appears
to already be merged and tested (`sim/tests/test_growing_season_weather_
correlation.py`, 15 tests, all pass - see section 6).

### 1.4 What was already fixed on the regions side too

`Complaints/46` recommended two fixes in order: (1) an intensive margin on
land rent, cheap, fixes the region-count artefact without touching the map;
(2) re-tiling, expensive, the real fix. Fix (1) is done:

```
grep -n "intensive_rent_kg_grain_equivalent_per_iugerum\|LABOUR INTENSITY" sim/world/land.py | head -3
-> present; labour_hours_applied_per_iugerum and margin_outcome_for_civilization
   both combine extensive + intensive rent

grep -n "test_han_china_no_longer_prices_at_zero" sim/tests/test_land.py
-> present, and passes (see section 6)
```

So `iugerum_land` no longer prices at exactly zero for Han China. That is
NOT the same as the region-size defect being fixed - see section 2.

---

## 2. The real cost of the split: concrete wrong answers

### 2.1 Fixed already, but instructive: the weather bug (Complaints/50)

Before the commit described in 1.3, weather drew one independent sample per
REGION RECORD. Complaints/50's own measurement, from before that fix (I am
quoting its numbers, not re-deriving them - the mechanism they describe no
longer exists to re-run):

    civilisation       home regions   unshocked century   mean nutrition
    rome_100ad                    7              107.6%          1.0042
    han_china_100ad                1              83.8%          1.0222

Han China ate BETTER than Rome on average and still lost a quarter of its
population, because its harvest was one weather draw for 9.6 million km2
while Rome's was seven, purely a filing artefact - China holds MORE
cultivable land than all seven Roman regions combined. That specific,
concrete, wrong number - a quarter of a civilisation's population lost to a
JSON file's row count - is what an unmigrated consumer looks like when
weather was the one on the old system. It no longer produces this number
(section 1.3), but every other consumer still on `regions` is exposed to the
same class of error, in whatever variable each one drives.

### 2.2 Still live: land rent's extensive margin

`sim/world/land.py`'s intensive-margin fix stops `iugerum_land` pricing at
exactly zero for a one-region civilisation, but it does this by adding a
SEPARATE rent channel (crowding on the SAME ground), not by fixing what the
extensive margin sees. The extensive margin - which region is the worst one
actually needed, and how much every better region earns over it - still
ranks by REGION, not by land quality within a region. `north_africa` is
5,750,000 km2 rated at a single `fertility_quality_multiplier`, described in
Complaints/46 as "96% Sahara, rated 1.35 fertility on the strength of the
Nile". Any consumer that asks "is there a margin between good and bad land
inside north_africa" gets no answer, because the region has one row. This is
not hypothetical: it is the literal shape of the data today -

```
python3 -c "
import json
g = json.load(open('data/world/geography.json'))
print(g['regions']['north_africa']['land'])
"
-> land_area_km2: 5750000, one arable_fraction, one fertility_quality_multiplier
```

versus 47 tiles of varying Koppen class for the same footprint
(`region_to_tiles['north_africa']`, length 47, confirmed in section 3). A
player or a validation run comparing "how much does a desert region's rent
respond to more population" would see the SAME answer whether that
population sits on the Nile delta or 900 km into the Sahara, because the
model cannot distinguish them.

### 2.3 Still live: mineral deposits

`sim/world/deposits.py` keys every deposit's location to a region
(`geography["regions"].get(region)`), the same one-parcel-per-label pattern.
A validation run comparing ore rent or extraction cost between two
similarly-endowed empires would see the same region-count sensitivity
Complaints/50 measured for weather, on whichever deposit-driven price it
computes, for as long as this file stays on `regions`. I did not re-derive a
specific wrong number here - that is a further investigation, not this
one - but the mechanism that produced Complaints/50's number is present in
this file's own region keying, unexamined.

### 2.4 Not actually broken: freight

Complaints/46 argues freight (region centroids, `economy_freight.py`) is
fine as-is, because a centroid is a point and 21 of them give reasonable
great-circle distance bands regardless of the region's OWN area. I re-read
`economy_freight.py`'s use (`self._regions[region_id]["lat"/"lon"]`,
confirmed) and agree: nothing about freight distance depends on how big the
region is, only on where its centre sits. This consumer does not need to
wait for a map migration.

---

## 3. Weather complexity: confirmed, not asserted, and measured

### 3.1 The exponents, from the loop structure

`_compute_farm_weather_correlation_cholesky(self, cells)`, read directly:

```python
cell_count = len(cells)
correlation = [[0.0] * cell_count for _ in range(cell_count)]
positions_km = [_cell_chordal_position_km(cell.lat, cell.lon) for cell in cells]
for row in range(cell_count):                      # O(n)
    for col in range(row):                          # O(n) -> O(n^2) so far
        ...
lower = [[0.0] * cell_count for _ in range(cell_count)]
for row in range(cell_count):                       # O(n)
    for col in range(row + 1):                       # O(n)
        total = sum(lower[row][k] * lower[col][k] for k in range(col))  # O(n)
        ...                                          # -> O(n^3) total
```

The correlation-matrix build is a double loop over pairs: O(n^2). The
Cholesky factorisation proper (the classic Cholesky-Banachiewicz
column-by-column form) is a triple nested loop, row/col/k, each ranging up
to n: **O(n^3)**. This runs once, in `Sim.__init__`, unconditionally -
confirmed by reading the call site:

```
grep -n "_compute_farm_weather_cells()\|_compute_farm_weather_correlation_cholesky(self._farm_weather_cells)" sim/engine/core.py
-> both called directly in __init__, no `if self.events` or similar guard
```

So a `--no-events` run pays this exactly as much as one with events on.

`_pooled_farm_weather_multiplier(self, yr, ...)`, the per-year cost:

```python
independent_draws = [...]                            # O(n)
for row, cell in enumerate(cells):                    # O(n)
    correlated_z = sum(cholesky_lower[row][col] * independent_draws[col]
                        for col in range(row + 1))    # O(n) -> O(n^2) total
```

A lower-triangular matrix-vector product: **O(n^2)**, run once per
simulated year.

### 3.2 n for Rome today: 88, confirmed two independent ways

From the data directly:

```
python3 -c "
import json
civ = json.load(open('data/civilizations/rome_100ad.json'))
g = json.load(open('data/world/geography.json'))
r2t = g['land_tiles']['region_to_tiles']
print({r: len(r2t.get(r, [])) for r in civ['home_regions']})
print(sum(len(r2t.get(r, [])) for r in civ['home_regions']))
"
-> italia 5, gaul_germania 9, britannia 4, hispania 7, north_africa 47,
   greece_anatolia 11, levant_mesopotamia 5  ->  88
```

And from a committed, passing test that pins this exact number:

```
python3 -m unittest sim.tests.test_growing_season_weather_correlation.WeatherCellsTests.test_romes_seven_regions_resolve_to_88_land_tiles_cells -v
-> ok
```

n for the other shipped civilisations, same method:

```
python3 -c "
import json, glob
g = json.load(open('data/world/geography.json'))
r2t = g['land_tiles']['region_to_tiles']
for f in sorted(glob.glob('data/civilizations/*.json')):
    civ = json.load(open(f))
    hr = civ.get('home_regions') or []
    print(f, len(hr), sum(len(r2t.get(r, [])) for r in hr))
"
-> england_1300: 2 regions -> 13 cells
   han_china_100ad: 1 region -> 69 cells
   mexica_1500: 1 region -> 32 cells
   norse_900ad: 1 region -> 14 cells
   rome_100ad: 7 regions -> 88 cells
```

north_africa alone contributes 47 of Rome's 88 cells - more than half - a
direct measurement of how unevenly the OLD region boundaries carve up the
NEW tile grid; nothing about Rome's real cultivated footprint makes it
"53% north_africa".

### 3.3 Measured cost, current scale

Isolated timing of the two hot functions, called directly (not through a
full `Sim()` construction, to separate the weather-specific cost from
everything else `__init__` does), using `time.perf_counter` (the same clock
`time` reports against) with the real Rome tile positions read out of
`geography.json`:

```
python3 -c "
import sys, time, json
sys.path.insert(0, 'sim')
import engine.core as core
g = json.load(open('data/world/geography.json'))
lt = g['land_tiles']; civ = json.load(open('data/civilizations/rome_100ad.json'))
cells = [core.Sim._WeatherCell(cell_id=tid, lat=lt['tiles'][tid]['lat'],
         lon=lt['tiles'][tid]['lon'], weight=1.0)
         for r in civ['home_regions'] for tid in lt['region_to_tiles'].get(r, [])]
N = 200
t0 = time.perf_counter()
for _ in range(N): core.Sim._compute_farm_weather_correlation_cholesky(None, cells)
print((time.perf_counter() - t0) / N)
"
-> 0.0071785 sec  (n=88, real Rome positions)
```

Growth with n (synthetic positions - the cost is a pure function of n, not
of where the points sit, so synthetic and real positions time the same):

    n      Cholesky (sec)   matvec/year (sec)
     44        0.00142            -
     88        0.00693/0.00720    0.000195
    176        0.04706            0.000640
    352        0.34673            0.002703
    704        2.59247            0.011679
    773        3.4883/3.5365      0.012897
   1139       10.832               -

Log-log regression slope of Cholesky time against n, across n = 176 to
1,139 (excluding the two smallest points, where fixed per-call Python
overhead measurably pulls the fitted exponent down):

```
python3 -c "
import math
ns=[176,352,704,773,1139]; ts=[0.04706,0.34673,2.59247,3.4883,10.832]
xs=[math.log(n) for n in ns]; ys=[math.log(t) for t in ts]
n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
print(sum((x-mx)*(y-my) for x,y in zip(xs,ys)) / sum((x-mx)**2 for x in xs))
"
-> 2.91
```

2.91, against a triple-nested-loop prediction of exactly 3. The loop
structure and the timing agree: this is cubic. (Across the full range
including the two smallest, noisier points, the fitted slope drops to 2.78 -
still clearly super-quadratic, but the smaller-n end is not a clean fit for
an asymptotic exponent and I would not quote it as the number.)

Per-year matvec cost scales the same way against n^2: n=704 to n=1408
(separately measured, synthetic positions) gives a ratio of 3.8-4.3x per
doubling against a 4x prediction.

### 3.4 The scaling question, with arithmetic

**Assumption, stated plainly because it is load-bearing and I cannot verify
it against a real 10,000-tile dataset that does not exist yet:** going from
1,139 tiles to 10,000 tiles worldwide, holding the same total land area
(`land_tiles`'s own `_doc` and generation rule imply the same Natural-Earth
land mass, just cut finer), means each civilisation's own tile count scales
by the same factor as the world total - 10,000 / 1,139 = 8.78x - because the
tiles fall inside the SAME historical footprints, only more finely divided.
This is the natural reading of "shift to a 10k tile system"; if a future
generator instead concentrates the extra tiles somewhere else (finer
resolution only in populated regions, say), the numbers below would differ,
and that generator does not exist yet to check.

```
python3 -c "print(10000/1139)"
-> 8.779631255487269
```

n for Rome at 10,000 tiles: 88 * 8.78 = 773 (measured directly above, not
just formula-extrapolated - I built 773 real-shaped synthetic cells and
timed them, same method as section 3.3). For the other civilisations, same
scale factor applied and directly measured, not formula-only:

```
python3 -c "
import sys, time, random
sys.path.insert(0, 'sim')
import engine.core as core
def make_cells(n):
    random.seed(11)
    return [core.Sim._WeatherCell(cell_id=str(i), lat=random.uniform(-60,70),
            lon=random.uniform(-180,180), weight=1.0/n) for i in range(n)]
scale = 10000/1139
for name, n0 in {'rome':88,'han':69,'norse':14,'england':13,'mexica':32}.items():
    n = round(n0*scale); cells = make_cells(n)
    reps = 5 if n>200 else 50
    t0=time.perf_counter()
    for _ in range(reps): chol = core.Sim._compute_farm_weather_correlation_cholesky(None, cells)
    chol_time=(time.perf_counter()-t0)/reps
    draws=[random.gauss(0,1) for _ in range(n)]
    reps2 = 50 if n>200 else 500
    t0=time.perf_counter()
    for _ in range(reps2):
        pooled=sum(cells[row].weight*sum(chol[row][col]*draws[col] for col in range(row+1))
                   for row in range(n))
    matvec=(time.perf_counter()-t0)/reps2
    print(name, n0, '->', n, 'chol=%.4fs'%chol_time, 'matvec/yr=%.6fs, x200y=%.4fs'%(matvec, matvec*200))
"
-> rome:   88 -> 773   chol=3.5365s   matvec/yr=0.012897s   x200y=2.5794s
   han:    69 -> 606   chol=1.6784s   matvec/yr=0.007745s   x200y=1.5490s
   norse:  14 -> 123   chol=0.0169s   matvec/yr=0.000353s   x200y=0.0707s
   england:13 -> 114   chol=0.0140s   matvec/yr=0.000332s   x200y=0.0665s
   mexica: 32 -> 281   chol=0.1810s   matvec/yr=0.001715s   x200y=0.3430s
```

**One Sim() construction for Rome at 10,000 tiles: about 3.5 seconds spent
on the correlation factorisation alone**, against 0.007 seconds today - a
~500x increase in wall time for an 8.78x increase in n, in line with the
cubic exponent measured in 3.3.

**What actually breaks: `--mc`, not the fingerprint suite.** `run`,
`compare` and `sensitivity` all default to `--mc 200` - confirmed:

```
grep -n 'add_argument("--mc", type=int, default=200)' sim/engine/cli.py
-> three matches, one per subcommand
```

Each of those 200 trials constructs its own `Sim()` (`res = [Sim(nodes,
order, random.Random(a.seed + i), ...) for i in range(a.mc)]` in
`sim/engine/cli.py`), paying the Cholesky factorisation fresh every time -
nothing caches it across trials today. At 10,000 tiles:

    200 * 3.5365 sec = 707.3 sec ~= 11.8 minutes

for ONE default `python3 sim/simulator.py run --civ rome_100ad` invocation's
worth of pure weather-matrix setup, against about 1.4 seconds today. That is
the "cannot go to 10k tiles because of the weather" the stakeholder
described - it does not show up as a crash, it shows up as a routine command
taking twelve minutes longer than it used to, on top of whatever else that
run does.

**What does NOT break, for contrast: `perf_fingerprint.py`.** Its 9
scenarios (`sim/perf_fingerprint.py`'s own `SCENARIOS` list: 4 at n=88, 2 at
n=69, one each at n=14/13/32) each construct exactly ONE `Sim()`, not 200.
Today's weather-only cost across all nine, summed from the measured
per-civilisation figures in 3.3 (4 Rome constructions - three 200-year, one
400-year - plus 2 Han, 1 each Norse/England/Mexica): roughly 0.29 seconds,
against a total suite time CLAUDE.md §5 gives as about six minutes -
unmeasurable. At 10,000 tiles, the same nine-scenario weather-only cost
rises to roughly 34 seconds (summing the 3.4 figures the same way): about
118x more, but still a small fraction of a six-minute suite, because
`perf_fingerprint` never multiplies by `--mc`. The Monte Carlo commands are
where this actually hurts.

**What definitely does NOT scale this way: the price solver.** Land rent's
extensive margin (`find_margin_of_cultivation` in `sim/world/land.py`) sorts
parcels by fertility and walks a supply curve - O(n log n), confirmed by
reading the function (it sorts, then does one linear pass; no nested loop
over parcels at all). Measured directly:

```
time python3 sim/solve_prices.py --civ rome_100ad > /dev/null
-> real 0m0.220s
time python3 sim/solve_prices.py > /dev/null
-> real 0m0.247s
```

(Complaints/46 quotes 0.37 seconds for this; my own measurement here is
0.22-0.25s, likely just machine variance rather than a real discrepancy - I
am flagging the difference rather than silently picking the better-sounding
number.) So migrating land rent from 21 regions to however many tiles a
future map uses - even 10,000 of them - does not reproduce weather's cubic
problem. Only the correlation/Cholesky step is cubic; ordinary Ricardian
margin-finding is a sort.

**A further wrinkle worth recording: how often is this cost paid per
game?** Within one running `agent` or `play` process, `Sim()` (and its
Cholesky factorisation) is built exactly once, before the command loop -
confirmed by reading `cli_agent.py`: `sim = Sim(...)` at the top of
`cmd_agent`, before `for line in sys.stdin:`. Many commands sent down one
open pipe amortise this cost over the whole session. But the test harness's
own session-resuming pattern, and CLAUDE.md §3.5's description ("with
`--session` every single command is a save followed by a load"), both show
a session being reopened by a FRESH subprocess - confirmed in
`sim/tests/test_five_things_winner.py`, two separate `subprocess.run([...,
"--session", _sess_session])` calls sharing one save file, each one a new
process, a new `Sim()`, a new factorisation. Whether the weather setup cost
is paid once per game or once per exchange depends entirely on whether
whatever is driving `agent` keeps one process alive across a whole session
or relaunches per command; the protocol supports both, and CLAUDE.md's own
description of normal play leans toward the expensive pattern.

---

## 4. Options for the weather cost, costed and compared

### 4.1 numpy or vectorised linear algebra

**Cost saved:** large. numpy's BLAS-backed Cholesky is compiled, typically
one to two orders of magnitude faster than a pure-Python triple loop for
n in the low hundreds, and the matrix-vector product drops from a Python
loop to a single BLAS call.

**What it changes about the answer:** nothing, if implemented as a direct
port of the same kernel and the same random draws feeding the same seeds -
the maths is identical, only the arithmetic engine changes. It WOULD change
bit-for-bit output if floating-point summation order differs (BLAS routines
do not sum in the same order a hand-written Python loop does), which is
exactly what `perf_fingerprint.py`'s byte-identical check would catch - see
section 6.

**The real obstacle, and it is not technical:** `sim/simulator.py`'s own
module docstring says "No third-party dependencies. Python 3.8+." -
confirmed, and repeated verbatim in `sim/engine/data.py`. There is no
`requirements.txt`, `pyproject.toml`, or `setup.py` anywhere in the repo
(`find . -iname "requirements*.txt" -o -iname "pyproject.toml" -o -iname
"setup.py"` returns nothing), and numpy is not installed in this
environment (`python3 -c "import numpy"` raises `ModuleNotFoundError`).
Adding numpy would be the FIRST third-party dependency this project has
ever taken on. That is not this task's call to make - it is a project-wide
policy change, not a weather-module decision - and it should be surfaced to
the stakeholder explicitly rather than done quietly inside a performance
fix. Satisfies CLAUDE.md §3.1 (changes nothing about how any number is
derived); does not satisfy the project's own stated zero-dependency rule
unless that rule is deliberately revisited.

### 4.2 Cap pooled cells per civilisation, independent of tile count

Instead of pooling over every `land_tiles` cell a civilisation's regions map
to, aggregate down to a fixed ceiling - say, cap at roughly today's largest
figure (Rome's 88) regardless of how finely the underlying map is cut,
merging adjacent fine tiles into a coarser weather-cell only for this
purpose. Land rent, mining and freight would still read the full-resolution
`land_tiles` for area and quality; only the weather draw would work on a
coarser aggregate.

**Cost saved:** total, and it does not scale with map resolution at all - n
stays flat as tile count grows, so the O(n^3) setup cost stays flat too.

**What it changes about the answer:** very little, if the cap is chosen
above what the correlation kernel can actually resolve. At the current
150,000 km2 tile size (roughly 387 km on a side, an interior tile), a
neighbouring tile sits well inside the 600 km decorrelation length
(`exp(-387/600) = 0.526`, still substantially correlated); a genuinely
useful independent climate cell needs to be closer to the decorrelation
length itself than to a small fraction of it. Cutting tiles below roughly
100-200 km on a side (which 10,000 tiles worldwide would do - side length
about sqrt(133,328,366 km2 / 10,000) = 115 km, computed from the measured
total tile land area in section 1.1) buys spatial resolution the weather
model has no physical basis to use, because two 115 km cells 115 km apart
correlate at `exp(-115/600) = 0.83` - almost the same climate. A cap set at
"however many cells this civilisation actually spans, capped so neighbours
are meaningfully decorrelated" is not a computational shortcut dressed as
physics - it is closer to the physically right resolution than the 10,000-
tile grid would be for THIS purpose, even though the 10,000-tile grid is
right for area/land-rent purposes. This is the recommended option; expanded
in section 7.

**CLAUDE.md §3.1:** satisfied. The cap follows from the decorrelation
length, a sourced (if confidence-D) physical constant, not from a tuned
number chosen to make Rome look right.

### 4.3 Exploit the kernel's distance decay for sparsity or banding

Measured on Rome's actual 88-cell footprint today:

```
python3 -c "
import sys, json, math
sys.path.insert(0, 'sim')
import engine.core as core
g = json.load(open('data/world/geography.json'))
lt = g['land_tiles']; civ = json.load(open('data/civilizations/rome_100ad.json'))
cells = [(tid, lt['tiles'][tid]['lat'], lt['tiles'][tid]['lon'])
         for r in civ['home_regions'] for tid in lt['region_to_tiles'].get(r, [])]
positions = [core._cell_chordal_position_km(lat, lon) for _, lat, lon in cells]
n = len(cells); pairs = 0; near_zero = 0; max_dist = 0.0
for i in range(n):
    for j in range(i):
        d = math.dist(positions[i], positions[j])
        max_dist = max(max_dist, d)
        pairs += 1
        if math.exp(-d/600.0) < 0.01: near_zero += 1
print(n, pairs, near_zero, near_zero/pairs, round(max_dist))
"
-> 88 cells, 3828 pairs, 1138 pairs (29.7%) below 0.01 correlation, max chordal
   distance 5731 km
```

Only 29.7% of Rome's own pairwise correlations are negligible - the Roman
Mediterranean is compact enough that most of the empire sits within a few
decorrelation lengths of most of the rest of it. A sparse or banded solver
would help more for a widely dispersed empire and less for a compact one,
and Rome (this project's largest shipped civilisation by cell count) is the
compact case. Exploiting this needs the cells REORDERED by spatial locality
(the current code processes them in whatever order `region_to_tiles`
happens to list them) before a banded factorisation gains anything, which is
real implementation work, not a flag to flip.

**Cost saved:** real but partial for a compact empire, larger for a spread-
out one; needs measuring per civilisation, not assumed uniform.

**What it changes about the answer:** nothing if done as a true sparsity
exploit (dropping numerically negligible entries, not physically zeroing
correlations that are merely small) - it is the same matrix, computed
cheaper. It becomes an approximation, and a CLAUDE.md §3.1 question, the
moment "negligible" is chosen to hit a performance target rather than a
numerical tolerance.

**Verdict:** worth doing eventually, not worth doing first - it is real
engineering effort for a benefit that this project's own largest
civilisation only partially realises, while 4.2 removes the cubic scaling
entirely for every civilisation regardless of geographic spread.

### 4.4 Hierarchical or FFT approach

An FFT-based approach needs a regular grid to transform; `land_tiles` is an
equal-AREA grid clipped to real coastlines, not a regular lat/lon or
Cartesian lattice, so this would mean re-gridding onto a regular lattice as
a separate step, losing the "tile boundary matches a real coastline"
property the current generator was built for. A hierarchical
(multi-resolution) approach is a legitimate direction but is a genuinely
different mechanism, not a drop-in replacement for the current Cholesky
step, and would need its own design and validation pass. Both are real
options for a future rewrite of the whole weather model; neither is a
patch to the existing one. Not recommended as the near-term fix.

### 4.5 Cache the factorisation

The Cholesky factor depends only on a civilisation's `home_regions` and the
(static, per-build) contents of `geography.json` - never on the random seed,
the year, or anything else that varies trial to trial. Nothing prevents
memoising it, keyed on civilisation id (plus a cheap invalidation check
against the geography file, so a data edit does not serve a stale factor).

**Cost saved:** for a `--mc 200` batch, this turns 200 Cholesky
factorisations into 1 - the dominant cost in section 3.4's twelve-minute
estimate almost entirely disappears for BATCH runs. It does NOT help the
`--session`-per-command pattern described in 3.4's last paragraph, if each
command really is a fresh OS process: an in-memory cache does not survive
across process boundaries, and this project persists no compiled artefacts
between runs (SAVE_FIELDS deliberately excludes anything derivable, per
CLAUDE.md §3.5's "no save migration, ever" - correctly, a cached matrix
is exactly the kind of derived-and-reconstructible thing that section says
should NOT be saved).

**What it changes about the answer:** nothing - it is the same computation,
computed once instead of 200 times, for inputs that were never going to
differ across trials anyway.

**Verdict:** a real, cheap, complementary fix - worth doing alongside 4.2,
not instead of it, because it only helps the "many trials, one process"
pattern and does nothing for the cubic cost of any SINGLE factorisation,
which is what 4.2 actually removes.

### 4.6 Comparison table

| Option | Removes O(n^3)? | Changes the answer? | Violates §3.1? | New dependency? |
|---|---|---|---|---|
| numpy/vectorised | No (same exponent, faster constant) | No, if ported faithfully | No | Yes - first ever, needs a policy decision |
| Cap pooled cells (4.2) | Yes, decouples n from tile count | Marginally, and defensibly (kernel-resolution argument) | No | No |
| Sparse/banded (4.3) | Partially, civ-dependent | No, if done as true sparsity | No | No |
| Hierarchical/FFT (4.4) | Yes, different mechanism | Yes, materially - new model | Needs its own case | No, but re-grids the data |
| Cache factorisation (4.5) | No (helps `--mc`, not a single call) | No | No | No |

---

## 5. A staged migration for the map

Each stage is independently shippable. Stages already complete are marked
so as not to re-propose finished work.

**Stage 0 - intensive margin on land rent. DONE.** (Complaints/46's own
recommendation 1; confirmed merged, section 1.4.) Fixes the exact-zero
symptom for a one-region civilisation without touching the map. Changes
`iugerum_land`'s price for any civilisation this affects - a deliberate,
called-out output change, not a regression.

**Stage 0.5 - weather onto `land_tiles` with spatial correlation. DONE.**
(Complaints/50's own recommendation; confirmed merged and tested, sections
1.3 and 6.) Changes every civilisation's harvest variance from what it was
under per-region pooling. Also a deliberate, already-shipped output change.

**Stage 1 - decouple weather cell count from tile count (section 4.2).**
Cap pooled weather cells at a fixed figure per civilisation, independent of
how many `land_tiles` cells its regions map to. Prerequisite for stage 3
below (10,000-tile map) to be affordable at all. Does NOT change land rent,
mining, or freight. DOES slightly change weather variance for any
civilisation whose current cell count already exceeds the chosen cap (Rome
at 88 might, depending on where the cap lands) - call this out per
civilisation rather than assuming it is silent everywhere.

**Stage 2 - land rent's extensive margin onto `land_tiles`.** Replace
`sim/world/land.py`'s region-keyed `cultivable_land_for_civilization` with
a tile-keyed version, feeding `find_margin_of_cultivation` many small
parcels instead of 7-to-21 large ones. Cheap computationally (section 3.4:
O(n log n), confirmed by reading the sort-and-walk function) even at 10,000
tiles. **This WILL change `iugerum_land`'s price, and every price that
depends on land rent through `sim/solve_prices.py` - which per Complaints/
32 and 43 is not a side channel, it is close to the center of the price
system.** Call this out explicitly when shipped; do not present it as a
neutral refactor.

**Stage 3 - mineral deposits onto `land_tiles`.** `sim/world/deposits.py`'s
region-keyed deposit locations move to tile grain. Changes ore rent and
extraction cost. Lower priority than stage 2 - I did not find a measured
wrong-answer example for this consumer the way Complaints/46 and 50
document for land and weather (section 2.3), only the same mechanism
present, unexamined - so this stage should start with the same kind of
measurement those complaints did, not go straight to a rewrite.

**Stage 4 - grow `land_tiles` toward 10,000, now affordable.** Once stage 1
has decoupled weather cost from tile count, and stage 2/3 have moved the
remaining region-keyed consumers onto tiles (or at minimum, confirmed they
tolerate a finer `land_tiles` grid without a cost blowup of their own -
section 3.4 already confirms this for the price solver), regenerating
`tools/generate_geography_tiles.py`'s output at a smaller
`TARGET_TILE_AREA_KM2` becomes a data change, not an engine change. Changes
land rent again (finer parcels), freight not at all (still centroids of the
21 regions, or of `home_regions` however stage 2 ends up naming them),
weather not at all (stage 1 already decoupled it).

**Stage 5 - retire or re-scope `regions`.** Once every consumer in the
table in section 1.2 reads `land_tiles`, `regions` either goes away or
survives as a naming/display layer only (grouping tiles under a label a
player recognises - "Italia", not "tile italy_02" - which tiles already
support via their own `old_region` field). Not urgent; freight
(section 2.4) may reasonably keep using region centroids indefinitely.

---

## 6. The verification story

`perf_fingerprint.py record`/`check` proves nine scenarios byte-identical
and takes about six minutes (CLAUDE.md §5's own figure; I did not re-run the
full six-minute suite myself for this document, since section 3's isolated
timings of the two hot functions already give a real, directly-measured
base for the extrapolation, which is what was asked for - re-running the
whole suite would not add a number this document needs). It compares
FULL-PRECISION SIMULATION OUTPUT, so it is the wrong tool wherever a stage
is EXPECTED to move a number, and the right one everywhere else.

| Stage | Will `perf_fingerprint` pass? | What to check instead |
|---|---|---|
| 0 (intensive margin) | No - `iugerum_land` and downstream prices move | `sim/tests/test_land.py`'s own targeted assertions (`test_han_china_no_longer_prices_at_zero` and neighbours); re-record a NEW fingerprint baseline after, so future stages compare against the post-stage-0 world, not pre-stage-0 |
| 0.5 (weather correlation) | No - harvest variance changes for every civilisation with >1 region | `sim/tests/test_growing_season_weather_correlation.py` (15 tests, confirmed passing, see below); re-record baseline |
| 1 (cap weather cells) | No, for any civilisation whose cell count today exceeds the chosen cap | A targeted variance test per affected civilisation (does capped-n variance still sit close to the uncapped-n figure it approximates?), not the fingerprint |
| 2 (land rent onto tiles) | No - this is the stage most likely to move the most prices, per Complaints/32/43 | `sim/tests/test_land.py`, `sim/tests/test_price_solver_land.py` (confirmed registered as topic `price_solver_land` in `sim/test_regressions.py --list`), and a fresh `audit_costs.py` pass to see where the cost base actually moved |
| 3 (deposits onto tiles) | No, if it changes ore rent | Whatever `sim/world/deposits.py`'s own test module asserts, plus a before/after `audit_costs.py --materials` |
| 4 (10,000 tiles) | No - land rent granularity changes again | `sim/tests/test_geography_tiles.py`'s STRUCTURAL checks (its own docstring: "orderings and structural properties, not particular numbers" - it is written to survive exactly this kind of regeneration) |
| 5 (retire `regions`) | Depends - if every consumer already reads `land_tiles` identically, this can be a true no-op and SHOULD pass the fingerprint | If it does not pass, something was still silently reading `regions` |

**How to tell a deliberate change from a regression, across all of the
above:** the fingerprint's own report names the FIRST YEAR two runs diverge
and what value diverged. For any stage in this list, the expected diff is
narrow and named in this table (a price, a variance figure, a rent number).
A regression looks different in kind: it shows up in a civilisation or a
quantity this stage's own description does not touch at all (freight
distances moving when only land rent was supposed to change, for instance),
or it shows up as a crash/exception rather than a numeric drift, or the
`sim/tests/test_determinism.py` guard against `id()`-based caching (CLAUDE.
md §6) starts failing, which none of these stages have any reason to touch.
"The number I expected to move, moved" is not a finding; "a number I did
not expect to move, moved" is.

I ran the weather-specific test files directly rather than assume their own
docstrings' claims about pass/fail state, since those docstrings are
themselves prose and CLAUDE.md §8 asks that assertions be measured:

```
python3 -m unittest sim.tests.test_regional_weather_wiring -v
-> Ran 15 tests in 7.961s, OK (all pass)

python3 -m unittest sim.tests.test_growing_season_weather_correlation -v
-> Ran 15 tests in 6.694s, OK (all pass)
```

Both pass today. This is worth flagging precisely because `test_growing_
season_weather_correlation.py`'s own module docstring says it replaces "
`RegionWeightsTests`/`PooledWeatherMultiplierTests` (which pinned WIRING
TWO's per-region-record mechanism bit for bit, and fail after this
change)" - that claim did not hold when I actually ran the old file. Either
those two classes test properties general enough to survive the tile
migration (weights summing to one, cells sitting inside their claimed home
region - true under EITHER mechanism), or this is itself a small piece of
stale documentation. I did not chase which; I ran it and report what
happened rather than repeat the docstring's claim unchecked.

Registered topics touching this area, confirmed via `python3 sim/test_
regressions.py --list`: `land`, `geography_tiles`, `regional_weather_
wiring`, `growing_season_weather_correlation`, `price_solver_land` - all
five exist today and can be run narrowly with `--only` during any of the
staged work above, e.g. `python3 sim/test_regressions.py --only land,
growing_season_weather_correlation`.

---

## 7. Recommendation

**Do stage 1 (decouple weather cell count from map resolution) before
anything else in this document, including stage 2.** Reasons, in order of
how much they weigh:

1. It is the one stage that unblocks the stakeholder's stated 10,000-tile
   goal directly, and it does so without touching land rent, mining, or
   freight at all - lowest blast radius of any stage that actually helps.
2. It is defensible on the model's own terms, not just as an optimisation:
   section 4.2 shows the current 150,000 km2 tile is already within one
   decorrelation length of its neighbours, and a 10,000-tile grid (about
   115 km cells) would sit well inside it - so capping weather resolution
   below full tile resolution is closer to the physically meaningful
   answer, not a concession against it.
3. It does not require a policy decision (unlike numpy, section 4.1) or
   nontrivial new engineering (unlike sparse/banded or hierarchical
   methods, sections 4.3-4.4) - it is a bound on an existing loop.
4. Pair it with stage 4.5 (cache the factorisation per civilisation) in the
   same pass - both are cheap, both are provably answer-preserving, and
   caching alone would not fix the `--session`-per-process pattern in
   section 3.4 the way capping does.

After that, **stage 2 (land rent onto tiles) before stage 4 (grow the tile
count)** - migrating the consumer that is currently WRONG (section 2.2:
region-size-blind rent) matters more than migrating the consumer that is
merely coarse, and doing it before the tile count grows means it gets
tested once at today's scale rather than twice.

**Do not do stage 4 (regenerate at 10,000 tiles) until stage 1 and stage 2
are both shipped and separately verified.** Growing the tile count first
would reproduce section 3.4's twelve-minute-per-run problem immediately,
for no benefit yet realised on the land-rent side, and would make stage 2's
own before/after comparison harder to read (two things changing size at
once instead of one).

Stage 3 (deposits) and stage 5 (retiring `regions`) are real but not
urgent; neither blocks the stakeholder's two stated items, and stage 3 in
particular should start with the kind of measurement Complaints/46 and 50
did for their own consumers - a concrete wrong number - before committing
to a rewrite, since I did not find one already on record for deposits.

Do not add numpy (4.1) as part of this work. It is the faster fix in raw
constant-factor terms, but it does not remove the cubic exponent (stage 1
does, for free, with no new dependency), and taking on this project's first
third-party dependency to solve a problem stage 1 already solves is a
worse trade than it looks, not a better one.
