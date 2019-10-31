import datetime
import functools
import logging
import unittest

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

    def assertValueErrorRaised(self, expected, field, value):
        with self.assertRaises(ValueError) as cm:
            field.check(value)
        self.assertEqual(expected, cm.exception.args[0])


class TestCharField(TestSuite):
    @cases([
        ("first_name", 12345, "CharField first_name must be a str."),
    ])
    def test_invalid_default_char_field(self, name, value, expected):
        field = api.CharField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a",
        "Alexander",
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_char_field(self, value):
        field = api.CharField('name')
        self.assertTrue(field.check(value))

    @cases([
        ("first_name", None, "Field first_name must be presented in request."),
    ])
    def test_invalid_required_char_field(self, name, value, expected):
        field = api.CharField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a",
        "Alexander",
    ])
    def test_valid_required_char_field(self, value):
        field = api.CharField('name', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("first_name", None, "Field first_name can't be empty."),
        ("first_name", [], "Field first_name can't be empty."),
        ("first_name", {}, "Field first_name can't be empty."),
        ("first_name", "", "Field first_name can't be empty."),
    ])
    def test_invalid_not_nullable_char_field(self, name, value, expected):
        field = api.CharField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a",
        "Alexander",
    ])
    def test_valid_not_nullable_char_field(self, value):
        field = api.CharField('name', nullable=False)
        self.assertTrue(field.check(value))


class TestArgumentsField(TestSuite):
    @cases([
        ("arguments", 12345, "ArgumentsField arguments must be a dict."),
        ("arguments", '{"first_name": "a", "last_name": "b"}', "ArgumentsField arguments must be a dict."),
        ("arguments", ['a', "b"], "ArgumentsField arguments must be a dict."),
    ])
    def test_invalid_default_arguments_field(self, name, value, expected):
        field = api.ArgumentsField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        {"first_name": "a", "last_name": "b"},
        {"first_name": "Alexander", "age": 32, "balance": 123.45, "last_login": "1900-01-01 00:00:00"},
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_arguments_field(self, value):
        field = api.ArgumentsField('arguments')
        self.assertTrue(field.check(value))

    @cases([
        ("arguments", None, "Field arguments must be presented in request."),
    ])
    def test_invalid_required_arguments_field(self, name, value, expected):
        field = api.ArgumentsField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        {"first_name": "a", "last_name": "b"},
        {"first_name": "Alexander", "age": 32, "balance": 123.45, "last_login": "1900-01-01 00:00:00"},
    ])
    def test_valid_required_arguments_field(self, value):
        field = api.ArgumentsField('arguments', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("arguments", None, "Field arguments can't be empty."),
        ("arguments", {}, "Field arguments can't be empty."),
        ("arguments", [], "Field arguments can't be empty."),
        ("arguments", "", "Field arguments can't be empty."),
    ])
    def test_invalid_not_nullable_arguments_field(self, name, value, expected):
        field = api.CharField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        {"first_name": "a", "last_name": "b"},
        {"first_name": "Alexander", "age": 32, "balance": 123.45, "last_login": "1900-01-01 00:00:00"},
    ])
    def test_valid_not_nullable_arguments_field(self, value):
        field = api.ArgumentsField('arguments', nullable=False)
        self.assertTrue(field.check(value))


class TestEmailField(TestSuite):
    @cases([
        ("email", "stupnikovotus.ru", "EmailField email must contain '@'."),
        ("email", 12345, "CharField email must be a str."),
    ])
    def test_invalid_default_email_field(self, name, value, expected):
        field = api.EmailField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a@a",
        "acsdfsfsfsfsfs_321ASSDsdf@fdrer.ru",
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_email_field(self, value):
        field = api.EmailField('email')
        self.assertTrue(field.check(value))

    @cases([
        ("email", None, "Field email must be presented in request."),
    ])
    def test_invalid_required_email_field(self, name, value, expected):
        field = api.EmailField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a@a",
        "acsdfsfsfsfsfs_321ASSDsdf@fdrer.ru",
    ])
    def test_valid_required_email_field(self, value):
        field = api.EmailField('email', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("email", None, "Field email can't be empty."),
        ("email", {}, "Field email can't be empty."),
        ("email", [], "Field email can't be empty."),
        ("email", "", "Field email can't be empty."),
    ])
    def test_invalid_not_nullable_email_field(self, name, value, expected):
        field = api.EmailField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "a@a",
        "acsdfsfsfsfsfs_321ASSDsdf@fdrer.ru",
    ])
    def test_valid_not_nullable_email_field(self, value):
        field = api.EmailField('email', nullable=False)
        self.assertTrue(field.check(value))


