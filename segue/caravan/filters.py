from models import Caravan
from segue.filters import FilterStrategies
from segue.account.models import Account

class CaravanFilterStrategies(FilterStrategies):

    def by_id(self, value):
        return Caravan.id == value

    def by_caravan_name(self, value):
        return Caravan.name.ilike('%'+value+'%')

    def by_owner_name(self, value):
        return Account.name.ilike('%'+value+'%')

    def join_for_owner_name(self, queryset, needle=None):
        return queryset.join('owner')
