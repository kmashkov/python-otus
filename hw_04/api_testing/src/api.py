#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import logging
import hashlib
import re
import uuid
from collections import OrderedDict
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from dateutil.relativedelta import relativedelta

import hw_03.scoring_api.src.scoring as scoring
from store import CachedStore

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}
STORE_CONFIG = {
    "store_host": "localhost",
    "store_port": 6379,
    "cache_host": "localhost",
    "cache_port": 11211,
    "store_db": 1,
}
LOGGING_CONFIG = {
    "level": logging.INFO,
    "format": "[%(asctime)s] %(levelname).1s %(message)s",
    "datefmt": "%Y.%m.%d %H:%M:%S",
}


class GeneralField(metaclass=abc.ABCMeta):

    def __init__(self, name=None, required=False, nullable=True, value=None):
        self._name = name
        self._required = required
        self._nullable = nullable
        self._value = value

    @property
    def name(self):
        return self._name

    def __get__(self, obj, owner):
        return self._value

    def __set__(self, obj, value):
        self._value = value

    def __add__(self, other):
        if not isinstance(other, self.__class__):
            return self._value
        return self._value + other._value

    def __sub__(self, other):
        if not isinstance(other, self.__class__):
            return self._value
        return self._value - other._value

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._value == other._value
        if isinstance(other, self._value.__class__):
            return self._value == other
        return False

    def __hash__(self):
        return hash(self._value)

    def check(self, validation_errors):
            if self._required and self._value is None:
                validation_errors.append(f"Field {self.name} must be presented in request")
            if not self._nullable and not self._value:
                validation_errors.append(f"Field {self.name} can't be empty.")
            if self._value:
                self.check_value(validation_errors)
            return validation_errors

    @abc.abstractmethod
    def check_value(self, validation_errors):
        raise NotImplementedError


class DeclarativeFieldsMetaclass(type):
    """
    Metaclass that collects Fields declared on the base classes.
    """
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        current_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, GeneralField):
                value._name = key
                current_fields.append((key, value))
                attrs.pop(key)
        attrs['declared_fields'] = OrderedDict(current_fields)

        new_class = (super(DeclarativeFieldsMetaclass, mcs)
                     .__new__(mcs, name, bases, attrs))

        # Walk through the MRO.
        declared_fields = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)

        new_class.declared_fields = declared_fields

        return new_class


class GeneralRequest(metaclass=DeclarativeFieldsMetaclass):
    def __init__(self, d):
        for key, value in d.items():
            self.declared_fields[key]._value = value

    def __getattr__(self, item):
        return self.declared_fields.get(item)

    def check(self):
        validation_errors = []
        for _ in self.declared_fields.values():
            _.check(validation_errors)
        return validation_errors


class CharField(GeneralField):
    def check_value(self, validation_errors):
        if not isinstance(self._value, str):
            validation_errors.append(f"CharField {self.name} must be a str.")
            return False
        return True


class ArgumentsField(GeneralField):
    def check_value(self, validation_errors):
        if not isinstance(self._value, dict):
            validation_errors.append(f"ArgumentsField {self.name} must be a dict.")
            return False
        return True


class EmailField(CharField):
    def check_value(self, validation_errors):
        if super().check_value(validation_errors):
            if '@' not in self._value:
                validation_errors.append(f"EmailField {self.name} must contain '@'.")
                return False
            return True
        return False


class PhoneField(GeneralField):
    def check_value(self, validation_errors):
        if not isinstance(self._value, (str, int)):
            validation_errors.append(f"PhoneField {self.name} must be a str or an int.")
            return False
        else:
            match = re.match("^7\d{10}$", self._value if isinstance(self._value, str) else str(self._value))
            if not match:
                validation_errors.append(f"PhoneField {self.name} must contain 11 digits, starting from 7.")
                return False
        return True


class DateField(CharField):
    def check_value(self, validation_errors):
        if super().check_value(validation_errors):
            match = re.match("^\d{2}\.\d{2}\.\d{4}$", self._value)
            if not match:
                validation_errors.append(f"DateField {self.name} must has pattern DD.MM.YYYY")
                return False
            return True
        return False


class BirthDayField(DateField):
    def check_value(self, validation_errors):
        if super().check_value(validation_errors):
            boundary_date = datetime.now() - relativedelta(years=70)
            value_date = datetime.strptime(self._value, "%d.%m.%Y")
            if value_date < boundary_date:
                validation_errors.append(f"BirthdayField {self.name} must be less than 70 years ago.")
                return False
            return True
        return False


