from segue.core import db
from segue.filters import FilterStrategies
from models import PromoCode
from segue.account.models import Account

class PromoCodeFilterStrategies(FilterStrategies):
    def by_hash_code(self, value, as_user=None):
        return PromoCode.hash_code.ilike("%"+value+"%")

    def by_used(self, value, as_user=None):
        if not isinstance(value, bool): return None
        if value:
            return PromoCode.payment != None
        return PromoCode.payment == None

    def by_description(self, value, as_user=None):
        return PromoCode.description.ilike("%"+value+"%")

    def by_creator_id(self, value, as_user=None):
        if not isinstance(value, int): return None
        return PromoCode.creator_id==value

    #TODO: REMOVE FOR FRONTDESK
    def by_purchase_id(self, value, as_user=None):
        from segue.purchase.models import Purchase
        if not isinstance(value, int): return None
        customer_id = db.session.query(Purchase.customer_id).filter(Purchase.id == value).subquery()
        return PromoCode.creator_id == customer_id
