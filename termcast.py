import json
import re

import vt100

class Handler(object):
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.buf = b''
        self.vt = vt100.vt100(rows, cols)

    def process(self, data):
        self.buf += data
        self.vt.process(data)

    def get_term(self):
        term = ''
        for i in range(0, self.rows):
            for j in range(0, self.cols):
                term += self.vt.cell(i, j).contents()
            term += "\n"

        return term[:-1]

class Connection(object):
    def __init__(self, client, connection_id, publisher):
        self.client = client
        self.connection_id = connection_id
        self.publisher = publisher

    def run(self):
        buf = b''
        while len(buf) < 1024 and b"\n" not in buf:
            buf += self.client.recv(1024)

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
        self.client.send(b"hello, " + m.group(1) + b"\n")

        extra_data = {}
        extra_data_re = re.compile(b'^\033\[H\000([^\377]*)\377\033\[H\033\[2J(.*)$')
        m = extra_data_re.match(buf)
        if m is not None:
            extra_data_json = m.group(1)
            extra_data = json.loads(extra_data_json.decode('utf-8'))
            buf = m.group(2)

        if "geometry" in extra_data:
            self.handler = Handler(extra_data["geometry"][1], extra_data["geometry"][0])
        else:
            self.handler = Handler(24, 80)

        self.handler.process(buf)
        while True:
            buf = self.client.recv(1024)
            if len(buf) > 0:
                self.handler.process(buf)
            else:
                return

    def msg_new_viewer(self, sock, connection_id):
        # XXX restore this once we start passing in meaningful connection ids
        # if connection_id != self.connection_id:
        #     return
        term_contents = self.handler.get_term()
        sock.send(term_contents.replace("\n", "\r\n"))
