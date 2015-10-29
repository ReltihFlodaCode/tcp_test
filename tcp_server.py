from tornado.tcpserver import TCPServer


class ReaderStream:
    def __init__(self, stream, address, history, open_sockets):
        self.stream = stream
        self.address = address
        self.stream.set_close_callback(self._on_close)
        self.stream.read_until('\n', self._read)
        self.name = None
        self.auth = False
        self.history = history
        self.open_sockets = open_sockets

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
                    if self.history.get(self.name):
                        self.history[self.name]['auth'] = self.auth
                    else:
                        self.history[self.name] = {'auth': self.auth, 'history': []}
                    self.broadcast()
            else:
                self._on_close()
        else:
            if 'End' == line:
                self.history[self.name]['auth'] = False
                self.broadcast()
                self._on_close()
            else:
                valid = self.validation_line(line)
                if valid['error']:
                    print 'Incorrect mess'
                else:
                    key = valid['key']
                    value = valid['value']
                    self.history[self.name]['history'].append('%s | %s' % (key, value))
                    self.broadcast()

        self.stream.read_until('\n', self._read)

    def broadcast(self):
        for sock in self.open_sockets:
            sock.write_message(self.history)

    def _read(self, line):
        self._on_read_line(line)

    def _on_close(self):
        self.auth = False

    @staticmethod
    def validation_line(line):
        line = line.split('::')
        if not (len(line) == 2) or not line[0].strip() or not line[1].strip():
            return {'error': True}
        else:
            return {'error': False, 'key': line[0].strip(), 'value': line[1].strip()}


class SimpleTcpServer(TCPServer):
    def __init__(self, echo_history, open_sockets, *args, **kwargs):
        super(SimpleTcpServer, self).__init__(*args, **kwargs)
        self.echo_history = echo_history
        self.open_sockets = open_sockets

    def handle_stream(self, stream, address):
        ReaderStream(stream, address, history=self.echo_history, open_sockets=self.open_sockets)
