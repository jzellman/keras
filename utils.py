import itertools
from datetime import datetime, timedelta


def day_range(dt=None):
    "Returns the start and end times for the day td falls in"
    dt = dt or datetime.now()
    start = datetime(dt.year, dt.month, dt.day)
    end = start + timedelta(days=1) - timedelta(microseconds=1)
    return start, end


def year_range(dt=None):
    "Returns the start and end times for for the year dt falls in"
    dt = dt or datetime.now()
    start = datetime(dt.year, 1, 1)
    end = start.replace(year=start.year + 1) - timedelta(microseconds=1)
    return start, end


def week_range(dt=None):
    "Returns the start and end times for for the week dt falls in"
    dt = dt or datetime.now()
    start = dt - timedelta(days=dt.isoweekday())
    start = datetime(start.year, start.month, start.day)
    end = start + timedelta(days=7) - timedelta(microseconds=1)
    return start, end


def month_range(dt=None):
    "Returns the start and end times for for the month dt falls in"
    dt = dt or datetime.now()
    start = datetime(dt.year, dt.month, 1)
    if start.month == 12:
        end = start.replace(year=dt.year+1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    end = end - timedelta(microseconds=1)
    return start, end


def prev_year_range(dt=None):
    dt = dt or datetime.now()
    return year_range(datetime(dt.year-1, dt.month, dt.day))


def prev_month_range(dt=None):
    dt = dt or datetime.now()
    in_month = datetime(dt.year, dt.month, 1) - timedelta(days=5)
    return month_range(in_month)


def prev_week_range(dt=None):
    cur_start, _ = week_range(dt)
    return week_range(cur_start - timedelta(days=1))


def prev_day_range(dt=None):
    dt = dt or datetime.now()
    return day_range(dt - timedelta(days=1))


def compute_end_time(duration, start_time):
    def grouped(lst, n):
        assert len(lst) % n == 0
        return itertools.izip(*[itertools.islice(lst, i, None, n)
                                for i in range(n)])

    if not duration:
        return None
    duration = duration.strip()
    try:
        mins = int(duration)
        return start_time + timedelta(minutes=mins)
    except ValueError:
        pass
    try:
        e = datetime.strptime(duration, '%I:%M %p')
        return start_time.replace(hour=e.hour, minute=e.minute)
    except ValueError:
        pass

    parts = [p for p in duration.split(' ') if p]
    res = start_time
    for amount, name in grouped(parts, 2):
        amount = int(amount)
        if 'hour' in name:
            res += timedelta(hours=amount)
        if 'minute' in name:
            res += timedelta(minutes=amount)
    return res
