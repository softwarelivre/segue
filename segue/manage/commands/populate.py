# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from decimal import Decimal
from segue.core import db
from tests.support.factories import *
from segue.models import Account, Proposal, ProposalInvite, Track, Room, Slot, Role
from support import *

def populate(clean=False):
    if clean:
        Payment.query.delete()
        Purchase.query.delete()
        ProposalInvite.query.delete()
        Proposal.query.delete()
        Account.query.delete()
        tracks, products = populate_reference_data(True)

    accounts = [
        ValidAccountFactory.build(password='1234', email='xxxx@sandbox.pagseguro.com.br'),
        ValidAccountFactory.build(password='1234'),
        ValidAccountFactory.build(password='1234'),
    ]
    proposals = [
        ValidProposalFactory.build(owner=accounts[0]),
        ValidProposalFactory.build(owner=accounts[0]),
        ValidProposalFactory.build(owner=accounts[1]),
        ValidProposalFactory.build(owner=accounts[1]),
    ]
    proposal_invites = [
        ValidInviteFactory.build(proposal=proposals[0]),
        ValidInviteFactory.build(proposal=proposals[0]),
        ValidInviteFactory.build(proposal=proposals[0]),
    ]
    purchases = [
        ValidPurchaseByPersonFactory.build(product=products[0], customer=accounts[0]),
        ValidPurchaseByPersonFactory.build(product=products[0], customer=accounts[1])
    ]
    payments = [
        ValidPagSeguroPaymentFactory.build(purchase=purchases[0], amount=products[0].price, status='pending'),
        ValidPagSeguroPaymentFactory.build(purchase=purchases[0], amount=products[0].price, status='pending'),
        ValidPagSeguroPaymentFactory.build(purchase=purchases[1], amount=products[1].price, status='paid'),
    ]

    db.session.add_all(accounts)
    db.session.add_all(proposals)
    db.session.add_all(proposal_invites)
    db.session.add_all(purchases)
    db.session.add_all(payments)
    db.session.commit()

def populate_slots(start=0,end=0):
    init_command()
    dates = [ datetime(2017,7,5), datetime(2017,7,6), datetime(2016,7,7), datetime(2016,7,8) ]
    hours = [ 10, 11, 12, 13, 14, 15, 16, 17, 18, 19 ]

    rooms = Room.query.filter(Room.id.between(int(start), int(end))).all()
    for room in rooms:
        print "{}creating slots for room {}{}{}...".format(F.RESET, F.RED, room.name, F.RESET)
        for date in dates:
            for hour in hours:
                slot = Slot()
                slot.room = room
                slot.begins = date + timedelta(hours=hour)
                slot.duration = 60
                db.session.add(slot)
    db.session.commit()

def populate_reference_data(clean=False):
    if clean:
        Track.query.delete()

    tracks   = _build_tracks()
    products = _build_products()
    roles    = _build_roles()

    if not Track.query.all():   db.session.add_all(tracks)
    if not Product.query.all(): db.session.add_all(products)
    if not Role.query.all(): db.session.add_all(roles)

    db.session.commit()
    return tracks, products

def _build_products():
    def _build_one(entry):
        return ValidProductFactory(
            kind='ticket',
            category=entry[0],
            description="Ingresso FISL18 - {} - lote {}".format(entry[1], entry[2]),
            sold_until=entry[3],
            price=Decimal(entry[4])
        )

    data = [
        ("student", "estudante",  1, "2017-03-30 23:59:59", 60 ),
        ("normal",  "individual", 1, "2017-03-30 23:59:59", 120),

        ("student", "estudante",  2, "2017-04-13 23:59:59", 85 ),
        ("normal",  "individual", 2, "2017-04-13 23:59:59", 170),

        ("student", "estudante",  3, "2017-05-11 23:59:59", 110),
        ("normal",  "individual", 3, "2017-05-11 23:59:59", 220),

        ("student", "estudante",  4, "2017-06-08 23:59:59", 135),
        ("normal",  "individual", 4, "2017-06-08 23:59:59", 270),

        ("student", "estudante",  5, "2017-06-30 23:59:59", 160),
        ("normal",  "individual", 5, "2017-06-30 23:59:59", 320),
    ]
    return [ _build_one(x) for x in data ]

