from segue.factory import Factory

from models import Account, ResetPassword

import schema

class AccountFactory(Factory):
    model = Account

    UPDATE_WHITELIST = schema.signup["properties"].keys()
    ITEMS_TO_REMOVE = ['type', 'password_confirm', 'email_confirm']

    @classmethod
    def clean_for_insert(cls, data):
        for item in AccountFactory.ITEMS_TO_REMOVE:
            if item in data:
                data.pop(item)
        data['document'] = data.pop('cpf', None) or data.pop('passport', None) or data.pop('document', None) or data.pop('cnpj', None)
        return data

    @classmethod
    def clean_for_update(cls, data):
        #TODO: FIX
        update_whitelist = AccountFactory.UPDATE_WHITELIST[:]
        data['document'] = data.pop('cpf', None) or data.pop('passport', None) or data.pop('cnpj', None) or data.pop('document', None)
        update_whitelist.remove('email')
        data = { c:v for c,v in data.items() if c in update_whitelist }
        return data


class ResetPasswordFactory(Factory):
    model = ResetPassword

    @classmethod
    def create(cls, account, hash_code):
        reset = cls.model()
        reset.account = account
        reset.hash    = hash_code
        return reset
