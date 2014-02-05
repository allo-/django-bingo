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

# Time, after which voting is possible.
# Needs to come after the start time start.
VOTE_START_TIME = getattr(settings, "VOTE_START_TIME", None)


def now():
    return timezone.get_current_timezone().normalize(timezone.now())


def get_times():
    time_now = now()

    start_time_start = None
    start_time_end = None
    end_time = None
    vote_start_time = None
    if GAME_START_TIMES:
        start, end = GAME_START_TIMES
        start_time_start = time_now.replace(
            hour=start[0], minute=start[1], second=0, microsecond=0)
        start_time_end = time_now.replace(
            hour=end[0], minute=end[1], second=0, microsecond=0)

        # when the end of start time is "before" the start of start time,
        # the end of start time is tomorrow
        if start_time_end < start_time_start:
            start_time_end += timezone.timedelta(1, 0)

    if GAME_END_TIME:
        end = GAME_END_TIME
        end_time = time_now.replace(
            hour=end[0], minute=end[1], second=0, microsecond=0)

        # when the end time is "before" the end of starttime_end,
        # the game ends tomorrow
        if start_time_end is not None and end_time < start_time_end:
            end_time = end_time + timezone.timedelta(1, 0)

    if VOTE_START_TIME:
        vote_start = VOTE_START_TIME
        vote_start_time = time_now.replace(
            hour=vote_start[0], minute=vote_start[1], second=0, microsecond=0)

        # The vote time must come after the start of starttime.
        # If it comes before, it must be tomorrow
        if start_time_start is not None and vote_start_time < start_time_start:
            vote_start_time = vote_start_time + timezone.timedelta(1, 0)

    # some sanity checks
    if GAME_START_TIMES and VOTE_START_TIME:
        start_time_start < vote_start_time
    if GAME_END_TIME and VOTE_START_TIME:
        assert end_time > vote_start_time
    if GAME_START_TIMES and GAME_END_TIME:
        assert end_time > start_time_end

    return {
        'now': time_now,
        'start_time_start': start_time_start,
        'start_time_end': start_time_end,
        'end_time': end_time,
        'vote_start_time': vote_start_time,
    }


def get_endtime():
    """ returns the (static) game end time """
    return get_times()['end_time']


def is_starttime():
    """
        returns True, if no start times are set, or the current time
        lies inside the starttime.
    """
    if GAME_START_TIMES is None:
        return True
    else:
        times = get_times()
        return times['start_time_start'] \
            < times['now'] \
            < times['start_time_end']


def is_after_votetime_start():
    """
        returns True, if no VOTE_START_TIME is set,
        or the current time is after the start of vote
        time
    """
    if VOTE_START_TIME is None:
        return True
    else:
        times = get_times()
        return times['vote_start_time'] <= times['now']


def is_after_endtime():
    if GAME_END_TIME is None or is_starttime():
        return False
    else:
        times = get_times()
        return times['end_time'] < times['now']
