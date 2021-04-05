import serial
import threading


class AmpSerial(object):
    def __init__(self, port, baudrate):
        self.serial = serial.Serial(port=port, baudrate=baudrate)
        self.alive = False
        self.reader_thread = None
        self.read_cb = None
        self.write_lock = threading.Lock()

    def set_read_cb(self, cb):
        self.read_cb = cb

    def send(self, info):
        self.write_lock.acquire()
        print('>>>: ' + info)
        self.serial.write(bytes(info + '\r\n', 'utf-8'))
        self.write_lock.release()

    def start(self):
        self.alive = True
        self.reader_thread = threading.Thread(target=self.reader_fn, name='reader')
        self.reader_thread.daemon = True
        self.reader_thread.start()

    def join(self):
        self.reader_thread.join()

    def reader_fn(self):
        while self.alive:
            try:
                str_seq = self.serial.read_until(serial.LF, 256)
                str_seq = str(str_seq, 'utf-8').strip()
                if self.read_cb:
                    self.read_cb(str_seq)
                if str_seq == 'quit':
                    self.alive = False
            except:
                pass
