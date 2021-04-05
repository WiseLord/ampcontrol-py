import dbus
import time
import threading


class AmpBluez(object):
    def __init__(self):
        self.alive = False
        self.check_thread = None
        self.notify_cb = None

        self.player_iface = None
        self.player_props = None

        self.info = {}

        bus = dbus.SystemBus()
        bus.add_signal_receiver(
            self.on_properties_changed,
            bus_name='org.bluez',
            signal_name='PropertiesChanged',
            dbus_interface='org.freedesktop.DBus.Properties')

    def set_notify_cb(self, cb):
        self.notify_cb = cb

    def start(self):
        self.alive = True
        self.check_thread = threading.Thread(target=self.check_fn, name='check')
        self.check_thread.daemon = True
        self.check_thread.start()

    def check_fn(self):
        while self.alive:

            bus = dbus.SystemBus()
            proxy = bus.get_object('org.bluez', "/")
            mgr = dbus.Interface(proxy, 'org.freedesktop.DBus.ObjectManager')

            player_iface = None
            player_props = None
            for path, ifaces in mgr.GetManagedObjects().items():
                if 'org.bluez.MediaPlayer1' in ifaces:
                    player_proxy = bus.get_object('org.bluez', path)
                    player_iface = dbus.Interface(player_proxy, 'org.bluez.MediaPlayer1')
                    player_props = dbus.Interface(player_proxy, 'org.freedesktop.DBus.Properties')
                    break
            self.player_iface = player_iface
            self.player_props = player_props

            time.sleep(1)

    def get_meta(self, track):
        meta = ''
        if 'Title' in track:
            self.info['title'] = str(track.get('Title'))
        if 'Artist' in track:
            self.info['artist'] = str(track.get('Artist'))

        if self.info.get('title'):
            meta = self.info.get('title')
            if self.info.get('artist'):
                meta = self.info.get('artist') + " - " + meta
        else:
            if self.info.get('artist'):
                meta = self.info.get('artist')

        return meta

    def on_properties_changed(self, interface, changed, invalidated):
        if interface != 'org.bluez.MediaPlayer1':
            return

        cb_data = {}
        for prop, value in changed.items():
            if prop == 'Status':
                self.info['state'] = value
                cb_data['state'] = str(value)
            elif prop == 'Track':
                cb_data['meta'] = self.get_meta(value)
            # elif prop == 'Position':
            #     cb_data['elapsed'] = float(value / 1000)

        if cb_data and self.notify_cb:
            self.notify_cb(cb_data)

    def on_info(self):
        cb_data = {}
        print('bluez on_info:')

        if self.player_props:
            track = self.player_props.Get('org.bluez.MediaPlayer1', 'Track')
            cb_data['meta'] = self.get_meta(track)
            # print(track)
        else:
            print("No bluetooth player!")

        if cb_data and self.notify_cb:
            # print('call bt notify_cb' + str(cb_data))
            self.notify_cb(cb_data)

    def on_cmd(self, cmd):
        if not self.player_iface:
            print("No bluetooth player!")
            return

        if cmd == 'info':
            self.info.clear()
            self.on_info()
        if cmd == "next":
            self.player_iface.Next()
        elif cmd == "previous":
            self.player_iface.Previous()
        elif cmd == "pause":
            if self.info.get('state') == "playing":
                self.player_iface.Pause()
            else:
                self.player_iface.Play()
        elif cmd == "play":
            self.player_iface.Play()
        elif cmd == "stop":
            self.player_iface.Stop()
