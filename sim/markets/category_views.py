"""The goods categories: one market shared by every seller, and the income effect of cheap staples."""
from . import categories, rules


class Categories:

	def goods_reach_factor(self):
		"""How much further than a purely local market your goods can travel, and so how fast you saturate the market you
		can reach: the mechanics' reach channel, capped."""
		return rules.reach_factor(self.needs.effect_factor("reach", 1.0))

	def goods_category_state(self, category):
		"""(sellers, age of the oldest, the category's curve) for a goods category: every concern of the seat operating in it
		and every actor's, and how long the oldest of the seat's has been open. None if this is not a goods category at all
		or nothing sells in it. Cached per year, operating set and actor concerns."""
		config = categories.GOODS_CATEGORIES.get(category)
		if not config:
			return None
		year = self.needs.year()
		key = (year, self.needs.legacy_done_versions()[1], self.needs.concern_versions()[0])
		cache = self._seat_cache("goods_cat_state")
		if cache is None or cache[0] != key:
			cache = (key, {})
			self._set_seat_cache("goods_cat_state", cache)
		bucket = cache[1]
		if category in bucket:
			return bucket[category]
		operating = self.needs.operating()
		done_year = self.needs.done_year()
		ages = []
		for node_id in self.nodes_in_category(category):
			if node_id not in operating:
				continue
			started = self.needs.venture_opened_year(node_id, None)
			if started is None:
				started = done_year.get(node_id, year)
			ages.append(max(0.0, year - started))
		# firms and governments selling into the category share the same demand
		sellers = len(ages) + self.needs.concern_counts[category]
		if not sellers:
			bucket[category] = None
			return None
		result = (sellers, max(ages, default=0.0), config)
		bucket[category] = result
		return result

	def nodes_in_category(self, category):
		"""Every node key that carries this goods category, in the tree's own order (never changing after load)."""
		cache = self._nodes_by_category
		if cache is None:
			cache = {}
			for node_id, node in self.needs.tree_nodes().items():
				node_category = node.get("cat")
				if node_category:
					cache.setdefault(node_category, []).append(node_id)
			self._nodes_by_category = cache
		return cache.get(category, ())

	def _category_key(self):
		"""What a category's cached figures depend on."""
		done_version, operating_version = self.needs.legacy_done_versions()
		return (self.needs.year(), self.needs.pop_scale(), self.needs.real_output_per_head(), operating_version, done_version,
		        self.needs.concern_versions()[0])

	def goods_category_ratios(self, category, extra=0):
		"""(price ratio, quantity ratio, sellers) for a whole category, shared by every concern that sells into it; `extra`
		more concerns price in as already sharing its supply. None if nothing sells in the category."""
		shared_key = self._category_key()
		cache = self._seat_cache("goods_category_ratios")
		if cache is None or cache[0] != shared_key:
			cache = (shared_key, {})
			self._set_seat_cache("goods_category_ratios", cache)
		bucket = cache[1]
		pair_key = (category, extra)
		if pair_key in bucket:
			return bucket[pair_key]
		state = self.goods_category_state(category)
		if state is None:
			bucket[pair_key] = None
			return None
		sellers, world_age, config = state
		result = rules.category_ratios(config, sellers, extra, world_age, self.needs.pop_scale(), self.goods_reach_factor())
		bucket[pair_key] = result
		return result

	def goods_category_price_ratio(self, category):
		"""The price this category's market currently pays, as a fraction of its day-one figure (falls toward the category's
		own floor as supply catches up); None if nothing sells in it."""
		ratios = self.goods_category_ratios(category)
		return None if ratios is None else ratios[0]

	def essential_price_ratio(self):
		"""A stand-in for the cost of living: the mean price ratio of the essential categories the seat sells in, lowered by
		the household's own farmland."""
		return rules.essential_price_ratio(
			[self.goods_category_price_ratio(category) for category in sorted(categories.ESSENTIAL_CATEGORIES)],
			self.needs.farm_holdings()["hectares"])

	def income_factor(self):
		"""How much extra a population has to spend on everything that is not a staple, from how cheap staples currently are
		(neutral when the seat runs no essential concern)."""
		shared_key = self._category_key() + (self.needs.farm_holdings()["hectares"] or 0.0,)
		cache = self._seat_cache("income_factor")
		if cache is not None and cache[0] == shared_key:
			return cache[1]
		factor = rules.income_factor(self.essential_price_ratio())
		self._set_seat_cache("income_factor", (shared_key, factor))
		return factor

	def goods_category_factor(self, category):
		"""What one seller's revenue in a goods category has become relative to the day-one figure, once the whole category's
		supply (the seat's concerns and every actor's) is shared out: price times quantity over the number of sellers,
		lifted or dampened by the income effect."""
		shared_key = self._category_key() + (self.needs.farm_holdings()["hectares"] or 0.0,)
		cache = self._seat_cache("goods_mkt_op_factor")
		if cache is None or cache[0] != shared_key:
			cache = (shared_key, {})
			self._set_seat_cache("goods_mkt_op_factor", cache)
		bucket = cache[1]
		if category in bucket:
			return bucket[category]
		ratios = self.goods_category_ratios(category)
		if ratios is None:
			bucket[category] = 1.0
			return 1.0
		factor = rules.seller_revenue_factor(*ratios, self._staples_factor(category))
		bucket[category] = factor
		return factor

	def goods_category_factor_with_entrants(self, category, entrants):
		"""One seller's revenue in a goods category relative to day one once `entrants` more sellers share the category's
		demand: the clearing price falls as supply rises."""
		ratios = self.goods_category_ratios(category, extra=entrants)
		if ratios is None:
			return 1.0
		return rules.seller_revenue_factor(*ratios, self._staples_factor(category))

	def _staples_factor(self, category):
		return 1.0 if category in categories.ESSENTIAL_CATEGORIES else self.income_factor()
