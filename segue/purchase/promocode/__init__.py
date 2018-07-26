# -*- coding: utf-8 -*-

import datetime
import copy

from requests.exceptions import RequestException

from segue.purchase.errors import InvalidPaymentNotification, NoSuchPayment, MustProvideDescription
from segue.core import db, logger
from segue.hasher import Hasher

from segue.purchase.schema import PromoCodeSchema
from filters import PromoCodeFilterStrategies
from factories import PromoCodeFactory, PromoCodePaymentFactory, PromoCodeTransitionFactory
from models import PromoCode, PromoCodePayment
from segue.purchase.cash import CashPaymentService
from ..errors import InvalidHashCode, MustDefineCreator, PromoCodeAlreadyUsed
from copy import deepcopy

class PromoCodeService(object):
    def __init__(self, hasher=None, products=None, filters=None):
        self.hasher            = hasher  or Hasher(length=10, prefix="PC")
        self.filter_strategies = filters or PromoCodeFilterStrategies()

    def lookup(self, criteria=None, page=1, per_page=25):
        filter_list = self.filter_strategies.given_criteria(**criteria)
        return PromoCode.query.filter(*filter_list).paginate(page=page, per_page=per_page)

    def query(self, **kw):
        base        = self.filter_strategies.joins_for(PromoCode.query, **kw)
        filter_list = self.filter_strategies.given(**kw)
        return base.filter(*filter_list).order_by(PromoCode.id).all()

    def create(self, data, quantity=None, creator=None):
        if not 'description' in data: raise MustProvideDescription()
        if not creator: raise MustDefineCreator()
        
        result = []
        unmodified_description = data['description']
        for counter in range(quantity):
            promocode_data = deepcopy(data)
            promocode_data['description'] = u'{description} - {counter}/{total}'.format(
                description=unmodified_description, counter=counter+1, total=quantity
            )
            
            if not 'hash_code' in data:
                promocode_data['hash_code'] = self.hasher.generate()
             
            p = PromoCodeFactory.from_json(promocode_data, PromoCodeSchema())
            p.creator = creator
            
            
            db.session.add(p)
            result.append(p)
            
        db.session.commit()
        return result

    def check(self, hash_code, by=None):
        logger.info("PromoCodeService.check, hash_code: %s", hash_code)

        for promocode in self.available_promocodes(hash_code):
            if promocode.product.check_eligibility(by):
                return promocode

        return None
    
    def remove(self, promocode):
        
        if not promocode.used:
            db.session.delete(promocode)
            db.session.commit()
        else:
            raise PromoCodeAlreadyUsed()

    def available_promocodes(self, hash_code, by=None):
        promocodes = PromoCode.query.filter(PromoCode.hash_code==hash_code).all()
        available_promocodes = []
        for promocode in promocodes:
            if not promocode.used:
                available_promocodes.append(promocode)

        return available_promocodes
        
    def get_one(self, promocode_id):
        return PromoCode.query.filter(PromoCode.id==promocode_id).first()

class PromoCodePaymentService(object):
    def __init__(self, cash_service=None, promocodes=None, factory=None):
        self.factory  = factory  or PromoCodePaymentFactory()
        self.cash_service = cash_service or CashPaymentService()
        self.promocodes = promocodes or PromoCodeService()

    def create(self, purchase, data=dict(), commit=True, force_product=False):
        hash_code = data.get('hash_code',None)
        if not hash_code: raise InvalidHashCode(hash_code)

        promocode = self.promocodes.check(hash_code, by=purchase.customer)
        if not promocode: raise InvalidHashCode(hash_code)

        if force_product:
            purchase.product = promocode.product
            purchase.amount = promocode.product.price

        payment = self.factory.create(purchase, promocode)
        purchase.recalculate_status()

        db.session.add(purchase)
        db.session.add(payment)
        if commit: db.session.commit()
        return payment

    def process(self, payment):
        # the endpoint is the same of CashPaymentService
        return self.cash_service.process(payment)

    def notify(self, purchase, payment, payload=None, source='notification'):
        pass
