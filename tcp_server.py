from tornado import ioloop
from tornado.tcpserver import TCPServer
from tornado.template import Loader
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler


class ReaderStream:
    def __init__(self, stream, address, socket_class):
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self._on_close)
        self.stream.read_until('\n', self._read)
        self.name = None
        self.auth = False
        if socket_class._instance is None:
            self.sock = None
        else:
            self.sock = socket_class.__new__(socket_class)

    def _on_read_line(self, data):
        line = data.rstrip()
        print('Auth: %s, Name: %s, Line: %s' % (self.auth, self.name, line))
        if not self.auth:
            if line.startswith('Auth::'):
                self.auth = True
                self.name = line.split('::')[-1].strip()
                if not self.name:
                    self._on_close()
                else:
                    if echo_history.get(self.name):
                        echo_history[self.name]['auth'] = self.auth
                    else:
                        echo_history[self.name] = {'auth': self.auth, 'history': []}
                    self.sock.write_message(echo_history)
            else:
                self._on_close()
        else:
            if 'End' == line:
                echo_history[self.name]['auth'] = False
                self.sock.write_message(echo_history)
                self._on_close()
            else:
                valid = self.validation_line(line)
                if valid['error']:
                    print 'Incorrect mess'
                else:
                    key = valid['key']
                    value = valid['value']
                    echo_history[self.name]['history'].append('%s | %s' % (key, value))
                    if self.sock:
                        self.sock.write_message(echo_history)

        self.stream.read_until('\n', self._read)

    def _read(self, line):
        self._on_read_line(line)

    def _on_close(self):
        self.auth = False

    def validation_line(self, line):
        line = line.split('::')
        if not (len(line) == 2) or not line[0].strip() or not line[1].strip():
            return {'error': True}
        else:
            return {'error': False, 'key': line[0].strip(), 'value': line[1].strip()}


class History(WebSocketHandler):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(History, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def open(self):
        if echo_history:
            self.write_message(echo_history)

    def check_origin(self, origin):
        return True


class Main(RequestHandler):
    def get(self):
        loader = Loader(".")
        self.write(loader.load("template.html").generate())


class TestTcpServer(TCPServer):
    def handle_stream(self, stream, address):
        ReaderStream(stream, address, History)


application = Application([
    (r"/", Main),
    (r"/hist/", History),
], debug=True)

echo_history = {}


def main():
    server = TestTcpServer()
    server.listen(8888)
    application.listen(8080)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    main()
