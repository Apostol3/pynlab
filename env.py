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


class ERestartInfo:
    def __init__(self):
        self.result = [-1]


class EnvState:
    def __init__(self):
        self.mode = SendModes.specified
        self.count = -1
        self.incount = -1
        self.outcount = -1