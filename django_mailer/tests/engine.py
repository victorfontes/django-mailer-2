from django.test import TestCase
from django_mailer import engine
from django_mailer.lockfile import FileLock
from StringIO import StringIO
import logging
import time


class LockTest(TestCase):
    """
    Tests for Django Mailer trying to send mail when the lock is already in
    place.
    """

    def setUp(self):
        # Create somewhere to store the log debug output. 
        self.output = StringIO()
        # Create a log handler which can capture the log debug output.
        self.handler = logging.StreamHandler(self.output)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')
        self.handler.setFormatter(formatter)
        # Add the log handler.
        logger = logging.getLogger('django_mailer')
        logger.addHandler(self.handler)
        
        # Set the LOCK_WAIT_TIMEOUT to the default value.
        self.original_timeout = engine.LOCK_WAIT_TIMEOUT
        engine.LOCK_WAIT_TIMEOUT = -1

    def tearDown(self):
        # Remove the log handler.
        logger = logging.getLogger('django_mailer')
        logger.removeHandler(self.handler)

        # Revert the LOCK_WAIT_TIMEOUT to it's original value.
        engine.LOCK_WAIT_TIMEOUT = self.original_timeout

    def test_locked(self):
        # Acquire the lock (under a different unique name) so that send_all
        # will fail.
        lock = FileLock(engine.LOCK_PATH)
        lock.unique_name = 'mailer-test'
        lock.acquire()
        try:
            engine.send_all()
            self.output.seek(0)
            self.assertEqual(self.output.readlines()[-1].strip(),
                             'Lock already in place. Exiting.')
            # Try with a timeout.
            engine.LOCK_WAIT_TIMEOUT = .1
            engine.send_all()
            self.output.seek(0)
            self.assertEqual(self.output.readlines()[-1].strip(),
                             'Waiting for the lock timed out. Exiting.')
        finally:
            # Always release the test lock.
            lock.release()

    def test_locked_timeoutbug(self):
        lock = FileLock(engine.LOCK_PATH)
        lock.unique_name = 'mailer-test'
        lock.acquire()
        # We want to emulate the lock acquiring taking no time, so the next
        # three calls to time.time() always return 0 (then set it back to the
        # real function).
        original_time = time.time
        global time_call_count
        time_call_count = 0
        def fake_time():
            global time_call_count
            time_call_count = time_call_count + 1
            if time_call_count >= 3:
                time.time = original_time
            return 0
        time.time = fake_time
        try:
            engine.send_all()
            self.output.seek(0)
            self.assertEqual(self.output.readlines()[-1].strip(),
                             'Lock already in place. Exiting.')
        finally:
            lock.release()
            time.time = original_time
