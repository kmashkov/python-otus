import unittest

from ru.otus.python import log_analyzer


class LogAnalyzerTest(unittest.TestCase):

    def test_merge_config(self):
        """
        Проверяем правильность объединения конфигов
        """
        config = log_analyzer.merge_configs("../src/ru/otus/python/resources/config.properties")
        self.assertEqual(len(config), 4, "Неправильное количество настроек")
        self.assertEqual(config["ALLOWED_ERRORS_PERCENT"], 25, "Неправильно объединены конфиги")


if __name__ == "__main__":
    unittest.main()
