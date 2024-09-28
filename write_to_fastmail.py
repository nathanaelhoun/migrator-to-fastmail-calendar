import os
import caldav
import caldav.elements.ical # for calendarColor
from datetime import datetime
import json
import _mapcal
import glob

# Needs the pip3 version of caldav not the debian version.

# url = 'https://caldav.fastmail.com/dav/principals/user/amoe@solasistim.net/'
url = 'https://caldav.fastmail.com/dav/'

# my_event = my_new_calendar.save_event(
#     dtstart=datetime.datetime(2020,5,17,8),
#     dtend=datetime.datetime(2020,5,18,1),
#     summary="Do the needful",
#     rrule={'FREQ': 'YEARLY'))


fastmail_username = os.environ['FASTMAIL_USERNAME']
fastmail_password = os.environ['FASTMAIL_PASSWORD']

with caldav.DAVClient(url=url, username=fastmail_username, password=fastmail_password) as client:
    my_principal = client.principal()
    for calendar_file in glob.glob('./out/*.json'):
        with open(calendar_file, 'r') as f:
            data = json.load(f)

        print("Importing calendar {}".format(data['summary']))
        the_c = my_principal.make_calendar("{} (imported at {})".format(data['summary'], datetime.today().strftime('%Y-%m-%d %H:%M:%S')));

        new_events = _mapcal.CalendarConverter(data).get_mapped_calendar()

        nb_new_events = len(new_events)
        for i, event in enumerate(reversed(new_events), start=1):
            print("  creating event", i, "/", nb_new_events)
            the_c.save_event(**event)
