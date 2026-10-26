"""The year's first step: people whose apprenticeship ended join the staff before the year's work is handed out."""
from sim.reporting.api import RecordEvent


class Apprenticeships:

	def step_apprenticeships(self, seat_id=None):
		# 0. PEOPLE WHOSE APPRENTICESHIP ENDED, FIRST, BEFORE THE YEAR'S WORK
		#    IS HANDED OUT: a man who finishes his training at the turn of the
		#    year works that year, so a machinist promised "ready in 102" must
		#    be usable in 102, not only from 103.
		# People bought this year are not artisans this year.
		household = self.needs.legacy_acting_household()
		if household.training:
			still = []
			for row in household.training:
				cap, completion_year = row[0], row[1]
				trade = row[2] if len(row) > 2 else None
				count = row[3] if len(row) > 3 else 0.0
				if self.needs.year() >= completion_year:
					if trade:
						# A trade you taught. They are now yours to pay, and
						# they are that trade and no other.
						self.labour.add_employed(trade, count)
						self.needs.send(RecordEvent.of("training_finished", "%g %s%s finish their training"
						                               % (count, trade, "s" if count != 1 else "")))
						self.labour.resync_pools()
					else:
						# They are trained now, so _resync_pools counts them
						# from the people you actually hold - see the note
						# there about why adding to household.artisans directly was
						# thrown away at the next call.
						self.needs.send(RecordEvent.of("bought_people_trained", "%g of the people you bought finish "
						                               "learning the work" % round(cap / 0.55, 1)))
				else:
					still.append(row)
			# BEFORE the resync, not after: _resync_pools counts who is still
			# learning off this very list, so recomputing while the matured row
			# was still on it cost a whole extra year of everybody's time.
			household.training = still
			self.labour.resync_pools()
