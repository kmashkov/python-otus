import unittest

from ru.otus.python import log_analyzer


class LogAnalyzerTest(unittest.TestCase):

    def test_merge_config(self):
        """
        Проверяем правильность объединения конфигов
        """
        config = log_analyzer.merge_configs("../src/ru/otus/python/resources/config.properties")
        self.assertIsNotNone(config, "Возвращён пустой конфиг")
        self.assertEqual(len(config), 4, "Неправильное количество настроек")
        self.assertEqual(config["ALLOWED_ERRORS_PERCENT"], 25, "Неправильно объединены конфиги")

        # Объединяем с несуществущим конфигом
        config = log_analyzer.merge_configs("../src/ru/otus/python/resources/cfg.properties")
        self.assertIsNotNone(config, "Возвращён пустой конфиг")
        self.assertEqual(len(config), 4, "Неправильное количество настроек")
        self.assertEqual(config["ALLOWED_ERRORS_PERCENT"], 15, "Неправильно объединены конфиги")

    def test_find_last_log(self):
        """
        Проверяем правильность нахождения последнего лога
        """
        last_log = log_analyzer.find_last_log_path({"LOG_DIR": "../src/ru/otus/python/log"})
        self.assertIsNotNone(last_log, "Последний лог не найден")
        self.assertIsNotNone(last_log.date, "Не распарсилась дата в имени лога")
        self.assertIsNotNone(last_log.ext, "Не распарсилось расширение в имени лога")
        self.assertEqual(last_log.path, 'nginx-access-ui.log-20170630.gz', "Неправильно выбран лог")
        self.assertEqual(last_log.date, '20170630', "Неправильно распарсилась дата в имени лога")
        self.assertEqual(last_log.ext, '.gz', "Неправильно распарсилось расширение в имени лога")


if __name__ == "__main__":
    unittest.main()
