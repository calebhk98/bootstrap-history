"""The "heard of but cannot begin" list is paged (`heard_paging.heard_page`, used by `available`): a page is cut at its size, says
how many remain, and successive pages do not repeat."""
QUICK_TOPIC = True

import unittest

from sim.ui.proto.heard_paging import HEARD_PAGE_SIZE, heard_page

HEARD = ["node_%03d" % i for i in range(60)]


class HeardPageTest(unittest.TestCase):
    def test_the_first_page_is_cut_at_its_size_and_counts_what_is_left(self):
        page, more = heard_page(HEARD, 0)
        self.assertEqual(page, HEARD[:HEARD_PAGE_SIZE])
        self.assertEqual(more, len(HEARD) - HEARD_PAGE_SIZE)

    def test_successive_pages_do_not_repeat_and_the_last_has_nothing_beyond_it(self):
        first, _more = heard_page(HEARD, 0)
        second, more_after_second = heard_page(HEARD, HEARD_PAGE_SIZE)
        third, more_after_third = heard_page(HEARD, 2 * HEARD_PAGE_SIZE)
        self.assertFalse(set(first) & set(second))
        self.assertEqual(first + second + third, HEARD)
        self.assertEqual((more_after_second, more_after_third), (len(HEARD) - 2 * HEARD_PAGE_SIZE, 0))

    def test_a_short_list_fits_one_page_with_nothing_more(self):
        self.assertEqual(heard_page(HEARD[:3], 0), (HEARD[:3], 0))

    def test_an_offset_past_the_end_is_an_empty_page(self):
        self.assertEqual(heard_page(HEARD, 500), ([], 0))


if __name__ == "__main__":
    unittest.main()
