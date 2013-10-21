from datetime import datetime

import gdata.calendar.client as gclient


def parse_gcal_date(date_str):
    dt, _, tz = date_str.partition(".")
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")


def eventToDict(calendar_event):
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


def fetchEvents(username, password, calendar_name):
    client = gclient.CalendarClient(source='calbil-v0.0.1')
    client.ClientLogin(username, password, client.source)
    calendar_feed = client.GetAllCalendarsFeed()
    calendar_name = "Work Log"
    results = [e for e in calendar_feed.entry if e.title.text == calendar_name]
    if not results:
        raise Exception("Calendar not found")
    calendar = results[0]
    print "Using calendar %s" % calendar.title.text

    event_feed = client.GetCalendarEventFeed(calendar.content.src)
    return [eventToDict(e) for e in event_feed.entry]

if __name__ == "__main__":
    for e in fetchEvents():
        print e
        print
