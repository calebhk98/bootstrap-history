"""The year's first step: people whose apprenticeship ended join the staff before the year's work is handed out."""
from sim.assembly.api import Part
from sim.reporting.api import RecordEvent


class Apprenticeships(Part):

	def step_apprenticeships(self, seat_id=None):
		# 0. PEOPLE WHOSE APPRENTICESHIP ENDED, FIRST, BEFORE THE YEAR'S WORK
		#    IS HANDED OUT: a man who finishes his training at the turn of the
		#    year works that year, so a machinist promised "ready in 102" must
		#    be usable in 102, not only from 103.
		# People bought this year are not artisans this year.
		workforce = self.seat
		if workforce.training:
			still = []
			for row in workforce.training:
				trade, count = row.trade, row.people
				if self.needs.year() >= row.ready_year:
					if trade:
						# A trade you taught. They are now yours to pay, they are
						# that trade and no other, and they join the labour core's
						# people to be hired at the clearing like anyone.
						self.parts.core.labour.book.add_newcomers(trade, count)
						self.needs.send(RecordEvent.of("training_finished", "%g %s%s finish their training"
						                               % (count, trade, "s" if count != 1 else "")))
						self.parts.core.labour.pools.resync_pools()
					else:
						# They are trained now, so _resync_pools counts them
						# from the people you actually hold - see the note
						# there about why adding to the artisans directly was
						# thrown away at the next call.
						self.needs.send(RecordEvent.of("bought_people_trained", "%g of the people you bought finish "
						                               "learning the work" % round(count, 1)))
				else:
					still.append(row)
			# BEFORE the resync, not after: _resync_pools counts who is still
			# learning off this very list, so recomputing while the matured row
			# was still on it cost a whole extra year of everybody's time.
			workforce.training = still
			self.parts.core.labour.pools.resync_pools()
