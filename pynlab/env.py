import json
from urllib.parse import urlparse


from pynlab.types import *

__author__ = 'apostol3'

PIPES_VER = 0x00000100


class Env:
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
        self.stream.create()

    def wait(self):
        self.stream.wait()

    def get_start_info(self):
        doc = self.__unpack(self.stream.receive())

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
        self.stream.send(self.__pack(buf))

    def get(self):
        doc = self.__unpack(self.stream.receive())
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
        self.stream.send(self.__pack(buf))

    def restart(self, inf):
        if not isinstance(inf, NRestartInfo):
            raise TypeError('object must be NRestartInfo, not {!r}'.format(
                inf.__class__.__name__))
        buf = {"type": PacketType.n_send_info.value, "n_send_info": {"head": VerificationHeader.restart.value}}
        buf["n_send_info"]["count"] = inf.count
        self.stream.send(self.__pack(buf))

    def stop(self):
        buf = {"type": PacketType.n_send_info.value}
        ser = {"head": VerificationHeader.stop.value}
        buf["n_send_info"] = ser
        self.stream.send(self.__pack(buf))

    def terminate(self):
        self.stream.close()
