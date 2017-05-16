import socket

__author__ = 'leon.ljsh'


class TCPStream:
    def __init__(self, ip_address, tcp_port, buf_size=1024):
        self._is_connected = False
        self.connection = None
        self.address = None
        self.tcp_address = ip_address
        self.tcp_port = tcp_port
        self.buf_size = buf_size
        self._is_server = False
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    @property
    def is_connected(self):
        return self._is_connected

    def receive(self):
        if self._is_server:
            socket_ = self.connection
        else:
            socket_ = self.socket_
        buf = socket_.recv(self.buf_size)

        while buf[-1] != 0:
            buf_tmp = socket_.recv(self.buf_size)
            buf += buf_tmp

        return buf

    def send(self, buf):
        if self._is_server:
            socket_ = self.connection
        else:
            socket_ = self.socket_
        socket_.send(buf)

    def connect(self):
        self.socket_.connect((self.tcp_address, self.tcp_port))
        self._is_connected = True

    def create(self):
        self.socket_.bind((self.tcp_address, self.tcp_port))
        self.socket_.listen()
        self._is_server = True

    def wait(self):
        self.connection, self.address = self.socket_.accept()

    def disconnect(self):
        self._is_connected = False
        self.socket_.close()

    def close(self):
        self._is_connected = False
        self.connection.close()
