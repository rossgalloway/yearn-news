WEEK_SECONDS = 7 * 24 * 60 * 60


def week_start_timestamp(start_time: int, week: int) -> int:
    """Return the timestamp at which a distributor week starts."""
    return start_time + week * WEEK_SECONDS


def nearest_reporting_week(*, start_time: int, target_period_end: int) -> int:
    """Return the native week whose end is nearest the target boundary."""
    first_week_end = start_time + WEEK_SECONDS
    nearest_week = (target_period_end - first_week_end + WEEK_SECONDS // 2) // WEEK_SECONDS
    return max(0, nearest_week)


def select_latest_closed_pair(
    *,
    primary_start_time: int,
    paired_start_time: int,
    report_timestamp: int,
) -> tuple[int, int]:
    """Select the newest aligned native weeks that have both ended."""
    primary_current_week = (report_timestamp - primary_start_time) // WEEK_SECONDS
    primary_week = primary_current_week - 1
    if primary_week < 0:
        raise ValueError("No completed primary reward week is available")

    primary_period_end = week_start_timestamp(primary_start_time, primary_week + 1)
    paired_week = nearest_reporting_week(
        start_time=paired_start_time,
        target_period_end=primary_period_end,
    )
    paired_period_end = week_start_timestamp(paired_start_time, paired_week + 1)

    if paired_period_end > report_timestamp:
        primary_week -= 1
        paired_week -= 1

    if primary_week < 0 or paired_week < 0:
        raise ValueError("No completed reward-week pair is available")

    return primary_week, paired_week
