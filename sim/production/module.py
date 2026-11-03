"""The production module: what runs, what it earns and costs, and how established each industry is.

It answers which of the acting seat's techniques and capabilities are running, what its concerns take in and cost to keep this year,
what a concern makes from the techniques its society runs, how deep an industry's experience is, and which techniques some producer
uses. It owns each seat's stock of industry experience (`ProductionSeat`) and the memos over what is done and operating (`caches`).
The record of what is done, operating and granted, the tree and the economy's objects have not moved yet, so the module reads them
through the views of their owners and every view it publishes is uncached: legacy code writes that state directly. The engine's
household hooks drop the memos by sending the commands here."""
from sim.assembly.api import Module

from .book_sales import BookSales
from .capability import Capability
from .concern_market import ConcernMarket
from .depth import Depth
from .learning import Learning
from .module_views import Views
from .revenue import Revenue
from .techniques import Techniques
from .upkeep import Upkeep
from .volume import Volume


class Production(Module):

	PARTS = {
		"views": Views,
		"revenue": Revenue,
		"upkeep": Upkeep,
		"concern_market": ConcernMarket,
		"book_sales": BookSales,
		"volume": Volume,
		"learning": Learning,
		"depth": Depth,
		"techniques": Techniques,
		"capability": Capability,
	}
