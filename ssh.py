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

    def run(self):
        self.transport.start_server(server=Server())
        chan = self.transport.accept(None)

        # XXX need to have the user select a stream, and then pass the stream's
        # id in here
        contents = self.publisher.request_one("new_viewer", "some-random-id")
        chan.send(contents)

        time.sleep(5)
        chan.close()

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
