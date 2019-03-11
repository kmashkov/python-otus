import datetime
import functools
import hashlib
import unittest
import logging

import api2

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
        self.store = None

    def get_response(self, request):
        return api2.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def set_valid_auth(self, request):
        if request.get("login") == api2.ADMIN_LOGIN:
            string = (datetime.datetime.now().strftime("%Y%m%d%H") + api2.ADMIN_SALT).encode('utf-8')
            request["token"] = hashlib.sha512(string).hexdigest()
        else:
            msg = request.get("account", "") + request.get("login", "") + api2.SALT
            request["token"] = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api2.INVALID_REQUEST, code)

    @cases([
        ({"account": "horns&hoofs", "method": "online_score", "arguments":
            {"first_name": "a", "last_name": "b"}}, "Field login must be presented in request"),
        ({"account": "horns&hoofs", "login": "h&f", "method": "", "arguments":
            {"first_name": "a", "last_name": "b"}}, "Field method can't be empty."),
        ({"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments":
            {"first_name": 12345, "last_name": "b"}}, "CharField first_name must be a str."),
    ])
    def test_invalid_charfield(self, request, message):
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api2.INVALID_REQUEST, code)
        self.assertEqual(message, response)

    @cases([
        {"phone": "79175002040", "email": "stupnikov@otus.ru"},
        {"phone": 79175002040, "email": "stupnikov@otus.ru"},
        {"gender": 1, "birthday": "01.01.2000", "first_name": "a", "last_name": "b"},
        {"gender": 0, "birthday": "01.01.2000"},
        {"gender": 2, "birthday": "01.01.2000"},
        {"first_name": "a", "last_name": "b"},
        {"phone": "79175002040", "email": "stupnikov@otus.ru", "gender": 1, "birthday": "01.01.2000",
         "first_name": "a", "last_name": "b"},
    ])
    def test_ok_score_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "online_score", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api2.OK, code, arguments)
        score = response.get("score")
        self.assertTrue(isinstance(score, (int, float)) and score >= 0, arguments)
        self.assertEqual(sorted(self.context["has"]), sorted(arguments.keys()))

    @cases([
        {"client_ids": [1, 2, 3], "date": datetime.datetime.today().strftime("%d.%m.%Y")},
        {"client_ids": [1, 2], "date": "19.07.2017"},
        {"client_ids": [0]},
    ])
    def test_ok_interests_request(self, arguments):
        request = {"account": "horns&hoofs", "login": "h&f", "method": "clients_interests", "arguments": arguments}
        self.set_valid_auth(request)
        response, code = self.get_response(request)
        self.assertEqual(api2.OK, code, arguments)
        self.assertEqual(len(arguments["client_ids"]), len(response))
        self.assertTrue(all(v and isinstance(v, list) and all(isinstance(i, (str, bytes)) for i in v)
                            for v in response.values()))
        self.assertEqual(self.context.get("nclients"), len(arguments["client_ids"]))


if __name__ == "__main__":
    unittest.main()
