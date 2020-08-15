from django.utils import timezone
from django.conf import settings
from . import config

from datetime import datetime, timedelta

def now():
    return timezone.localtime()

def get_times(site):
    time_now = now()

    start_time_begin = config.get("start_time_begin", site=site)
    if start_time_begin is not None:
        start_time_begin = timezone.make_aware(
                datetime.combine(time_now, start_time_begin))

    start_time_end = config.get("start_time_end", site=site)
    if start_time_end is not None:
        start_time_end = timezone.make_aware(datetime.combine(
            time_now, start_time_end))

    end_time = config.get("end_time", site=site)
    if end_time is not None:
        end_time = timezone.make_aware(datetime.combine(time_now, end_time))

    vote_start_time = config.get("vote_start_time", site=site)
    if vote_start_time is not None:
        vote_start_time = timezone.make_aware(datetime.combine(
            time_now,vote_start_time))

    if start_time_begin is not None and start_time_end is not None:
        # when the end of start time is "before" the start of start time,
        # the end of start time is tomorrow
        if start_time_end < start_time_begin:
            start_time_end += timezone.timedelta(1, 0)

    if end_time is not None:
        # when the end time is "before" the end of start_time_end,
        # the game ends tomorrow
        if start_time_begin is not None and end_time < start_time_begin:
            end_time = end_time + timezone.timedelta(1, 0)

    if vote_start_time is not None:
        # The vote time must come after the start of starttime.
        # If it comes before, it must be tomorrow
        if start_time_begin is not None and vote_start_time < start_time_begin:
            vote_start_time = vote_start_time + timezone.timedelta(1, 0)
            # When end time is now before the vote start time, end time needs to
            # be adjusted to be tomorrow as well
            if end_time < vote_start_time:
                end_time = end_time + timezone.timedelta(1, 0)

    # some sanity checks
    if start_time_begin and start_time_end and vote_start_time:
        assert start_time_begin < vote_start_time
    if end_time and vote_start_time:
        assert end_time > vote_start_time
    if start_time_begin and start_time_end and end_time:
        assert end_time > start_time_end

    return {
        'now': time_now,
        'start_time_begin': start_time_begin,
        'start_time_end': start_time_end,
        'end_time': end_time,
        'vote_start_time': vote_start_time,
    }


def get_endtime(site):
    """ returns the (static) game end time """
    return get_times(site)['end_time']


def is_starttime(site):
    """
        returns True, if no start times are set, or the current time
        lies inside the starttime.
    """
    if not config.get("start_time_begin", site=site) or \
        not config.get("start_time_end", site=site):
        return True
    else:
        times = get_times(site)
        return times['start_time_begin'] \
            < now() \
            < times['start_time_end']


def is_after_votetime_start(site):
    """
        returns True, if no vote_start_time is set,
        or the current time is after the start of vote
        time
    """
    if not config.get("vote_start_time", site=site):
        return True
    else:
        times = get_times(site)
        return times['vote_start_time'] <= times['now']


def is_after_endtime(site):
    end_time = config.get("end_time", site=site)
    if end_time is None or is_starttime(site):
        return False
    else:
        times = get_times(site)
        return times['end_time'] < times['now']
