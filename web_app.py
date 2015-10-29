from tornado import ioloop
from tornado.template import Loader
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler

from tcp_server import SimpleTcpServer


class History(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(History, self).__init__(*args, **kwargs)

    def open(self):
        open_sockets.append(self)
        if echo_history:
            self.write_message(echo_history)

    def on_message(self, message):
        print(message)

    def check_origin(self, origin):
        return True

    def on_close(self):
        open_sockets.remove(self)


class Main(RequestHandler):
    def get(self):
        loader = Loader(".")
        self.write(loader.load("template.html").generate())


application = Application([
    (r"/", Main),
    (r"/hist/", History),
], debug=True)

echo_history = {}
open_sockets = []


def main():
    loop = ioloop.IOLoop.current()
    server = SimpleTcpServer(echo_history, open_sockets, io_loop=loop)
    server.listen(8888)
    application.listen(8080)
    loop.start()


if __name__ == '__main__':
    main()
