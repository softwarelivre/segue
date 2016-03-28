from segue.filters import FilterStrategies

from models import Purchase, Payment
from segue.account.models import Account

class PurchaseFilterStrategies(FilterStrategies):
    def enforce_user(self, user):
        return self.by_customer_id(user.id)

    def by_id(self, value):
        return Purchase.id == value

    def by_status(self, value):
        return Purchase.status == value

    def by_product_id(self, value):
        return Purchase.product_id == value

    def by_customer_id(self, value, as_user=None):
        return Purchase.customer_id == value

    def by_customer_name(self, value):
        return Account.name.ilike('%' + value + '%')

    def join_for_customer_name(self, queryset, needle=None):
        return queryset.join('customer')

class PaymentFilterStrategies(FilterStrategies):
    def enforce_user(self, user):
        return self.by_customer_id(user.id)

    def by_purchase_id(self, value, as_user=None):
        return Payment.purchase_id == value

    def by_customer_id(self, value, as_user=None):
        return True




