import csv

from collections import defaultdict
from itertools import groupby
from StringIO import StringIO
from datetime import datetime

import web

from http_basic import basic_auth
import utils
import gcal

import config
from config import db


def fmt_date(date, date2):
    return "{} - {}".format(date.strftime('%a %b %d %I:%M %p'),
                            date2.strftime('%I:%M %p'))


def minutes(delta):
    return delta.seconds / 60


def breadcrumbs():
    yield ("Clients", "/clients/")
    path = web.ctx.fullpath
    if "entries" in path:
        yield ("Time Entries", path.split("entries")[0] + "entries/")
    if "invoices" in path:
        yield ("Invoices", path.split("invoices")[0] + "invoices/")


render = web.template.render("templates/", base='layout',
                             globals={'minutes': minutes,
                                      'breadcrumbs': breadcrumbs,
                                      'markdown': web.safemarkdown,
                                      'fmt_date': fmt_date})


urls = (
    r'/clients/', 'ClientList',
    r'/clients/add', 'ClientEdit',
    r'/clients/(\d*)/edit', 'ClientEdit',
    r'/clients/(\d*)', 'ClientView',
    r'/clients/(\d*)/categories/', 'CategoryList',
    r'/clients/(\d*)/categories/add', 'CategoryEdit',
    r'/clients/(\d*)/categories/(\d*)/edit', 'CategoryEdit',
    r'/clients/(\d*)/entries/', 'EntryList',
    r'/clients/(\d*)/entries/add', 'EntryEdit',
    r'/clients/(\d*)/entries/(\d*)/edit', 'EntryEdit',
    r'/clients/(\d*)/invoices/generate', 'GenerateInvoice',
    r'/clients/(\d*)/invoices/', 'InvoiceList',
    r'/clients/(\d*)/invoices/(\d*)/edit', 'InvoiceEdit',
    r'/clients/(\d*)/invoices/(\d*)/receipt', 'InvoiceReceipt',
    r'/clients/(\d*)/invoices/(\d*).?(\w*)', 'InvoiceView',
    r'/calfetch', 'CalendarFetch',
    r'/', 'Index',
)


def get_or_404(res):
    try:
        return res[0]
    except IndexError:
        raise web.notfound()


def get_one(table, record_id):
    if not record_id:
        return None
    return get_or_404(db.select(table,
                                where="id=$record_id",
                                vars={'record_id': record_id}))


def invoice_entries(invoice_id):
    return list(reversed(time_entries("invoice_id=$invoice_id",
                                      invoice_id=invoice_id)))


def time_entries(where, **vars):
    query = """
            SELECT time_entries.*, categories.name as category
            FROM time_entries left join categories ON
              time_entries.category_id = categories.id
            WHERE %s
            ORDER BY time_entries.start_time DESC
            """ % where

    def map_minutes(e):
        e.duration = minutes(e.end_time - e.start_time)
        e.hours = round(e.duration / 60.0, 2)
        return e
    return [map_minutes(e) for e in db.query(query, vars=vars)]


def total_ranges():
    return (
        ("prev_year", utils.prev_year_range()),
        ("this_year", utils.year_range()),
        ("prev_month", utils.prev_month_range()),
        ("this_month", utils.month_range()),
        ("prev_week", utils.prev_week_range()),
        ("this_week", utils.week_range()),
        ("this_day", utils.day_range()),
        ("prev_day", utils.prev_day_range()))


def add_client_totals(client, totals=None):
    ranges = total_ranges()

    client.total_invoiced = sum([i.total for i in invoices(client.id)])
    if totals is not None:
        totals['total_invoiced'] += client.total_invoiced
    for name, drange in ranges:
        start, end = drange
        entries = time_entries(
            """ start_time >= $start AND
            start_time <= $end AND time_entries.client_id = $cid""",
            start=start, end=end, cid=client.id)
        total = sum([t.hours for t in entries])
        setattr(client, name, total)
        if totals is not None:
            totals[name] += total
    if totals is not None:
        return client, totals
    else:
        return client


def get_clients():
    totals = dict([(total_name, 0.0) for total_name, _ in total_ranges()])
    totals['total_invoiced'] = 0.0
    clients = []
    for c in db.select("clients"):
        client, totals = add_client_totals(c, totals)
        clients.append(client)
    return clients, web.storage(totals)


def month_entries(entries):
    month_entries = []
    grouper = lambda i: [i.start_time.date().year, i.start_time.date().month]
    for year_month, entries in groupby(entries, grouper):
        d = datetime(year_month[0], year_month[1], 1).strftime("%B %Y")
        entries = list(entries)
        total = sum([minutes(te.end_time-te.start_time)
                     for te in entries]) / 60.0
        month_entries.append(web.Storage({'date': d,
                                          'total': round(total, 2),
                                          'entries': entries}))
    return month_entries


