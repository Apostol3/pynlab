import win32api
import win32file
import win32pipe

import pywintypes
import win32con
import winerror

__author__ = 'apostol3'


def get_readable_string(e):
    return "Function {func} raised error: {error} Error code: {code}". \
        format(func=e.funcname, error=e.strerror, code=e.winerror)


class PipeStream:
    def __init__(self, pipe_name, in_buf_size, out_buf_size):
        self._is_connected = False
        self.hPipe = pywintypes.HANDLE()
        self.name = pipe_name
        self.inBufSize = in_buf_size
        self.outBufSize = out_buf_size

    @property
    def is_connected(self):
        return self._is_connected

    def receive(self):
        try:
            f_success, buf = win32file.ReadFile(self.hPipe, self.inBufSize, None)
        except win32api.error as e:
            raise RuntimeError(get_readable_string(e))

        if (f_success != 0) or len(buf) == 0:
            if f_success == winerror.ERROR_MORE_DATA:
                raise RuntimeError("InstanceThread: ERROR MORE DATA")
            else:
                raise RuntimeError("InstanceThread ReadFile failed")

        return buf

    def send(self, buf):
        sz = len(buf)
        if sz > self.outBufSize:
            raise RuntimeError("Buffer overflow {} > {}".format(sz, self.outBufSize))
        # todo: check sending if needed
        _, _ = win32file.WriteFile(self.hPipe, buf, None)

    def connect(self):
        try:
            self.hPipe = win32file.CreateFile(self.name, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                                              0, None, win32con.OPEN_EXISTING, 0, None)
        except win32api.error as e:
            raise RuntimeError(get_readable_string(e))
        else:
            self._is_connected = True

    def create(self):
        try:
            self.hPipe = win32pipe.CreateNamedPipe(self.name,
                                                   win32con.PIPE_ACCESS_DUPLEX,
                                                   win32con.PIPE_TYPE_MESSAGE | win32con.PIPE_READMODE_MESSAGE |
                                                   win32con.PIPE_WAIT,
                                                   win32con.PIPE_UNLIMITED_INSTANCES,
                                                   self.outBufSize, self.inBufSize, 0, None)
        except win32api.error as e:
            raise RuntimeError(get_readable_string(e))

    def wait(self):
        if self._is_connected:
            return

        try:
            win32pipe.ConnectNamedPipe(self.hPipe, None)
        except win32api.error as e:
            raise RuntimeError(get_readable_string(e))
        else:
            self._is_connected = True

    def disconnect(self):
        self._is_connected = False
        self.hPipe.close()

    def close(self):
        if not self._is_connected:
            return
        self._is_connected = False
        win32file.FlushFileBuffers(self.hPipe)
        win32pipe.DisconnectNamedPipe(self.hPipe)
        self.hPipe.close()
