import signal
import socket
import sys
import threading
import uuid

from . import pubsub
from . import ssh
from . import termcast
from . import web

class Server(object):
    def __init__(self, keyfile):
        self.publisher = pubsub.Publisher()
        self.keyfile = keyfile

    def listen(self):
        ssh_sock = self._open_socket(2200)
        termcast_sock = self._open_socket(2201)
        web_sock = self._open_socket(2202)

        threading.Thread(
            target=lambda: self.wait_for_ssh_connection(ssh_sock)
        ).start()
        threading.Thread(
            target=lambda: self.wait_for_termcast_connection(termcast_sock)
        ).start()
        threading.Thread(
            target=lambda: self.wait_for_web_connection(web_sock)
        ).start()

    def wait_for_ssh_connection(self, sock):
        self._wait_for_connection(
            sock,
            lambda client: self.handle_ssh_connection(client)
        )

    def wait_for_termcast_connection(self, sock):
        self._wait_for_connection(
            sock,
            lambda client: self.handle_termcast_connection(client)
        )

    def wait_for_web_connection(self, sock):
        sock.setblocking(0)
        sock.listen(100)
        web.start_server(sock)

    def handle_ssh_connection(self, client):
        self._handle_connection(
            client,
            lambda client, connection_id: ssh.Connection(
                client, connection_id, self.publisher, self.keyfile
            )
        )

    def handle_termcast_connection(self, client):
        self._handle_connection(
            client,
            lambda client, connection_id: termcast.Connection(
                client, connection_id, self.publisher
            )
        )

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

    def _handle_connection(self, client, cb):
        connection_id = uuid.uuid4().hex
        connection = cb(client, connection_id)
        self.publisher.subscribe(connection)
        connection.run()
        self.publisher.unsubscribe(connection)

    def _open_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        return sock

def main():
    server = Server(sys.argv[1])
    server.listen()
