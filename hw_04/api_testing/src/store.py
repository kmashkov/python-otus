#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from pymemcache.client import base
import redis


class CachedStore(object):

    def __init__(self, store_config, logging_config):
        self._cache = base.Client((store_config.get('cache_host'), store_config.get('cache_port')), timeout=15,
                                  connect_timeout=45)
        self._store = redis.StrictRedis(host=store_config.get('store_host'), port=store_config.get('store_port'),
                                        db=store_config.get('store_db'),
                                        socket_timeout=15, socket_connect_timeout=45)
        logging.basicConfig(filename=logging_config.get("filename"), level=logging_config.get("level"),
                            format=logging_config.get("format"), datefmt=logging_config.get("datefmt"))

    def set(self, key, value, expire):
        return self._store.set(key, value, expire)

    def get(self, key):
        result = self._store.get(key)
        return result.decode('utf-8') if result else None

    def cache_set(self, key, value, expire=0):
        try:
            self._cache.set(key, value, expire)
        except Exception as e:
            logging.error(e)
            logging.error("Couldn't set cache value. Trying to set store value.")
            return self.set(key, value)

    def cache_get(self, key):
        try:
            result = self._cache.get(key)
            if result is None:
                result = self.get(key)
                self.cache_set(key, result)
            return result.decode('utf-8') if result else None
        except Exception as e:
            logging.error("Couldn't get cache value. Trying to get store value.")
            logging.error(e)
            return self.get(key)
