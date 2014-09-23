from pkg_resources import resource_string
import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

class RootHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(resource_string(__name__, "index.html"))

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        # XXX
        pass

    def on_message(self, message):
        # XXX
        pass

    def close(self):
        # XXX
        pass

def make_app():
    return tornado.web.Application([
        ('/', RootHandler),
        ('/-/', WebSocketHandler),
    ])

def start_server(sock):
    server = tornado.httpserver.HTTPServer(make_app())
    server.add_socket(sock)
    tornado.ioloop.IOLoop.instance().start()
