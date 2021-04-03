import getopt
import sys

import dbus.mainloop.glib
from gi.repository import GLib

from ampbluez import AmpBluez
from ampserial import AmpSerial


def on_property_changed(interface, changed, invalidated):
    if interface != 'org.bluez.MediaPlayer1':
        return

    for prop, value in changed.items():
        if prop == 'Status':
            print('Playback Status: {}'.format(value))
        elif prop == 'Track':
            print('Music Info:')
            for key in ('Title', 'Artist', 'Album'):
                print('   {}: {}'.format(key, value.get(key, '')))
        elif prop == 'Position':
            print(value)


class AmpControl(object):
    def __init__(self, argv):
        serial = '/dev/ttyS0'
        baud = 115200
        host = 'localhost'
        port = 6600

        try:
            opts, args = getopt.getopt(argv, "s:b:h:p:", ["serial=", "baud=", "host=", "port="])
        except getopt.GetoptError:
            print("Wrong command line arguments")
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-s", "--serial"):
                serial = arg
            if opt in ("-b", "--baud"):
                baud = arg
            if opt in ("-h", "--host"):
                host = arg
            if opt in ("-p", "--port"):
                port = arg

        self.serial = AmpSerial(port=serial, baudrate=baud)
        self.bluez = AmpBluez()

    def run(self):
        pass


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    amp = AmpControl(sys.argv[1:])
    # amp.run()

    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        on_property_changed,
        bus_name='org.bluez',
        signal_name='PropertiesChanged',
        dbus_interface='org.freedesktop.DBus.Properties')

    GLib.MainLoop().run()
