"""The state's revenue assessments as tables: one row per declared form, one row per (form, payer), and the kernels that fill them.

A form is a share of a base the world measures (the boundary, `assessment_table.py`, reads each base once through the world's views
and puts its figures in the row). The kernels do what `revenue.py` did per form: the money and tonnes a form yields after the
state's reach and the officials' share (`assess_forms`), the income each payer leaves on the rolls and owes (`assess_payers`), and
what each payer pays when the year's revenue is taken (`plan_collection`). No kernel sees a name: a form, a payer and a material are
numbers; the boundary keeps the names beside the rows."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec
from sim.jit import njit

PLAIN, HELD_BY_PAYERS, LABOUR = 0, 1, 2   # `kind` of a form row

FORMS = TableSpec("RevenueForms", (
    Column("kind", numpy.int8, "0: a share of a base the world measures; 1: a share of what named payers hold; 2: labour owed", "code"),
    Column("base", numpy.float64, "money's worth of the base (kind 2: a year of the liable people's work at the going wage; kind 1: not read)", "currency units"),
    Column("base_tonnes", numpy.float64, "tonnes of the base when it is a good", "tonnes"),
    Column("in_kind", numpy.int8, "1 when the form is paid in a good, so tonnes are taken", "flag"),
    Column("rate", numpy.float64, "share of the base the form takes (kind 2: the share of a working year the days come to)", "fraction"),
    Column("collectible", numpy.float64, "share of what is due that the state's officials reach", "fraction"),
    Column("kept", numpy.float64, "share of what is collected that officials keep", "fraction"),
    Column("person_days", numpy.float64, "kind 2: days of work owed, before any commuted to coin", "person-days"),
    Column("commute", numpy.float64, "kind 2: the share of a labour due paid in coin instead", "fraction"),
    Column("visible_share", numpy.float64, "kind 1: the share of a payer's income left on the rolls after hiding", "fraction"),
    Column("first_payer", numpy.int64, "kind 1: the form's first row in the payers table", "row number"),
    Column("payer_count", numpy.int64, "kind 1: how many payer rows the form has", "rows"),
    Column("assessed_base", numpy.float64, "out: the `base` of the assessment (kind 1: the income left on the rolls)", "currency units"),
    Column("money", numpy.float64, "out: money's worth the form yields after reach and leakage", "currency units"),
    Column("tonnes", numpy.float64, "out: tonnes taken in kind after reach and leakage", "tonnes"),
    Column("concealed", numpy.float64, "out: kind 1: money's worth of income kept off the rolls", "currency units"),
    Column("kept_by_officials", numpy.float64, "out: the share the officials kept (0 when none)", "fraction"),
    Column("coin_money", numpy.float64, "out: money that reaches the purse from nowhere the actors' books show (not goods, not payers; of labour only the commuted share)", "currency units"),
    Column("labour_hours", numpy.float64, "out: kind 2: hours of work the state is owed in labour, after the share commuted", "hours"),
))
RevenueForms = FORMS.make_type(__name__)

PAYERS = TableSpec("RevenuePayers", (
    Column("form", numpy.int64, "the form's row in the forms table", "row number"),
    Column("payer", numpy.int64, "the payer's number among the payers of this assessment", "payer number"),
    Column("income", numpy.float64, "the income the payer earned over the base's period", "currency units"),
    Column("purse", numpy.float64, "what the payer holds when assessed (an owing payer pays no more than this)", "currency units"),
    Column("seen", numpy.float64, "out: the income left on the rolls", "currency units"),
    Column("owed", numpy.float64, "out: what the payer owes the form, after the officials' share", "currency units"),
    Column("first_visit", numpy.int8, "at collection: 1 when this is the first row of its payer, so its purse is the one read", "flag"),
    Column("purse_now", numpy.float64, "at collection: what the payer holds, read for a first visit", "currency units"),
    Column("decided", numpy.int8, "out: 1 when the kernel decided `collected`; 0 leaves the row to the Python rule", "flag"),
    Column("collected", numpy.float64, "out: what the payer pays when the revenue is taken", "currency units"),
))
RevenuePayers = PAYERS.make_type(__name__)


@njit
def after_leakage(amount, kept):
    """authority.after_leakage: what reaches the state of `amount` when officials keep the share `kept`."""
    return amount * (1.0 - max(0.0, min(1.0, kept)))


@njit
def compensate(total, compensation, value):
    """One step of Python's built-in float `sum` (Neumaier): the new running total and compensation."""
    step = total + value
    if abs(total) >= abs(value):
        compensation += (total - step) + value
    else:
        compensation += (value - step) + total
    return step, compensation