def invoices(client_id):
    for i in db.select("invoices", where="client_id=$client_id",
                       vars={'client_id': client_id}, order="month desc"):
        i.total = sum([e.hours for e in invoice_entries(i.id)])
        yield i


def get_or_create_category(client, name):
    cat = get_or_404(db.select("categories",
                               where="client_id=$client_id AND name=$name",
                               vars={'client_id': client.id, 'name': name}))
    if cat:
        return cat
    db.insert("categories", client_id=client.id, name=name)
    return get_or_create_category(client, name)


class CalendarFetch:
    def GET(self):
        title = "Fetch Events from Google Calendar '{}'".format(
            config.g_calendar_name)
        return render.form(web.form.Form(), name="Fetch", title=title)

    def POST(self):
        events = [web.storage(e) for e
                  in gcal.fetchEvents(config.g_username, config.g_password,
                                      config.g_calendar_name)]

        for event in events:
            client = get_or_404(db.select("clients",
                                          where="lower(name)=lower($name)",
                                          vars={'name': event.client_name}))
            if not client:
                event['status'] = 'Client could not be found.'
                continue
            category_id = None
            if event.category_name:
                category = get_or_create_category(client, event.category_name)
                category_id = category.id

            entry = get_or_404(db.select("time_entries",
                                         where="external_reference=$ref",
                                         vars={'ref': event.id}))
            if not entry:
                db.insert("time_entries",
                          client_id=client.id,
                          description=event.description,
                          start_time=event.start,
                          end_time=event.end,
                          category_id=category_id,
                          external_reference=event.id)
                event.status = 'Creating new time entry'

            elif entry.invoice_id:
                event.status = 'Skipping, entry has already been invoiced.'
            else:
                db.update("time_entries",
                          where="id=$entry_id",
                          vars={'entry_id': entry.id},
                          description=event.description,
                          start_time=event.start,
                          end_time=event.end,
                          category_id=category_id)
                event.status = 'Updated time entry'
        return render.fetch_status(events=events)


class GenerateInvoice:
    def POST(self, client_id):
        start = datetime.now().date().replace(day=1)
        start = datetime(start.year, start.month, start.day)
        earliest = time_entries(
            "time_entries.client_id=$client_id and invoice_id is null",
            client_id=client_id)[0]

        beg_month = earliest.start_time.date().replace(day=1)
        invoice_id = db.insert("invoices",
                               month=beg_month,
                               client_id=client_id,
                               status='billed')
        db.update('time_entries',
                  where="client_id=$client_id and invoice_id is null",
                  vars=locals(),
                  invoice_id=invoice_id)
        raise web.seeother("/clients/%s/entries/" % client_id)


class InvoiceList:
    def GET(self, client_id):
        client = get_one("clients", client_id)
        return render.invoice_list(client, invoices(client.id))


class InvoiceEdit:
    def GET(self, client_id, invoice_id):
        f = web.form.Form(
            web.form.Dropdown("status", ["billed", "closed"]),
            web.form.File("receipt"))()
        return render.form(f)

    def POST(self, client_id, invoice_id):
        i = web.input(receipt={}, status="")
        to_update = {'status': i.status}
        if i.receipt.filename:
            to_update = {'receipt_name': i.receipt.filename,
                         'receipt': buffer(i.receipt.file.read())}
        db.update("invoices", where="id=$invoice_id and client_id=$client_id",
                  vars=locals(), **to_update)
        raise web.seeother("/clients/%s/invoices/" % client_id)


class InvoiceReceipt:
    def GET(self, client_id, invoice_id):
        i = get_or_404(
            db.select("invoices",
                      where="id=$invoice_id and client_id=$client_id",
                      limit=1,
                      vars=locals()))
        return str(i.receipt)


class InvoiceView:
    def generate_csv(self, entries, hourly_rate):
        s = StringIO()
        w = csv.writer(s)

        categories = list(set([e.category for e in entries]))

        w.writerow(["Start Time", "End Time",
                    "Hours", "Description"] + categories)

        totals = defaultdict(lambda: 0.0)
        for e in entries:
            totals[e.category] += e.hours
            row = [e.start_time, e.end_time, e.hours, e.description]
            for c in categories:
                if e.category == c:
                    row.append(e.hours)
                else:
                    row.append("")
            w.writerow(row)
        total_row = ["Totals", "", "", ""] + [totals[c] for c in categories]
        w.writerow(total_row)
        w.writerow(())
        w.writerow(())
        total = sum(totals.values())
        w.writerow(("Total Hours",  total))
        w.writerow(("Rate per Hour",  '$%d' % hourly_rate))
        w.writerow(("Total",  "$%s" % (hourly_rate * total)))
        return s.getvalue()

    def GET(self, client_id, invoice_id, format):
        client = get_one("clients", client_id)
        invoice = get_one('invoices', invoice_id)
        entries = invoice_entries(invoice.id)

        if format == "csv":
            filename = 'Invoice for {} for {}.csv'.format(
                client.name, invoice.month.strftime("%B %Y"))
            web.header('Content-Type', 'text/csv')
            web.header('Content-disposition', 'attachment; filename={}'.format(
                filename))
            return self.generate_csv(entries, client.hourly_rate)
        else:
            return render.entry_list(client, entries)


