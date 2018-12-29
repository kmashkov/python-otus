import unittest

from ru.otus.python import log_analyzer

LAST_LOG_EXTENSION = '.gz'
LAST_LOG_DATE = '20170630'
LAST_LOG_FILENAME = 'nginx-access-ui.log-20170630.gz'
USER_ALLOWED_ERRORS_PERCENT = 25
DEFAULT_ALLOWED_ERRORS_PERCENT = 15
CONFIG_SIZE = 5


class LogAnalyzerTest(unittest.TestCase):

    def test_merge_config(self):
        """
        Проверяем правильность объединения конфигов
        """
        config = log_analyzer.merge_configs("../src/ru/otus/python/resources/config.properties")
        self.assertIsNotNone(config, "Возвращён пустой конфиг")
        self.assertEqual(len(config), CONFIG_SIZE, "Неправильное количество настроек")
        self.assertEqual(config["ALLOWED_ERRORS_PERCENT"], USER_ALLOWED_ERRORS_PERCENT, "Неправильно объединены конфиги")

        # Объединяем с несуществущим конфигом
        config = log_analyzer.merge_configs("../src/ru/otus/python/resources/cfg.properties")
        self.assertIsNotNone(config, "Возвращён пустой конфиг")
        self.assertEqual(len(config), CONFIG_SIZE, "Неправильное количество настроек")
        self.assertEqual(config["ALLOWED_ERRORS_PERCENT"], DEFAULT_ALLOWED_ERRORS_PERCENT, "Неправильно объединены конфиги")

    def test_find_last_log(self):
        """
        Проверяем правильность нахождения последнего лога
        """
        last_log = log_analyzer.find_last_log_path({"LOG_DIR": "../src/ru/otus/python/log"})
        self.assertIsNotNone(last_log, "Последний лог не найден")
        self.assertIsNotNone(last_log.date, "Не распарсилась дата в имени лога")
        self.assertIsNotNone(last_log.ext, "Не распарсилось расширение в имени лога")
        self.assertEqual(last_log.path, LAST_LOG_FILENAME, "Неправильно выбран лог")
        self.assertEqual(last_log.date, LAST_LOG_DATE, "Неправильно распарсилась дата в имени лога")
        self.assertEqual(last_log.ext, LAST_LOG_EXTENSION, "Неправильно распарсилось расширение в имени лога")


if __name__ == "__main__":
    unittest.main()
