# -*- coding: utf-8 -*-
import codecs, os
import datetime
import tablib
import json
import yaml
import codecs

from segue.core import db
from segue.hasher import Hasher
from segue.models import *
from segue.product.services import ProductService
from segue.caravan.services import CaravanService, CaravanInviteService
from segue.account.services import AccountService
from segue.purchase.services import PurchaseService
from segue.purchase.boleto.models import BoletoPayment, BoletoTransition
from segue.mailer import MailerService

ds = tablib.Dataset()

product_service = ProductService()
caravan_service = CaravanService()
caravan_invite_service = CaravanInviteService()
account_service = AccountService()
purchase_service = PurchaseService()
mailer_service = MailerService()

def import_caravan(in_file, caravan_yaml):
    caravan_data = yaml.load(open(caravan_yaml))
    product = product_service.get_product(caravan_data['product_id'])
    product.price = int(caravan_data['price'])
    our_number = caravan_data['our_number']
    payment_date = caravan_data['payment_date']
    caravan_id = caravan_data['caravan_id'] or None
    print "################## IMPORTAR CARAVANA #######################"
    print "Caravana:", caravan_data['caravan_name']
    print "Produto:", product.description, product.price

    with open(in_file, 'r') as f:
        lines = f.readlines()
        #TODO: FIX THIS HACK
        ds.headers = lines.pop(0).replace('\n','').replace('\r','').split(';')

        for line in lines:
            # TODO: FIX THIS HACK
            data = line.replace('\n', '').replace('\r','').decode('utf8').split(';')
            ds.append(data)


    caravan = None
    if caravan_id:
        caravan = Caravan.query.get(caravan_id)

    for item in ds.dict:
        if not caravan:
            caravan_id = get_or_add_caravan(item, caravan_data)
            caravan = Caravan.query.get(caravan_id)
            print "lider da caravana:", item['NOME COMPLETO'], item['EMAIL']

            #add_leader_exemption(caravan, product, item, our_number, payment_date)
        else:
            account = get_or_add_account(item)
            print "convidado da caravana: ", account.email
            add_caravan_rider(caravan, account)
            add_rider_purchase_and_payment(product, account, caravan, item, our_number, payment_date)

    print "####################### DONE! #############################"


def get_or_add_caravan(item, caravan_data):
    is_owner_registered = account_service.is_email_registered(item['EMAIL'])
    if is_owner_registered:
        caravan_owner = Account.query.filter(Account.email == item['EMAIL']).one()
        caravan = Caravan.query.filter(Caravan.owner_id == caravan_owner.id).first()
        if caravan:
            return caravan.id
        else:
            caravan = add_caravan(caravan_data, caravan_owner)
    else:
        account = get_or_add_account(item)
        caravan = add_caravan(caravan_data, account)

    return caravan.id

def add_caravan(caravan_data, account):
    data = {
        'name': caravan_data['caravan_name'],
        'city': caravan_data['caravan_city'],
        'description': caravan_data['caravan_description']
    }
    return caravan_service.create(data, account)

def get_or_add_account(item):
    h = Hasher(10)
    password = h.generate();

    account_data = {
        'role': 'user',
        'name': item['NOME COMPLETO'],
        'badge_name':item['NOME PARA O CRACHA'],
        'email': item['EMAIL'],
        'email_confirm': item['EMAIL'],

        'cpf': str(item['CPF']).translate(None, './-'),
        'sex': item['SEXO'],
        'born_date': item['DATA DE NASCIMENTO'],
        'membership': False,
        'disability': 'none',
        'education': 'graduation_incomplete',
        'occupation': 'student',
        'country': 'BRASIL',
        'address_state': item['ESTADO'].strip(),
        'city': item['CIDADE'].strip(),
        'address_neighborhood': item['BAIRRO'],
        'address_street': item['ENDERECO'],
        'address_number': item['NUMERO'],
        'address_extra': item['COMPLEMENTO'],
        'address_zipcode': item['CEP'],

        'phone': item['TELEFONE'],

        'password': password,
        'password_confirm': password,
    }

    if account_service.is_email_registered(account_data['email']):
        return Account.query.filter(Account.email == account_data['email']).one()
    else:
        return account_service.create(account_data)

