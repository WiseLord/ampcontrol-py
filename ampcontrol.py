import getopt
import subprocess
import sys
import threading

import dbus.mainloop.glib
from gi.repository import GLib

from ampbluez import AmpBluez
from ampmpd import AmpMpd
from ampnetwork import AmpNetwork
from ampserial import AmpSerial

class AmpControl(object):
    def __init__(self, argv):
        self.serial = '/dev/ttyS0'
        self.baud = 115200
        self.host = 'localhost'
        self.port = 6600
        self.get_args(argv)

        self.info = {}
        self.mode = "mpd"

        self.network = AmpNetwork()
        self.network.set_notify_cb(self.on_notify)

        self.cmd_queue = []
        self.cmd_event = threading.Event()
        self.cmd_thread = threading.Thread(target=self.cmd_fn, name='cmd')
        self.cmd_thread.daemon = True

        self.serial = AmpSerial(port=self.serial, baudrate=self.baud)
        self.serial.set_read_cb(self.on_cmd)

        self.bluez = AmpBluez()
        self.bluez.set_notify_cb(self.on_notify)

        self.mpd = AmpMpd(host=self.host, port=self.port)
        self.mpd.set_notify_cb(self.on_notify)

    def start(self):
        self.cmd_thread.start()
        self.serial.start();
        self.network.start();
        self.mpd.start();

    def on_notify(self, keys):
        for key in keys:
            if key not in self.info or key != self.info[key]:
                self.info[key] = keys[key]
        self.notify(keys)

    def on_cmd(self, cmd):
        cmd = str(cmd).strip()
        if cmd:
            print("<<<: '" + cmd + "'")
            if cmd.startswith('cli.'):
                self.cmd_queue.append(cmd[len('cli.'):])
                self.cmd_event.set()

    def cmd_fn(self):
        while True:
            self.cmd_event.wait()
            while self.cmd_queue:
                cmd = self.cmd_queue.pop(0)
                if cmd == 'info':
                    self.info.clear()
                    self.network.clear()
                if cmd.startswith('mode'):
                    try:
                        mode = cmd[6:-2].strip()
                        self.mode = mode
                        if mode == 'bluez':
                            subprocess.call(['/usr/bin/bluetoothctl', 'discoverable', 'on'])
                        else:
                            subprocess.call(['/usr/bin/bluetoothctl', 'discoverable', 'off'])
                    except:
                        pass
                elif self.mode == "bluez":
                    self.bluez.on_cmd(cmd)
                elif self.mode == "mpd":
                    self.mpd.on_cmd(cmd)
            self.cmd_event.clear()

    def get_args(self, argv):
        try:
            opts, args = getopt.getopt(argv, "s:b:h:p:", ["serial=", "baud=", "host=", "port="])
        except getopt.GetoptError:
            print("Wrong command line arguments")
            sys.exit(2)

        for opt, arg in opts:
            if opt in ("-s", "--serial"):
                self.serial = arg
            if opt in ("-b", "--baud"):
                self.baud = arg
            if opt in ("-h", "--host"):
                self.host = arg
            if opt in ("-p", "--port"):
                self.port = arg

    def notify(self, keys):
        if 'all' in keys:
            keys = self.info.keys()
        for key in keys:
            if key in 'ip':
                self.serial.send('ip:' + str(self.info.get('ip')))
            elif key in 'meta':
                self.serial.send('##CLI.META#: ' + str(self.info.get('meta')))
            elif key in 'state':
                state = str(self.info.get('state'))
                if state.startswith('play'):
                    self.serial.send('##CLI.PLAYING#')
                elif state.startswith('pause'):
                    self.serial.send('##CLI.PAUSED#')
                elif state.startswith('stop'):
                    self.serial.send('##CLI.STOPPED#')
            elif key in 'elapsed':
                self.serial.send('##CLI.ELAPSED#: ' + str(round(self.info['elapsed'])))
            elif key in 'repeat':
                self.serial.send('##CLI.REPEAT#: ' + str(self.info.get('repeat')))
            elif key in 'random':
                self.serial.send('##CLI.RANDOM#: ' + str(self.info.get('random')))
            elif key in 'single':
                self.serial.send('##CLI.SINGLE#: ' + str(self.info.get('single')))
            elif key in 'consume':
                self.serial.send('##CLI.CONSUME#: ' + str(self.info.get('consume')))


if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    amp = AmpControl(sys.argv[1:])
    amp.start()

    GLib.MainLoop().run()