class GenderField(GeneralField):
    def check_value(self, validation_errors):
        if not isinstance(self._value, int):
            validation_errors.append(f"GenderField {self.name} must be an int.")
            return False
        if not any(self._value == digit for digit in [0, 1, 2]):
            validation_errors.append(f"GenderField {self.name} must be 0, 1 or 2.")
            return False
        return True


class ClientIDsField(GeneralField):
    def check_value(self, validation_errors):
        if not isinstance(self._value, list) or not all(isinstance(val, int) for val in self._value):
            validation_errors.append(f"ClientIDsField {self.name} must be a list of int.")
            return False
        return True


class ClientsInterestsRequest(GeneralRequest):
    client_ids = ClientIDsField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def count_ids(self):
        if self.client_ids is None:
            return 0
        return len(self.client_ids)


class OnlineScoreRequest(GeneralRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def has_attrs(self):
        attrs = []
        for _ in self.declared_fields:
            attrs.append(_.name)
        return attrs

    def check(self):
        validation_errors = super().check()
        if not ((self.phone and self.email) or
                (self.first_name and self.last_name) or
                (self.gender is not None and self.birthday)):
            validation_errors.append(
                'Some of the pairs phone‑email, first_name‑last_name or gender‑birthday must be filled')
        return validation_errors


class MethodRequest(GeneralRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        string = str(datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode('utf-8')
        digest = hashlib.sha512(string).hexdigest()
    elif request.account is None or request.login is None:
        return False
    else:
        string = str(request.account + request.login + SALT)
        digest = hashlib.sha512(string.encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def online_score_handler(request, ctx, store):
    req = OnlineScoreRequest(request.arguments._value)
    validate(req)
    ctx['has'] = req.has_attrs()
    phone = str(req.phone) if isinstance(req.phone, int) else req.phone
    email = req.email
    birthday = datetime.strptime(req.birthday, "%d.%m.%Y") if req.birthday else None
    gender = req.gender
    first_name = req.first_name
    last_name = req.last_name
    return {'score': 42 if request.is_admin else scoring.get_score(store, phone, email, birthday, gender, first_name,
                                                                   last_name)}


def clients_interests_handler(request, ctx, store):
    result = {}
    req = ClientsInterestsRequest(request.arguments._value)
    validate(req)
    cnt = ctx['nclients'] = req.count_ids()
    if cnt > 0:
        for client_id in req.client_ids:
            result[client_id] = scoring.get_interests(store, client_id)
    return result


def method_handler(request, ctx, store):
    inv_rqst = f"Wrong request: {request}."
    if not request.get('body'):
        return inv_rqst, INVALID_REQUEST
    method_request = MethodRequest(request.get('body'))
    try:
        validate(method_request)
        if not check_auth(method_request):
            return "Not authorized", FORBIDDEN
        method = method_request.method
        logging.debug(f"method: {method}")
        response = methods[method](method_request, ctx, store)
        code = OK
    except ValueError as ve:
        response = str(ve)
        code = INVALID_REQUEST
    except Exception as e:
        response = inv_rqst
        logging.error(response)
        logging.error(e)
        code = INVALID_REQUEST

    return response, code


def validate(req):
    validation_errors = req.check()
    if validation_errors:
        raise ValueError(' '.join(validation_errors))


methods = {
    'online_score': online_score_handler,
    'clients_interests': clients_interests_handler
}


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = CachedStore(STORE_CONFIG, LOGGING_CONFIG)

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-c", "--config", action="store", default=None)
    (opts, args) = op.parse_args()
    LOGGING_CONFIG["filename"] = opts.log
    logging.basicConfig(filename=LOGGING_CONFIG.get("filename"), level=LOGGING_CONFIG.get("level"),
                        format=LOGGING_CONFIG.get("format"), datefmt=LOGGING_CONFIG.get("datefmt"))
    if opts.config:
        try:
            with open(opts.config, 'r', encoding='UTF-8') as config_file:
                for line in config_file:
                    line = line.rstrip()
                    if '=' not in line:
                        continue
                    if line.startswith('#'):
                        continue
                    k, v = line.split('=', 1)
                    STORE_CONFIG[k.lower()] = int(v) if v.isdigit() else v
        except FileNotFoundError:
            raise FileNotFoundError(f"There is no config file at {opts.config}")

    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
