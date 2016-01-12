# -*- coding: utf-8 -*-
from datetime import datetime
import requests

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
        if len(data) == self.number_of_digits:
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
            datetime.strptime(self.date, DateValidator.DATE_FORMAT)
            return True
        except ValueError:
            return False


class AddressFetcherError(Exception):
    pass


class AddressFetcher(object):

    API = 'http://maps.googleapis.com/maps/api/geocode/json'

    def __init__(self):
        self.api = AddressFetcher.API
        self.data = {}

    def fetch(self, zipcode):
        try:
            params = {'sensor': 'false', 'address': str(zipcode)}
            request = requests.get(self.api, params=params)
            response = request.json()
            if response['status'] == 'OK':
                self.data['zipcode'] = str(zipcode)
                for address_compent in response['results'][0]['address_components']:
                    if address_compent['types'][0] == u'country':
                        self.data['country'] = address_compent['short_name']
                    if address_compent['types'][0] == 'administrative_area_level_1':
                        self.data['state'] = address_compent['short_name']
                    if address_compent['types'][0] == 'administrative_area_level_2':
                        self.data['city'] = address_compent['long_name']
        except ValueError:
            self.data = {}
            raise AddressFetcherError("Error while fetching data")

    @property
    def city(self):
        return self.data['city']

    @property
    def state(self):
        return self.data['state']

    @property
    def country(self):
        return self.data['country']

    @property
    def zipcode(self):
        return self.data['zipcode']

    def has_data(self):
        return bool(self.data)

class AddressValidator(object):

    """ address = {zipcode = '99999999', state = 'UF', city = 'city'} """
    def __init__(self, address, address_fetcher=None):
        self.address_fetcher = address_fetcher or AddressFetcher()
        self.address = address
        self.valid = False

    def is_valid(self):
        self._validate()
        return self.valid

    def _validate(self):
        self.address_fetcher.fetch(self.address['zipcode'])
        if self.address_fetcher.has_data():
            if (self.address_fetcher.country.lower() == self.address['country'].lower() and
                self.address_fetcher.state.lower() == self.address['state'].lower() and
                self.address_fetcher.city.lower() == self.address['city'].lower()):
                self.valid = True
        else:
            self.valid = False
