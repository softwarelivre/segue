# -*- coding: utf-8 -*-

from segue.babel import _l
from segue.errors import SegueError, SegueFieldError, FieldError, SegueGenericError

class PaymentVerificationFailed(SegueError):
    code = 500
    def to_json(self):
        return { 'message': 'the fetching notification data from payment provider failed' }

class PurchaseAlreadySatisfied(SegueError):
    code = 400;
    def to_json(self):
        return { 'message': 'this purchase has already been paid completely' }

class NoSuchPayment(SegueError):
    code = 404
    def to_json(self):
        return { 'message': 'notification was sent to an invalid payment' }

class NoSuchPurchase(SegueError):
    code = 404
    def to_json(self):
        return { 'message': 'no such purchase' }

class PurchaseIsStale(SegueError):
    code = 404
    def to_json(self):
        return { 'message': 'this purchase is stale and cannot be paid' }

class InvalidPaymentNotification(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'the notification data from payment provider is not correct for this payment method' }

class InvalidHashCode(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'invalid hash code: {}'.format(self.args) }

class MustProvideDescription(SegueGenericError):
    MESSAGE = 'please provide promocode description'
    
class MustDefineCreator(SegueGenericError):
    MESSAGE = 'You must provide the creator id'

class PromoCodeAlreadyUsed(SegueGenericError):
    MESSAGE = 'This promocode is already used'

class InvalidZipCodeNumber(FieldError):
    FIELD = 'address_zipcode'
    MESSAGE = _l('Invalid Zip Code number')

class InvalidCPF(FieldError):
    FIELD = 'cpf'
    MESSAGE = _l('Invalid CPF number')

class InvalidCNPJ(FieldError):
    FIELD = 'cnpj'
    MESSAGE = _l('Invalid CNPJ number')

class DocumentIsNotDefined(SegueError):
    code = 400
    def to_json(self):
        return {'message': _l('You must define a document number')}

class StudentDocumentIsNotDefined(SegueError):
    code = 400
    def to_json(self):
        return {'message': _l('You must define a student document')}


class GovDocumentIsNotDefined(SegueError):
    code = 400
    def to_json(self):
        return {'message': _l('You must define the governament document')}


class StudentDocumentIsInvalid(SegueError):
    code = 400

    def __init__(self, document):
        self.document = document

    def to_json(self):
        return {'message': _l('The student document {} is not valid'.format(self.document))}


class BlockedDiscount(SegueError):
    code = 400;
    def to_json(self):
        return { 'message': 'Este código promocional não consede 100% de desconto!' }