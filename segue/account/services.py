# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_,and_

from ..core import logger
from ..core import db
from ..hasher import Hasher

from segue.errors import SegueGenericError
from segue.babel import _l
from segue.mailer import MailerService
from ..filters import FilterStrategies

from jwt import Signer

from models import Account, ResetPassword
from factories import AccountFactory, ResetPasswordFactory
from filters import AccountFilterStrategies
from errors import InvalidLogin, EmailAlreadyInUse, NotAuthorized, NoSuchAccount, InvalidResetPassword, CertificateNameAlreadySet
from errors import DocumentAlreadyExist, DocumentIsNotDefined


import schema

class AccountService(object):
    def __init__(self, db_impl=None, signer=None, mailer=None, hasher=None):
        self.db     = db_impl or db
        self.mailer = mailer or MailerService()
        self.signer = signer or Signer()
        self.hasher = hasher or Hasher()
        self.filters = AccountFilterStrategies()

    def set_certificate_name(self, account_id, new_name, by=None):
        account = self.get_one(account_id, by, strict=True)
        if account.certificate_name: raise CertificateNameAlreadySet()

        account.certificate_name = new_name
        db.session.add(account)
        db.session.commit()

        return account

    def by_range(self, start, end):
        return Account.query.filter(Account.id.between(start, end)).order_by(Account.id)

    def create_for_email(self, email, commit=False):
        if self.is_email_registered(email): raise EmailAlreadyInUse(email)
        account = Account(email=email)
        account.password = self.hasher.generate()
        db.session.add(account)
        if commit: db.session.commit()
        return account

    def is_email_registered(self, email):
        return Account.query.filter(Account.email == email).count() > 0

    def get_by_email(self, email):
        return Account.query.filter(Account.email == email).first()

    def try_to_change_email(self, account, new_email):
        if account.email == new_email:
            return account
        if self.is_email_registered(new_email):
            raise EmailAlreadyInUse(new_email)

        account.email = new_email
        return account

    def get_one(self, account_id, by=None, check_ownership=True, strict=False):
        account = self._get_account(account_id)
        if check_ownership and not self.check_ownership(account, by): raise NotAuthorized
        if strict and not account: raise NoSuchAccount()
        return account

    def _get_account(self, id):
        return Account.query.get(id)

    def migrate_role(self, account_id, new_role):
        account = self.get_one(account_id, strict=True, check_ownership=False)
        account.role = new_role
        db.session.add(account)
        db.session.commit()
        db.session.expunge(account)
        db.session.close()

        return self.get_one(account_id, strict=True, check_ownership=False)

    def modify(self, account_id, data, by=None, allow_email_change=False):
        account = self._get_account(account_id)
        if not self.check_ownership(account, by): raise NotAuthorized
        #TODO: IMPROVE RULE SELECTION
        rule = 'edit_account'
        if account.role == 'corporate':
            rule = 'edit_corporate'

        if allow_email_change:
            self.try_to_change_email(account, data.get('email', account.email))

        account = AccountFactory.update_model(account, data, schema.whitelist[rule])
        account.dirty = False

        if not account.document: raise DocumentIsNotDefined()

        return self._create_or_update(account)

    def lookup(self, criteria=None, by=None, limit=0):
        #TODO: IMPROVE THIS FUNCTION
        base = self.filters.joins_for(Account.query, **criteria)
        filters = self.filters.given_criteria(**criteria)
        queryset = base.filter(and_(*filters))

        if limit:
            queryset = queryset.limit(limit)

        return queryset.all()

    def check_ownership(self, account, alleged):
        if isinstance(account, int): account = self._get_account(id)
        return account and account.can_be_acessed_by(alleged)

    def create(self, data, rules='create_account'):
        #TODO: IMPROVE ROLE AND RULES SELECTION
        role = 'user'
        if 'cnpj' in data:
            role = 'corporate'
            rules = 'create_corporate'
        if 'passport' in data:
            role = 'foreign'

        account = AccountFactory.from_json(data, schema.whitelist[rules])
        account.role = role

        if not account.document: raise DocumentIsNotDefined()
        if not account.password: account.password = self.hasher.generate()

        return self._create_or_update(account)

    def _create_or_update(self, account):
        try:
            db.session.add(account)
            db.session.commit()
            return account
        except IntegrityError as e:
            #TODO: IMPROVE psycopg2.IntegrityError
            if 'account_email_UK' in e.orig.pgerror:
                raise EmailAlreadyInUse()
            if 'account_document_UK' in e.orig.pgerror:
                raise DocumentAlreadyExist()

    def login(self, email=None, password=None, acceptable_roles=None):
        try:
            account = Account.query.filter(Account.email == email).one()
            if account.password != password:
                raise InvalidLogin()
            if acceptable_roles and account.role not in acceptable_roles:
                raise InvalidLogin()
            return self.signer.sign(account)
        except NoResultFound:
            raise InvalidLogin()

    def ask_reset(self, email):
        account = Account.query.filter(Account.email == email).first()
        if not account: raise NoSuchAccount()

        reset = ResetPasswordFactory.create(account, self.hasher.generate())
        self.mailer.reset_password(account, reset)

        db.session.add(reset)
        db.session.commit()

        return reset

    def get_reset(self, account_id, hash_code):
        reset = ResetPassword.query.filter(Account.id == account_id, ResetPassword.hash == hash_code).first()
        if not reset: raise InvalidResetPassword()
        return reset

    def perform_reset(self, account_id, hash_code, new_password):
        reset = self.get_reset(account_id, hash_code)
        if reset.spent: raise InvalidResetPassword()

        reset.spent = True
        reset.account.password = new_password

        db.session.add(reset)
        db.session.add(reset.account)
        db.session.commit()

        return reset
