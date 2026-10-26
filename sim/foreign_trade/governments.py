"""What happens to a partner's state when the founder's people deal with it.

(needs: cast)"""
from typing import Any


class Governments:

    def apply_record_stock_taken(self, command: Any) -> None:
        """Smugglers took stock out of a partner's holding, so its state holds that much less."""
        government = self.partner_government(command.partner)
        if government is not None:
            taken = government.record.stock_taken
            taken[command.material] = taken.get(command.material, 0.0) + command.units

    def apply_close_markets_to(self, command: Any) -> None:
        government = self.partner_government(command.partner)
        if government is not None:
            government.close_markets_to(command.party, command.until)
