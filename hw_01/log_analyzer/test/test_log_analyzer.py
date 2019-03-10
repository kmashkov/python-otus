import os
import unittest
from collections import namedtuple
from datetime import datetime

import log_analyzer


LogParams = namedtuple('LogParams', 'path date ext')

LAST_LOG_EXTENSION = '.gz'
LAST_LOG_DATE = datetime.strptime('20170530', "%Y%m%d").date()
LAST_LOG_FILENAME = 'nginx-access-ui.log-20170530.gz'
LAST_LOG_REPORT = 'report-2017.05.30.html'
NOT_EMPTY_LOG_REPORT = 'sample-report-2017.08.02.html'
ERROR_LOG_DATE = datetime.strptime('20170801', "%Y%m%d").date()
EMPTY_LOG_DATE = datetime.strptime('20161209', "%Y%m%d").date()
NOT_EMPTY_LOG_DATE = datetime.strptime('20170802', "%Y%m%d").date()
USER_ALLOWED_ERRORS_PERCENT = 25
DEFAULT_ALLOWED_ERRORS_PERCENT = 15
CONFIG_SIZE = 10
ANOTHER_REGEXP = '(?P<method>GET|POST|UPDATE|DELETE)\s+(?P<url>.+)\s+HTTP/1.[0-1].+\s+(?P<request_time>\d+.\d+)$'

test_config = {
    "REPORT_SIZE": 100,
    "REPORT_DIR": "../src/reports",
    "LOG_DIR": "../src/log",
    "SELF_LOG_DIR": None,
    "REPORT_TEMPLATE_DIR": "../src/resources",
    "LOG_REGEXP": '(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(?P<remote_user>\-|.*)\s+(?P<http_x_real_ip>\-|.*)\s+\[(?P<time_local>\d{2}\/[a-zA-Z]{3}\/\d{4}:\d{2}:\d{2}:\d{2}\s+(?P<offset_tz>(?P<offset_dir>\+|\-)(?P<offset_hour>\d{2})(?P<offset_min>\d{2})))\]\s+(?P<request>\"(?P<method>GET|POST|UPDATE|DELETE)\s+(?P<url>.+)\s+(?P<http_version>HTTP\/1\.[0-1])\")\s+(?P<status>\d{3})\s+(?P<body_bytes_sent>\d+)\s+\"(?P<http_referer>.+)\"\s+\"(?P<http_user_agent>.+)\"\s+\"(?P<http_x_forwarded_for>\-|.*)\"\s+\"(?P<http_X_REQUEST_ID>.+)\"\s+\"(?P<http_X_RB_USER>\-|.*)\"\s+(?P<request_time>.+)',
    "ALLOWED_ERRORS_PERCENT": 15,
    "ALLOWED_EXTENSIONS": ['', '.gz', 'zip'],
    "LOG_ENCODING": 'utf-8',
    "LOGGING_LEVEL": 'DEBUG'
}


