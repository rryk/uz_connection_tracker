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
  for connection in connections:
    if connection['num'] != 'new':
      if not connection['ignored']:
        msg = connection['num'] + ". "
        msg += connection['from_actual'] + " - "
        msg += connection['till_actual'] + ", "
        from_d = timezone('UTC').localize(datetime.utcfromtimestamp(connection['from_date']))
        msg += from_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + " - "
        till_d = timezone('UTC').localize(datetime.utcfromtimestamp(connection['till_date']))
        msg += till_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + "."
        print msg.replace(u'\u0456', u'i')
    else:
      msg = "New connections: ";
      msg += connection["from"]["title"] + " - "
      msg += connection["till"]["title"] + " on "
      msg += connection["date"] + ", from "
      msg += connection["time"] + "."
      print msg.replace(u'\u0456', u'i')
  f.close()
sys.stdin.readline()