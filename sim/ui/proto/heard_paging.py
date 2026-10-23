"""The "heard of but cannot begin" list is cut to a page, and says how many more there are."""

HEARD_PAGE_SIZE = 25


def heard_page(heard_all, heard_offset):
    """(the page of `heard_all` starting at `heard_offset`, how many entries lie beyond it)."""
    page = heard_all[heard_offset:heard_offset + HEARD_PAGE_SIZE]
    return page, max(0, len(heard_all) - heard_offset - len(page))
