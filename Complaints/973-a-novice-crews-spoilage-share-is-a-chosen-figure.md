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

**Searched, no source found.** Opened and read in full text:
- Levitt, List and Syverson 2013 (JPE 121(4)), NBER w18017 PDF (nber.org/system/files/working_papers/w18017/w18017.pdf). It
  measures defects per vehicle only: "defects per vehicle fall more than 80 percent in the first eight weeks of production", and
  a learning exponent of about 0.3 (defects halve per tenfold cumulative output). It states it does not measure unit cost or hours,
  because line speed is driven by demand and calendar effects. With no fall in hours over the same period, no split follows.
- Thompson 2001 working paper "How Much Did the Liberty Shipbuilders Learn?" (econwpa.ub.uni-muenchen.de/econ-wp/dev/papers/9712/9712001.pdf):
  finds the Calship gain in output per worker came with a reduction in quality (fracture probability), so quality fell as speed
  rose; the opposite sign to a scrap share of novice effort, and no split.
- Not opened (abstract or record only, paywalled): Thornton and Thompson 2001 (AER 91(5)) and Hatch and Mowery 1998 (Management
  Science 44(11)). Nothing is cited from them.
Still needed: a study giving both the fall in hours and the fall in scrap or rework over one learning period, whose full text is opened.

Split from Complaint 644, which wired the curve into spoilage.
