from time import sleep
from threading import Thread
from unittest import TestCase

from chalicelib.concurrentutils import CountDownLatch, ThreadSafeList


class TestCountDownLatch(TestCase):
    def setUp(self):
        self._value = 'origin'

    def task_wait(self, latch):
        latch.wait()
        self._value = 'changed'

    def task(self, latch_start, latch_wait_complete, i, numberList):
        latch_start.wait()
        numberList.append(i)
        latch_wait_complete.count_down()

    def test_countdown_one_thread(self):
        latch = CountDownLatch(1)
        thread = Thread(target=TestCountDownLatch.task_wait, args=(self, latch))
        thread.start()

        # wait to see if it changed
        sleep(0.5)
        self.assertEqual('origin', self._value)
        # start to change
        latch.count_down()
        thread.join()
        # verify the changed value
        self.assertEqual('changed', self._value)

    def test_countdown_with_5_threads(self):
        number_list = ThreadSafeList()
        latch_start = CountDownLatch(1)
        latch_done = CountDownLatch(5)
        for i in range(5):
            thread = Thread(target=TestCountDownLatch.task,
                            args=(self, latch_start, latch_done, i, number_list))
            thread.start()

        # wait to see if list is still empty
        sleep(0.2)
        self.assertEqual(0, number_list.length())

        # start to add
        latch_start.count_down()

        # all added
        latch_done.wait()

        # verify added values
        self.assertEqual(5, number_list.length())
        self.assertIn(0, number_list.list())
        self.assertIn(1, number_list.list())
        self.assertIn(2, number_list.list())
        self.assertIn(3, number_list.list())
        self.assertIn(4, number_list.list())


class TestThreadSafeList(TestCase):
    # add items to the list
    def add_items(safe_list):
        for i in range(100000):
            safe_list.append(i)

    # add extend items to the list
    def extend_items(safe_list, max):
        safe_list.extend(range(max))

    # add extend items to the list
    def add_exception(safe_list):
        safe_list.add_exception('test_operation_name', Exception('Test Exception'))

    def test_add_items(self):
        # create the thread safe list and add items to the list
        safe_list = ThreadSafeList()
        # configure threads to add to the list
        threads = [Thread(target=TestThreadSafeList.add_items, args=(safe_list,)) for i in range(50)]
        # start threads
        for thread in threads:
            thread.start()

        # wait for all threads to terminate
        for thread in threads:
            thread.join()

        # verify numbers
        self.assertEqual(5000000, safe_list.length())

    def test_extend_items(self):
        # create the thread safe list and add items to the list
        safe_list = ThreadSafeList()
        # configure threads to add to the list
        threads = [Thread(target=TestThreadSafeList.extend_items, args=(safe_list, 100000)) for i in range(50)]
        # start threads
        for thread in threads:
            thread.start()

        # wait for all threads to terminate
        for thread in threads:
            thread.join()

        # verify numbers
        self.assertEqual(5000000, safe_list.length())

    def test_extend_exceptions(self):
        # create the thread safe list and add items to the list
        safe_list = ThreadSafeList()
        # configure threads to add to the list
        threads = [Thread(target=TestThreadSafeList.add_exception, args=(safe_list,)) for i in range(50)]
        # start threads
        for thread in threads:
            thread.start()

        # wait for all threads to terminate
        for thread in threads:
            thread.join()

        # verify numbers
        self.assertTrue(safe_list.has_exception())
        self.assertEqual(len(safe_list.exceptions()), 50)

        print(safe_list.exceptions())

        for exception in safe_list.exceptions():
            self.assertEqual(exception[0], 'test_operation_name')
            self.assertEqual(exception[1].args[0], 'Test Exception')
