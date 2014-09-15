import socket
import threading
import uuid

import ssh
import termcast

class Server(object):
    def __init__(self):
        self.termcast_connections = {}
        self.ssh_connections = {}

    def listen(self):
        ssh_sock = self._open_socket(2200)
        termcast_sock = self._open_socket(2201)

        threading.Thread(
            target=lambda: self.wait_for_ssh_connection(ssh_sock)
        ).start()
        threading.Thread(
            target=lambda: self.wait_for_termcast_connection(termcast_sock)
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

    def handle_ssh_connection(self, client):
        self._handle_connection(
            client,
            self.ssh_connections,
            self.termcast_connections,
            lambda client, connection_id: ssh.Connection(client, connection_id)
        )

    def handle_termcast_connection(self, client):
        self._handle_connection(
            client,
            self.termcast_connections,
            self.ssh_connections,
            lambda client, connection_id: termcast.Connection(client, connection_id)
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

    def _handle_connection(self, client, connection_store, other_store, cb):
        connection_id = uuid.uuid4().hex
        connection = cb(client, connection_id)
        connection_store[connection_id] = connection
        connection.run(other_store)
        del connection_store[connection_id]

    def _open_socket(self, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        return sock

if __name__ == '__main__':
    server = Server()
    server.listen()
