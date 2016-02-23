# -*- coding: utf-8 -*-
from datetime import datetime
import requests

from segue.core import logger

class DocumentValidator(object):

    def __init__(self, data, number_of_digits):
        self.number_of_digits = number_of_digits
        self.valid = False
        self.digits = []
        self._parse(data)

    def is_valid(self):
        if self.digits:
            self._validate()
        return self.valid

    def _parse(self, data):
        if data and len(data) == self.number_of_digits:
            for c in data:
                if c.isdigit():
                    self.digits.append(int(c))
            if len(self.digits) != self.number_of_digits:
                self.digits = []

    def _all_digits_are_equal(self):
        first_digit = self.digits[0]
        for digit in self.digits:
            if first_digit != digit:
                return False
        return True

    def _calc_digit(self, digits, weighs):
        sum = 0
        for i in range(len(digits)):
                sum += digits[i] * weighs[i]

        rest = 11 - (sum % 11)
        if(rest == 10 or rest == 11):
                    rest = 0
        return rest

class CPFValidator(DocumentValidator):

    NUMBER_OF_DIGITS = 11

    def __init__(self, data):
        super(CPFValidator, self).__init__(data, CPFValidator.NUMBER_OF_DIGITS)

    def _validate(self):
        first_cpf_weighs = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        second_cpf_weighs = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        first_cd = self.digits[9]
        second_cd = self.digits[10]

        if not self._all_digits_are_equal():
            self.valid = (first_cd == self._calc_digit(self.digits[:9], first_cpf_weighs) and
                          second_cd == self._calc_digit(self.digits[:10], second_cpf_weighs))

class CNPJValidator(DocumentValidator):

    NUMBER_OF_DIGITS = 14

    def __init__(self, data):
        super(CNPJValidator, self).__init__(data, CNPJValidator.NUMBER_OF_DIGITS)

    def _validate(self):
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        first_cd = self.digits[12]
        second_cd = self.digits[13]

        if not self._all_digits_are_equal():
                self.valid = (first_cd == self._calc_digit(self.digits[:12], first_weights) and
                                second_cd == self._calc_digit(self.digits[:13], second_weights))


class DateValidator(object):

    # FIX CREATE A CONFIG
    DATE_FORMAT = '%d/%m/%Y'

    def __init__(self, date):
        self.date = date

    def is_valid(self):
        try:
            date = datetime.strptime(self.date, DateValidator.DATE_FORMAT)
            if date >= datetime(1900, 1, 1):
                return True
            else:
                return False
        except ValueError:
            return False

class AddressFetcher(object):

    def __init__(self):
        self.api = AddressFetcher.API
        self.data = {}


class ZipCodeValidator(object):

    API = 'https://viacep.com.br/ws/{}/json/'

    def __init__(self, zipcode):
        self.zipcode = zipcode
        self.valid = False

    def is_valid(self):
        self._validate()
        return self.valid

    def _validate(self):
        try:
            url = ZipCodeValidator.API.format(self.zipcode)
            request = requests.get(url)
            if request.status_code == 200:
                response = request.json()
                if 'erro' not in response:
                    self.valid = True
        except Exception as ex:
            logger.error('Error while validating CEP. Message: {}'.format(ex.message))
            self.valid = True #IO EXCEPTION