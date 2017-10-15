import transitfeed as tr
import requests as r
import json
from lxml import html
import datetime
from dateutil import parser

schedule = tr.Schedule()
schedule.AddAgency("Texas A&M Transportation Services","transport.tamu.edu/transit.aspx","America/Chicago")

# load the calendar
x = r.get("http://transport.tamu.edu:80/BusRoutesFeed/api/Announcements/Calendar-Today")
j = json.loads(x.content)

# AddServicePeriodObject(self, service_period, problem_reporter=None, validate=True)
service_period = schedule.GetDefaultServicePeriod()
data_html = html.fromstring(j['Items'][0]['Summary']['Text'])
#TODO take data_html and see if there is service today or there's a game. It might be best to just edit manually.

# get today and one year from now
now = datetime.date.today()
try:
    later = now.replace(year=now.year+1)
except ValueError:
    later = now + datetime.timedelta(days=365)
service_period.SetStartDate(now.strftime("%Y%m%d"))
service_period.SetEndDate(later.strftime("%Y%m%d"))
service_period.SetWeekdayService(True)
service_period.SetWeekendService(True)


#get routes
x = r.get("http://transport.tamu.edu:80/BusRoutesFeed/api/Routes")
j = json.loads(x.content)
# AddRoute(self, short_name, long_name, route_type, route_id=None)
for y in j:
    route = schedule.AddRoute(y['ShortName'],y['Name'],'Bus',y['ShortName'])
    x = r.get("http://transport.tamu.edu:80/BusRoutesFeed/api/route/" + y['ShortName'] + "/stops")
    k = json.loads(x.content)
    stops = {}
    # AddStop(self, lat, lng, name, stop_id=None)
    for z in k:
        stops[z['Name']] = schedule.AddStop(z['Latitude'],z['Longtitude'],z['Name'])
    x = r.get("http://transport.tamu.edu:80/BusRoutesFeed/api/Route/" + y['ShortName'] + "/TimeTable")
    k = json.loads(x.content)
    for z in k:
        trip = route.AddTrip()
        trip_stops = []
        for stop,time in z.items():
            stop_time = parser.parse(time)
            stop_name = "".join(s for s in list(stops) if s in stop)
            trip_stops.append((stop_time,stop_name))

        trip_stops.sort()
        for time,stop in trip_stops:
            trip.AddStop(stops[stop],stop_time=time.strftime("%H:%M:%S"))


schedule.Validate()
schedule.WriteGoogleTransitFeed('public/tamu_transit.zip')
