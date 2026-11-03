"""The world, apart from the founder: standalone domain models.

These models import nothing from `sim/engine/` and are tested without a `Sim`; the modules of `sim/` import them.

CONTENTS. Standalone domain models, each importable and testable with no `Sim` and no save file: age-cohort demography
(`demography*.py`, nutrition linking food to births and deaths), agriculture (`agriculture*.py`: yield, storage, labour, tables of
crops, soils, rotations and toolkits), land, deposits and mining, the needs and demand kernels (`need_*.py`, `demand.py`),
military and campaign rules, and the rest listed by `ls sim/world`. The modules of `sim/` call these through their own code;
the economy's farms and plots are the one food model, so `agriculture.py` supplies yield, seed, loss and labour arithmetic and
no national farm year runs.

What that means for anyone editing here: a change to a model's shape reaches every module that imports it, so run the
suite, not just this package's tests. `agriculture.py` is a facade that re-exports `agriculture_core.py` (the declared constants and the
crop, soil, rotation and toolkit tables), `agriculture_yield.py` (the production function), `agriculture_storage.py` (the
granary) and `agriculture_labour.py`.
"""