class TestPhoneField(TestSuite):
    @cases([
        ("phone", 7917500.2040, "PhoneField phone must be a str or an int."),
        ("phone", [79175002040], "PhoneField phone must be a str or an int."),
        ("phone", "89175002040", "PhoneField phone must contain 11 digits, starting from 7."),
        ("phone", 89175002040, "PhoneField phone must contain 11 digits, starting from 7."),
        ("phone", "791750020", "PhoneField phone must contain 11 digits, starting from 7."),
        ("phone", 9175002040, "PhoneField phone must contain 11 digits, starting from 7."),
    ])
    def test_invalid_default_phone_field(self, name, value, expected):
        field = api.PhoneField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "79175002040",
        79175002040,
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_phone_field(self, value):
        field = api.PhoneField('phone')
        self.assertTrue(field.check(value))

    @cases([
        ("phone", None, "Field phone must be presented in request."),
    ])
    def test_invalid_required_phone_field(self, name, value, expected):
        field = api.PhoneField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "79175002040",
        79175002040,
    ])
    def test_valid_required_phone_field(self, value):
        field = api.PhoneField('phone', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("phone", None, "Field phone can't be empty."),
        ("phone", [], "Field phone can't be empty."),
        ("phone", {}, "Field phone can't be empty."),
        ("phone", "", "Field phone can't be empty."),
    ])
    def test_invalid_not_nullable_phone_field(self, name, value, expected):
        field = api.PhoneField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "79175002040",
        79175002040,
    ])
    def test_valid_not_nullable_phone_field(self, value):
        field = api.PhoneField('phone', nullable=False)
        self.assertTrue(field.check(value))


class TestDateField(TestSuite):
    @cases([
        ("date", 19072017, "CharField date must be a str."),
        ("date", datetime.datetime.today(), "CharField date must be a str."),
        ("date", "2017.07.19", "DateField date must has pattern DD.MM.YYYY."),
    ])
    def test_invalid_default_date_field(self, name, value, expected):
        field = api.DateField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1900",
        "31.12.2040",
        "06.31.2040",
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_date_field(self, value):
        field = api.DateField('date')
        self.assertTrue(field.check(value))

    @cases([
        ("date", None, "Field date must be presented in request."),
    ])
    def test_invalid_required_date_field(self, name, value, expected):
        field = api.DateField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1900",
        "31.12.2040",
        "06.31.2040",
    ])
    def test_valid_required_date_field(self, value):
        field = api.DateField('date', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("date", None, "Field date can't be empty."),
        ("date", [], "Field date can't be empty."),
        ("date", {}, "Field date can't be empty."),
        ("date", "", "Field date can't be empty."),
    ])
    def test_invalid_not_nullable_date_field(self, name, value, expected):
        field = api.DateField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1900",
        "31.12.2040",
        "06.31.2040",
    ])
    def test_valid_not_nullable_date_field(self, value):
        field = api.DateField('date', nullable=False)
        self.assertTrue(field.check(value))


