from enum import Enum

__author__ = 'apostol3'


class VerificationHeader(Enum):
    ok = 0
    restart = 1
    stop = 2
    fail = 3


class SendModes(Enum):
    specified = 0
    undefined = 1


class EStartInfo:
    def __init__(self):
        self.mode = SendModes.specified
        self.count = -1
        self.incount = -1
        self.outcount = -1


class NStartInfo:
    def __init__(self):
        self.count = -1
        self.round_seed = 0


class NSendInfo:
    def __init__(self):
        self.head = VerificationHeader.fail
        self.data = []


class ESendInfo:
    def __init__(self):
        self.head = VerificationHeader.fail
        self.data = []


class NRestartInfo:
    def __init__(self):
        self.count = -1
        self.round_seed = 0


class ERestartInfo:
    def __init__(self):
        self.result = [-1]


class EnvState:
    def __init__(self):
        self.mode = SendModes.specified
        self.count = -1
        self.incount = -1
        self.outcount = -1
        self.round_seed = 0


class PacketType(Enum):
    none = 0
    e_start_info = 1
    n_start_info = 2
    n_send_info = 3
    e_send_info = 4
    n_restart_info = 5
    e_restart_info = 6
