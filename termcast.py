import re

import vt100

class Handler(object):
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

class Connection(object):
    def __init__(self, client, connection_id):
        self.client = client

    def run(self, ssh_connections):
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
        self.handler = Handler()
        self.client.send(b"hello, " + m.group(1) + b"\n")

        self.handler.process(buf)
        while True:
            buf = self.client.recv(1024)
            if len(buf) > 0:
                self.handler.process(buf)
            else:
                return
