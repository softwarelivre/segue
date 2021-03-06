from segue.responses import BaseResponse
from segue.frontdesk.models import Badge


class PersonResponse(BaseResponse):
    def __init__(self, person, embeds=False, links=True):
        self.id                 = person.id
        self.customer_id        = person.customer_id
        self.role               = person.role
        self.name               = person.name
        self.email              = person.email
        self.phone              = person.phone

        self.city                 = person.city
        self.country              = person.country
        self.address_state        = person.address_state
        self.address_neighborhood = person.address_neighborhood
        self.address_street       = person.address_street
        self.address_number       = person.address_number
        self.address_extra        = person.address_extra
        self.address_zipcode      = person.address_zipcode

        self.document           = person.document
        self.category           = person.category
        self.price              = person.price
        self.status             = person.status
        self.kind               = person.kind
        self.badge_name         = person.badge_name
        self.badge_corp         = person.badge_corp
        self.is_brazilian       = person.is_brazilian
        self.reception_desk     = person.reception_desk

        self.product_description   = person.product_description
        self.is_corporate          = person.is_corporate
        self.related_count         = person.related_count
        self.has_valid_ticket      = person.is_valid_ticket
        self.has_promocode         = person.has_promocode
        self.can_change_product    = person.can_change_product
        self.outstanding_amount    = person.outstanding_amount
        self.has_payable_ticket    = person.has_payable_ticket

        self.can_change_badge_corp = person.can_change_badge_corp

        self.donation_promocodes = DonationPromocode.create(person.donation_promocodes)

        if embeds:
            self.payments   = PaymentResponse.create(person.purchase.valid_payments.all())
            self.product    = ProductResponse.create(person.purchase.product)
            self.last_badge = BadgeResponse.create(person.last_badge)

        if links:
            self.add_link('related',  person.related_count,     'fd.person.related',  person_id=person.id)
            self.add_link('buyer',    person.buyer,             'fd.person.buyer',    person_id=person.id)
            self.add_link('eligible', -1,                       'fd.person.eligible', person_id=person.id)


class EmployeerResponse(BaseResponse):

    def __init__(self, account):
        self.account_id     = account.id
        self.name           = account.name
        self.document       = account.document
        self.incharge_name  = account.corporate_owned.incharge_name
        self.phone          = account.phone
        self.incharge_email = account.email

class EmployeeResponse(BaseResponse):

    def __init__(self, payment, embeds=True):
        self.account_id  = payment.purchase.customer_id
        self.purchase_id = payment.purchase.id
        self.name        = payment.purchase.customer.name
        self.document    = payment.purchase.customer.document
        self.hash_code   = payment.promocode.hash_code

        if embeds:
            self.last_badge = BadgeResponse.create(payment.purchase.badges.order_by(Badge.created.desc()).first())



class BadgeResponse(BaseResponse):
    def __init__(self, badge):
        self.id      = badge.id
        self.prefix  = badge.prefix
        self.name    = badge.name
        self.corp    = badge.organization
        self.printer = badge.printer
        self.was_ok  = badge.was_ok
        self.given   = badge.given

class VisitorResponse(BaseResponse):
    def __init__(self, visitor):
        self.id     = visitor.id
        self.name   = visitor.name
        self.email  = visitor.email

class ReceptionResponse(PersonResponse):
    def __init__(self, person):
        super(ReceptionResponse, self).__init__(person, embeds=True, links=False)
        self.buyer = BuyerResponse.create(person.buyer)

class PurchaseResponse(BaseResponse):
    def __init__(self, person, embeds=False, links=True):
        self.id          = person.id
        self.name        = person.customer.name
        self.category    = person.product.category
        self.price       = person.product.price
        self.description = person.product.description

class PaymentResponse(BaseResponse):
    def __init__(self, payment, transitions=False, person=False):
        self.id     = payment.id
        self.type   = payment.type
        self.amount = payment.amount
        self.status = payment.status

        if person:
            self.person = PurchaseResponse.create(payment.purchase)

        if transitions:
            self.transitions = PaymentTransitionResponse.create(payment.transitions.all())
            self.created = self.transitions[0].created if self.transitions else None
        else:
            setattr(self, payment.type, payment.extra_fields)

class PaymentTransitionResponse(BaseResponse):
    def __init__(self, transition):
        self.id         = transition.id
        self.created    = transition.created
        self.old_status = transition.old_status
        self.new_status = transition.new_status
        for key, value in transition.extra_fields.items():
            setattr(self, key, value)

class BuyerResponse(BaseResponse):
    def __init__(self, buyer):
        self.id              = buyer.id
        self.kind            = buyer.kind
        self.name            = buyer.name
        self.document        = buyer.document
        self.contact         = buyer.contact
        self.address_street  = buyer.address_street
        self.address_number  = buyer.address_number
        self.address_extra   = buyer.address_extra
        self.address_zipcode = buyer.address_zipcode
        self.address_neighborhood = buyer.address_neighborhood
        self.address_city    = buyer.address_city
        self.address_state   = buyer.address_state
        self.address_country = buyer.address_country

class ProductResponse(BaseResponse):
    def __init__(self, product):
        self.id                = product.id
        self.kind              = product.kind
        self.category          = product.category
        self.public            = product.public
        self.price             = product.price
        self.sold_until        = product.sold_until
        self.description       = product.description
        self.is_promo          = product.is_promo
        self.is_speaker        = product.is_speaker
        self.gives_kit         = product.gives_kit
        self.can_pay_cash      = product.can_pay_cash
        self.original_deadline = product.original_deadline


class DonationPromocode(BaseResponse):
    def __init__(self, promocode):
        self.hash_code = promocode.hash_code
        self.used      = promocode.used

#TODO: REMOVE
class PromoCodeResponse(BaseResponse):
    def __init__(self, promocode):
        self.id             = promocode.id
        self.creator_id     = promocode.creator.id
        self.product_id     = promocode.product.id
        self.used           = promocode.used
        self.discount       = promocode.discount
        self.description    = promocode.description
        self.hash_code      = promocode.hash_code


