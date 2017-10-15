import transitfeed as tr
import requests as r
import json
from lxml import html
import datetime
from dateutil import parser

# returns json from url request
def get(url):
    x = r.get(url)
    return json.loads(x.content)

# create schedule and set agency
schedule = tr.Schedule()
schedule.AddAgency("Texas A&M Transportation Services","transport.tamu.edu/transit.aspx","America/Chicago")

# load the calendar
x = r.get("http://transport.tamu.edu:80/BusRoutesFeed/api/Announcements/Calendar-Today")
j = json.loads(x.content)
data_html = html.fromstring(j['Items'][0]['Summary']['Text'])
#TODO take data_html and see if there is service today or there's a game. It might be best to just edit manually.

# get today and one year from now
now = datetime.date.today()
try:
    later = now.replace(year=now.year+1)
except ValueError:
    later = now + datetime.timedelta(days=365)

# set service period
service_period = schedule.GetDefaultServicePeriod()
service_period.SetStartDate(now.strftime("%Y%m%d"))
service_period.SetEndDate(later.strftime("%Y%m%d"))
service_period.SetWeekdayService(True)
service_period.SetWeekendService(True)


# get routes
routes = get("http://transport.tamu.edu:80/BusRoutesFeed/api/Routes")
# add each route to schedule
for y in routes:
    # create route
    route = schedule.AddRoute(y['ShortName'],y['Name'],'Bus',y['ShortName'])
    # get stops
    stops_json = get("http://transport.tamu.edu:80/BusRoutesFeed/api/route/" + y['ShortName'] + "/stops")
    # create dict of stops
    stops = {}
    for z in stops_json:
        stops[z['Name']] = schedule.AddStop(z['Latitude'],z['Longtitude'],z['Name'])
    # get timetable
    timetable = get("http://transport.tamu.edu:80/BusRoutesFeed/api/Route/" + y['ShortName'] + "/TimeTable")
    # create trips and add all stops
    for t in timetable:
        # create trip
        trip = route.AddTrip()
        # find stop_time and stop_name, then put in a list to sort so the stops are in ascending time order
        trip_stops = []
        for stop,time in t.items():
            stop_time = parser.parse(time)
            stop_name = "".join(s for s in list(stops) if s in stop)
            trip_stops.append((stop_time,stop_name))
        trip_stops.sort()
        # add all stops to trip
        for time,stop in trip_stops:
            trip.AddStop(stops[stop],stop_time=time.strftime("%H:%M:%S"))

# validate and write to zip file
schedule.Validate()
schedule.WriteGoogleTransitFeed('public/tamu_transit.zip')
