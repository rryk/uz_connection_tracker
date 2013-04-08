import urllib
import urllib2
import json
import sys
from datetime import datetime
from pytz import timezone

TRACKED_CONNECTIONS_FILE = 'tracked_connections'
LAST_KNOWN_SEATS_FILE = 'last_known_seats'

def query(path, data, headers):
  url = "http://booking.uz.gov.ua/" + path;
  if data != None:
    data = urllib.urlencode(data)
  request = urllib2.Request(url, data, headers);
  response = urllib2.urlopen(request);
  json_response = json.load(response)
  if json_response[u'error'] == True:
    if json_response[u'data'] != None:
      print "Server returned an error!";
      msg = str(json_response[u'data'])
      msg += " "
      msg += json_response[u'value'].replace(u'\u0456', u'i')
      print msg
      sys.exit(0)
    else:
      return [];
  return json_response[u'value']

def chooseStation(name):
  response = query("purchase/station/" + urllib.quote(name, '') + "/", {}, {});
  i = 0;
  for station in response:
    i+=1
    print(" " + str(i) + ". " + station[u'title'].replace(u'\u0456', u'i'));
  sys.stdout.write("Choose station: ");
  res = int(sys.stdin.readline().strip())
  return {'station_id': response[res-1][u'station_id'],
          'title': response[res-1][u'title']}

def query_connections(fromStation, tillStation, date, time):
  connections = query(
    "purchase/search/",
    [
      (u'station_id_from', fromStation['station_id']),
      (u'station_id_till', tillStation['station_id']),
      (u'station_from', fromStation['title'].encode('utf-8')),
      (u'station_till', tillStation['title'].encode('utf-8')),
      (u'date_dep', date),
      (u'time_dep', time),
      (u'search', u'')
    ],
    {
      "GV-Ajax": "1",
      "GV-Referer": "http://booking.uz.gov.ua/",
      "GV-Screen": "1440x900",
      "GV-Unique-Host": "1",
      "Origin": "http://booking.uz.gov.ua",
      "Host": "booking.uz.gov.ua",
    }
  );
  for index in range(len(connections)):
    connections[index][u'from'][u'actual'] = fromStation['title']
    connections[index][u'till'][u'actual'] = tillStation['title']
  return connections

def conn_id(connection, ignored=False):
  return {
    'from_station_id': connection[u'from'][u'station_id'],
    'from_station_title': connection[u'from'][u'station'],
    'from_date': connection[u'from'][u'date'],
    'from_actual': connection[u'from'][u'actual'],
    'till_station_id': connection[u'till'][u'station_id'],
    'till_station_title': connection[u'till'][u'station'],
    'till_date': connection[u'till'][u'date'],
    'till_actual': connection[u'till'][u'actual'],
    'model': connection[u'model'],
    'num': connection[u'num'],
    'ignored': ignored
  }

def load_seats(id):
  fromStation = {
    'station_id': id['from_station_id'],
    'title': id['from_actual']
  };
  tillStation = {
    'station_id': id['till_station_id'],
    'title': id['till_actual']
  };

  utc_datetime = timezone('UTC').localize(datetime.utcfromtimestamp(id['from_date']))
  ukraine_date = utc_datetime.astimezone(timezone("Europe/Kiev")).strftime("%d.%m.%Y")
  connections = query_connections(fromStation, tillStation, ukraine_date, "00:00")
  full_connection = None
  for connection in connections:
    if conn_id(connection) == id:
      full_connection = connection
  if full_connection == None:
    return {}
  seats = {}
  for type in full_connection[u'types']:
    new_seats = load_seats_for_coach_type(id, type[u'letter']);
    seats = dict(seats.items() + new_seats.items())
  return seats

def load_seats_for_coach_type(conn_id, coach_type):
  coaches = query(
    'purchase/coaches/',
    {
      'station_id_from': conn_id['from_station_id'],
      'station_id_till': conn_id['till_station_id'],
      'train': conn_id['num'].encode('utf-8'),
      'coach_type': coach_type.encode('utf-8'),
      'model': conn_id['model'],
      'date_dep': conn_id['from_date'],
      'round_trip': '0',
      'another_ec': '0'
    },
    {
      "GV-Ajax": "1",
      "GV-Referer": "http://booking.uz.gov.ua/",
      "GV-Screen": "1440x900",
      "GV-Unique-Host": "1",
      "Origin": "http://booking.uz.gov.ua",
      "Host": "booking.uz.gov.ua",
    }
  );
  res = {}
  for coach in coaches[u'coaches']:
    seats = query(
      "purchase/coach/",
      {
        'station_id_from': conn_id['from_station_id'],
        'station_id_till': conn_id['till_station_id'],
        'train': conn_id['num'].encode('utf-8'),
        'coach_num': coach[u'num'],
        'coach_type_id': coaches[u'coach_type_id'],
        'date_dep': conn_id['from_date'],
        'change_scheme': 0
      },
      {
        "GV-Ajax": "1",
        "GV-Referer": "http://booking.uz.gov.ua/",
        "GV-Screen": "1440x900",
        "GV-Unique-Host": "1",
        "Origin": "http://booking.uz.gov.ua",
        "Host": "booking.uz.gov.ua",
      }
    );
    res[coach[u'num']] = {
      'type': coach_type,
      'places': seats[u'places'][0]
    }
  return res