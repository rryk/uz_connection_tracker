import sys
import uz_tools
import pickle
import os.path
from pprint import pprint
from datetime import datetime
from pytz import timezone

if not os.path.isfile(uz_tools.TRACKED_CONNECTIONS_FILE):
  print "No tracked connections."
else:
  f = open(uz_tools.TRACKED_CONNECTIONS_FILE, 'r')
  connections = pickle.load(f)
  f.close()
  seats = {}
  if os.path.isfile(uz_tools.LAST_KNOWN_SEATS_FILE):
    f = open(uz_tools.LAST_KNOWN_SEATS_FILE, 'r')
    seats = pickle.load(f)
    f.close()
  for conn_id in reversed(connections):
    if conn_id['num'] != 'new':
      msg = "\n" + conn_id['num'] + ". "
      msg += conn_id['from_actual'] + " - "
      msg += conn_id['till_actual'] + ", "
      from_d = timezone('UTC').localize(datetime.utcfromtimestamp(conn_id['from_date']))
      msg += from_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + " - "
      till_d = timezone('UTC').localize(datetime.utcfromtimestamp(conn_id['till_date']))
      msg += till_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M')
      if conn_id['ignored']:
        msg += ", ignored."
      else:
        msg += "."
      print msg.replace(u'\u0456', u'i')
      if not conn_id['ignored']:
        conn_str = pickle.dumps(conn_id)
        if conn_str in seats:
          print "Tracked seats:"
          for coach_num in seats[conn_str].keys():
            sys.stdout.write("  Coach " + str(coach_num))
            sys.stdout.write(" (" + seats[conn_str][coach_num]["type"] + "): ")
            for place in seats[conn_str][coach_num]["places"]:
              sys.stdout.write(str(place) + " ");
            sys.stdout.write("\n")
        else:
          print "Seats have not been retrieved yet."
    else:
      msg = "\nNew connections: ";
      msg += conn_id["from"]["title"] + " - "
      msg += conn_id["till"]["title"] + " on "
      msg += conn_id["date"] + ", from "
      msg += conn_id["time"] + "."
      print msg.replace(u'\u0456', u'i')
sys.stdin.readline()