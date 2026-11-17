from datetime import datetime

from django.test import SimpleTestCase

from scheduling.services.overlap import overlaps, subtract_interval


class OverlapTests(SimpleTestCase):
    def test_overlaps_when_inside(self):
        self.assertTrue(
            overlaps(
                datetime(2026, 11, 12, 10, 0),
                datetime(2026, 11, 12, 10, 30),
                datetime(2026, 11, 12, 9, 0),
                datetime(2026, 11, 12, 12, 0),
            )
        )

    def test_no_overlap_when_touching(self):
        self.assertFalse(
            overlaps(
                datetime(2026, 11, 12, 10, 30),
                datetime(2026, 11, 12, 11, 0),
                datetime(2026, 11, 12, 9, 0),
                datetime(2026, 11, 12, 10, 30),
            )
        )

    def test_subtract_middle_leaves_two(self):
        result = subtract_interval(
            datetime(2026, 11, 12, 9, 0),
            datetime(2026, 11, 12, 12, 0),
            datetime(2026, 11, 12, 10, 0),
            datetime(2026, 11, 12, 10, 30),
        )
        self.assertEqual(
            result,
            [
                (datetime(2026, 11, 12, 9, 0), datetime(2026, 11, 12, 10, 0)),
                (datetime(2026, 11, 12, 10, 30), datetime(2026, 11, 12, 12, 0)),
            ],
        )

    def test_subtract_all_leaves_nothing(self):
        result = subtract_interval(
            datetime(2026, 11, 12, 10, 0),
            datetime(2026, 11, 12, 10, 30),
            datetime(2026, 11, 12, 9, 0),
            datetime(2026, 11, 12, 12, 0),
        )
        self.assertEqual(result, [])