class TestBirthdayField(TestSuite):
    @cases([
        ("birthday", 19072017, "CharField birthday must be a str."),
        ("birthday", datetime.datetime.today(), "CharField birthday must be a str."),
        ("birthday", "2017.07.19", "DateField birthday must has pattern DD.MM.YYYY."),
        ("birthday", "01.01.1949", "BirthdayField birthday must be less than 70 years ago."),
        ("birthday", "06.31.2040", "time data '06.31.2040' does not match format '%d.%m.%Y'"),
    ])
    def test_invalid_default_birthday_field(self, name, value, expected):
        field = api.BirthDayField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1990",
        "31.12.2040",
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_birthday_field(self, value):
        field = api.BirthDayField('birthday')
        self.assertTrue(field.check(value))

    @cases([
        ("birthday", None, "Field birthday must be presented in request."),
    ])
    def test_invalid_required_birthday_field(self, name, value, expected):
        field = api.BirthDayField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1990",
        "31.12.2040",
    ])
    def test_valid_required_birthday_field(self, value):
        field = api.BirthDayField('birthday', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("birthday", None, "Field birthday can't be empty."),
        ("birthday", [], "Field birthday can't be empty."),
        ("birthday", {}, "Field birthday can't be empty."),
        ("birthday", "", "Field birthday can't be empty."),
    ])
    def test_invalid_not_nullable_birthday_field(self, name, value, expected):
        field = api.BirthDayField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        "01.01.1990",
        "31.12.2040",
    ])
    def test_valid_not_nullable_birthday_field(self, value):
        field = api.BirthDayField('birthday', nullable=False)
        self.assertTrue(field.check(value))


class TestGenderField(TestSuite):
    @cases([
        ("gender", '1', "GenderField gender must be an int."),
        ("gender", -1, "GenderField gender must be 0, 1 or 2."),
        ("gender", 3, "GenderField gender must be 0, 1 or 2."),
    ])
    def test_invalid_default_gender_field(self, name, value, expected):
        field = api.GenderField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        0,
        1,
        2,
        None,
        [],
        "",
        {},
    ])
    def test_valid_default_gender_field(self, value):
        field = api.GenderField('gender')
        self.assertTrue(field.check(value))

    @cases([
        ("gender", None, "Field gender must be presented in request."),
    ])
    def test_invalid_required_gender_field(self, name, value, expected):
        field = api.GenderField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        0,
        1,
        2,
    ])
    def test_valid_required_gender_field(self, value):
        field = api.GenderField('gender', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("gender", None, "Field gender can't be empty."),
        ("gender", [], "Field gender can't be empty."),
        ("gender", {}, "Field gender can't be empty."),
        ("gender", "", "Field gender can't be empty."),
    ])
    def test_invalid_not_nullable_gender_field(self, name, value, expected):
        field = api.GenderField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        0,
        1,
        2,
    ])
    def test_valid_not_nullable_gender_field(self, value):
        field = api.GenderField('gender', nullable=False)
        self.assertTrue(field.check(value))


class TestClientIdsField(TestSuite):
    @cases([
        ("client_ids", 1, "ClientIDsField client_ids must be a list of int."),
        ("client_ids", ['1', '2'], "ClientIDsField client_ids must be a list of int."),
        ("client_ids", (1, 2), "ClientIDsField client_ids must be a list of int."),
        ("client_ids", [1.0, 2.0], "ClientIDsField client_ids must be a list of int."),
    ])
    def test_invalid_default_client_ids_field(self, name, value, expected):
        field = api.ClientIDsField(name)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        [1, 100234, 48900776],
        [24343254545],
        [],
        None,
        {},
        ""
    ])
    def test_valid_default_client_ids_field(self, value):
        field = api.ClientIDsField('client_ids')
        self.assertTrue(field.check(value))

    @cases([
        ("client_ids", None, "Field client_ids must be presented in request."),
    ])
    def test_invalid_required_client_ids_field(self, name, value, expected):
        field = api.ClientIDsField(name, required=True)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        [1, 100234, 48900776],
        [24343254545],
    ])
    def test_valid_required_client_ids_field(self, value):
        field = api.ClientIDsField('client_ids', required=True)
        self.assertTrue(field.check(value))

    @cases([
        ("client_ids", None, "Field client_ids can't be empty."),
        ("client_ids", [], "Field client_ids can't be empty."),
        ("client_ids", {}, "Field client_ids can't be empty."),
        ("client_ids", "", "Field client_ids can't be empty."),
    ])
    def test_invalid_not_nullable_client_ids_field(self, name, value, expected):
        field = api.ClientIDsField(name, nullable=False)
        self.assertValueErrorRaised(expected, field, value)

    @cases([
        [1, 100234, 48900776],
        [24343254545],
    ])
    def test_valid_not_nullable_client_ids_field(self, value):
        field = api.ClientIDsField('client_ids', nullable=False)
        self.assertTrue(field.check(value))


if __name__ == "__main__":
    unittest.main()
