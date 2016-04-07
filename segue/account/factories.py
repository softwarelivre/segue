from segue.factory import Factory

from models import Account, ResetPassword

import schema

class AccountFactory(Factory):
    model = Account
    #TODO: HACK REMOVE INCHARGE
    ITEMS_TO_REMOVE = ['type', 'password_confirm', 'email_confirm', 'incharge']

    @classmethod
    def clean_for_insert(cls, data):
        for item in AccountFactory.ITEMS_TO_REMOVE:
            if item in data:
                data.pop(item)
        data['document'] = data.pop('cpf', None) or data.pop('passport', None) or data.pop('cnpj', None)
        return data

    @classmethod
    def clean_for_update(cls, data):
        for item in AccountFactory.ITEMS_TO_REMOVE:
            if item in data:
                data.pop(item)
        data['document'] = data.pop('cpf', None) or data.pop('passport', None) or data.pop('cnpj', None)
        return data


class ResetPasswordFactory(Factory):
    model = ResetPassword

    @classmethod
    def create(cls, account, hash_code):
        reset = cls.model()
        reset.account = account
        reset.hash    = hash_code
        return reset
