import json
from datetime import date
from dateutil import parser

# if we fail to map the color then fall back this beautiful yellow
FALLBACK_COLOR = "#e8ae0c"

calendar_colors_mappings = {}
events_colors_mappings = {}

# gcal_colors.json comes from the Google Calendar API
# https://developers.google.com/calendar/api/v3/reference/colors/get
with open("gcal_colors.json") as f:
    data = json.load(f)

    for key, color in data["event"].items():
        events_colors_mappings[key] = color["background"]
    for key, color in data["calendar"].items():
        calendar_colors_mappings[key] = color["background"]

def get_calendar_color(gcal: int, fallback=FALLBACK_COLOR) -> str:
    try:
        return calendar_colors_mappings[gcal]
    except KeyError:
        return fallback

# -----------------------------------------------------------------------------

class ConvertError(Exception):
    pass

# BEGIN:VCALENDAR
# VERSION:2.0
# CALSCALE:GREGORIAN
# PRODID:-//CyrusIMAP.org/Cyrus
#  3.7.0-alpha0-1115-g8b801eadce-fm-20221102.001-g8b801ead//EN
# BEGIN:VEVENT
# UID:836cd37f-4832-4fb8-8a1d-c98accbb7575
# SEQUENCE:0
# DTSTAMP:20221111T073200Z
# CREATED:20221111T073200Z
# DTSTART;VALUE=DATE:20221116
# DURATION:P1D
# PRIORITY:0
# SUMMARY:Dave's event
# STATUS:CONFIRMED
# TRANSP:TRANSPARENT
# X-APPLE-DEFAULT-ALARM;VALUE=BOOLEAN:TRUE
# END:VEVENT
# END:VCALENDAR

# no need to fuck with durations, just use either 'date' or 'datetime' here.
# event = {
#     'dtstart': date(2022, 11, 18),
#     'color': '#e12162',
#     'summary': "Dave's event from python",
#     'created': datetime(2022, 11, 18, 1, 2, 3)
#     'duration': vDuration(timedelta(days=1))
# }
# event = {
#     'dtstart': datetime(2022,11,28, 9, 30),
#     'dtend': datetime(2022,11,29, 11, 30),
#     'summary': "Dave's multi day event",
# }
class CalendarConverter:
    def __init__(self, data: dict) -> None:
        self.default_color = data['defaultColor']
        self.events = data['events']

    def get_event_color(self, gcal: int) -> str:
        try:
            return events_colors_mappings[gcal]
        except KeyError:
            return self.default_color

    def convert_event(self, gcal: dict):
        result = {}

        status = gcal['status']
        if status != 'confirmed':
            raise ConvertError(f'unknown status {status}')

        summary = gcal['summary']
        start = gcal['start']
        end = gcal['end']

        result['summary'] = summary

        is_date_based_event = 'date' in start and 'date' in end
        is_datetime_based_event = 'dateTime' in start and 'dateTime' in end

        if not (is_date_based_event ^ is_datetime_based_event):
            raise Exception('weirdly formatted event')


        if is_datetime_based_event:
            result['dtstart'] = parser.isoparse(start['dateTime'])
            result['dtend'] = parser.isoparse(end['dateTime'])
        elif 'date' in start:
            result['dtstart'] = date.fromisoformat(start['date'])
            result['dtend'] = date.fromisoformat(end['date'])
        else:
            raise ConvertError(f'unrecognized start {start!r}')

        recurrence = gcal.get('recurrence')
        if recurrence is not None:
            if len(recurrence) != 1:
                raise ConvertError('weird recurrence spec')

            rrule = recurrence[0]
            result['rrule'] = self.map_rrule(rrule)

        result['color'] = self.get_event_color(gcal.get('colorId'))

        return result

    def map_rrule(self, rrule):
        remaining = rrule.removeprefix('RRULE:')
        pairs = remaining.split(';')
        result = {}

        for x in pairs:
            k, v = x.split('=', maxsplit=1)
            if k == 'UNTIL':
                if 'T' in v:
                    v = parser.isoparse(v)
                else:
                    v = parser.isoparse(v).date()

            result[k] = v

        return result


    def get_mapped_calendar(self):
        converted = []

        for x in self.events:
            try:
                y = self.convert_event(x)
                converted.append(y)
            except ConvertError as e:
                print(e)

        return converted
