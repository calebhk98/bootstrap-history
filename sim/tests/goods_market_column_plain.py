"""`MarketColumn.items` and iteration as they were before the cached saved-order rank: the names sorted with a key per call."""


def items_by_sorting(names, figures, integer=False):
    ordered = sorted(zip(names, figures), key=lambda pair: pair[0].replace("|", "\x00"))
    return [(name, int(figure) if integer else figure) for name, figure in ordered]
