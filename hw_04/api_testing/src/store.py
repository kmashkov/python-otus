#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import time

from pymemcache.client import base
import redis


def with_reconnection(tries=5, delay_shift=0.3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            count = 1
            delay = 0.0
            while True:
                time.sleep(delay)
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if count < tries:
                        delay += delay_shift
                        count += 1
                    else:
                        raise e
        return wrapper
    return decorator


class CachedStore(object):

    def __init__(self, store_config, logging_config):
        self._cache = base.Client((store_config.get('cache_host'), store_config.get('cache_port')), timeout=15,
                                  connect_timeout=45)
        self._store = redis.StrictRedis(host=store_config.get('store_host'), port=store_config.get('store_port'),
                                        db=store_config.get('store_db'), decode_responses=True,
                                        socket_timeout=15, socket_connect_timeout=45)
        logging.basicConfig(filename=logging_config.get("filename"), level=logging_config.get("level"),
                            format=logging_config.get("format"), datefmt=logging_config.get("datefmt"))

    @with_reconnection(3, 0.1)
    def set(self, key, value):
        return self._store.set(key, value)

    @with_reconnection(2)
    def get(self, key):
        return self._store.get(key)

    def cache_set(self, key, value, expire=0):
        try:
            self._cache.set(key, value, expire)
        except Exception as e:
            logging.error("Couldn't set cache value.")
            logging.error(e)

    def cache_get(self, key):
        try:
            result = self._cache.get(key)
            if result is None:
                result = self.get(key)
                self.cache_set(key, result)
            return result
        except Exception as e:
            logging.error("Couldn't get cache value.")
            logging.error(e)
        return None
