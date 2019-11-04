import datetime
import hashlib
import logging
import os
import time
import unittest
from unittest.mock import patch, call, MagicMock, Mock

import redis
from pymemcache.client import base

import hw_04.api_testing.src.api as api
from hw_04.api_testing.src.store import CachedStore
from hw_04.api_testing.test.utils import cases

REAL_STORE_CONFIG = {
            "store_host": os.environ.get('store_host'),
            "store_port": os.environ.get('store_port') or 6379,
            "store_db": os.environ.get('store_db') or 1,
            "cache_host": os.environ.get('cache_host'),
            "cache_port": os.environ.get('cache_port') or 11211,
}

FAKE_STORE_CONFIG = {
            "store_host": '123.4.5.6',
            "store_port": 6379,
            "store_db": 1,
            "store_timeout": 2,
            "store_connection_timeout": 2,
            "cache_host": '123.45.6.7',
            "cache_port": 11211,
            "cache_timeout": 2,
            "cache_connection_timeout": 2,
}

LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "[%(asctime)s] %(levelname).1s %(message)s",
    "datefmt": "%Y.%m.%d %H:%M:%S",
}

logging.basicConfig(**LOGGING_CONFIG)


@unittest.skipUnless(os.environ.get('store_host') and os.environ.get('cache_host'),
                     "System variables 'store_host' and 'cache_host' hadn't determined.")
class TestWithRealStoreServer(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = CachedStore(REAL_STORE_CONFIG, LOGGING_CONFIG)

    def tearDown(self):
        self.store._store.flushall()
        self.store._cache.flush_all()

    @cases([('a', '0'), ('b', 'True'), ('c', 'test'), ('d', '["football", "computer games"]')])
    def test_store_set_get_value(self, key, value):
        self.store.set(key, value)
        self.assertEqual(value, self.store.get(key))

    @cases(['a', 'b', 'c', 'd'])
    def test_store_not_set_get_value(self, key):
        self.assertEqual(None, self.store.get(key))

    @cases([('a', '0')])
    def test_store_expire(self, key, value):
        self.store.set(key, value, 2)
        self.assertEqual(value, self.store.get(key))
        time.sleep(2)
        self.assertIsNone(self.store.get(key))

    @cases([('a', b'0'), ('b', b'True'), ('c', b'test'), ('d', b'["football", "computer games"]')])
    def test_cache_set_get_value(self, key, value):
        self.store.cache_set(key, value)
        self.assertEqual(value, self.store.cache_get(key))

    @cases(['a', 'b', 'c', 'd'])
    def test_cache_not_set_get_value(self, key):
        self.assertEqual(None, self.store.cache_get(key))

    @cases([('a', b'0')])
    def test_cache_expire(self, key, value):
        self.store.cache_set(key, value, 2)
        self.assertEqual(value, self.store.cache_get(key))
        time.sleep(2)
        self.assertIsNone(self.store.cache_get(key))


class TestReconnection(unittest.TestCase):
    def setUp(self):
        self.store = CachedStore(FAKE_STORE_CONFIG, LOGGING_CONFIG)

    @cases(['a'])
    def test_reconnection_store_get_value(self, key):
        with self.assertRaises(redis.exceptions.TimeoutError) as e:
            self.store.get(key)
        # TODO Не очень красиво, подумать как лучше вытащить количество реконнектов
        self.assertEqual(e.exception.count_calls, 2)

    @cases([('a', '1')])
    def test_reconnection_store_set_value(self, key, value):
        with self.assertRaises(redis.exceptions.TimeoutError) as e:
            self.store.set(key, value)
        self.assertEqual(e.exception.count_calls, 3)


if __name__ == "__main__":
    unittest.main()
