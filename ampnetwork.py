import threading
import time
import socket

class AmpNetwork(object):
    def __init__(self):
        self.ip = "127.0.0.1"
        self.alive = False
        self.check_thread = None
        self.notify_cb = None

    def set_notify_cb(self, cb):
        self.notify_cb = cb

    def start(self):
        self.alive = True
        self.check_thread = threading.Thread(target=self.check_fn, name='check')
        self.check_thread.daemon = True
        self.check_thread.start()

    def join(self):
        self.check_thread.join()

    def get_ip(self):
        return self.ip

    def update_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)

        try:
            s.connect(('8.8.8.8', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def check_fn(self):
        while self.alive:
            ip = self.update_ip()
            if ip != self.ip:
                self.ip = ip
                if self.notify_cb:
                    cb_data = {'ip': ip}
                    self.notify_cb(cb_data)
            time.sleep(2)

