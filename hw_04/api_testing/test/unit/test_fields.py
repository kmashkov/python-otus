import datetime
import functools
import hashlib
import logging
import unittest
from unittest.mock import patch

import hw_04.api_testing.src.api as api

logging.basicConfig(filename=None, level=logging.INFO,
                    format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')


def cases(cases):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args):
            for i, c in enumerate(cases):
                new_args = args + (c if isinstance(c, tuple) else (c,))
                try:
                    f(*new_args)
                except Exception as e:
                    logging.error(f"Error while testing {f.__name__} with case number {i + 1}: {c}.")
                    raise e
        return wrapper
    return decorator


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}

    def get_response(self, request):
        with patch('hw_04.api_testing.src.store.CachedStore') as MockedStore:
            cached_store = MockedStore.return_value
            cached_store.get.return_value = '["football", "computer games"]'
            cached_store.cache_get.return_value = None
            return api.method_handler({"body": request, "headers": self.headers}, self.context, cached_store)

    def set_valid_auth(self, request):
        if request.get("login") == api.ADMIN_LOGIN:
            string = (datetime.datetime.now().strftime("%Y%m%d%H") + api.ADMIN_SALT).encode('utf-8')
            request["token"] = hashlib.sha512(string).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api.SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    @cases([
        ({"account": "horns&hoofs", "method": "online_score", "arguments":
            {"first_name": "a", "last_name": "b"}}, ["Field login must be presented in request"]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "", "arguments":
            {"first_name": "a", "last_name": "b"}}, ["Field method can't be empty."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"first_name": 12345, "last_name": "b"}}, ["CharField first_name must be a str."]),
    ])
    def test_invalid_char_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score"},
         ["Field arguments must be presented in request"]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            ['a', "b"]}, ["ArgumentsField arguments must be a dict."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            '{"first_name": "a", "last_name": "b"}'}, ["ArgumentsField arguments must be a dict."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            42}, ["ArgumentsField arguments must be a dict."]),
    ])
    def test_invalid_arguments_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"phone": "79175002040", "email": "stupnikovotus.ru"}}, ["EmailField email must contain '@'."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"phone": "79175002040", "email": 42}}, ["CharField email must be a str."]),
    ])
    def test_invalid_email_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": 7917500.2040, "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must be a str or an int."]
        ),
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": [79175002040], "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must be a str or an int."]
        ),
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": "89175002040", "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must contain 11 digits, starting from 7."]
        ),
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": 89175002040, "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must contain 11 digits, starting from 7."]
        ),
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": "791750020", "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must contain 11 digits, starting from 7."]
        ),
        (
                {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
                    {"phone": 9175002040, "email": "stupnikov@otus.ru"}},
                ["PhoneField phone must contain 11 digits, starting from 7."]
        ),
    ])
    def test_invalid_phone_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": [1, 2], "date": 19072017}}, ["CharField date must be a str."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": [1, 2], "date": datetime.datetime.today()}}, ["CharField date must be a str."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": [1, 2], "date": '2017.07.19'}}, ["DateField date must has pattern DD.MM.YYYY"]),
    ])
    def test_invalid_date_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": 0, "birthday": 19072017}}, ["CharField birthday must be a str."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": 0, "birthday": datetime.datetime.today()}}, ["CharField birthday must be a str."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": 0, "birthday": '2017.07.19'}}, ["DateField birthday must has pattern DD.MM.YYYY"]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": 0, "birthday": '01.01.1949'}}, ["BirthdayField birthday must be less than 70 years ago."]),
    ])
    def test_invalid_birthday_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": '1', "birthday": '01.01.1979'}}, ["GenderField gender must be an int."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": -1, "birthday": '01.01.1979'}}, ["GenderField gender must be 0, 1 or 2."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"gender": 3, "birthday": '01.01.1979'}}, ["GenderField gender must be 0, 1 or 2."]),
    ])
    def test_invalid_gender_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)

    @cases([
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": 1, "date": '01.01.1979'}}, ["ClientIDsField client_ids must be a list of int."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": ['1', '2'], "date": '01.01.1979'}}, ["ClientIDsField client_ids must be a list of int."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": (1, 2), "date": '01.01.1979'}}, ["ClientIDsField client_ids must be a list of int."]),
        ({"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments":
            {"client_ids": [1.0, 2.0], "date": '01.01.1979'}}, ["ClientIDsField client_ids must be a list of int."]),
    ])
    def test_invalid_client_ids_field(self, request, expected):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)
        self.assertEqual(expected, response)


if __name__ == "__main__":
    unittest.main()
