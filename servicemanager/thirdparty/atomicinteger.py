#!/usr/bin/env python

"""
   Life's short, Python more.
   bug report to bazhen.csy@taobao.com.
"""

import sys
import threading


class AtomicInteger:

    def __init__(self, integer, minimum=0, maximum=sys.maxint):
        self.counter = integer
        self.min = minimum
        self.max = maximum
        self.lock = threading.RLock()
        return

    def increment_and_get(self):
        self.lock.acquire()

        if self.counter >= self.max:
            self.counter = self.min
        else:
            self.counter += 1

        value = self.counter
        self.lock.release()
        return value

    def decrement_and_get(self):
        self.lock.acquire()

        if self.counter <= self.min:
            self.counter = self.max
        else:
            self.counter -= 1

        value = self.counter
        self.lock.release()
        return value

    def set_value(self, integer):
        self.lock.acquire()
        self.counter = integer
        value = self.counter
        self.lock.release()
        return value

    def get(self):
        return self.counter

if __name__ == r"__main__":
    sys.exit(0)