@njit
def assess_payers(forms, payers, form):
    """Fill the seen income and the amount owed of every payer row of form `form`, and return the three sums the assessment needs
    (income, seen, owed) added as Python's `sum` adds them. Reads the payers' income and purse and the form's visible share, rate
    and collectible; a payer owes the reach times the lesser of the rate on what is seen and what it holds."""
    gross = seen_total = owed_total = 0.0
    gross_c = seen_c = owed_c = 0.0
    first = forms.first_payer[form]
    for row in range(first, first + forms.payer_count[form]):
        income = payers.income[row]
        payers.seen[row] = max(0.0, income) * forms.visible_share[form]
        payers.owed[row] = forms.collectible[form] * min(forms.rate[form] * payers.seen[row], max(0.0, payers.purse[row]))
        gross, gross_c = compensate(gross, gross_c, income)
        seen_total, seen_c = compensate(seen_total, seen_c, payers.seen[row])
        owed_total, owed_c = compensate(owed_total, owed_c, payers.owed[row])
    return gross + gross_c, seen_total + seen_c, owed_total + owed_c


@njit
def assess_forms(forms, payers):
    """Fill the output columns of every form row. A plain form takes the reach times the rate times the base (and in kind the same
    share of the tonnes); a form on payers takes the sum of what its payers owe; labour is the share of a working year times the base.
    Where officials keep a share, money, tonnes and each payer's amount are cut by it (the payers' sum is cut once, not summed again)."""
    for form in range(forms.row_count[0]):
        kind = forms.kind[form]
        forms.kept_by_officials[form] = 0.0
        forms.concealed[form] = 0.0
        forms.tonnes[form] = 0.0
        if kind == LABOUR:
            forms.assessed_base[form] = forms.base[form]
            forms.money[form] = forms.rate[form] * forms.base[form]
            continue
        if kind == HELD_BY_PAYERS:
            gross, seen_total, owed_total = assess_payers(forms, payers, form)
            forms.assessed_base[form] = seen_total
            forms.money[form] = owed_total
            forms.concealed[form] = gross - seen_total
        else:
            forms.assessed_base[form] = forms.base[form]
            forms.money[form] = forms.collectible[form] * forms.rate[form] * forms.base[form]
            if forms.in_kind[form] == 1:
                forms.tonnes[form] = forms.collectible[form] * forms.rate[form] * forms.base_tonnes[form]
        kept = forms.kept[form]
        if kept > 0.0:
            forms.money[form] = after_leakage(forms.money[form], kept)
            forms.tonnes[form] = after_leakage(forms.tonnes[form], kept)
            forms.kept_by_officials[form] = kept
            first = forms.first_payer[form]
            for row in range(first, first + (forms.payer_count[form] if kind == HELD_BY_PAYERS else 0)):
                payers.owed[row] = after_leakage(payers.owed[row], kept)


@njit
def plan_collection(payers):
    """Decide what each payer pays when the year's revenue is taken: the lesser of what it owes and what it holds (never below
    nothing), for the first row of each payer. A payer's later rows depend on what the earlier postings left of its purse (a posting may
    also cost it carriage), so they are left to the Python rule (`decided` = 0)."""
    for row in range(payers.row_count[0]):
        payers.decided[row] = 0
        payers.collected[row] = 0.0
        if payers.first_visit[row] == 1:
            payers.decided[row] = 1
            payers.collected[row] = min(payers.owed[row], max(0.0, payers.purse_now[row]))


@njit
def receipts(forms, hours_per_working_day):
    """Fill `coin_money` and `labour_hours` of every form row (what `Assessment.coin_money` and the labour owed come to)."""
    for form in range(forms.row_count[0]):
        kind = forms.kind[form]
        forms.coin_money[form] = 0.0
        forms.labour_hours[form] = 0.0
        if kind == LABOUR:
            forms.coin_money[form] = forms.commute[form] * forms.money[form]
            forms.labour_hours[form] = (1.0 - forms.commute[form]) * (forms.person_days[form] * hours_per_working_day)
        elif kind == PLAIN and forms.in_kind[form] == 0:
            forms.coin_money[form] = forms.money[form]


@njit
def collectors_needed(forms, wage, base_per_collector):
    """Collectors the forms need: each form's assessed base in years of an unskilled `wage`, over what a collector handles of that kind of
    base in a year (`base_per_collector[form]`, in wage-years), added in form order."""
    total = 0.0
    for form in range(forms.row_count[0]):
        total += forms.assessed_base[form] / wage / base_per_collector[form]
    return total


@njit
def accumulate_by_group(totals, group, values, count):
    """Add `values[row]` onto `totals[group[row]]` in row order, one add at a time (the order a loop over the forms added them in)."""
    for row in range(count):
        totals[group[row]] += values[row]
