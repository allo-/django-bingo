from django.utils import timezone
from django.conf import settings

import pytz
from datetime import datetime

# Time range, in which a game can be started. None = no limit
# or a ((Hour, Minute), (Hour, Minute)) tuple defining the range.
GAME_START_TIMES = getattr(settings, "GAME_START_TIMES", None)

# Time, after which a running game is ended. Has only effect, if
# GAME_START_TIMES is set, and needs to be outside of GAME_START_TIMES.
# Values: tuple (hour, minute) or None for no restriction
GAME_END_TIME = getattr(settings, "GAME_END_TIME", None)


def get_times():
    now = timezone.get_current_timezone().normalize(timezone.now())

    start_time_start = None
    start_time_end = None
    end_time = None
    if GAME_START_TIMES:
        start, end = GAME_START_TIMES
        start_time_start = now.replace(
            hour=start[0], minute=start[1], second=0, microsecond=0)
        start_time_end = now.replace(
            hour=end[0], minute=end[1], second=0, microsecond=0)

        # when the end of start time is "before" the start of start time,
        # the end of start time is tomorrow
        if start_time_end < start_time_start:
            start_time_end += timezone.timedelta(1, 0)

    if GAME_END_TIME:
        end = GAME_END_TIME
        end_time = now.replace(
            hour=end[0], minute=end[1], second=0, microsecond=0)

        # when the end time is "before" the end of start timeend_time,
        # the game ends tomorrow
        if start_time_end is not None and end_time < start_time_end:
            end_time = end_time + timezone.timedelta(1, 0)

    return {
        'now': now,
        'start_time_start': start_time_start,
        'start_time_end': start_time_end,
        'end_time': end_time
    }


def get_endtime():
    return get_times()['end_time']


def is_starttime():
    if GAME_START_TIMES is None:
        return True
    else:
        times = get_times()
        return times['start_time_start'] \
            < times['now'] \
            < times['start_time_end']


def is_after_endtime():
    if GAME_END_TIME is None or is_starttime():
        return False
    else:
        times = get_times()
        return times['end_time'] < times['now']
