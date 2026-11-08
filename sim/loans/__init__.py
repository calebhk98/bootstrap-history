"""The term loans as a table: the one copy of every loan the economy has out, and the kernels that read and change it.

    columns.py         the table's columns, each with a meaning and a unit
    store.py           LoanStore: the table, the numbering of its names, and the operations that change it as a whole
    view.py            LoanRow and LoanList: a loan and the loan list as Contract-like objects over the columns (UI, protocol, mods, tests)
    select.py          selections of rows by name (what a lender may sell, what a title pledges)
    read_kernels.py    per-agent totals added in loan order; reads.py hands them back as the dicts the credit rules take
    service_kernel.py  the yearly service: each borrower pays its due loans, in id order, until its cash runs out
    write_down_kernel.py, close_kernel.py   a write-off of loans; the close's loan loop
    clearing_tables.py, clearing_kernel.py  one clearing of the credit market over a requests table and an offers table
    risk_kernel.py, order_kernel.py         its parts: the price of risk, and queues of lenders and borrowers

Money moves only through the book (`sim/economy/transfer_rows.py` posts the payments as rows). The rules are described in
docs/architecture/COMPILED_YEAR.md."""
