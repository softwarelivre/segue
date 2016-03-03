from segue.core import db
from ..models import Payment, Transition

class PayPalPayment(Payment):
    __mapper_args__ = {'polymorphic_identity': 'paypal'}

    invnum = db.Column(db.String(32), name='pp_invnum')
    correlation_id = db.Column(db.Text, name='pp_correlation_id')
    token = db.Column(db.Text, name='pp_token')

    @property
    def extra_fields(self):
        return dict(invnum=self.invnum, correlation_id=self.correlation_id, token=self.token)


class PayPalPaymentTransition(Transition):
    __mapper_args__ = { 'polymorphic_identity': 'paypal' }

    payload = db.Column(db.Text, name='pp_payload')

