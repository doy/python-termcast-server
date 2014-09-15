import paramiko
import time

class Handler(object):
    def __init__(self, sock, connections):
        self.sock = sock
        self.connections = connections
        self.which

    def show(self):
        pass

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

        # XXX need to have the user select a stream, and then pass the stream's
        # id in here
        self.publisher.notify("new_viewer", "some-stream")

        while True:
            c = self.chan.recv(1)
            if c == b'q':
                break
        self.chan.close()

    def msg_new_data(self, connection_id, prev_buf, data):
        # XXX uncomment this once we implement stream selection
        # if self.watching_id != connection_id:
        #     return

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
