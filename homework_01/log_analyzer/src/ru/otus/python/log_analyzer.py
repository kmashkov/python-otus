#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

import optparse
from collections import namedtuple

from os import walk

import re

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "ALLOWED_ERRORS_PERCENT": 15
}


def is_last(f):
    pass


def get_named_tuple_with_newest_date(first, second):
    return first if first.date > second.date else second


def find_last_log_path(config):
    # Находим по регулярке последний лог
    last_log_path = None
    for (dirpath, dirnames, filenames) in walk(config['LOG_DIR']):
        for f in filenames:
            match = re.match("(nginx-access-ui.log-)(\d{8})(.*)", f)
            if match:
                LogParams = namedtuple("LogParams", "path date ext")
                params = LogParams(path=f, date=match.groups()[1], ext=match.groups()[2])
                last_log_path = params if not last_log_path else get_named_tuple_with_newest_date(last_log_path, params)
    return last_log_path


def already_parsed(log_path):
    # Проверяем в папке отчётов, есть ли уже отчёт для данного лога
    pass


def merge_configs(user_config_path):
    try:
        user_config = parse_user_config(user_config_path)
    except FileNotFoundError:
        return config
    return {**config, **user_config}


def parse_user_config(user_config_path):
    user_config = {}
    with open(user_config_path, 'r', encoding='UTF-8') as config_file:
        for line in config_file:
            line = line.rstrip()

            if "=" not in line:
                continue
            if line.startswith("#"):
                continue

            k, v = line.split("=", 1)
            user_config[k.upper()] = int(v) if v.isdigit() else v
    return user_config


def get_actual_config():
    parser = optparse.OptionParser('usage: %prog --config <config_path>')
    parser.add_option('--config', dest='path', type='string', help='specify config file path')
    (options, args) = parser.parse_args()
    if options.path is None:
        return config
    else:
        path = options.path
        return merge_configs(path)


def parse_log(log_path):
    # Парсим лог и возвращаем список кортежей строк с обращениями к страницам
    pass


def create_report(parsed_data):
    # считаем статистику по страницам
    # готовим table_json
    # генерируем html с отчётом
    pass

# TODO Добавить логирование
def main():
    actual_config = get_actual_config()
    log_path = find_last_log_path(actual_config)
    if (already_parsed(log_path)):
        return
    parsed_data = parse_log(log_path)
    if parsed_data.errors_percent > actual_config['ALLOWED_ERRORS_PERCENT']:
        return
    create_report(parsed_data)


if __name__ == "__main__":
    main()
