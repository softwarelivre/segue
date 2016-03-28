from models import Account
from segue.purchase.models import Purchase
from segue.filters import FilterStrategies

class AccountFilterStrategies(FilterStrategies):

    def by_id(self, value):
        return Account.id == value

    def by_email(self, value):
        return Account.email.ilike('%'+value+'%')

    def by_name(self, value):
        return Account.name.ilike('%'+value+'%')

    def by_document(self, value):
        return Account.document.like('%'+value+'%')

    def by_product_id(self, value):
        return Purchase.product_id == value

    def by_purchase_id(self, value):
        return Purchase.id == value

    def join_for_purchase_id(self, queryset, needle=None):
        return queryset.join('purchases')

    def join_for_product_id(self, queryset, needle=None):
        return queryset.join('purchases')