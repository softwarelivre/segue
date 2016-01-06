# -*- coding: utf-8 -*-

class CPFValidator(object):

    NUMBER_OF_DIGITS = 11

    def __init__(self, data):
        self.valid = False
        self.digits = []
        self._parse(data)

    def isValid(self):
        if self.digits:
                self._validate()
        return self.valid

    def _parse(self, data):
        if len(data) == self.NUMBER_OF_DIGITS:
            for c in data:
                if c.isdigit():
                    self.digits.append(int(c))
            if len(self.digits) != self.NUMBER_OF_DIGITS:
                self.digits = []

    def _all_digits_are_equal(self):
        first_digit = self.digits[0]
        for digit in self.digits:
                if first_digit != digit:
                        return False
        return True

    def _calc_check_digit(self, digits, weighs):
        sum = 0
        for i in range(len(digits)):
                sum += digits[i] * weighs[i]

        rest = 11 - (sum % 11)
        if( rest == 10 or rest == 11):
                rest = 0
        return rest

    def _validate(self):
        first_cpf_weighs = [10, 9, 8, 7, 6, 5, 4, 3, 2]
        second_cpf_weighs = [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]
        first_cd = self.digits[9]
        second_cd = self.digits[10]

        if not self._all_digits_are_equal():
                self.valid = (first_cd == self._calc_check_digit(self.digits[:9], first_cpf_weighs) and
                                second_cd == self._calc_check_digit(self.digits[:10], second_cpf_weighs))

#FIX ME
class CNPJValidator(object):

    NUMBER_OF_DIGITS = 14

    def __init__(self, data):
        self.valid = False
        self.digits = []
        self._parse(data)

    def isValid(self):
        if self.digits:
                self._validate()
        return self.valid

    def _parse(self, data):
        if len(data) == self.NUMBER_OF_DIGITS:
            for c in data:
                if c.isdigit():
                    self.digits.append(int(c))
            if len(self.digits) != self.NUMBER_OF_DIGITS:
                self.digits = []

    def _all_digits_are_equal(self):
        first_digit = self.digits[0]
        for digit in self.digits:
                if first_digit != digit:
                        return False

    def _calc_check_digit(self, digits, weight):
        sum = 0
        for i in range(len(digits)):
                sum += digits[i] * weight[i]

        rest = 11 - (sum % 11)
        if(rest == 10 or rest == 11):
            rest = 0
        return rest

    def _validate(self):
        first_weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        second_weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

        first_cd = self.digits[12]
        second_cd = self.digits[13]

        if not self._all_digits_are_equal():
                self.valid = (first_cd == self._calc_check_digit(self.digits[:12], first_weights) and
                                second_cd == self._calc_check_digit(self.digits[:13], second_weights))
