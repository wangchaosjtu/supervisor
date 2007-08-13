import sys
import unittest

from supervisor.tests.base import DummySupervisor
from supervisor.tests.base import PopulatedDummySupervisor
from supervisor.tests.base import DummyPConfig
from supervisor.tests.base import DummyOptions
from supervisor.tests.base import DummyRequest
from supervisor.tests.base import DummyProcess

from supervisor.http import NOT_DONE_YET

class LogtailHandlerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import logtail_handler
        return logtail_handler

    def _makeOne(self, supervisord):
        return self._getTargetClass()(supervisord)

    def test_handle_request_stdout_logfile_none(self):
        options = DummyOptions()
        pconfig = DummyPConfig(options, 'process1', '/bin/process1', priority=1,
                               stdout_logfile='/tmp/process1.log')
        supervisord = PopulatedDummySupervisor(options, 'process1', pconfig)
        handler = self._makeOne(supervisord)
        request = DummyRequest('/logtail/process1', None, None, None)
        handler.handle_request(request)
        self.assertEqual(request._error, 410)

    def test_handle_request_stdout_logfile_missing(self):
        supervisor = DummySupervisor()
        options = DummyOptions()
        pconfig = DummyPConfig(options, 'foo', 'foo', 'it/is/missing')
        supervisord = PopulatedDummySupervisor(options, 'foo', pconfig)
        handler = self._makeOne(supervisord)
        request = DummyRequest('/logtail/foo', None, None, None)
        handler.handle_request(request)
        self.assertEqual(request._error, 410)

    def test_handle_request(self):
        supervisor = DummySupervisor()
        import tempfile
        import os
        import stat
        f = tempfile.NamedTemporaryFile()
        t = f.name
        options = DummyOptions()
        pconfig = DummyPConfig(options, 'foo', 'foo', stdout_logfile=t)
        supervisord = PopulatedDummySupervisor(options, 'foo', pconfig)
        handler = self._makeOne(supervisord)
        request = DummyRequest('/logtail/foo', None, None, None)
        handler.handle_request(request)
        self.assertEqual(request._error, None)
        from medusa import http_date
        self.assertEqual(request.headers['Last-Modified'],
                         http_date.build_http_date(os.stat(t)[stat.ST_MTIME]))
        self.assertEqual(request.headers['Content-Type'], 'text/plain')
        self.assertEqual(len(request.producers), 1)
        self.assertEqual(request._done, True)


class TailFProducerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import tail_f_producer
        return tail_f_producer

    def _makeOne(self, request, filename, head):
        return self._getTargetClass()(request, filename, head)

    def test_handle_more(self):
        request = DummyRequest('/logtail/foo', None, None, None)
        import tempfile
        from supervisor import http
        f = tempfile.NamedTemporaryFile()
        f.write('a' * 80)
        f.flush()
        t = f.name
        producer = self._makeOne(request, t, 80)
        result = producer.more()
        self.assertEqual(result, 'a' * 80)
        f.write('w' * 100)
        f.flush()
        result = producer.more()
        self.assertEqual(result, 'w' * 100)
        result = producer.more()
        self.assertEqual(result, http.NOT_DONE_YET)
        f.truncate(0)
        f.flush()
        result = producer.more()
        self.assertEqual(result, '==> File truncated <==\n')

class DeferringChunkedProducerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import deferring_chunked_producer
        return deferring_chunked_producer

    def _makeOne(self, producer, footers=None):
        return self._getTargetClass()(producer, footers)

    def test_more_not_done_yet(self):
        wrapped = DummyProducer(NOT_DONE_YET)
        producer = self._makeOne(wrapped)
        self.assertEqual(producer.more(), NOT_DONE_YET)

    def test_more_string(self):
        wrapped = DummyProducer('hello')
        producer = self._makeOne(wrapped)
        self.assertEqual(producer.more(), '5\r\nhello\r\n')

    def test_more_nodata(self):
        wrapped = DummyProducer()
        producer = self._makeOne(wrapped, footers=['a', 'b'])
        self.assertEqual(producer.more(), '0\r\na\r\nb\r\n\r\n')

class DeferringCompositeProducerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import deferring_composite_producer
        return deferring_composite_producer

    def _makeOne(self, producers):
        return self._getTargetClass()(producers)

    def test_more_not_done_yet(self):
        wrapped = DummyProducer(NOT_DONE_YET)
        producer = self._makeOne([wrapped])
        self.assertEqual(producer.more(), NOT_DONE_YET)

    def test_more_string(self):
        wrapped1 = DummyProducer('hello')
        wrapped2 = DummyProducer('goodbye')
        producer = self._makeOne([wrapped1, wrapped2])
        self.assertEqual(producer.more(), 'hello')
        self.assertEqual(producer.more(), 'goodbye')
        self.assertEqual(producer.more(), '')

    def test_more_nodata(self):
        wrapped = DummyProducer()
        producer = self._makeOne([wrapped])
        self.assertEqual(producer.more(), '')

class DeferringGlobbingProducerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import deferring_globbing_producer
        return deferring_globbing_producer

    def _makeOne(self, producer, buffer_size=1<<16):
        return self._getTargetClass()(producer, buffer_size)

    def test_more_not_done_yet(self):
        wrapped = DummyProducer(NOT_DONE_YET)
        producer = self._makeOne(wrapped)
        self.assertEqual(producer.more(), NOT_DONE_YET)

    def test_more_string(self):
        wrapped = DummyProducer('hello', 'there', 'guy')
        producer = self._makeOne(wrapped, buffer_size=1)
        self.assertEqual(producer.more(), 'hello')

        wrapped = DummyProducer('hello', 'there', 'guy')
        producer = self._makeOne(wrapped, buffer_size=50)
        self.assertEqual(producer.more(), 'hellothereguy')

    def test_more_nodata(self):
        wrapped = DummyProducer()
        producer = self._makeOne(wrapped)
        self.assertEqual(producer.more(), '')

class DeferringHookedProducerTests(unittest.TestCase):
    def _getTargetClass(self):
        from supervisor.http import deferring_hooked_producer
        return deferring_hooked_producer

    def _makeOne(self, producer, function):
        return self._getTargetClass()(producer, function)

    def test_more_not_done_yet(self):
        wrapped = DummyProducer(NOT_DONE_YET)
        producer = self._makeOne(wrapped, None)
        self.assertEqual(producer.more(), NOT_DONE_YET)

    def test_more_string(self):
        wrapped = DummyProducer('hello')
        L = []
        def callback(bytes):
            L.append(bytes)
        producer = self._makeOne(wrapped, callback)
        self.assertEqual(producer.more(), 'hello')
        self.assertEqual(L, [])
        producer.more()
        self.assertEqual(L, [5])

    def test_more_nodata(self):
        wrapped = DummyProducer()
        L = []
        def callback(bytes):
            L.append(bytes)
        producer = self._makeOne(wrapped, callback)
        self.assertEqual(producer.more(), '')
        self.assertEqual(L, [0])

class DummyProducer:
    def __init__(self, *data):
        self.data = list(data)

    def more(self):
        if self.data:
            return self.data.pop(0)
        else:
            return ''

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')