def _build_tracks():
    return [
        #Zona Administração
        ValidTrackFactory(name_pt='Administração - Administração de Sistemas',
                          name_en='Administration - Systems Administration'),

        ValidTrackFactory(name_pt='Administração - Bancos de Dados',
                          name_en='Administration - Databases'),

        ValidTrackFactory(name_pt='Administração - Sistemas operacionais',
                          name_en='Administration - Operating Systems'),

        ValidTrackFactory(name_pt='Administração - Segurança',
                          name_en='Administration - Security'),

        #Zona Desenvolvimento
        ValidTrackFactory(name_pt='Desenvolvimento - Ferramentas, Metodologias e Padrões',
                          name_en='Development - Tools, Methodologies and Standards'),

        ValidTrackFactory(name_pt='Desenvolvimento - Gerência de Conteúdo / CMS',
                          name_en='Development - Content Management / CMS'),

        ValidTrackFactory(name_pt='Desenvolvimento - Linguagens de programação',
                          name_en='Development - Programming Languages'),

        #Zona Desktop
        ValidTrackFactory(name_pt='Desktop - Aplicações Desktop',
                          name_en='Desktop - Desktop Applications'),

        ValidTrackFactory(name_pt='Desktop - Multimídia',
                          name_en='Desktop - Multimedia'),

        ValidTrackFactory(name_pt='Desktop - Jogos',
                          name_en='Desktop - Games'),

        ValidTrackFactory(name_pt='Desktop - Distribuições',
                          name_en='Desktop - Distros'),

        #Zona Ecossistema
        ValidTrackFactory(name_pt='Ecossistema - Cultura, Filosofia, e Política',
                          name_en='Ecosystem - Culture, Philosophy, and Politics'),

        ValidTrackFactory(name_pt='Ecossistema - Negócios, Migrações e Casos',
                          name_en='Ecosystem - Business, Migrations and Cases'),

        #Zona Educação
        ValidTrackFactory(name_pt='Educação - Inclusão Digital',
                          name_en='Education - Digital Inclusion'),

        ValidTrackFactory(name_pt='Educação - Educação',
                          name_en='Education - Education'),

        #Zona Encontros Comunitários
        ValidTrackFactory(name_pt='Encontros Comunitários - Principal',
                          name_en='Community Meetings - Main'),

        ValidTrackFactory(name_pt='Encontros Comunitários - ASL',
                          name_en='Community Meetings - ASL'),

        ValidTrackFactory(name_pt='Encontros Comunitários - WSL',
                          name_en='Community Meetings - WSL'),

        #Zona Tópicos Emergentes
        ValidTrackFactory(name_pt='Tópicos Emergentes - Hardware Aberto',
                          name_en='Trending Topics - Open Hardware'),

        ValidTrackFactory(name_pt='Tópicos Emergentes - Dados Abertos',
                          name_en='Trending Topics - Open Data'),

        ValidTrackFactory(name_pt='Tópicos Emergentes - Acesso Aberto',
                          name_en='Trending Topics - Open Access'),

        ValidTrackFactory(name_pt='Tópicos Emergentes - Governança da Internet',
                          name_en='Trending Topics - Internet Governance'),

        ValidTrackFactory(name_pt='Tópicos Emergentes - Privacidade e Vigilância',
                          name_en='Trending Topics - Privacy and Surveillance'),

        ValidTrackFactory(name_pt='Tópicos Emergentes - Energia Livre',
                          name_en='Trending Topics - Free Energy'),
    ]


def _build_roles():
    def create_one(name, description):
        role = Role()
        role.name = name
        role.description = description
        return role

    roles = []

    roles.append(create_one('admin', 'Admin'))
    roles.append(create_one('user', 'User'))
    roles.append(create_one('corporate', 'Corporate'))
    roles.append(create_one('cashier', 'Cachier'))
    roles.append(create_one('frontdesk', 'Frontdesk'))
    roles.append(create_one('foreign', 'Foreign'))

    return roles
