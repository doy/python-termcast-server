import multiprocessing
import paramiko
import select
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

        self.rpipe, self.wpipe = multiprocessing.Pipe(False)

    def run(self):
        self.server = Server()
        self.transport.start_server(server=self.server)
        self.chan = self.transport.accept(10)

        if self.chan is not None:
            self.server.pty_event.wait()

            while True:
                self.initialized = False
                self.watching_id = None

                streamer = self.select_stream()
                if streamer is None:
                    break
                self.watching_id = streamer["id"]

                print(
                    "new viewer watching %s (%s)" % (
                        streamer["name"], streamer["id"]
                    )
                )
                self.chan.send(
                    "\033[1;%d;1;%dr\033[m\033[H\033[2J" % (
                        streamer["rows"], streamer["cols"]
                    )
                )
                self.publisher.notify("new_viewer", self.watching_id)

                while True:
                    rout, wout, eout = select.select(
                        [self.chan, self.rpipe],
                        [],
                        []
                    )
                    if self.chan in rout:
                        c = self.chan.recv(1)
                        if c == b'q':
                            print(
                                "viewer stopped watching %s (%s)" % (
                                    streamer["name"], streamer["id"]
                                )
                            )
                            self._cleanup_watcher()
                            break

                    if self.rpipe in rout:
                        self._cleanup_watcher()
                        break

        if self.chan is not None:
            self.chan.close()
        self.transport.close()

    def select_stream(self):
        key_code = ord('a')
        keymap = {}
        streamers = self.publisher.request_all("get_streamers")
        # XXX this will require pagination
        for streamer in streamers:
            key = chr(key_code)
            if key == "q":
                key_code += 1
                key = chr(key_code)
            streamer["key"] = key
            keymap[key] = streamer
            key_code += 1

        self._display_streamer_screen(streamers)

        c = self.chan.recv(1).decode('utf-8', 'ignore')
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
            print("sending %d bytes", len(prev_buf))
            sent = self.chan.send(prev_buf)
            print("successfully sent %d bytes", sent)
            self.initialized = True

        self.chan.send(data)

    def msg_streamer_disconnect(self, connection_id):
        if self.watching_id != connection_id:
            return

        self.wpipe.send("q")

    def _display_streamer_screen(self, streamers):
        self.chan.send("\033[H\033[2JWelcome to Termcast!")
        self.chan.send(
            "\033[3H   %-20s  %-15s  %-10s  %-12s  %-15s" % (
                "User", "Terminal size", "Viewers", "Idle time", "Total time"
            )
        )
        row = 4
        for streamer in streamers:
            key = streamer["key"]
            name = streamer["name"].decode('utf-8', 'replace')
            rows = streamer["rows"]
            cols = streamer["cols"]
            viewers = streamer["viewers"]
            idle = streamer["idle_time"]
            total = streamer["total_time"]
            size = "(%dx%d)" % (cols, rows)
            size_pre = ""
            size_post = ""
            if cols > self.server.cols or rows > self.server.rows:
                size_pre = "\033[31m"
                size_post = "\033[m"
            self.chan.send(
                "\033[%dH%s) %-20s  %s%-15s%s  %-10s  %-12s  %-15s" % (
                    row, key, name, size_pre, size, size_post,
                    viewers, idle, total
                )
            )
            row += 1
        self.chan.send("\033[%dHChoose a stream: " % (row + 1))

    def _cleanup_watcher(self):
        self.publisher.notify(
            "viewer_disconnect", self.watching_id
        )
        self.chan.send(
            ("\033[1;%d;1;%dr"
            + "\033[m"
            + "\033[?9l\033[?1000l"
            + "\033[H\033[2J") % (
                self.server.rows, self.server.cols
            )
        )

class Server(paramiko.ServerInterface):
    def __init__(self):
        super()
        self.cols = 80
        self.rows = 24
        self.pty_event = threading.Event()

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        self.cols = width
        self.rows = height
        self.pty_event.set()
        return True

    def check_channel_window_change_request(
        self, channel, width, height, pixelwidth, pixelheight
    ):
        self.cols = width
        self.rows = height
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        return "password"
