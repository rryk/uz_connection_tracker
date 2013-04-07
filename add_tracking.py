import sys
import pickle
import os.path
import uz_tools
from datetime import datetime
  
def prompt(query):
  sys.stdout.write(query);
  return sys.stdin.readline().strip().decode('cp866').encode('utf-8');
 
fromStation = uz_tools.chooseStation(prompt("From: "))
tillStation = uz_tools.chooseStation(prompt("Till: "))
#fromStation = chooseStation("Миколаїв")
#toStation = chooseStation("Київ")
date = prompt("Date: ");
time = prompt("Time from [00:00]: ");
if time == "":
  time = "00:00";

connections = uz_tools.query_connections(fromStation, tillStation, date, time);

print "Please choose connections that you would like to track."
tracked_connections = []
for connection in connections:
  prompt = "  "
  prompt += connection[u'num'] + ". "
  prompt += connection[u'from'][u'actual'] + " - "
  prompt += connection[u'till'][u'actual'] + ", "
  prompt += datetime.fromtimestamp(connection[u'from'][u'date']).strftime('%d.%m.%Y %H:%M') + " - "
  prompt += datetime.fromtimestamp(connection[u'till'][u'date']).strftime('%d.%m.%Y %H:%M') + " (y/n): "
  sys.stdout.write(prompt.replace(u'\u0456', u'i'))
  if sys.stdin.readline().strip() == 'y':
    tracked_connections.append(uz_tools.conn_id(connection));
  else:
    tracked_connections.append(uz_tools.conn_id(connection, True));

sys.stdout.write('  Track new connections? (y/n): ');
if sys.stdin.readline().strip() == 'y':
  tracked_connections.append({"num": "new", "from": fromStation, "till": tillStation, "date": date, "time": time});

if os.path.isfile(uz_tools.TRACKED_CONNECTIONS_FILE):
  f = open(uz_tools.TRACKED_CONNECTIONS_FILE, 'r');
  old_tracked_connections = pickle.load(f);
  for connection in old_tracked_connections:
    if not connection in tracked_connections:
      tracked_connections.append(connection);
  f.close()

f = open(uz_tools.TRACKED_CONNECTIONS_FILE, 'w');
pickle.dump(tracked_connections, f);
f.close();