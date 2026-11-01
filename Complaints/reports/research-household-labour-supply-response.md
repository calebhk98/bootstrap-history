# Research: how pre-industrial households' market labour supply responded to the wage

Input to Complaint 960 (the first-year supply schedule is nearly vertical down to the reservation) and to
`research-labour-models.md` recommendation 5. Question: is there a sourced elasticity of hours or days sold with
respect to the wage, and a sourced role for the home alternative (own plot, by-employments), that could set how much
the hours a household sells rise with the wage?

Labels: **[read]** (full text or abstract page opened in this session), **[snippet]** (search-result text only, not
opened), **[no source found]**.

Result: **no source found** for a numerical wage elasticity of hours or days worked in any pre-industrial setting. The
opened sources say the direction is contested (backward-bending at low income, per Koyama) and that the days worked
were bounded by seasonal demand as much as by household choice (Stephenson). No elasticity is typed into code.

## Sources

- **Koyama 2012** [read, abstract pages only: econpapers.repec.org/RePEc:eee:jeborg:v:81:y:2012:i:2:p:505-523 and the
  Mercatus listing]. Mark Koyama, "The transformation of labor supply in the pre-industrial world", Journal of
  Economic Behavior & Organization 81(2), 505-523.
  - "In pre-industrial economies labor supply curves bent backwards at very low levels of income."
  - Model in which consumption takes time: a rise in subsistence costs and a fall in the price of time-intensive
    consumption can both raise hours, but "only the latter would lead to an increase in the elasticity of labor
    supply". England is read as the second case; Italy (and possibly Japan) as hours raised by involution.
  - No elasticity figure in the abstract; full text not opened. Nothing on land or by-employment in the opened text.
- **Stephenson 2018** [read, full text]. Judy Z. Stephenson, "Looking for work? Or looking for workers? Days and hours of
  work in London construction in the eighteenth century", MPRA Paper 84828 (mpra.ub.uni-muenchen.de/84828/).
  - Abstract: "Construction workers' working days were bounded by structural factors of both supply and demand, men
    worked a far lower number of days than has been assumed until now."
  - Days worked per week when on site averaged 5.2, "not a lot of Saint Mondays"; the maximum year on the seasonal
    low of January and a 5.2-day week is 250.6 days; "The clear evidence is that they did not" all get every week. Her
    reading: industriousness "was determined by Kempster's demand for skilled labour as well as any leisure
    preference". She notes days not worked cannot be split between employer rationing and chosen leisure.
  - A single firm's skilled and semi-skilled London men, 1700s: not agricultural, not a wage elasticity.
- **Jensen, Radu and Sharp 2019** [read, full text, SDU DP 10/2019, sdu.dk .../dpbe10_2019.pdf]. Only the line (in a
  note under a figure of days a week by skill) that low-skilled workers who worked fewer days a week were "probably
  again because this category includes agricultural workers with their own land to tend to". A reading by the authors,
  not a measurement. Earlier figures on days (292 casual, 184 with winter seasonality) are in `research-working-year.md`.
- **Allen and Weisdorf 2011**, Economic History Review 64(3) (Copenhagen DP 10-14) [snippet only this session: the
  KU server returned 503 and a reset; the PDF was not opened here]. The search abstract says the authors compute the
  working year needed to buy a fixed basket and find two rural "industrious" episodes attributable to hardship, not to
  a consumer revolution. `research-working-year.md` quotes the paper from an earlier session; that is not re-opened.
- **Humphries and Weisdorf 2015**, "The wages of women in England, 1260-1850", Journal of Economic History 75
  [snippet only, abstract]. Nothing on days worked by agricultural labourers or an elasticity. A separate search
  snippet attributes to a Humphries-Weisdorf working paper the statement that farm workers' supply curve "appears to
  be largely backward-bending" and a rise in annual input from under 150 days (medieval) to over 300 (industrial
  revolution) [snippet, not opened, not relied on].
- **Voth** on eighteenth-century London hours and Saint Monday [snippet only]: the snippet says backward-bending
  supply was tested and rejected as the explanation of longer hours. Not opened, not relied on.
- Search for a numerical wage elasticity of days worked for early modern day labourers or harvest hands returned
  only modern labour-economics pages (modern male elasticity "roughly 0.1" in a review, a different setting).
  **[no source found]** for any pre-industrial value.

## What applies here

- The direction the sources agree on is that the schedule is not vertical in the wage at the margin the household
  decides at, but with no usable magnitude: Koyama says it can bend backward at low income; Stephenson says days
  worked are set at least as much by employers' seasonal demand. A typed elasticity would be unsourced
  (CLAUDE.md section 6): a labelled heuristic needing a `retire`.
- The home alternative is already modelled with a sourced-in-code exponent. `households_hours_offered.plot_hours_kept`
  keeps hours on the plot down to where the next hour there equals the wage, with the next hour's return falling as
  hours rise by the land-labour output elasticity (`LABOUR_OUTPUT_ELASTICITY`, `sim/world/shared_constants.py`). That
  is diminishing returns on the plot, and the hours kept rise as the wage falls (kept hours scale with the ratio of the
  plot's return to the wage to the power one over one minus the elasticity). So a cohort with a plot already has a
  wage-responsive schedule. The household work and plan hours stay fixed (no source on their response either).
- What is missing is not the mechanism but its inputs: a household with no plot (the `small` fixture's, and any
  cohort with no land held) keeps nothing, and `stationary_setup` sets hours so that exactly the hired hours remain.
  A by-employment (spinning, carting, fishing) has no modelled return for a household without land; the opened
  sources give no value for one.
- Verdict: no code change made on this evidence. Whether the stationary opening's plot return is mis-scaled against
  the wage is a measurement of the fixture, not a question these sources answer.
