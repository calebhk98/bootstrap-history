"""Ballpark numbers behind how taxpayers hide income from a form; each cites the pages it was read from."""
from sim.constants import declare

HIDEABLE_SHARE_OF_INCOME = declare(
	"HIDEABLE_SHARE_OF_INCOME", 0.55, kind="engineering_estimate", unit="share of a payer's income",
	source="Modern analogue for income with no third-party reporting: IRS tax-gap net misreporting percentages, tax years "
		"2014-2016, 1 per cent of wages and salaries (withheld and reported by the employer), 15 per cent of partnership and "
		"S-corporation income and 55 per cent of sole-proprietor income (Congressional Research Service IF11887, "
		"https://www.everycrsreport.com/reports/IF11887.html, opened 2026-11). Pre-modern direct evidence: Arslan 2022 "
		"(Medeniyet Belleten 2/3, p. 21, https://dergipark.org.tr/en/download/article-file/2568111) finds 14 per cent of the "
		"registered adult men of Uskudar again missing from the 1560 tahrir, a lower bound on persons off the rolls. Further opened pages (2026-11): Kleven, Knudsen, Kreiner, Pedersen and Saez 2011, Econometrica 79(3), Danish randomised audit (https://eml.berkeley.edu/~saez/kleven-knudsen-kreiner-pedersen-saezEMA11taxaudit.pdf): detected evasion 14.9 per cent of self-employment income against 1.1 per cent of personal income (mostly third-party reported), and 44.9 per cent of self-employed taxpayers adjusted; audits find only part, and the paper cites the US practice of multiplying detected underreporting by 3.28, which would put the self-employed at 14.9 x 3.28 = 49 per cent, near 0.55, while the detected figure alone is 3.7 times lower. Wikipedia, Tax evasion (opened): UK 2016-17 wider tax gap 5.7 per cent of liabilities, Scandinavian evasion about 3 per cent of personal taxes (Alstadsaeter et al. 2017) and about 30 per cent for the top 0.01 per cent of wealth. Wikipedia, Poll taxes of 1376-1381 (opened): the 1379 poll tax raised 18,600 pounds of 50,000 sought and the 1381 tax was evaded in the south-east by refusing to register; the target was a hope, not a measured base, so only the direction is evidence. Medieval lay subsidy under-assessment: no source found.",
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
