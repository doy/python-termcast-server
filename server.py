import paramiko
import re
import socket
import time
import threading
import vt100

class Connection(object):
    def __init__(self):
        self.buf = b''
        self.vt = vt100.vt100()

    def process(self, data):
        self.buf += data
        self.vt.process(data)

    def get_term(self):
        term = ''
        for i in range(0, 24):
            for j in range(0, 80):
                term += self.vt.cell(i, j).contents.contents()
            term += "\n"

        return term[:-1]

class SSHServer(paramiko.ServerInterface):
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

class TermcastServer(object):
    def __init__(self):
        self.sessions = {}

    def listen(self):
        ssh_sock = self._open_socket(2200)
        tc_sock = self._open_socket(2201)

        threading.Thread(
            target=lambda: self.wait_for_ssh_connection(ssh_sock)
        ).start()
        threading.Thread(
            target=lambda: self.wait_for_tc_connection(tc_sock)
        ).start()

    def wait_for_ssh_connection(self, sock):
        self._wait_for_connection(
            sock,
            lambda client: self.handle_ssh_connection(client)
        )

    def wait_for_tc_connection(self, sock):
        self._wait_for_connection(
            sock,
            lambda client: self.handle_tc_connection(client)
        )

    def handle_ssh_connection(self, client):
        t = paramiko.Transport(client)
        t.add_server_key(paramiko.RSAKey(filename='test_rsa.key'))
        t.start_server(server=SSHServer())
        chan = t.accept(None)

        if b'doy' in self.sessions:
            chan.send(self.sessions[b'doy'].get_term())
        else:
            chan.send("no data for doy\r\n")

        time.sleep(5)
        chan.close()

    def handle_tc_connection(self, client):
        buf = b''
        while len(buf) < 1024 and b"\n" not in buf:
            buf += client.recv(1024)

        pos = buf.find(b"\n")
        if pos == -1:
            print("no authentication found")
            return

        auth = buf[:pos]
        buf = buf[pos+1:]

        auth_re = re.compile(b'^hello ([^ ]+) ([^ ]+)$')
        m = auth_re.match(auth)
        if m is None:
            print("no authentication found (%s)" % auth)
            return

        print(b"got auth: " + auth)
        conn = Connection()
        self.sessions[m.group(1)] = conn
        client.send(b"hello, " + m.group(1) + b"\n")

        conn.process(buf)
        while True:
            buf = client.recv(1024)
            if len(buf) > 0:
                conn.process(buf)
            else:
                return

    def _wait_for_connection(self, sock, cb):
        while True:
            try:
                sock.listen(100)
                client, addr = sock.accept()
            except Exception as e:
                print('*** Listen/accept failed: ' + str(e))
                traceback.print_exc()
                continue

            threading.Thread(target=cb, args=(client,)).start()

    def _open_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        return sock

if __name__ == '__main__':
    server = TermcastServer()
    server.listen()
