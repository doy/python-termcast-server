import paramiko
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
        self.transport.start_server(server=Server())
        self.chan = self.transport.accept(None)

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
        self.chan.send("\033[2J\033[HWelcome to Termcast!")
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
