import dbus


class AmpBluez(object):
    def __init__(self):
        self.notify_cb = None

        bus = dbus.SystemBus()
        obj = bus.get_object('org.bluez', "/")
        mgr = dbus.Interface(obj, 'org.freedesktop.DBus.ObjectManager')

        self.player_iface = None
        self.status = "stopped"
        self.title = ""
        self.artist = ""

        for path, ifaces in mgr.GetManagedObjects().items():
            if 'org.bluez.MediaPlayer1' in ifaces:
                self.player_iface = dbus.Interface(
                    bus.get_object('org.bluez', path),
                    'org.bluez.MediaPlayer1')

        bus.add_signal_receiver(
            self.on_properties_changed,
            bus_name='org.bluez',
            signal_name='PropertiesChanged',
            dbus_interface='org.freedesktop.DBus.Properties')

    def on_properties_changed(self, interface, changed, invalidated):
        if interface != 'org.bluez.MediaPlayer1':
            return

        cb_data = {}
        for prop, value in changed.items():
            if prop == 'Status':
                self.status = value
                cb_data['state'] = str(value)
            elif prop == 'Track':
                if 'Title' in value:
                    self.title = str(value.get('Title', ''))
                if 'Artist' in value:
                    self.artist = str(value.get('Artist', ''))
                cb_data['meta'] = self.artist + " - " + self.title
            elif prop == 'Position':
                cb_data['elapsed'] = float(value / 1000);

        if cb_data:
            self.notify_cb(cb_data)


    def set_notify_cb(self, cb):
        self.notify_cb = cb

    def cmd_handler(self, cmd):
        if not self.player_iface:
            print("No bluetooth player interface!")
            return

        if cmd == "next":
            self.player_iface.Next()
        if cmd == "previous":
            self.player_iface.Previous()
        if cmd == "pause":
            if self.status == "playing":
                self.player_iface.Pause()
            else:
                print("call Play")
                self.player_iface.Play()
        if cmd == "play":
            self.player_iface.Play()
        if cmd == "stop":
            self.player_iface.Stop()
