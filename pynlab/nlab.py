import json
from urllib.parse import urlparse

from pynlab.types import *

__author__ = 'apostol3'

PIPES_VER = 0x00000100


class NLab:
    def __init__(self, connection_uri='tcp://127.0.0.1:5005'):
        self.uri = connection_uri
        url_scheme = urlparse(connection_uri)
        if url_scheme.scheme == 'tcp':
            from pynlab.tcp_stream import TCPStream

            self.stream = TCPStream(ip_address=url_scheme.hostname, tcp_port=url_scheme.port)
        elif url_scheme.scheme == 'winpipe':
            from pynlab.pipe_stream import PipeStream
            self.stream = PipeStream('\\\\{}\\pipe{}'.format(url_scheme.hostname, url_scheme.path.replace('/', '\\')),
                                     307200, 307200)
        else:
            raise RuntimeError('URI protocol must be tcp or winpipe')
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
        self.stream.connect()

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
        self.stream.send(self.__pack(buf))

    def get_start_info(self):
        doc = self.__unpack(self.stream.receive())
        if doc["type"] != PacketType.n_start_info.value:
            raise RuntimeError("Unknown packet type")
        ser = doc["n_start_info"]
        nsi = NStartInfo()
        nsi.count = ser["count"]
        nsi.round_seed = ser.get("round_seed", 0)
        # todo: check constraints
        self.state.count = nsi.count
        self.state.round_seed = nsi.round_seed
        self.lrinfo = VerificationHeader.ok
        return nsi

    def get(self):
        doc = self.__unpack(self.stream.receive())
        if doc["type"] != PacketType.n_send_info.value:
            raise RuntimeError("Unknown packet type")
        dnsi = doc["n_send_info"]
        nsi = NSendInfo()

        nsi.head = self.lasthead = VerificationHeader(dnsi["head"])
        if nsi.head != VerificationHeader.ok:
            if nsi.head == VerificationHeader.restart:
                self.lrinfo.count = self.state.count = dnsi["count"]
                self.lrinfo.round_seed = self.state.round_seed = dnsi.get("round_seed", 0)
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

        self.stream.send(self.__pack(buf))
        return buf

    def restart(self, inf):
        if not isinstance(inf, ERestartInfo):
            raise TypeError('object must be ERestartInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.e_send_info.value, "e_send_info": {"head": VerificationHeader.restart.value}}
        buf["e_send_info"]["score"] = inf.result
        self.stream.send(self.__pack(buf))
        return buf

    def stop(self):
        buf = {"version": PIPES_VER, "type": PacketType.e_send_info.value}
        ser = {"head": VerificationHeader.stop.value}
        buf["e_send_info"] = ser
        self.stream.send(self.__pack(buf))
        return buf

    def disconnect(self):
        self.stream.disconnect()
