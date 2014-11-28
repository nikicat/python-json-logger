"""
This library is provided to allow standard python logging
to output log data as JSON formatted strings
"""
import logging
import json
import datetime
import inspect
import traceback

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
RESERVED_ATTRS = (
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module',
    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
    'processName', 'relativeCreated', 'thread', 'threadName')

RESERVED_ATTR_HASH = dict(zip(RESERVED_ATTRS, RESERVED_ATTRS))


class JsonFormatter(logging.Formatter):
    """
    A custom formatter to format logging records as json strings.
    extra values will be formatted as str() if nor supported by
    json default encoder
    """

    def __init__(self, fmt=None, *args, **kwargs):
        """
        :param json_default: a function for encoding non-standard objects
            as outlined in http://docs.python.org/2/library/json.html
        :param json_encoder: optional custom encoder
        """
        self.json_default = kwargs.pop("json_default", None)
        self.json_encoder = kwargs.pop("json_encoder", None)
        self.json_depth = kwargs.pop("json_depth", 3)
        super(JsonFormatter, self).__init__(fmt, *args, **kwargs)

    def format(self, record):
        """Format a log record and serializes to json"""

        def convert(value, depth):
            """Covert nested dict to dict with limited depth ready for json serialization."""
            if isinstance(value, (str, int, float, bool, type(None))):
                return value
            if isinstance(value, datetime.datetime):
                return '{:%FT%TZ}'.format(datetime.datetime.utcfromtimestamp(value.timestamp()))
            if inspect.istraceback(value):
                return '\n\n'.join(traceback.format_tb(value))
            if isinstance(value, type):
                return '{}.{}'.format(value.__module__, value.__name__)
            if isinstance(value, (dict, list, set, tuple)):
                if depth > 0:
                    if isinstance(value, dict):
                        return {key: convert(subvalue, depth-1) for key, subvalue in value.items()}
                    else:
                        return [convert(subvalue, depth-1) for subvalue in value]
                else:
                    return json.dumps(value)
            else:
                return repr(value)

        # add extras
        log_record = convert(vars(record), self.json_depth)

        # dump
        return json.dumps(log_record,
                          default=self.json_default,
                          cls=self.json_encoder)