def add_leader_exemption(caravan, product, owner_data, our_number, payment_date):
    # verify if the account already has a leader exemption
    leader_account = get_or_add_account(owner_data)
    if not leader_account.has_valid_purchases:
        # creates fake purchase for the caravan leader
        buyer_data = {
            'kind': 'person',
            'name': owner_data['NOME COMPLETO'],
            'cpf': owner_data['CPF'],
            'contact': owner_data['NOME COMPLETO'],
            'address_country': 'BRASIL',
            'address_state': owner_data['ESTADO'],
            'address_city': owner_data['CIDADE'],
            'address_neighborhood': owner_data['BAIRRO'],
            'address_street': owner_data['ENDERECO'],
            'address_number': owner_data['NUMERO'],
            'address_extra': owner_data['COMPLEMENTO'],
            'address_zipcode': owner_data['CEP'],
        }

        purchase = purchase_service.create(buyer_data, product, caravan.owner)
        purchase.kind = 'caravan-leader'
        purchase.caravan = caravan
        purchase.status = 'paid'
        db.session.add(purchase)

        payment_data = {
            'type': 'boleto',
            'purchase': purchase,
            'status': 'paid',
            'amount': product.price,
            'our_number': our_number
        }
        leader_payment = BoletoPayment(**payment_data)

        transition_data = {
            'old_status': 'pending',
            'new_status': 'paid',
            'source': 'import_caravan',
            'payment': leader_payment,
            'payment_date': payment_date,
            'paid_amount' : product.price
        }
        transition = BoletoTransition(**transition_data)

        db.session.add(leader_payment)
        db.session.add(transition)
        db.session.commit()

        #mailer_service.notify_payment(purchase, leader_payment)

def add_caravan_rider(caravan, account):
    h = Hasher()

    invite_data = {
        'hash': h.generate(),
        'recipient': account.email,
        'name': account.name,
        'status': 'accepted'
    }

    invite = caravan_invite_service.create(caravan.id, invite_data, by=caravan.owner, send_email=False)
    caravan_invite_service.accept_invite(invite.hash, by=account)

def add_rider_purchase_and_payment(product, account, caravan, item, our_number, payment_date):
    if not account.has_valid_purchases:
        # create fake purchase/payment for the caravan rider (account)

        purchase_data = {
            'product': product,
            'amount': product.price,
            'due_date': product.due_date,
            'customer': account,
            'buyer': get_or_add_buyer(item),
            'status': 'paid',
            'caravan': caravan
        }
        rider_purchase = CaravanRiderPurchase(**purchase_data)

        payment_data = {
            'type': 'boleto',
            'purchase': rider_purchase,
            'status': 'paid',
            'amount': product.price,
            'our_number': our_number
        }
        rider_payment = BoletoPayment(**payment_data)

        transition_data = {
            'old_status': 'pending',
            'new_status': 'paid',
            'source': 'import_caravan',
            'payment': rider_payment,
            'payment_date': payment_date,
            'paid_amount' : product.price
        }
        transition = BoletoTransition(**transition_data)

        db.session.add(rider_purchase)
        db.session.add(rider_payment)
        db.session.add(transition)
        db.session.commit()

        #mailer_service.notify_payment(rider_purchase, rider_payment)

def get_or_add_buyer(item):
    buyer_data = {
        'kind': 'person',
        'name': item['NOME COMPLETO'],
        'document': item['CPF'],
        'contact': item['NOME COMPLETO'],
        'address_country': 'BRASIL',
        'address_state': item['ESTADO'],
        'address_city': item['CIDADE'],
        'address_street': item['ENDERECO'],
        'address_number': item['NUMERO'],
        'address_extra': item['COMPLEMENTO'],
        'address_zipcode': item['CEP'],
    }

    buyer = Buyer.query.filter(Buyer.document == buyer_data['document']).first()
    if not buyer:
        buyer = Buyer(**buyer_data)
        db.session.add(buyer)
        db.session.commit()

    return buyer
