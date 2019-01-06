#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';
import gzip
import io
import json
import logging
import optparse
import os
import re
from collections import namedtuple
from datetime import datetime
from operator import attrgetter
from os import walk
from statistics import median
from string import Template

LogParams = namedtuple('LogParams', 'path date ext')
ReportParams = namedtuple('ReportParams', 'url count count_perc time_sum time_perc time_avg time_max time_med')
StatisticParams = namedtuple('StatisticParams', 'count time_sum time_max')

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "SELF_LOG_DIR": None,
    "REPORT_TEMPLATE_DIR": "./resources",
    "LOG_REGEXP": '(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+'
                  '(?P<remote_user>\-|.*)\s+(?P<http_x_real_ip>\-|.*)\s+'
                  '\[(?P<time_local>\d{2}\/[a-zA-Z]{3}\/\d{4}:\d{2}:\d{2}:\d{2}\s+'
                  '(?P<offset_tz>(?P<offset_dir>\+|\-)(?P<offset_hour>\d{2})(?P<offset_min>\d{2})))\]\s+'
                  '(?P<request>\"(?P<method>GET|POST|UPDATE|DELETE)\s+(?P<url>.+)\s+'
                  '(?P<http_version>HTTP\/1\.[0-1])\")\s+(?P<status>\d{3})\s+(?P<body_bytes_sent>\d+)\s+'
                  '\"(?P<http_referer>.+)\"\s+\"(?P<http_user_agent>.+)\"\s+\"(?P<http_x_forwarded_for>\-|.*)\"\s+'
                  '\"(?P<http_X_REQUEST_ID>.+)\"\s+\"(?P<http_X_RB_USER>\-|.*)\"\s+(?P<request_time>.+)',
    "ALLOWED_ERRORS_PERCENT": 15,
    "ALLOWED_EXTENSIONS": ['', '.gz'],
    "LOG_ENCODING": 'utf-8',
    "LOGGING_LEVEL": 'DEBUG'
}

logging.basicConfig(
    level=logging.getLevelName(config['LOGGING_LEVEL']),
    filename=None if not config['SELF_LOG_DIR'] else os.path.join(config['SELF_LOG_DIR'], 'log_analyzer.log-' + str(datetime.now().date())),
    format='[%(asctime)s] %(levelname).1s %(message)s',
    datefmt='%Y.%m.%d %H:%M:%S',
)


def get_named_tuple_with_newest_date(actual_config, first, second):
    if second.ext not in actual_config['ALLOWED_EXTENSIONS']:
        return first
    return second if not first or first.date < second.date else first


def find_last_log_params(actual_config):
    last_log_params = None
    for (dirpath, dirnames, filenames) in walk(actual_config['LOG_DIR']):
        for f in filenames:
            match = re.match('(nginx-access-ui.log-)(\d{8})(.*)', f)
            if match:
                params = LogParams(path=f, date=match.groups()[1], ext=match.groups()[2])
                last_log_params = get_named_tuple_with_newest_date(actual_config, last_log_params, params)
    return last_log_params


def already_parsed(actual_config, log_params):
    date = log_params.date
    for (dirpath, dirnames, filenames) in walk(actual_config['REPORT_DIR']):
        for f in filenames:
            match = re.match('^report-' + date[:4] + '.' + date[4:6] + '.' + date[6:], f)
            if match:
                return True
    return False


def merge_configs(user_config_path):
    try:
        user_config = parse_user_config(user_config_path)
    except FileNotFoundError:
        raise RuntimeError("Не найден файл конфигурации по переданному пути %s" % user_config_path)
    return {**config, **user_config}


def parse_user_config(user_config_path):
    user_config = {}
    with open(user_config_path, 'r', encoding='UTF-8') as config_file:
        for line in config_file:
            line = line.rstrip()

            if '=' not in line:
                continue
            if line.startswith('#'):
                continue

            k, v = line.split('=', 1)
            user_config[k.upper()] = int(v) if v.isdigit() else v
    return user_config


def get_actual_config():
    parser = optparse.OptionParser('usage: %prog --config <config_path>')
    parser.add_option('--config', dest='path', type='string', help='specify config file path')
    (options, args) = parser.parse_args()
    if options.path is None:
        logging.info('Путь к конфигурационному файлу не передан, используются стандартные настройки')
        return config
    else:
        path = options.path
        logging.info('Передан путь к конфигурационному файлу, переопределяем стандартные настройки')
        return merge_configs(path)


def parse_line(actual_config, line):
    data = re.search(actual_config['LOG_REGEXP'], line)
    if data:
        datadict = data.groupdict()
        LineParams = namedtuple('LineParams', ' '.join(datadict.keys()))
        return LineParams(**datadict)


