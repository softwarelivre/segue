# -*- coding: utf-8 -*-
import sys, codecs, os
import itertools as it
import requests
import datetime
import tablib
import json
import yaml
import xmltodict
import dateutil.parser

from unidecode import unidecode
from segue.models import *
from segue.core import db
from segue.hasher import Hasher
from support import *

class Correios():
    url = "http://api.postmon.com.br/v1/cep/{}"

    def cep(self, zipcode):
        ret = {}
        if zipcode is not None and zipcode is not 'nulo':
            print "checking zipcode: ", zipcode
            query_url = self.url.format(zipcode)
            result = requests.get(query_url)
            if result.status_code == 200:
                ret = result.json()
            else:
                ret = {}

        return ret

def get_Correios():
    return Correios()

def get_Dataset():
    return tablib.Dataset()

def get_states_cache():
    cache_file = '/tmp/states.cache'

    f_cache_content = codecs.open(cache_file, 'a+')
    if os.path.getsize(cache_file) == 0:
        states_cache = {}
    else:
        states_cache = json.load(f_cache_content)

    f_cache_content.close()
    return states_cache, cache_file

def caravan_report(out_file = "caravan_report"):
    ds = get_Dataset()
    states_cache, cache_file = get_states_cache()
    filename = out_file + "_" + str(datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")) + ".xls"
    print "generating report " + filename
    f = codecs.open('./' + filename,'w')
    ds.headers = ["NOME DA CARAVANA", "NOME DO LIDER", "EMAIL DO LIDER", "CIDADE", "ESTADO"]

    class fakeBuyer(object):
        def __init__(self, city):
            self.address_zipcode = 'NONEXISTENT'
            self.address_city = city

    for caravan in Caravan.query.all():
        buyer = fakeBuyer(caravan.city)

        data_list = [
            caravan.name,
            caravan.owner.name,
            caravan.owner.email,
            caravan.city,
            guess_state(buyer, states_cache)
        ]
        ds.append(data_list)

    print "fechando arquivo..."
    f.write(ds.xls)
    f.close()

    print "done!"


def adempiere_format(initial_date, end_date, out_file="adempiere_export"):
    extension = ".txt"
    filename = out_file + "_" + str(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) + extension
    print "generating report " + filename
    f = codecs.open('./' + filename, 'w', 'utf-8')
    ds = []

    exclude_categories = ['donation']
    purchases = Purchase.query \
        .join('product') \
        .filter(Purchase.status == 'paid')\
        .filter(Product.category.notin_(exclude_categories))\
        .order_by(Purchase.id)\
        .all()

    for purchase in purchases:
        account = purchase.customer
        buyer = purchase.buyer

        finished_payments = [payment for payment in purchase.payments if (payment.status in Payment.VALID_PAYMENT_STATUSES)]

        paid_amount = purchase.total_amount
        payments = []
        for payment in finished_payments:
            if hasattr(payment, 'promocode') and payment.promocode:
                paid_amount -= payment.paid_amount
            else:
                payments.append(payment)

        #free fries = exclude from report
        if not paid_amount:
            #print("Free purchase id {} skipping".format(purchase.id))
            continue

        if len(payments) > 1:
            print('More than one payment for purchase id {}. Skipping'.format(purchase.id))
            continue

        transaction_date = get_transition_date(payments[0])

        initial = datetime.datetime.strptime(initial_date, '%Y-%m-%d')
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        transaction = datetime.datetime(transaction_date.year, transaction_date.month, transaction_date.day)
        if not (initial <= transaction <= end):
            continue

        print('Including purchase id {} transaction date {}'.format(purchase.id, transaction_date))

        data = {
            'purchase_id': purchase.id,
            'buyer_email': account.email,
            'buyer_name': buyer.name,
            'buyer_phone': buyer.contact,
            'buyer_document': buyer.document,
            'buyer_address_street': buyer.address_street,
            'buyer_address_number': buyer.address_number,
            'buyer_address_extra': buyer.address_extra,
            'buyer_address_city': buyer.address_city,
            'buyer_address_zipcode': buyer.address_zipcode,
            'buyer_address_state': buyer.address_state,
            'buyer_address_neighborhood': buyer.address_neighborhood,
            'purchase_category': get_category(purchase.product.category),
            'purchase_type': payment.type,
            'purchase_qty': purchase.qty,
            'paid_amount': paid_amount,
            'transaction_date': transaction_date,
            'bo_our_number': get_our_number(payment),
        }

        ds.append(data)

    print "fechando arquivo..."
    f.write(adempiere_filter(ds))
    f.close()


def adempiere_filter(data):
    content = u""

    for d in data:
        purchase_id = d['purchase_id']
        cpf = format_document(d['buyer_document']) or 'nulo'
        cnpj = format_document(d['buyer_document'], type='CNPJ') or 'nulo'
        name = d['buyer_name']
        email = d['buyer_email']
        phone_1 = d['buyer_phone'] or 'nulo'
        phone_2 = 'nulo'
        zipcode = d['buyer_address_zipcode'] or 'nulo'
        state = d['buyer_address_state'] or 'nulo'
        city = d['buyer_address_city'] or 'nulo'
        address = d['buyer_address_street']
        address_number = d['buyer_address_number'] or 'nulo'
        address_extra = d['buyer_address_extra'] or 'nulo'
        address_district = d['buyer_address_neighborhood'] or 'nulo'

        quantity = d['purchase_qty']
        amount = d['paid_amount']
        ticket_type = d['purchase_category']

        discount = "0"
        client_type = 'PF'
        if cnpj != 'nulo':
            client_type = 'PJ'

        description = get_description(ticket_type, quantity, purchase_id)
        content += u'{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ{}þ'.format(
            purchase_id, client_type, cpf, cnpj, name, email, format_phone(phone_1), format_phone(phone_2),
            format_cep(zipcode), state, city, address, address_number, address_district, address_extra,
            quantity, amount, discount
        )
        content += unicode(description, 'utf-8')
        content += '\n'

    return content

def get_description(category, quantity, number):
    first_paragraph = '{:0>2d} inscrição categoria {} para o 17º Fórum Internacional Software Livre, a realizar-se de 13 a 16 de julho de 2016, no Centro de Eventos da PUC, em Porto Alegre/RS. * * *'.format(quantity, category)
    second_paragraph = 'Inscrição nº {}. * * *'.format(number)
    third_paragraph = 'A Associação Software Livre.Org declara para fins de não incidência na fonte do IRPJ, da CSLL, da COFINS e da contribuição para PIS/PASEP ser associação sem fins lucrativos, conforme art. 64 da Lei nº 9.43 0/1996 e atualizações e Instrução Normativa RFB nº 1.234/2012. * * *'
    forth_paragraph = 'Tributos: ISS 5% + COFINS 7,6% = 12,6%.'
    text = first_paragraph + second_paragraph + third_paragraph + forth_paragraph
    return text

def format_phone(value):
    if len(value) < 10:
        return 'nulo'

    suffix_len = len(value) - 2
    f = '{}{}-' + '{}' * suffix_len

    return f.format(*list(value))

def format_cep(value):
    #possibilites:
        #None
        #formatted
        #not formatted
    if len(value) == 9:
        return value
    if len(value) == 8:
        return "{}{}{}{}{}-{}{}{}".format(*list(value))
    else:
        return "nulo"


def get_district(zipcode, states_cache):
    c = get_Correios()
    if zipcode in states_cache.keys():
        return states_cache[zipcode]['estado']
    else:
        result = c.cep(zipcode)
        if 'bairro' in result:
            states_cache[zipcode] = { 'estado': result['estado'], 'bairro': result['bairro'] }

    return result['bairro'] if 'bairro' in result else "CENTRO"

def format_document(value, type="CPF"):
    #possibilites:
        #None
        #formatted
        #not formatted
    if type == "CPF" and value and len(value) == 11:
        return "{}{}{}.{}{}{}.{}{}{}-{}{}".format(*list(value))
    elif type == 'CNPJ' and len(value) == 14:
        return "{}{}.{}{}{}.{}{}{}/{}{}{}{}-{}{}".format(*list(value))
    else:
        return "nulo"

def get_transition_date(payment):
    transition = [transition for transition in payment.transitions
                  if (transition.new_status in Payment.VALID_PAYMENT_STATUSES and
                      transition.old_status not in Payment.VALID_PAYMENT_STATUSES)][0]
    if payment.type == 'paypal':
        return transition.created
    if payment.type == 'pagseguro':
        return get_date_pagseguro(transition)
    elif payment.type == 'boleto':
        if hasattr(transition, 'payment_date'):
            return transition.payment_date
        else:
            return transition.created
    else:
        return transition.created

def get_date_pagseguro(transition):
    pagseguro_data = xmltodict.parse(transition.payload)
    date = dateutil.parser.parse(pagseguro_data['transaction']['lastEventDate'])
    naive = date.replace(tzinfo=None)
    return naive

def guess_state(buyer, states_cache):
    c = get_Correios()
    if buyer.address_zipcode in states_cache.keys():
        return states_cache[buyer.address_zipcode]['estado']
    else:
        result = c.cep(buyer.address_zipcode)
        bairro = ''
        if 'estado' in result:
            if 'bairro' in result:
                bairro = result['bairro']
            states_cache[buyer.address_zipcode] = { 'estado': result['estado'], 'bairro': bairro }
            return result['estado']
        else:
            found = City.query.filter_by(name = strip_accents(buyer.address_city.upper())).all()
            if len(found):
                states_cache[buyer.address_zipcode] = { 'estado': found[0].state, 'bairro': bairro }
                return found[0].state
            else:
                return ""

def strip_accents(item):
    return unidecode(item)

def get_category(name):
    if name == 'normal':
        return 'individual'
    elif name == 'student':
        return 'estudante'
    elif name == 'caravan':
        return 'caravanista'
    elif name == 'caravan-rider':
        return 'caravana'
    elif name == 'business':
        return 'corporativa'
    elif name == 'government':
        return 'empenho'
    elif name == 'foreigner':
        return 'estrangeiro'
    else:
        return "Tipo de ingresso desconhecido"

def get_our_number(payment):
    return payment.our_number if getattr(payment, 'our_number', None) is not None else ''
