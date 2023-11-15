import time
from threading import Condition, Lock


class CountDownLatch(object):
    """Simple countdown latch, starts closed then opens once count is reached"""

    # constructor
    def __init__(self, count):
        # store the count
        self.count = count
        # control access to the count and notify when latch is open
        self.condition = Condition()

    # count down the latch by one increment
    def count_down(self):
        # acquire the lock on the condition
        with self.condition:
            # check if the latch is already open
            if self.count == 0:
                return
            # decrement the counter
            self.count -= 1
            # check if the latch is now open
            if self.count == 0:
                # notify all waiting threads that the latch is open
                self.condition.notify_all()

    # wait for the latch to open
    def wait(self):
        # acquire the lock on the condition
        with self.condition:
            # check if the latch is already open
            if self.count == 0:
                return
            # wait to be notified when the latch is open
            self.condition.wait()


class Stopwatch(object):
    def start(self):
        self._start = time.time()
        return self

    def stop(self):
        if self._start is None:
            raise RuntimeError('Should start first')
        return time.time() - self._start


class ThreadSafeList(object):
    """List with lock on append and length"""

    # constructor
    def __init__(self):
        # initialize the list
        self._list = list()
        self._exceptions = list()
        # initialize the lock
        self._lock = Lock()

    # add a value to the list
    def append(self, value):
        # acquire the lock
        with self._lock:
            # append the value
            self._list.append(value)

    # add a value to the list
    def extend(self, values: list):
        # acquire the lock
        with self._lock:
            # append the value
            self._list.extend(values)

    # add a value to the list
    def add_exception(self, operation_name: str, exception):
        # acquire the lock
        with self._lock:
            # append the value
            self._exceptions.append((operation_name, exception))

    # add a value to the list
    def has_exception(self):
        # acquire the lock
        return len(self._exceptions) > 0

    # add a value to the list
    def exceptions(self):
        # acquire the lock
        return self._exceptions

    # return the number of items in the list
    def length(self):
        # acquire the lock
        with self._lock:
            return len(self._list)

    # return the number of items in the list
    def list(self):
        # acquire the lock
        with self._lock:
            return list(self._list)
