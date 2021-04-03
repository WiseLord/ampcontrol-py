import mpd
import threading
import time

class AmpMpd(object):
    def __init__(self, host, port):
        self.alive = False
        self.check_thread = None
        self.notify_cb = None

        self.client = mpd.MPDClient()
        self.client.connect(host=host, port=port)

        self.info = {}

    def set_notify_cb(self, cb):
        self.notify_cb = cb

    def start(self):
        self.alive = True
        self.check_thread = threading.Thread(target=self.check_fn, name='check')
        self.check_thread.daemon = True
        self.check_thread.start()

    def on_cmd(self, cmd):
        status = self.client.status()
        state = status.get('state')

        if cmd == 'info':
            self.info.clear()
        if cmd == 'start' or cmd == 'pause':
            if state == 'stop':
                self.client.play()
            else:
                self.client.pause()
        elif cmd == 'stop':
            self.client.stop()
        elif cmd == 'next':
            if state == 'play':
                self.client.next()
        elif cmd == 'previous':
            if state == 'play':
                self.client.previous()
        elif cmd == 'repeat':
            self.client.repeat(int(not int(status.get(cmd))))
        elif cmd == 'random':
            self.client.random(int(not int(status.get(cmd))))
        elif cmd == 'single':
            self.client.single(int(not int(status.get(cmd))))
        elif cmd == 'consume':
            self.client.consume(int(not int(status.get(cmd))))


    def on_mpd_info(self):
        cb_data = {}
        song = self.client.currentsong()
        status = self.client.status()

        update_meta = False
        for key in {'artist', 'title', 'name'}:
            if self.info.get(key) != song.get(key):
                self.info[key] = song.get(key)
                update_meta = True
        if update_meta:
            cb_data['meta'] = self.info.get('name')
            if self.info['title']:
                if self.info['artist']:
                    cb_data['meta'] = self.info.get('artist') + ' - ' + self.info.get('title')
                else:
                    cb_data['meta'] = self.info.get('title')

        for flag in {'state', 'repeat', 'random', 'single', 'consume'}:
            if self.info.get(flag) != status.get(flag):
                self.info[flag] = status.get(flag)
                cb_data[flag] = self.info.get(flag)

        if cb_data and self.notify_cb:
            self.notify_cb(cb_data)


    def check_fn(self):
        while self.alive:
            self.on_mpd_info();
            time.sleep(0.1)

