# -*- coding: utf-8 -*-

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from ..core import logger
from ..core import db
from ..hasher import Hasher

from segue.errors import SegueGenericError
from segue.babel import _l
from segue.validation import CNPJValidator, CPFValidator, DateValidator, ZipCodeValidator
from segue.mailer import MailerService
from ..filters import FilterStrategies

from jwt import Signer

from models import Account, ResetPassword
from factories import AccountFactory, ResetPasswordFactory
from filters import AccountFilterStrategies
from errors import InvalidLogin, EmailAlreadyInUse, NotAuthorized, NoSuchAccount, InvalidResetPassword, CertificateNameAlreadySet
from errors import InvalidDocumentNumber, InvalidDateFormat, PasswordMismatch, EmailMismatch, DocumentAlreadyExist, DocumentIsNotDefined, InvalidZipCodeNumber


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

    #TODO: REMOVE
    def modify(self, account_id, data, by=None, allow_email_change=False):
        try:
            account = self._get_account(account_id)
            if not self.check_ownership(account, by): raise NotAuthorized

            if allow_email_change:
                self.try_to_change_email(account, data.get('email', account.email))

            password = data.get('password', '')
            password_confirm = data.pop('password_confirm', '')
            for name, value in AccountFactory.clean_for_update(data).items():
                setattr(account, name, value)

            self._validate(account, password, password_confirm)
            account.dirty = False

            if not account.document: raise DocumentIsNotDefined()
            db.session.add(account)
            db.session.commit()
            return account
        except IntegrityError as e:
            #TODO: IMPROVE psycopg2.IntegrityError
            if 'account_email_UK' in e.orig.pgerror:
                #TODO: CREATE EXCEPTION
                raise SegueGenericError(_l('This e-mail is already in use'))
            if 'account_document_UK' in e.orig.pgerror:
                raise SegueGenericError(_l('This number document is already in use'))

    #TODO: RENAME
    def modify_from_admin(self, account_id, data, by=None, allow_email_change=False):
        try:
            account = self._get_account(account_id)
            if not self.check_ownership(account, by):
                raise NotAuthorized

            if allow_email_change:
                self.try_to_change_email(account, data.get('email', account.email))

            account = AccountFactory.update_model(
                account,
                data,
                schema.whitelist['admin_edit'])

            account.dirty = False
            if not account.document: raise DocumentIsNotDefined()
            db.session.add(account)
            db.session.commit()
            return account
        except IntegrityError as e:
            #TODO: IMPROVE psycopg2.IntegrityError
            if 'account_email_UK' in e.orig.pgerror:
                #TODO: CREATE EXCEPTION
                raise SegueGenericError(_l('This e-mail is already in use'))
            if 'account_document_UK' in e.orig.pgerror:
                raise SegueGenericError(_l('This number document is already in use'))


    def lookup(self, needle, by=None, limit=0):
        #TODO: IMPROVE THIS FUNCTION
        base    = self.filters.all_joins(Account.query, needle)
        filters = self.filters.needle(needle, by)
        queryset = base.filter(or_(*filters))
        if limit:
            return queryset.limit(limit).all()
        else:
            return queryset.all()

    def check_ownership(self, account, alleged):
        if isinstance(account, int): account = self._get_account(id)
        return account and account.can_be_acessed_by(alleged)

    #TODO: RENAME
    def create_from_admin(self, data, rules='signup'):
        try:
            role = 'user'
            if 'cnpj' in data:
                role = 'corporate'
            if 'passport' in data:
                role = 'foreign'

            account = AccountFactory.from_json(data, schema.whitelist[rules])
            account.role = role

            if not account.document: raise DocumentIsNotDefined()
            if not account.password: account.password = self.hasher.generate()
            db.session.add(account)
            db.session.commit()
            return account
        except IntegrityError as e:
            #TODO: IMPROVE psycopg2.IntegrityError
            #TODO: CREATE EXCEPTION
            if 'account_email_UK' in e.orig.pgerror:
                raise SegueGenericError(_l('This e-mail is already in use'))
            if 'account_document_UK' in e.orig.pgerror:
                raise SegueGenericError(_l('This number document is already in use'))

    #TODO: REMOVE
    def create(self, data, rules='signup'):
        try:
            password = data.get('password', '')
            password_confirm = data.pop('password_confirm', None)
            email_confirm = data.pop('email_confirm', '')


            role = 'user'
            if 'cnpj' in data:
                role = 'corporate'
                rules = 'corporate'
            if 'passport' in data:
                role = 'foreign'

            account = AccountFactory.from_json(data, schema.whitelist[rules])
            account.role = role

            self._validate(account, password, password_confirm, email_confirm)

            if not account.password: account.password = self.hasher.generate()
            db.session.add(account)
            db.session.commit()
            return account
        except IntegrityError as e:
            #TODO: IMPROVE psycopg2.IntegrityError
            if 'account_email_UK' in e.orig.pgerror:
                raise EmailAlreadyInUse(account.email)
            if 'account_document_UK' in e.orig.pgerror:
                raise DocumentAlreadyExist(account.email)

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

    #TODO: REMOVE
    def _validate(self, account, password, password_confirm, email_confirm=None):

        if password != password_confirm:
            raise PasswordMismatch('password does not match')

        if email_confirm and (account.email != email_confirm):
            raise EmailMismatch(email_confirm)

        if account.role == 'corporate':
            if not CNPJValidator(account.document).is_valid():
                raise InvalidDocumentNumber(account.document)
        else:
            if account.is_brazilian and not CPFValidator(account.document).is_valid():
                raise InvalidDocumentNumber(account.document)
            if not DateValidator(account.born_date).is_valid():
                raise InvalidDateFormat(account.born_date)

        if account.is_brazilian:
            if not ZipCodeValidator(account.address_zipcode).is_valid():
                raise InvalidZipCodeNumber(account.address_zipcode)
