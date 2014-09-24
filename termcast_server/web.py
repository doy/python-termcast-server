from pkg_resources import resource_string
import json
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(resource_string(__name__, "index.html"))

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, publisher):
        self.publisher = publisher
        self.watching_id = None
        self.initialized = False
        self.publisher.subscribe(self)

    def on_message(self, message):
        print(message)
        data = json.loads(message)
        if data["type"] == "request_streamer_list":
            streamers = self.publisher.request_all("get_streamers")
            reply = {
                "type": "streamer_list",
                "streamers": [ { "id": s["id"], "name": s["name"].decode('utf-8', 'replace') } for s in streamers ],
            }
            self.write_message(json.dumps(reply))
        elif data["type"] == "start_watching":
            self.watching_id = data["who"]
            self.publisher.notify("new_viewer", self.watching_id)

    def on_finish(self):
        self.publisher.unsubscribe(self)

    def msg_new_data(self, connection_id, prev_buf, data):
        if self.watching_id != connection_id:
            return
        self.write_message(json.dumps({"type": "update_screen"}))

def make_app(publisher):
    return tornado.web.Application([
        ('/', RootHandler),
        ('/-/', WebSocketHandler, dict(publisher=publisher)),
    ])

def start_server(sock, publisher):
    server = tornado.httpserver.HTTPServer(make_app(publisher))
    server.add_socket(sock)
    tornado.ioloop.IOLoop.instance().start()