def parse_log(actual_config, log_params):
    log_path = os.path.join(actual_config['LOG_DIR'], log_params.path)
    log = gzip.open(filename=log_path, mode='rt', encoding=actual_config['LOG_ENCODING'], errors='replace') \
        if log_params.ext == ".gz" \
        else io.open(log_path, mode='r', encoding=actual_config['LOG_ENCODING'], errors='replace')
    total = processed = 0
    with log:
        for line in log:
            parsed_line = parse_line(actual_config, line)
            total += 1
            if parsed_line:
                processed += 1
                yield parsed_line
    logging.info("Всего обработано %d строк из %d." % (processed, total))
    if total and processed * 100 / total < 100 - actual_config['ALLOWED_ERRORS_PERCENT']:
        raise RuntimeError('Превышен процент допустимых ошибок при разборе лога')


def calculate_statistics(parsed_data_gen):
    statistics = {}
    total_count = 0
    total_time = 0.0
    times = {}
    for data in parsed_data_gen:
        total_count += 1
        data_time = float(data.request_time)
        total_time += data_time
        try:
            current = statistics[data.url]
        except KeyError:
            current = None
        if not current:
            params = StatisticParams(1, data_time, data_time)
            times[data.url] = [data_time]
        else:
            times[data.url].append(data_time)
            params = StatisticParams(
                current.count + 1,
                current.time_sum + data_time,
                current.time_max if current.time_max - data_time > 0 else data_time)
        statistics[data.url] = ReportParams(
            data.url,
            params.count,
            params.count * 100.0 / total_count,
            params.time_sum,
            params.time_sum * 100.0 / total_time,
            params.time_sum / params.count,
            params.time_max,
            median(times[data.url])
        )
        logging.debug('Обработано ' + str(total_count) + ' строк.')
    return statistics.values()


def prepare_json(actual_config, data):
    res = []
    logging.info('Сортируем отчёт по количеству обращений.')
    for params in sorted(data, key=attrgetter('time_sum'), reverse=True)[:actual_config['REPORT_SIZE']]:
        res.append(params._asdict())
    logging.info('Передаём json с данными для дальнейшей обработки.')
    return json.dumps(res)


def generate_report(actual_config, report_data):
    with open(os.path.join(actual_config['REPORT_TEMPLATE_DIR'], 'report.html'), 'r', encoding='UTF-8') as f:
        html = f.read()
    return Template(html).safe_substitute(table_json=report_data)


def create_report(actual_config, parsed_data_gen, log_params):
    logging.info('Считаем статистику по страницам.')
    report_data = calculate_statistics(parsed_data_gen)
    logging.info('Генерируем html с отчётом.')
    report = generate_report(actual_config, prepare_json(actual_config, report_data))
    date = log_params.date
    logging.info('Сохраняем отчёт в файл.')
    with open(
            os.path.join(
                actual_config['REPORT_DIR'],
                'report-' + date[:4] + '.' + date[4:6] + '.' + date[6:] + '.html'
            ), 'w', encoding='UTF-8'
    ) as f:
        f.write(report)


def update_logger_config(actual_config):
    if actual_config['SELF_LOG_DIR'] != config['SELF_LOG_DIR']:
        new_handler = None if not actual_config['SELF_LOG_DIR']\
            else logging.FileHandler(
            os.path.join(actual_config['SELF_LOG_DIR'], 'log_analyzer_log-' + str(datetime.now().date())),
            'a')
        formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
        new_handler.setFormatter(formatter)
        new_handler.setLevel(logging.getLevelName(actual_config['LOGGING_LEVEL']))

        log = logging.getLogger()
        for handler in log.handlers[:]:
            log.removeHandler(handler)
        log.addHandler(new_handler)


def main():
    logging.info('Скрипт запущен. Получаем актуальные настройки.')
    actual_config = get_actual_config()
    update_logger_config(actual_config)

    logging.info('Ищем свежий файл с логами.')
    log_params = find_last_log_params(actual_config)
    if not log_params:
        logging.info('Свежий файл с логами не найден. Заканчиваем выполнение скрипта.')
        return

    logging.info('Проверяем, есть ли уже отчёт по найденному логу.')
    if already_parsed(actual_config, log_params):
        logging.info("Отчёт для последнего лога уже был составлен. Заканчиваем выполнение скрипта.")
        return

    logging.info('Разбираем файл с логами.')
    parsed_data_gen = parse_log(actual_config, log_params)

    logging.info('Создаём файл с отчётом.')
    create_report(actual_config, parsed_data_gen, log_params)


if __name__ == "__main__":
    main()
