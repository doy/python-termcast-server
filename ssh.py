import paramiko
import time

class Connection(object):
    def __init__(self, client, connection_id, publisher):
        self.transport = paramiko.Transport(client)
        self.transport.add_server_key(paramiko.RSAKey(filename='test_rsa.key'))
        self.connection_id = connection_id
        self.publisher = publisher
        self.initialized = False

    def run(self):
        self.transport.start_server(server=Server())
        self.chan = self.transport.accept(None)

        self.watching_id = self.select_stream()

        self.publisher.notify("new_viewer", self.watching_id)

        while True:
            c = self.chan.recv(1)
            if c == b'q':
                break
        self.chan.close()

    def select_stream(self):
        self.chan.send("\033[2J\033[HTermcast")
        row = 3
        key_code = ord('a')
        keymap = {}
        for streamer in self.publisher.request_all("get_streamers"):
            key = chr(key_code)
            keymap[key] = streamer["id"]
            self.chan.send("\033[%dH%s) %s" % (row, key, streamer["name"].decode('utf-8')))
            row += 1
            key_code += 1

        self.chan.send("\033[%dHChoose a stream: " % (row + 1))

        c = self.chan.recv(1).decode('utf-8')
        if c in keymap:
            self.chan.send("\033[2J\033[H")
            return keymap[c]
        else:
            return self.select_stream()

    def msg_new_data(self, connection_id, prev_buf, data):
        if self.watching_id != connection_id:
            return

        if not self.initialized:
            self.chan.send(prev_buf)
            self.initialized = True

        self.chan.send(data)

class Server(paramiko.ServerInterface):
    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_auth_password(self, username, password):
        if password == "blah":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"
