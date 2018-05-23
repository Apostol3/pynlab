__author__ = 'apostol3'

try:
    import ujson as json
except ImportError:
    json = None

if not json:
    try:
        import rapidjson as json
    except ImportError:
        json = None

if not json:
    import json as json
