import json
import win32api
import win32file

import win32con
import winerror

from env import *

__author__ = 'apostol3'

PIPES_VER = 0x00000100


def error_box(string):
    win32api.MessageBox(0, string, "Error", win32con.MB_OK | win32con.MB_ICONERROR)


def get_readable_string(e):
    return "Function {func} raised error:\n{error}\nError code: {code}". \
        format(func=e.funcname, error=e.strerror, code=e.winerror)


class PacketType(Enum):
    none = 0
    e_start_info = 1
    n_start_info = 2
    n_send_info = 3
    e_send_info = 4
    n_restart_info = 5
    e_restart_info = 6


class NLab:
    def __init__(self, pipe_name="\\\\.\\pipe\\nlab"):
        self._is_connected = False
        self.hPipe = 0
        self.pipe_name = pipe_name
        self.inBufSize = 307200
        self.outBufSize = 307200
        self.lasthead = VerificationHeader.fail
        self.state = EnvState()
        self.lrinfo = NRestartInfo()

    def connect(self):

        try:
            self.hPipe = win32file.CreateFile(self.pipe_name, win32con.GENERIC_READ | win32con.GENERIC_WRITE,
                                              0, None, win32con.OPEN_EXISTING, 0, None)
        except win32api.error as e:
            error_box(get_readable_string(e))
            return -1
        else:
            self._is_connected = True
        return 0

    def get_state(self):
        return self.state

    def _receive(self):

        f_success, buf = win32file.ReadFile(self.hPipe, self.inBufSize, None)

        if (f_success != 0) or len(buf) == 0:
            if f_success == winerror.ERROR_MORE_DATA:
                error_box("InstanceThread: ERROR MORE DATA")
            else:
                error_box("InstanceThread ReadFile failed")

        return buf

    @staticmethod
    def _pack(s):
        return bytes(json.dumps(s) + '\0', encoding='utf8')

    @staticmethod
    def _unpack(s):
        return json.loads(s.decode().strip("\0 "))

    def _send(self, buf):
        sz = len(buf)
        if sz > self.outBufSize:
            error_box("Buffer overflow {} > {}".format(sz, self.outBufSize))
        # todo: check sending if needed
        _, _ = win32file.WriteFile(self.hPipe, buf, None)

    def set_start_info(self, inf):
        if not isinstance(inf, EStartInfo):
            raise TypeError('object must be EStartInfo, not {!r}'.format(
                inf.__class__.__name__))
        self.state.mode = inf.mode.value
        self.state.count = inf.count
        self.state.incount = inf.incount
        self.state.outcount = inf.outcount
        buf = {"version": PIPES_VER, "type": PacketType.e_start_info.value}
        ser = {"mode": inf.mode.value, "count": inf.count,
               "incount": inf.incount, "outcount": inf.outcount}
        buf["e_start_info"] = ser
        self._send(self._pack(buf))
        return buf

    def get_start_info(self):
        doc = self._unpack(self._receive())
        if doc["type"] != PacketType.n_start_info.value:
            raise RuntimeError("Unknown packet type")
        ser = doc["n_start_info"]
        nsi = NStartInfo()
        nsi.count = ser["count"]
        # todo: check constraints
        self.state.count = nsi.count
        self.lrinfo = VerificationHeader.ok
        return nsi

    def get(self):
        doc = self._unpack(self._receive())
        if doc["type"] != PacketType.n_send_info.value:
            raise RuntimeError("Unknown packet type")
        dnsi = doc["n_send_info"]
        nsi = NSendInfo()

        nsi.head = self.lasthead = VerificationHeader(dnsi["head"])
        if nsi.head != VerificationHeader.ok:
            if nsi.head == VerificationHeader.restart:
                self.lrinfo.count = self.state.count = dnsi["count"]
            return nsi

        nsi.data = dnsi["data"]
        return nsi

    def set(self, inf):
        if not isinstance(inf, ESendInfo):
            raise TypeError('object must be ESendInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.e_send_info.value, "e_send_info": {"head": inf.head.value}}

        if inf.head == VerificationHeader.ok:
            buf["e_send_info"]["data"] = inf.data

        self._send(self._pack(buf))
        return buf

    def restart(self, inf):
        if not isinstance(inf, ERestartInfo):
            raise TypeError('object must be ERestartInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.e_send_info.value, "e_send_info": {"head": VerificationHeader.restart.value}}
        buf["e_send_info"]["score"] = inf.result
        self._send(self._pack(buf))
        return buf

    def stop(self):
        buf = {"version": PIPES_VER, "type": PacketType.e_send_info.value}
        ser = {"head": VerificationHeader.stop.value}
        buf["e_send_info"] = ser
        self._send(self._pack(buf))
        return buf

    @property
    def is_ok(self):
        return self.lasthead

    @property
    def is_connected(self):
        return self._is_connected

    @property
    def get_restart_info(self):
        return self.lrinfo

    def disconnect(self):
        win32file.CloseHandle(self.hPipe)
        self.hPipe = 0
        self._is_connected = False
