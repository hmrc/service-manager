#!/usr/bin/env python
# -*- coding:utf-8 -*-
import socket

from servicemanager.thirdparty.atomicinteger import AtomicInteger


class PortProvider:

    def __init__(self):
        self._port_counter = AtomicInteger(10000, 10000, 65535)

    @staticmethod
    def _is_available(port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(("127.0.0.1", int(port)))
            s.shutdown(2)
            return False
        except Exception:
            return True

    def next_available_port(self):
        next_port_value = self._port_counter.increment_and_get()

        while not self._is_available(next_port_value):
            next_port_value = self._port_counter.increment_and_get()

        return next_port_value
