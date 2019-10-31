#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import logging
import hashlib
import re
import uuid
from abc import ABCMeta
from optparse import OptionParser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from dateutil.relativedelta import relativedelta

import hw_03.scoring_api.src.scoring as scoring

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


class GeneralField(metaclass=ABCMeta):
    def __init__(self, name=None, required=False, nullable=True):
        self._name = name
        self._required = required
        self._nullable = nullable

    @property
    def name(self):
        return self._name

    def __get__(self, obj, owner):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        self.check(value)
        obj.__dict__[self.name] = value

    def check(self, value):
            if self._required and value is None:
                raise ValueError(f"Field {self.name} must be presented in request")
            if not self._nullable and value in ['', None, [], {}]:
                raise ValueError(f"Field {self.name} can't be empty.")
            if value:
                self.check_value(value)
            return True

    @abc.abstractmethod
    def check_value(self, value):
        raise NotImplementedError


class CharField(GeneralField):
    def check_value(self, value):
        if not isinstance(value, str):
            raise ValueError(f"CharField {self.name} must be a str.")


class ArgumentsField(GeneralField):
    def check_value(self, value):
        if not isinstance(value, dict):
            raise ValueError(f"ArgumentsField {self.name} must be a dict.")


class EmailField(CharField):
    def check_value(self, value):
        super().check_value(value)
        if '@' not in value:
            raise ValueError(f"EmailField {self.name} must contain '@'.")


class PhoneField(GeneralField):
    def check_value(self, value):
        if not isinstance(value, (str, int)):
            raise ValueError(f"PhoneField {self.name} must be a str or an int.")
        else:
            match = re.match("^7\d{10}$", value if isinstance(value, str) else str(value))
            if not match:
                raise ValueError(f"PhoneField {self.name} must contain 11 digits, starting from 7.")


class DateField(CharField):
    def check_value(self, value):
        super().check_value(value)
        match = re.match("^\d{2}\.\d{2}\.\d{4}$", value)
        if not match:
            raise ValueError(f"DateField {self.name} must has pattern DD.MM.YYYY")


class BirthDayField(DateField):
    def check_value(self, value):
        super().check_value(value)
        boundary_date = datetime.now() - relativedelta(years=70)
        value_date = datetime.strptime(value, "%d.%m.%Y")
        if value_date < boundary_date:
            raise ValueError(f"BirthdayField {self.name} must be less than 70 years ago.")


class GenderField(GeneralField):
    def check_value(self, value):
        if not isinstance(value, int):
            raise ValueError(f"GenderField {self.name} must be an int.")
        if value not in [UNKNOWN, MALE, FEMALE]:
            raise ValueError(f"GenderField {self.name} must be 0, 1 or 2.")


class ClientIDsField(GeneralField):
    def check_value(self, value):
        if not isinstance(value, list) or not all(isinstance(val, int) for val in value):
            raise ValueError(f"ClientIDsField {self.name} must be a list of int.")


class DeclarativeFieldsMetaclass(type, metaclass=ABCMeta):
    """
    Metaclass that collects Fields declared on the base classes.
    """
    def __new__(mcs, name, bases, attrs):
        # Collect fields from current class.
        current_field_names = set()
        for key, value in list(attrs.items()):
            if isinstance(value, GeneralField):
                value._name = key
                current_field_names.add(key)
        attrs['declared_field_names'] = current_field_names

        new_class = (super(DeclarativeFieldsMetaclass, mcs).__new__(mcs, name, bases, attrs))

        # Walk through the MRO.
        declared_field_names = set()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'declared_field_names'):
                declared_field_names.union(set(base.declared_field_names))

        new_class.declared_field_names.union(declared_field_names)

        return new_class


class GeneralRequest(metaclass=DeclarativeFieldsMetaclass):
    def __init__(self, d):
        self.validation_errors = []
        if not d:
            self.validation_errors.append('Request is empty.')
        if isinstance(d, dict):
            for name in self.declared_field_names:
                try:
                    setattr(self, name, d.get(name))
                except ValueError as e:
                    self.validation_errors.append(*e.args)
        if not self.validation_errors:
            self.check()

    def check(self):
        pass

    def has_errors(self):
        return bool(self.validation_errors)


class MethodRequest(GeneralRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


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
        for name in self.declared_field_names:
            if self.__dict__.get(name) is not None:
                attrs.append(name)
        return attrs

    def check(self):
        validation_errors = super().check()
        if not ((self.phone and self.email) or
                (self.first_name and self.last_name) or
                (self.gender is not None and self.birthday)):
            self.validation_errors.append(
                'Some of the pairs phone‑email, first_name‑last_name or gender‑birthday must be filled')
        return validation_errors


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
    req = OnlineScoreRequest(request.arguments)
    if req.has_errors():
        return req.validation_errors, INVALID_REQUEST
    ctx['has'] = req.has_attrs()
    phone = str(req.phone) if isinstance(req.phone, int) else req.phone
    email = req.email
    birthday = datetime.strptime(req.birthday, "%d.%m.%Y") if req.birthday else None
    gender = req.gender
    first_name = req.first_name
    last_name = req.last_name
    return {'score': 42 if request.is_admin else scoring.get_score(store, phone, email, birthday, gender, first_name,
                                                                   last_name)}, OK


def clients_interests_handler(request, ctx, store):
    response = {}
    req = ClientsInterestsRequest(request.arguments)
    if req.has_errors():
        return req.validation_errors, INVALID_REQUEST
    cnt = ctx['nclients'] = req.count_ids()
    if cnt > 0:
        for client_id in req.client_ids:
            response[client_id] = scoring.get_interests(store, client_id)
    return response, OK


def method_handler(request, ctx, store):
    inv_rqst = f"Wrong request: {request}."
    if not request.get('body'):
        return inv_rqst, INVALID_REQUEST
    try:
        method_request = MethodRequest(request.get('body'))
        if method_request.has_errors():
            return method_request.validation_errors, INVALID_REQUEST
        if not check_auth(method_request):
            return "Not authorized", FORBIDDEN
        method = method_request.method
        logging.debug(f"method: {method}")
        response, code = methods[method](method_request, ctx, store)
    except Exception as e:
        response, code = inv_rqst, INVALID_REQUEST
        logging.error(response)
        logging.error(e)
    return response, code


methods = {
    'online_score': online_score_handler,
    'clients_interests': clients_interests_handler
}


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request and data_string:
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
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
