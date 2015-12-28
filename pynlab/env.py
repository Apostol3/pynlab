import json

import pynlab.pipe_stream
from pynlab.types import *

__author__ = 'apostol3'

PIPES_VER = 0x00000100


class Env:
    def __init__(self, pipe_name="\\\\.\\pipe\\nlab"):
        self.pipe = pynlab.pipe_stream.PipeStream(pipe_name, 307200, 307200)
        self.lasthead = VerificationHeader.fail
        self.state = EnvState()
        self.lrinfo = ERestartInfo()

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

    def create(self):
        self.pipe.create()

    def wait(self):
        self.pipe.wait()

    def get_start_info(self):
        doc = self.__unpack(self.pipe.receive())

        if doc["type"] != PacketType.e_start_info.value:
            raise RuntimeError("Unknown packet type {}. Expected EStartInfo".format(doc["type"]))

        if doc["version"] != PIPES_VER:
            raise RuntimeError("Different protocol version {}!={}".format(doc["version"], PIPES_VER))

        ser = doc["e_start_info"]
        esi = EStartInfo()
        self.state.mode = esi.mode = SendModes(ser["mode"])
        self.state.count = esi.count = ser["count"]
        self.state.incount = esi.incount = ser["incount"]
        self.state.outcount = esi.outcount = ser["outcount"]
        return esi

    def set_start_info(self, inf):
        if not isinstance(inf, NStartInfo):
            raise TypeError('object must be NStartInfo, not {!r}'.format(
                inf.__class__.__name__))
        # todo: check constraints
        self.state.count = inf.count

        buf = {"type": PacketType.n_start_info.value}
        ser = {"count": inf.count}
        buf["n_start_info"] = ser
        self.pipe.send(self.__pack(buf))

    def get(self):
        doc = self.__unpack(self.pipe.receive())
        if doc["type"] != PacketType.e_send_info.value:
            raise RuntimeError("Unknown packet type {}. Expected ESendInfo".format(doc["type"]))
        desi = doc["e_send_info"]
        esi = ESendInfo()
        self.lasthead = esi.head = VerificationHeader(desi["head"])

        if esi.head != VerificationHeader.ok:
            if esi.head == VerificationHeader.restart:
                self.lrinfo.result = desi["score"]
            return esi

        esi.data = desi["data"]
        return esi

    def set(self, inf):
        if not isinstance(inf, NSendInfo):
            raise TypeError('object must be NSendInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.n_send_info.value, "n_send_info": {"head": inf.head.value}}

        if inf.head == VerificationHeader.ok:
            buf["n_send_info"]["data"] = inf.data
        self.pipe.send(self.__pack(buf))

    def restart(self, inf):
        if not isinstance(inf, NRestartInfo):
            raise TypeError('object must be NRestartInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.n_send_info.value, "n_send_info": {"head": VerificationHeader.restart.value}}
        buf["n_send_info"]["count"] = inf.count
        self.pipe.send(self.__pack(buf))

    def stop(self):
        buf = {"type": PacketType.n_send_info.value}
        ser = {"head": VerificationHeader.stop.value}
        buf["n_send_info"] = ser
        self.pipe.send(self.__pack(buf))

    def terminate(self):
        self.pipe.close()
