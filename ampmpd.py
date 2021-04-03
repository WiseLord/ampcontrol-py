import mpd

class AmpMpd(object):
    def __init__(self, host, port):
        self.client = mpd.MPDClient()
        self.client.connect(host=host, port=port)

    def cmd_handler(self, cmd):
        print("MPD: cmd " + cmd)
