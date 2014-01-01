from datetime import datetime

import gdata.calendar.client as gclient


def parse_gcal_date(date_str):
    dt, _, tz = date_str.partition(".")
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")


def event_to_dict(calendar_event):
    parts = [p.strip() for p in calendar_event.title.text.rsplit("-", 1)]
    when = calendar_event.when[0]
    try:
        category_name = parts[1]
    except IndexError:
        category_name = None

    return {'client_name': parts[0],
            'category_name': category_name,
            'description': calendar_event.content.text,
            'start': parse_gcal_date(when.start),
            'end': parse_gcal_date(when.end),
            'id': calendar_event.get_id()
            }


def fetch_events(username, password, calendar_name="Work Log"):
    client = gclient.CalendarClient(source='calbil-v0.0.1')
    client.ClientLogin(username, password, client.source)
    calendar = _find_calendar(client, calendar_name)
    
    print "Found calendar %s" % calendar.title.text
    entries = _fetch_all(client, calendar.content.src)
    return [event_to_dict(e) for e in entries]


def _find_calendar(client, calendar_name):
    calendar_feed = client.GetAllCalendarsFeed()
    results = [e for e in calendar_feed.entry if e.title.text == calendar_name]
    try:
        return results[0]
    except IndexError:
        raise Exception("Calendar '%s' not found" % calendar_name)


def _fetch_all(client, url, results=[]):
    feed = client.GetCalendarEventFeed(url)
    results += list(feed.entry)
    next_link = feed.GetNextLink()
    if next_link:
        return _fetch_all(client, next_link.href, results)
    else:
        return results


if __name__ == "__main__":
    import sys
    events = fetch_events(sys.argv[1], sys.argv[2], sys.argv[3])
    for idx, e in enumerate(events):
        print idx, e['end']
