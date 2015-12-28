import json

import pynlab.pipe_stream
from pynlab.types import *

__author__ = 'apostol3'

PIPES_VER = 0x00000100


class NLab:
    def __init__(self, pipe_name="\\\\.\\pipe\\nlab"):
        self.pipe = pynlab.pipe_stream.PipeStream(pipe_name, 307200, 307200)
        self.lasthead = VerificationHeader.fail
        self.state = EnvState()
        self.lrinfo = NRestartInfo()

    @property
    def is_ok(self):
        return self.lasthead

    @property
    def get_restart_info(self):
        return self.lrinfo

    @property
    def get_state(self):
        return self.state

    @staticmethod
    def __pack(s):
        return bytes(json.dumps(s) + '\0', encoding='utf8')

    @staticmethod
    def __unpack(s):
        return json.loads(s.decode().strip("\0 "))

    def connect(self):
        self.pipe.connect()

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
        self.pipe.send(self.__pack(buf))

    def get_start_info(self):
        doc = self.__unpack(self.pipe.receive())
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
        doc = self.__unpack(self.pipe.receive())
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

        self.pipe.send(self.__pack(buf))
        return buf

    def restart(self, inf):
        if not isinstance(inf, ERestartInfo):
            raise TypeError('object must be ERestartInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.e_send_info.value, "e_send_info": {"head": VerificationHeader.restart.value}}
        buf["e_send_info"]["score"] = inf.result
        self.pipe.send(self.__pack(buf))
        return buf

    def stop(self):
        buf = {"version": PIPES_VER, "type": PacketType.e_send_info.value}
        ser = {"head": VerificationHeader.stop.value}
        buf["e_send_info"] = ser
        self.pipe.send(self.__pack(buf))
        return buf

    def disconnect(self):
        self.pipe.disconnect()
