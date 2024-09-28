import datetime
from _google_calendar_auth_boilerplate import authboilerplate
import json
import os
import _mapcal

service = authboilerplate()

now = datetime.datetime.now(datetime.timezone.utc).isoformat() + 'Z'  # 'Z' indicates UTC time

collection = []
next_page_token = None

os.makedirs('out', exist_ok=True)

print("Getting calendar list…")
calendars = service.calendarList().list().execute()

# TODO : interactive selection?
selected_calendars = [c for c in calendars['items'] if (c['summary'] in ["WRITE_HERE_YOUR_CALENDARS_TO_EXPORT"])]

print("Exporting {} calendars...".format(len(selected_calendars)))
for calendar in selected_calendars:
    print("Exporting calendar {}…".format(calendar['summary']))

    while True:
        fields = {
            'calendarId': calendar['id'],
            'maxResults': 2500,
            'singleEvents': False,
            # 'timeMin': now,
            # 'orderBy': 'startTime',
            # 'maxTime': now
        }

        if next_page_token:
            fields['pageToken'] = next_page_token

        print("    Doing request…")
        events_result = service.events().list(**fields).execute()
        collection.extend(events_result.get('items'))

        next_page_token = events_result.get('nextPageToken')
        if not next_page_token:
            break

    result = {
        'summary': calendar['summary'],
        'defaultColor': _mapcal.get_calendar_color(calendar['colorId']),
        'events': collection,
    }
    with open("out/{id}.json".format(id=calendar['summary']), 'w') as f:
        json.dump(result, f, indent=4)

    print("Calendar {} done, {} events!".format(calendar['summary'], len(collection)))