class LogAnalyzerTest(unittest.TestCase):

    def test_merge_config(self):
        """
        Проверяем правильность объединения конфигов
        """
        # Объединяем с существущим конфигом
        config = log_analyzer.merge_configs('../src/resources/config.properties')
        self.assertIsNotNone(config, 'Empty config returned')
        self.assertEqual(len(config), CONFIG_SIZE, 'Wrong count of settings')
        self.assertEqual(
            config["ALLOWED_ERRORS_PERCENT"],
            USER_ALLOWED_ERRORS_PERCENT,
            'Wrong allowed_errors_percent in merged config'
        )
        self.assertEqual(
            config["LOG_REGEXP"],
            ANOTHER_REGEXP,
            'Wrong allowed_errors_percent in merged config'
        )

        # Объединяем с несуществущим конфигом
        with self.assertRaises(FileNotFoundError, msg='Wrong config path processed without errors'):
            log_analyzer.merge_configs("../src/resources/cfg.properties")

    def test_find_last_log(self):
        """
        Проверяем правильность нахождения последнего лога
        """
        last_log = log_analyzer.find_last_log_params(test_config)
        self.assertIsNotNone(last_log, 'Latest log is not found')
        self.assertIsNotNone(last_log.date, 'Log date has not parsed')
        self.assertIsNotNone(last_log.ext, 'Log extension has not parsed')
        self.assertEqual(last_log.path, LAST_LOG_FILENAME, 'Wrong log chosen as latest')
        self.assertEqual(last_log.date, LAST_LOG_DATE, 'Wrong date parsed')
        self.assertEqual(last_log.ext, LAST_LOG_EXTENSION, 'Wrong extension parsed')

    def test_already_parsed(self):
        """
        Проверяем правильность определения, что отчёт уже сформирован
        """
        # Передаём лог со сформированным отчётом
        report_path = os.path.join(test_config['REPORT_DIR'], 'report-2017.05.30.html')
        with open(report_path, 'a'):
            already_parsed = log_analyzer.already_parsed(
                test_config,
                LogParams(path='nginx-access-ui.log-20170530', date=datetime.strptime('20170530', "%Y%m%d").date(), ext='')
            )
            self.assertTrue(already_parsed, 'Could not determine that log is already parsed')
        os.remove(report_path)

        # Передаём лог с несформированным отчётом
        already_parsed = log_analyzer.already_parsed(
            test_config,
            LogParams(path='nginx-access-ui.log-20170724', date=datetime.strptime('20170724', "%Y%m%d").date(), ext='')
        )
        self.assertFalse(already_parsed, 'Could not determine that log is not parsed yet')

    def test_parse_log(self):
        """
        Проверяем правильность разбора лога
        """
        # Передаём лог с корректными строками
        log_gen = log_analyzer.parse_log(
            test_config,
            LogParams(path='test_not_empty_log-20170802', date=NOT_EMPTY_LOG_DATE, ext='')
        )
        self.assertIsNotNone(log_gen, 'Could not parse latest log')
        first_parsed_line = next(log_gen)
        self.assertEqual(first_parsed_line.url, '/api/v2/banner/25019354', 'Wrong url is parsed in first log row')
        self.assertEqual(first_parsed_line.request_time, '0.390', 'Wrong request_time is parsed in first log row')

        # Передаём лог с корректными строками в архиве .gz
        log_gen = log_analyzer.parse_log(
            test_config,
            LogParams(path='test_not_empty_log-20170802.gz', date=NOT_EMPTY_LOG_DATE, ext='.gz')
        )
        self.assertIsNotNone(log_gen, 'Could not parse latest log')
        first_parsed_line = next(log_gen)
        self.assertEqual(first_parsed_line.url, '/api/v2/banner/25019354', 'Wrong url is parsed in first log row')
        self.assertEqual(first_parsed_line.request_time, '0.390', 'Wrong request_time is parsed in first log row')

        # Передаём пустой лог
        empty_log_gen = log_analyzer.parse_log(
            test_config,
            LogParams(path='test_empty_log-20161209', date=EMPTY_LOG_DATE, ext='')
        )
        with self.assertRaises(StopIteration, msg='Empty log returned not empty results'):
            next(empty_log_gen)

        # Передаём лог с неправильными строками
        error_log_gen = log_analyzer.parse_log(
            test_config,
            LogParams(path='test_with_errors_log-20170801', date=ERROR_LOG_DATE, ext='')
        )
        with self.assertRaises(RuntimeError, msg='Log with wrong rows has processed without errors'):
            sum(1 for _ in error_log_gen)

    def test_create_report(self):
        """
        Проверяем правильность создания отчёта
        """
        # Передаём лог c демо данными
        log_analyzer.create_report(
            test_config,
            log_analyzer.parse_log(
                test_config,
                LogParams(path='test_not_empty_log-20170802', date=NOT_EMPTY_LOG_DATE, ext='')
            ),
            LogParams(path='test_not_empty_log-20170802', date=NOT_EMPTY_LOG_DATE, ext='')
        )
        expected_path = os.path.join(test_config['REPORT_DIR'], NOT_EMPTY_LOG_REPORT)
        with open(
                expected_path,
                'r',
                encoding='UTF-8') as f:
            expected = f.read()
        self.assertIsNotNone(expected, 'Generated report is empty')

        actual_path = os.path.join(test_config['REPORT_DIR'], 'report-2017.08.02.html')
        with open(
                actual_path,
                'r',
                encoding='UTF-8') as f:
            actual = f.read()
        self.assertEqual(expected, actual, 'Generated report is not equal to sample')
        os.remove(actual_path)

    def test_create_report_with_another_regex(self):
        """
        Проверяем правильность создания отчёта
        """
        # Передаём лог c демо данными
        log_analyzer.create_report(
            test_config,
            log_analyzer.parse_log(
                {
                    "LOG_DIR": "../src/log",
                    "ALLOWED_ERRORS_PERCENT": 15,
                    "LOG_ENCODING": 'utf-8',
                    "LOGGING_LEVEL": 'DEBUG',
                    "LOG_REGEXP": ANOTHER_REGEXP
                },
                LogParams(path='test_not_empty_log-20170802', date=NOT_EMPTY_LOG_DATE, ext='')
            ),
            LogParams(path='test_not_empty_log-20170802', date=NOT_EMPTY_LOG_DATE, ext='')
        )
        expected_path = os.path.join(test_config['REPORT_DIR'], NOT_EMPTY_LOG_REPORT)
        with open(
                expected_path,
                'r',
                encoding='UTF-8') as f:
            expected = f.read()
        self.assertIsNotNone(expected, 'Generated report is empty')

        actual_path = os.path.join(test_config['REPORT_DIR'], 'report-2017.08.02.html')
        with open(
                actual_path,
                'r',
                encoding='UTF-8') as f:
            actual = f.read()
        self.assertEqual(expected, actual, 'Generated report is not equal to sample')
        os.remove(actual_path)


if __name__ == "__main__":
    unittest.main()
