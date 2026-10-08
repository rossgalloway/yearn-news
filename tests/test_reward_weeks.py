import unittest

from reward_weeks import (
    WEEK_SECONDS,
    nearest_reporting_week,
    select_latest_closed_pair,
    week_start_timestamp,
)


class RewardWeekSelectionTests(unittest.TestCase):
    def test_ycrv_completed_cycle_ends_at_shared_boundary(self) -> None:
        ycrv_start_time = 1717632455
        current_ycrv_week = 116

        period_end = week_start_timestamp(ycrv_start_time, current_ycrv_week)

        self.assertEqual(period_end, 1787789255)

    def test_rolls_both_cycles_back_before_yyb_crossover(self) -> None:
        ycrv_start_time = 1717632455
        yyb_start_time = 1766071079
        report_timestamp = 1787838000

        selected_weeks = select_latest_closed_pair(
            primary_start_time=ycrv_start_time,
            paired_start_time=yyb_start_time,
            report_timestamp=report_timestamp,
        )

        self.assertEqual(selected_weeks, (114, 34))
        self.assertLessEqual(week_start_timestamp(ycrv_start_time, 115), report_timestamp)
        self.assertLessEqual(week_start_timestamp(yyb_start_time, 35), report_timestamp)

    def test_advances_both_cycles_after_yyb_crossover(self) -> None:
        ycrv_start_time = 1717632455
        yyb_start_time = 1766071079
        report_timestamp = 1787844000

        selected_weeks = select_latest_closed_pair(
            primary_start_time=ycrv_start_time,
            paired_start_time=yyb_start_time,
            report_timestamp=report_timestamp,
        )

        self.assertEqual(selected_weeks, (115, 35))
        self.assertEqual(
            week_start_timestamp(yyb_start_time, 36) - week_start_timestamp(ycrv_start_time, 116),
            15 * 60 * 60 + 10 * 60 + 24,
        )

    def test_finds_nearest_native_week_without_open_week_capping(self) -> None:
        selected_week = nearest_reporting_week(
            start_time=0,
            target_period_end=10 * WEEK_SECONDS,
        )

        self.assertEqual(selected_week, 9)

    def test_requires_a_completed_pair(self) -> None:
        with self.assertRaises(ValueError):
            select_latest_closed_pair(
                primary_start_time=0,
                paired_start_time=WEEK_SECONDS // 2,
                report_timestamp=WEEK_SECONDS,
            )


if __name__ == "__main__":
    unittest.main()
