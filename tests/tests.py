import inspect
import unittest
import logging
import json
import sys

try:
    import xmlrunner
except ImportError:
    pass

try:
    from StringIO import StringIO
except ImportError:
    # Python 3 Support
    from io import StringIO

sys.path.append('src')
import jsonformatter as jsonlogger
import datetime


def lineno():
    """Return the current line number in our program"""
    return inspect.currentframe().f_back.f_lineno


class TestJsonLogger(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('logging-test')
        self.logger.setLevel(logging.DEBUG)
        self.buffer = StringIO()

        self.logHandler = logging.StreamHandler(self.buffer)
        self.logger.addHandler(self.logHandler)

    def testLogException(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)
        raise_line_no = None
        # noinspection PyBroadException
        try:
            raise_line_no = lineno() + 1
            raise Exception('Some exception message')
        except Exception:
            self.logger.exception('Some log message')
        log_json = json.loads(self.buffer.getvalue())
        self.assertEqual(log_json['msg'], 'Some log message')
        self.assertEqual(len(log_json['exc_info']), 3)
        self.assertEqual(log_json['exc_info'][0], 'builtins.Exception')
        self.assertEqual(log_json['exc_info'][1], "Exception('Some exception message',)")
        trace = log_json['exc_info'][2]
        self.assertTrue('testLogException' in trace)
        self.assertTrue(str(raise_line_no) in trace)
        self.assertTrue('tests.py' in trace)

    def testDefaultFormat(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = "testing logging format"
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())

        self.assertEqual(logJson["msg"], msg)

    def testFormatKeys(self):
        supported_keys = [
            'created',
            'filename',
            'funcName',
            'levelname',
            'levelno',
            'lineno',
            'module',
            'msecs',
            'msg',
            'name',
            'pathname',
            'process',
            'processName',
            'relativeCreated',
            'thread',
            'threadName'
        ]

        log_format = lambda x: ['%({0:s})'.format(i) for i in x]
        custom_format = ' '.join(log_format(supported_keys))

        fr = jsonlogger.JsonFormatter(custom_format)
        self.logHandler.setFormatter(fr)

        msg = "testing logging format"
        self.logger.info(msg)
        log_msg = self.buffer.getvalue()
        log_json = json.loads(log_msg)

        for supported_key in supported_keys:
            self.assertIn(supported_key, log_json)

    def testUnknownFormatKey(self):
        fr = jsonlogger.JsonFormatter()

        self.logHandler.setFormatter(fr)
        msg = "testing unknown logging format"
        try:
            self.logger.info(msg)
        except:
            self.assertTrue(False, "Should succeed")

    def testFormatParsingWithParentheses(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)
        self.logger.info('some message')
        log_msg = self.buffer.getvalue()
        log_json = json.loads(log_msg)
        for key in ['name', 'msg']:
            self.assertIn(key, log_json)

    def testDefaultFormatKeys(self):
        supported_keys = [
            'created',
            'filename',
            'funcName',
            'levelname',
            'levelno',
            'lineno',
            'module',
            'msecs',
            'msg',
            'name',
            'pathname',
            'process',
            'processName',
            'relativeCreated',
            'thread',
            'threadName'
        ]

        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = "testing logging format"
        self.logger.info(msg)
        log_msg = self.buffer.getvalue()
        log_json = json.loads(log_msg)

        for supported_key in supported_keys:
            self.assertIn(supported_key, log_json)

    def testLogADict(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = {"text": "testing logging", "num": 1, 5: "9",
               "nested": {"more": "data"}}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("msg"), json.loads(json.dumps(msg)))

    def testLogExtra(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        extra = {"text": "testing logging", "num": 1, 5: "9",
                 "nested": {"more": "data"}}
        self.logger.info("hello", extra=extra)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson.get("text"), extra["text"])
        self.assertEqual(logJson.get("num"), extra["num"])
        self.assertEqual(logJson.get("5"), extra[5])
        self.assertEqual(logJson.get("nested"), extra["nested"])
        self.assertEqual(logJson["msg"], "hello")

    def testJsonDefaultEncoder(self):
        fr = jsonlogger.JsonFormatter()
        self.logHandler.setFormatter(fr)

        msg = {"adate": datetime.datetime(1999, 12, 31, 23, 59)}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson['msg'].get("adate"), "1999-12-31T20:59:00Z")

    def testJsonCustomDefault(self):
        def custom(o):
            return "very custom"
        fr = jsonlogger.JsonFormatter(json_default=custom)
        self.logHandler.setFormatter(fr)

        msg = {"adate": datetime.datetime(1999, 12, 31, 23, 59), "normal": "value"}
        self.logger.info(msg)
        logJson = json.loads(self.buffer.getvalue())
        self.assertEqual(logJson['msg'].get("adate"), "1999-12-31T20:59:00Z")
        self.assertEqual(logJson['msg'].get("normal"), "value")

if __name__ == '__main__':
    if len(sys.argv[1:]) > 0:
        if sys.argv[1] == 'xml':
            testSuite = unittest.TestLoader().loadTestsFromTestCase(TestJsonLogger)
            xmlrunner.XMLTestRunner(output='reports').run(testSuite)
    else:
        unittest.main()
