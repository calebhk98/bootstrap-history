# A novice crew's spoilage share is a chosen figure

**Status:** open - `SCRAPPED_SHARE_OF_EXTRA_EFFORT` is a labelled heuristic with no measured source

**What is wrong now.** A crew still learning a recipe needs more hours per run (`sim/economy/practice.py` `hours_multiplier`, the learning curve) and
loses part of its output: `practice.usable_output_share` takes the extra effort of the practised hours over the booked ones and spoils
`SCRAPPED_SHARE_OF_EXTRA_EFFORT` of it, as a lower yield factor (`practice.yield_after_practice`; `producers.with_practised_yield` for the plain
record, `year_arrays_producers.practised_yields` for the kernels). The share is an even split chosen by the author (confidence D): no source states how
much of a new crew's extra effort is slower work and how much is work redone or thrown away.

**What it would take.** A sourced split of a new crew's extra effort into slower work and scrap (Thornton and Thompson on quality learning in Liberty
shipbuilding, or a defect-rate study of a new line), opened and cited; then the constant takes its value and drops `temporary_heuristic`.
`python3 sim/constants.py --burndown` lists it.

Split from Complaint 644, which wired the curve into spoilage.
