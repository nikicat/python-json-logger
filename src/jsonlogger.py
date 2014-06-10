"""
This library is provided to allow standard python logging
to output log data as JSON formatted strings
"""
import logging
import json
import re
import datetime

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
RESERVED_ATTRS = (
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'module',
    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
    'processName', 'relativeCreated', 'thread', 'threadName')

RESERVED_ATTR_HASH = dict(zip(RESERVED_ATTRS, RESERVED_ATTRS))


def merge_record_extra(record, target, reserved=RESERVED_ATTR_HASH):
    """
    Merge extra attributes from LogRecord object into target dictionary

    :param record: logging.LogRecord
    :param target: dict to update
    :param reserved: dict or list with reserved keys to skip
    """
    for key, value in record.__dict__.iteritems():
        #this allows to have numeric keys
        if (key not in reserved and
            not (hasattr(key, "startswith") and
                 key.startswith('_'))):
            target[key] = value
    return target


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
        super(JsonFormatter, self).__init__(fmt, *args, **kwargs)
        if not self.json_encoder and not self.json_default:
            def _default_json_handler(obj):
                """Print dates in ISO format"""
                if isinstance(obj, datetime.datetime):
                    return obj.strftime(self.datefmt or '%Y-%m-%dT%H:%M')
                elif isinstance(obj, datetime.date):
                    return obj.strftime('%Y-%m-%d')
                elif isinstance(obj, datetime.time):
                    return obj.strftime('%H:%M')
                return str(obj)
            self.json_default = _default_json_handler

        if fmt:
            # parse format fields to get fields to include in output JSON
            self._required_fields = self.parse()
        else:
            # store all fields by default
            self._required_fields = list(RESERVED_ATTRS)

        self._skip_fields = dict(zip(self._required_fields,
                                     self._required_fields))
        self._skip_fields.update(RESERVED_ATTR_HASH)

    def parse(self):
        """Parse format string looking for substitutions"""
        standard_formatters = re.compile(r'\(([^()]+?)\)', re.IGNORECASE)
        return standard_formatters.findall(self._fmt)

    def format_trace(self, trace):
        """Format and return trace"""
        formatted_trace = []
        while trace is not None:
            frame = trace.tb_frame
            frame_code = frame.f_code
            formatted_trace.append(dict(
                filename=frame_code.co_filename,
                lineno=trace.tb_lineno,
                name=frame_code.co_name,
            ))
            trace = trace.tb_next
        return formatted_trace

    def format(self, record):
        """Format a log record and serializes to json"""
        extras = {}
        if isinstance(record.msg, dict):
            extras = record.msg
            record.message = None
        else:
            record.message = record.getMessage()

        # only format time if needed
        if "asctime" in self._required_fields:
            record.asctime = self.formatTime(record, self.datefmt)

        # copy required fields
        log_record = {}
        for field in self._required_fields:
            log_record[field] = record.__dict__.get(field)

        # add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_trace = record.exc_info
            if not record.exc_text:
                record.exc_text = str(exc_value)
            log_record['excType'] = exc_type.__module__ + '.' + exc_type.__name__
            log_record['excValue'] = str(exc_value)
            log_record['excTrace'] = self.format_trace(exc_trace)

        # add extras
        log_record.update(extras)

        # merge in fields
        merge_record_extra(record, log_record, reserved=self._skip_fields)

        # dump
        return json.dumps(log_record,
                          default=self.json_default,
                          cls=self.json_encoder)
