"""Ballpark numbers behind how taxpayers hide income from a form; each cites the pages it was read from."""
from sim.constants import declare

HIDEABLE_SHARE_OF_INCOME = declare(
	"HIDEABLE_SHARE_OF_INCOME", 0.55, kind="engineering_estimate", unit="share of a payer's income",
	source="Modern analogue for income with no third-party reporting: IRS tax-gap net misreporting percentages, tax years "
		"2014-2016, 1 per cent of wages and salaries (withheld and reported by the employer), 15 per cent of partnership and "
		"S-corporation income and 55 per cent of sole-proprietor income (Congressional Research Service IF11887, "
		"https://www.everycrsreport.com/reports/IF11887.html, opened 2026-11). Pre-modern direct evidence: Arslan 2022 "
		"(Medeniyet Belleten 2/3, p. 21, https://dergipark.org.tr/en/download/article-file/2568111) finds 14 per cent of the "
		"registered adult men of Uskudar again missing from the 1560 tahrir, a lower bound on persons off the rolls.",
	confidence="C",
	why="The most of its income a payer can keep out of the state's rolls however it tries; wages and rents in plain view "
		"cannot be. A pre-modern state had almost no third-party reporting of income, so the ceiling is read from the "
		"modern income class that has none: sole-proprietor income, 55 per cent misreported net (the wage class at 1 per cent "
		"is the floor of what is in plain view). A ballpark from an analogue, not a measure of any pre-modern state; the "
		"Uskudar figure is persons, not income, and lies below it, consistent with a lower bound.")
HIDING_MARGINAL_COST_AT_CEILING = declare(
	"HIDING_MARGINAL_COST_AT_CEILING", 0.5, kind="engineering_estimate",
	unit="share of the income hidden, for the last unit hidden",
	source="Derived from two opened pages. Anderson 2014, 'Informal Payments to the Tax Collector in Transition Countries', "
		"Ekonomi-tek 3(2): the average tax bribe ranged from 2.1 per cent of revenues in Croatia to 8.1 per cent in Georgia "
		"(https://dergipark.org.tr/en/download/article-file/1730550). Alm, Martinez-Vazquez and McClellan 2016, J. Economic "
		"Behavior and Organization 124: inspectors who solicit bribes go with 4 to 10 percentage points less of sales reported "
		"(abstract, https://econpapers.repec.org/RePEc:eee:jeborg:v:124:y:2016:i:c:p:146-163). Bribe per unit of sales hidden "
		"is then 2.1/10 = 0.21 at the low end and 8.1/4 = 2.0 at the high end; the geometric middle, "
		"sqrt(0.21 * 2.0) = 0.65, brackets 0.5.",
	confidence="C",
	why="What hiding the last unit of income costs (go-betweens, goods held out of the market, false books) when a payer "
		"already hides all it can; the cost of each unit before it rises in proportion to the share already hidden. "
		"A ballpark from modern bribe-to-evasion ratios (range 0.21 to 2.0 per unit hidden, from firm surveys of "
		"transition economies, not from a pre-modern state). With a penalty in proportion to the tax unpaid the "
		"rate has no effect on hiding except through this curve (Yitzhaki 1974; evasion.py), so it also sets the "
		"size of the whole rate response.")
