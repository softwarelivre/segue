# -*- coding: utf-8 -*-

from segue.errors import SegueError, SegueFieldError, NotAuthorized, FieldError
from segue.babel import _l

class InvalidResetPassword(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'invalid reset password code' }

class AccountAlreadyHasPurchase(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'this account already has a purchase' }

class NoSuchAccount(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'Esta conta de e-mail não foi encontrada no sistema!' }

class DocumentAlreadyExist(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'Já existe um usuário utilizando esse CPF ou CNPJ no sistema!' }

class DocumentIsNotDefined(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'Por favor defina um documento!' }

class InvalidLogin(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'bad login' }

class CertificateNameAlreadySet(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'cannot change certificate name' }

class EmailAlreadyInUse(SegueFieldError):

    FIELD = 'email'
    LABEL = 'already_in_use'
    MESSAGE = 'this e-mail address is already registered'

    def __init__(self, email):
        super(EmailAlreadyInUse, self).__init__()
        self.value = email


class InvalidZipCodeNumber(FieldError):
    FIELD = 'address_zipcode'
    MESSAGE = _l('Invalid Zip Code number')

class InvalidCPF(FieldError):
    FIELD = 'cpf'
    MESSAGE = _l('Invalid CPF number')

class InvalidCNPJ(FieldError):
    FIELD = 'cnpj'
    MESSAGE = _l('Invalid CNPJ number')

class EmailAddressMisMatch(FieldError):
    FIELD = 'email_confirm'
    MESSAGE = _l('Email does not match')

class PasswordsMisMatch(FieldError):
    FIELD = 'password_confirm'
    MESSAGE = _l('Password does not match')

