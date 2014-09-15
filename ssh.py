import paramiko
import threading
import time

class Connection(object):
    def __init__(self, client, connection_id, publisher, keyfile):
        self.transport = paramiko.Transport(client)

        key = None
        with open(keyfile) as f:
            header = f.readline()
            if header == "-----BEGIN DSA PRIVATE KEY-----\n":
                key = paramiko.DSSKey(filename=keyfile)
            elif header == "-----BEGIN RSA PRIVATE KEY-----\n":
                key = paramiko.RSAKey(filename=keyfile)
        if key is None:
            raise Exception("%s doesn't appear to be an SSH keyfile" % keyfile)
        self.transport.add_server_key(key)

        self.connection_id = connection_id
        self.publisher = publisher
        self.initialized = False
        self.watching_id = None

    def run(self):
        self.server = Server()
        self.transport.start_server(server=self.server)
        self.chan = self.transport.accept(10)
        self.server.pty_event.wait()

        while True:
            self.initialized = False
            self.watching_id = None

            self.watching_id = self.select_stream()
            if self.watching_id is None:
                break

            self.publisher.notify("new_viewer", self.watching_id)

            while True:
                c = self.chan.recv(1)
                if c == b'q':
                    self.publisher.notify("viewer_disconnect", self.watching_id)
                    break

        self.chan.close()

    def select_stream(self):
        key_code = ord('a')
        keymap = {}
        streamers = self.publisher.request_all("get_streamers")
        for streamer in streamers:
            key = chr(key_code)
            streamer["key"] = key
            keymap[key] = streamer["id"]
            key_code += 1

        self._display_streamer_screen(streamers)

        c = self.chan.recv(1).decode('utf-8')
        if c in keymap:
            self.chan.send("\033[2J\033[H")
            return keymap[c]
        elif c == 'q':
            self.chan.send("\r\n")
            return None
        else:
            return self.select_stream()

    def msg_new_data(self, connection_id, prev_buf, data):
        if self.watching_id != connection_id:
            return

        if not self.initialized:
            self.chan.send(prev_buf)
            self.initialized = True

        self.chan.send(data)

    def _display_streamer_screen(self, streamers):
        self.chan.send("\033[2J\033[HWelcome to Termcast!")
        self.chan.send(
            "\033[3H   %-20s  %-15s  %-15s" % (
                "User", "Terminal size", "Idle time",
            )
        )
        row = 4
        for streamer in streamers:
            key = streamer["key"]
            name = streamer["name"].decode('utf-8')
            size = "(%dx%d)" % (streamer["cols"], streamer["rows"])
            size_pre = ""
            size_post = ""
            if streamer["cols"] > self.server.cols or streamer["rows"] > self.server.rows:
                size_pre = "\033[31m"
                size_post = "\033[m"
            idle = streamer["idle"]
            self.chan.send(
                "\033[%dH%s) %-20s  %s%-15s%s  %-15s" % (
                    row, key, name, size_pre, size, size_post, idle
                )
            )
            row += 1
        self.chan.send("\033[%dHChoose a stream: " % (row + 1))

class Server(paramiko.ServerInterface):
    def __init__(self):
        super()
        self.cols = 80
        self.rows = 24
        self.pty_event = threading.Event()

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        self.cols = width
        self.rows = height
        self.pty_event.set()
        return True

    def check_channel_window_change_request(self, channel, width, height, pixelwidth, pixelheight):
        self.cols = width
        self.rows = height
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_auth_password(self, username, password):
        if password == "blah":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"
