import mpd
import threading
import time

class AmpMpd(object):
    def __init__(self, host, port):
        self.alive = False
        self.check_thread = None
        self.notify_cb = None
        self.mpd_lock = threading.Lock()

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

    def reset_duration(self):
        self.notify_cb({'duration': 0})

    def on_cmd(self, cmd):
        self.mpd_lock.acquire()

        state = self.info.get('state')

        try:
            if cmd == 'info':
                self.info.clear()
            elif cmd == 'start' or cmd == 'pause':
                if state == 'stop':
                    self.client.play()
                else:
                    self.client.pause()
            elif cmd == 'stop':
                self.reset_duration()
                self.client.stop()
            elif cmd == 'rewind':
                if state == 'play':
                    elapsed = float(self.info.get('elapsed'))
                    pos = elapsed - 5
                    if pos < 0:
                        pos = 0
                    self.client.seekcur(pos)
            elif cmd == 'ffwd':
                if state == 'play':
                    elapsed = float(self.info.get('elapsed'))
                    pos = elapsed + 5
                    self.client.seekcur(pos)
            elif cmd == 'next':
                if state == 'play':
                    self.reset_duration()
                    self.client.next()
            elif cmd == 'previous':
                if state == 'play':
                    self.reset_duration()
                    self.client.previous()
            elif cmd == 'repeat':
                self.client.repeat(int(not int(self.info.get('repeat'))))
            elif cmd == 'random':
                self.client.random(int(not int(self.info.get('random'))))
            elif cmd == 'single':
                self.client.single(int(not int(self.info.get('single'))))
            elif cmd == 'consume':
                self.client.consume(int(not int(self.info.get('consume'))))
            elif cmd.startswith('load'):
                playlists = self.client.listplaylists()
                pl_name = cmd[6:-2].strip()
                if next((pl for pl in playlists if pl['playlist'] == pl_name), False):
                    self.reset_duration()
                    self.client.clear()
                    self.client.load(pl_name)
                    self.client.play()
        except:
            pass

        self.mpd_lock.release()


    def on_mpd_info(self):
        cb_data = {}

        self.mpd_lock.acquire()
        song = self.client.currentsong()
        status = self.client.status()
        self.mpd_lock.release()

        update_meta = False
        for key in {'artist', 'title', 'name'}:
            value = song.get(key)
            if self.info.get(key) != value:
                self.info[key] = value
                update_meta = True

        if update_meta:
            cb_data['meta'] = self.info.get('name')
            if self.info.get('title'):
                if self.info.get('artist'):
                    cb_data['meta'] = self.info.get('artist') + ' - ' + self.info.get('title')
                else:
                    cb_data['meta'] = self.info.get('title')

        for key in {'state', 'repeat', 'random', 'single', 'consume'}:
            value = status.get(key)
            if self.info.get(key) != value:
                self.info[key] = value
                if key == 'state':
                    if value == 'stop':
                        cb_data[key] = 'stopped'
                    elif value == 'play':
                        cb_data[key] = 'playing'
                    elif value == 'pause':
                        cb_data[key] = 'paused'
                else:
                    cb_data[key] = value

        for key in {'duration', 'elapsed'}:
            value = status.get(key)
            if value:
                oldval = self.info.get(key)
                if not oldval or (round(float(oldval)) != round(float(value))):
                    self.info[key] = value
                    cb_data[key] = round(float(value))

        if cb_data and self.notify_cb:
            self.notify_cb(cb_data)


    def check_fn(self):
        while self.alive:
            self.on_mpd_info();
            time.sleep(0.1)