class CategoryEdit:

    form = web.form.Form(web.form.Textbox("name", web.form.notnull))

    def GET(self, client_id, category_id=None):
        category = get_one("categories", category_id)
        form = self.form()
        form.fill(category)
        return render.form(form)

    def POST(self, client_id, category_id=None):
        client = get_one("clients", client_id)
        category = get_one("categories", category_id)
        form = self.form()
        if not form.validates():
            return render.form(form)
        if category:
            db.update("categories",  where="id=$cat_id",
                      vars={'cat_id': category.id}, name=form.d.name)
        else:
            get_or_create_category(client, form.d.name)
        raise web.seeother("/clients/%s/categories/" % client_id)


class CategoryList:
    def GET(self, client_id):
        categories = db.select("categories", where="client_id=$client_id",
                               vars=locals())
        client = get_one("clients", client_id)
        return render.category_list(client, categories)


class EntryList:
    def GET(self, client_id, _open=None):
        client = get_one("clients", client_id)
        entries = time_entries(where="time_entries.client_id=$client_id",
                               client_id=client_id)

        return render.entry_list(client, month_entries(entries))


class EntryEdit:
    def form(self, client_id):
        categories = db.select("categories", where='client_id=$client_id',
                               vars=locals())
        cat_options = [""] + [(c.id, c.name) for c in categories]
        return web.form.Form(
            web.form.Textbox("start_date", web.form.notnull,
                             class_='datepicker',
                             description="date"),
            web.form.Textbox("start_time", web.form.notnull,
                             class_='timepicker',
                             description='start time'),
            web.form.Textbox("duration", web.form.notnull,
                             description="duration/end time"),
            web.form.Textarea("description", rows="8"),
            web.form.Dropdown("category_id", cat_options,
                              description="category"))()

    def GET(self, client_id, entry_id=None):
        form = self.form(client_id)

        entry = get_one("time_entries", entry_id) or web.storage()
        if entry:
            start_time = entry.start_time
            entry.duration = "%d minutes " % (
                minutes(entry.end_time - start_time))
        else:
            start_time = datetime.now()
        entry.start_date = start_time.strftime("%m/%d/%Y")
        entry.start_time = start_time.strftime("%I:%M %p")
        form.fill(entry)
        return render.form(form)

    def POST(self, client_id, entry_id=None):
        entry = get_one("time_entries", entry_id)
        f = self.form(client_id)
        if f.validates():
            date_str = "{} {}".format(f.d.start_date.strip(),
                                      f.d.start_time.strip())
            start_time = end_time = datetime.strptime(date_str,
                                                      "%m/%d/%Y %I:%M %p")

            end_time = utils.compute_end_time(f.d.duration, start_time)
            if entry:
                db.update("time_entries",
                          where="id=$entry_id",
                          vars={'entry_id': entry_id},
                          description=f.d.description,
                          start_time=start_time,
                          end_time=end_time,
                          category_id=f.d.category_id)
            else:
                db.insert("time_entries",
                          client_id=client_id,
                          description=f.d.description,
                          start_time=start_time,
                          end_time=end_time,
                          category_id=f.d.category_id)
            raise web.seeother("/clients/%s/entries/" % client_id)
        else:
            return render.form(f)


class ClientList:
    def GET(self):
        clients, totals = get_clients()
        return render.client_list(clients, totals)


class ClientView:
    def GET(self, client_id=None):
        client = get_one("clients", client_id)
        client = add_client_totals(client)
        return render.client_view(client)


class ClientEdit:
    require_number = web.form.regexp(r'^\d+$', 'must be a number')
    form = web.form.Form(web.form.Textbox("name", web.form.notnull),
                         web.form.Textarea("notes", rows=15,
                                           style="width:600px"),
                         web.form.Textbox("hourly_rate",
                                          web.form.notnull,
                                          require_number,
                                          description="hourly rate"))

    def GET(self, client_id=None):
        client = get_one("clients", client_id)
        f = self.form()
        f.fill(client or web.storage(hourly_rate=100))
        return render.form(f)

    def POST(self, client_id=None):
        f = self.form()
        if f.validates():
            if client_id:
                db.update("clients", where="id=$client_id",
                          vars=locals(), **f.d)
            else:
                db.insert("clients", **f.d)
            raise web.seeother("/clients/")
        else:
            return render.form(f)


class Index:
    def GET(self):
        raise web.seeother("/clients/")

app = web.application(urls, globals(), autoreload=True)
auth = basic_auth("Application", config.basic_auth_user,
                  config.basic_auth_pw)
if __name__ == "__main__":
    app.run(auth)
else:
    app_wsgi = app.wsgifunc(auth)
