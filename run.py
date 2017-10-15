import transitfeed as tr
import requests as r
import json
import datetime
from dateutil import parser
import utm

# returns json from url request
def get(url):
    x = r.get(url)
    return json.loads(x.content)

def from_weird_to_latlng(weird_x,weird_y):
    print weird_x,weird_y
    x = float(1.0023*weird_x-330240)/10.0
    y = float(1.006*weird_y+259177)/10.0
    print x,y
    return utm.to_latlon(x,y,14,'R')

# create schedule and set agency
schedule = tr.Schedule()
schedule.AddAgency("Texas A&M Transportation Services","transport.tamu.edu/transit.aspx","America/Chicago")

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
    print y['Name']
    print y['ShortName']
    # get stops
    stops_json = get("http://transport.tamu.edu:80/BusRoutesFeed/api/route/" + y['ShortName'] + "/stops")
    # create dict of stops
    stops = {}
    for z in stops_json:
        name = z['Stop']['Name']
        (lat,lng) = from_weird_to_latlng(z['Latitude'],z['Longtitude'])
        stop = schedule.AddStop(lat=lat,lng=lng,name=name)
        stop.Validate()
        stops[name] = stop
    # get timetable
    timetable = get("http://transport.tamu.edu:80/BusRoutesFeed/api/Route/" + y['ShortName'] + "/TimeTable")
    # create trips and add all stops
    for t in timetable:
        # create trip
        trip = route.AddTrip()
        # find stop_time and stop_name, then put in a list to sort so the stops are in ascending time order
        trip_stops = []
        for stop,time in t.items():
            try:
                stop_time = parser.parse(time)
            except Exception:
                continue
            stop_name = stop[36:].strip()
            trip_stops.append((stop_time,stop_name))
        trip_stops.sort()
        # add all stops to trip
        for time,stop in trip_stops:
            trip.AddStopTime(stops[stop],stop_time=time.strftime("%H:%M:%S"))

# validate and write to zip file
schedule.Validate()
schedule.WriteGoogleTransitFeed('public/tamu_transit.zip')
