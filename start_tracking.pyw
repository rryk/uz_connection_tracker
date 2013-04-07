import wx
import pickle
import threading
import uz_tools
import os.path
import os
import sys
from datetime import datetime
from pprint import pprint
from pytz import timezone

TRAY_TOOLTIP = 'UZ Connection Tracker'
TRAY_ICON = 'icon.png'

def create_menu_item(menu, label, func):
  item = wx.MenuItem(menu, -1, label)
  menu.Bind(wx.EVT_MENU, func, id=item.GetId())
  menu.AppendItem(item)
  return item

class TaskBarIcon(wx.TaskBarIcon):
  def __init__(self):
    super(TaskBarIcon, self).__init__()
    self.set_icon(TRAY_ICON)
    self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_check)
    self.LoadConnectionsToTrack()
    t = threading.Timer(600.0, self.check_new_seats);
    t.start()

  def LoadConnectionsToTrack(self):
    if os.path.isfile(uz_tools.TRACKED_CONNECTIONS_FILE):
      f = open(uz_tools.TRACKED_CONNECTIONS_FILE, 'r')
      self.tracked_connections = pickle.load(f);
      f.close()
    else:
      self.tracked_connections = []
      self.tell_user("No connections to track");

  def CreatePopupMenu(self):
    menu = wx.Menu()
    create_menu_item(menu, 'Check', self.on_check)
    create_menu_item(menu, 'Display tracked connections', self.list_connections)
    create_menu_item(menu, 'Add connection(s)', self.add_connections)
    create_menu_item(menu, 'Exit', self.on_exit)
    return menu

  def set_icon(self, path):
    icon = wx.IconFromBitmap(wx.Bitmap(path))
    self.SetIcon(icon, TRAY_TOOLTIP)

  def list_connections(self, event):
    os.system('python print_tracking.py')

  def add_connections(self, event):
    os.system('python add_tracking.py')
    self.LoadConnectionsToTrack()

  def tell_user(self, msg):
    wx.MessageBox(msg, 'UZ Tracker', wx.OK | wx.ICON_INFORMATION)

  def ask_user_yes_no(prompt, msg):
    return wx.MessageBox(msg, 'UZ Tracker', wx.YES | wx.NO | wx.ICON_QUESTION) == wx.YES

  def check_new_seats(self):
    # Check for new connections
    for conn_id in self.tracked_connections:
      if conn_id['num'] == 'new':
        new_connections = uz_tools.query_connections(conn_id['from'], conn_id['till'],
                                                     conn_id['date'], conn_id['time']);
        for connection in new_connections:
          if not uz_tools.conn_id(connection, True) in self.tracked_connections and \
             not uz_tools.conn_id(connection) in self.tracked_connections:
            prompt = "New connection available:\n  ";
            prompt += "\n Connection " + connection[u'num'] + "\n"
            prompt += connection[u'from'][u'actual'] + " - "
            prompt += connection[u'till'][u'actual'] + "\n"
            from_d = timezone('UTC').localize(
                datetime.utcfromtimestamp(connection[u'from'][u'date']))
            prompt += from_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + " - "
            till_d = timezone('UTC').localize(
                datetime.utcfromtimestamp(connection[u'till'][u'date']))
            prompt += till_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + "\n\n"
            prompt += "Track this connection?";
            ignore = not self.ask_user_yes_no(prompt);
            self.tracked_connections.append(uz_tools.conn_id(connection, ignore))
            f = open(uz_tools.TRACKED_CONNECTIONS_FILE, 'w')
            pickle.dump(self.tracked_connections, f)
            f.close()

    # Load current seats
    seats = {}
    for conn_id in self.tracked_connections:
      if conn_id['num'] != 'new' and not conn_id['ignored']:
        conn_str = pickle.dumps(conn_id)
        seats[conn_str] = uz_tools.load_seats(conn_id)

    # Load last known seat situation
    if os.path.isfile(uz_tools.LAST_KNOWN_SEATS_FILE):
      f = open(uz_tools.LAST_KNOWN_SEATS_FILE, 'r')
      last_known_seats = pickle.load(f)
      f.close()
    else:
      last_known_seats = {}

    # Notify user about new seats if any
    have_new_seats = False
    msg = ""
    for conn_id in self.tracked_connections:
      conn_str = pickle.dumps(conn_id)
      if conn_str in seats:
        new_seats = seats[conn_str];
        if conn_str in last_known_seats:
          old_seats = last_known_seats[conn_str];
          for coach_num in old_seats.keys():
            if coach_num in new_seats:
              for place in old_seats[coach_num]['places']:
                if place in new_seats[coach_num]['places']:
                  new_seats[coach_num]['places'].remove(place);
                  if len(new_seats[coach_num]['places']) == 0:
                    del new_seats[coach_num];
        if len(new_seats) == 0:
          continue
        msg += "\nConnection " + conn_id['num'] + "\n"
        msg += conn_id['from_actual'] + " - "
        msg += conn_id['till_actual'] + "\n"
        from_d = timezone('UTC').localize(datetime.utcfromtimestamp(conn_id['from_date']))
        msg += from_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + " - "
        till_d = timezone('UTC').localize(datetime.utcfromtimestamp(conn_id['till_date']))
        msg += till_d.astimezone(timezone("Europe/Kiev")).strftime('%d.%m.%Y %H:%M') + "\n"
        for coach_num in new_seats.keys():
          msg += "  Coach " + str(coach_num) + " (" + new_seats[coach_num]['type'] + "): ";
          for place in new_seats[coach_num]['places']:
            msg += str(place) + " "
          msg += "\n"
        have_new_seats = True

    if have_new_seats:
      self.tell_user("New seats are available for one or more tracked connections.\n" + msg);

    # Store current seats as last known seat situation
    f = open(uz_tools.LAST_KNOWN_SEATS_FILE, 'w')
    pickle.dump(seats, f)
    f.close()

    return have_new_seats

  def on_check(self, event):
    if not self.check_new_seats():
      self.tell_user('No new seats available');

  def on_exit(self, event):
    wx.CallAfter(self.Destroy)

def main():
  app = wx.PySimpleApp()
  TaskBarIcon()
  app.MainLoop()

if __name__ == '__main__':
  main()