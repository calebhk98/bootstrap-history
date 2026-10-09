"""The staffing half of the gate `open` applies, as one function."""


class OpenGateMixin:

    def staffing_open_refusal(self, node_id, unit_count=1.0, with_advice=True):
        """Why the people to run this concern are not free now, else None.

        `open` refuses with this text and `stuck` recommends only what
        passes it, so the two cannot disagree.
        """
        sch_free, art_free = self.venture_staff_free()
        need_sch, need_art = self.venture_hands(node_id)
        need_sch, need_art = need_sch * unit_count, need_art * unit_count
        foreman_trade, foreman_fte = self.venture_foreman(node_id)
        foreman_fte *= unit_count
        if need_sch > sch_free + 0.01 or need_art > art_free + 0.01:
            return ("nobody free to keep an eye on it: it needs %.2f "
                    "scholars and %.2f craftsmen to supervise (a continuous "
                    "share of their year, not a headcount), and you have "
                    "%.2f and %.2f not already watching something else.%s"
                    % (need_sch, need_art, sch_free, art_free,
                       " Hire, teach, or close something." if with_advice else ""))
        if foreman_trade and foreman_fte > self.venture_foreman_free(foreman_trade) + 0.01:
            return ("no qualified foreman is free: this concern needs "
                    "%.2f %s FTE to supervise its specialist work, and "
                    "you have %.2f free. Hire a %s or close another "
                    "concern using one. Generic artisans cannot "
                    "substitute for this trade."
                    % (foreman_fte, foreman_trade,
                       self.venture_foreman_free(foreman_trade), foreman_trade))
        for trade, people in self.venture_garrison(node_id, unit_count).items():
            free = self.venture_foreman_free(trade)
            if people > free + 0.01:
                return ("no garrison is free: this work needs %.2f %s to man it, and you have %.2f free. "
                        "%s" % (people, trade, free,
                                ("Hire %ss from the labour market or close another work using them."
                                 % trade) if with_advice else ""))
        return None
