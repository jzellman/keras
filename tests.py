import os
os.environ['WEB_ENV'] = 'test'

import unittest
from datetime import datetime

import utils


def dt(year=2000, month=2, day=14, hour=1, minute=1):
    return datetime(**locals())


class TestUtils(unittest.TestCase):
    def test_day_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.day_range(d)
        self.assertEqual(datetime(2010, 4, 16), start)
        self.assertEqual(datetime(2010, 4, 16, 23, 59, 59, 999999), end)

    def test_week_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.week_range(d)
        self.assertEqual(datetime(2010, 4, 11), start)
        self.assertEqual(datetime(2010, 4, 17, 23, 59, 59, 999999), end)

    def test_month_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.month_range(d)
        self.assertEqual(datetime(2010, 4, 1), start)
        self.assertEqual(datetime(2010, 4, 30, 23, 59, 59, 999999), end)

    def test_year_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.year_range(d)
        self.assertEqual(datetime(2010, 1, 1), start)
        self.assertEqual(datetime(2010, 12, 31, 23, 59, 59, 999999), end)

    def test_prev_day_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.prev_day_range(d)
        self.assertEqual(datetime(2010, 4, 15), start)
        self.assertEqual(datetime(2010, 4, 15, 23, 59, 59, 999999), end)

    def test_prev_week_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.prev_week_range(d)
        self.assertEqual(datetime(2010, 4, 4), start)
        self.assertEqual(datetime(2010, 4, 10, 23, 59, 59, 999999), end)

    def test_prev_month_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.prev_month_range(d)
        self.assertEqual(datetime(2010, 3, 1), start)
        self.assertEqual(datetime(2010, 3, 31, 23, 59, 59, 999999), end)

    def test_prev_year_range(self):
        d = datetime(2010, 4, 16, 23, 3)
        start, end = utils.prev_year_range(d)
        self.assertEqual(datetime(2009, 1, 1), start)
        self.assertEqual(datetime(2009, 12, 31, 23, 59, 59, 999999), end)

    def test_compute_end_time_from_duration(self):
        start_time = dt()
        computed = utils.compute_end_time(" 15 ", start_time)
        self.assertEqual(dt(minute=16), computed)

    def test_compute_end_time_from_hour_ordinal(self):
        start_time = dt()
        computed = utils.compute_end_time(' 4:57 AM ', start_time)
        self.assertEqual(dt(hour=4, minute=57), computed)

        computed = utils.compute_end_time(' 04:57 AM  ', start_time)
        self.assertEqual(dt(hour=4, minute=57), computed)

        start_time = dt(hour=13, minute=1)
        computed = utils.compute_end_time(' 04:57 PM  ', start_time)
        self.assertEqual(dt(hour=16, minute=57), computed)

    def test_compute_end_time_from_text(self):
        start_time = dt()
        computed = utils.compute_end_time(' 15  minutes ', start_time)
        self.assertEqual(dt(minute=16), computed)

        computed = utils.compute_end_time(' 15 hours  12 minutes ', start_time)
        self.assertEqual(dt(hour=16, minute=13), computed)

    def test_compute_end_time_empty(self):
        computed = utils.compute_end_time(None, None)
        self.assertEqual(None, computed)
        computed = utils.compute_end_time("  ", None)
        self.assertEqual(None, computed)


if __name__ == '__main__':
    unittest.main()
