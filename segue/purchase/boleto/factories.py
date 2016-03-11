import os.path
from datetime import date, timedelta

from pyboleto.bank.bancodobrasil import BoletoBB
from pyboleto.pdf import BoletoPDF

from segue.factory import Factory
from segue.hasher import Hasher
from ..factories import PaymentFactory, TransitionFactory

from segue.document.services import DocumentService

from models import BoletoPayment, BoletoTransition
from helpers import BoletoConfig

class BoletoPaymentFactory(PaymentFactory):
    model = BoletoPayment

    def __init__(self, hasher=None, boleto_config=None):
        self.hasher = hasher or Hasher()
        self.config = boleto_config or BoletoConfig()

    def create(self, purchase, payment_id, data=None):
        payment = super(BoletoPaymentFactory, self).create(purchase, target_model=self.model, extra_data=data)
        self.config.category = purchase.product.category
        payment.our_number = "{:010d}".format(self.config.OFFSET + payment_id)
        payment.document_hash = self.hasher.generate()
        return payment

class BoletoTransitionFactory(TransitionFactory):
    model = BoletoTransition

    @classmethod
    def create(cls, payment, payload, source):
        transition = TransitionFactory.create(payment, source, target_model=cls.model)
        transition.payment_date = payload['payment_date']
        transition.paid_amount  = payload['amount']
        transition.batch_line   = payload['line']

        if payment.legal_due_date < transition.payment_date:
            transition.new_status = 'pending'
            transition.errors     = 'late-payment'

        elif payment.amount > transition.paid_amount:
            transition.new_status = 'pending'
            transition.errors     = 'insufficient-amount'

        else:
            transition.new_status = 'paid'
            transition.errors     = None

        return transition

class BoletoFactory(object):
    def __init__(self, document_service=None, boleto_config=None):
        self.document_service = document_service or DocumentService()
        self.config = boleto_config or BoletoConfig()
        

    def as_pdf(self, boleto_data, document_hash, dest_dir):
        filename = "boleto-{}.pdf".format(document_hash)
        path = self.document_service.path_for_filename(dest_dir, filename, ensure_viable=True)

        pdf = BoletoPDF(path)
        pdf.drawBoleto(boleto_data)
        pdf.save()
        return filename

    def create(self, payment):
        self.config.category = payment.purchase.product.category

        boleto = BoletoBB(self.config.TIPO_CONVENIO, None)

        boleto.nosso_numero      = payment.our_number
        boleto.convenio          = self.config.CONVENIO
        boleto.numero_documento  = "{}{}".format(boleto.convenio, boleto.nosso_numero)
        boleto.especie_documento = 'DM'

        boleto.carteira          = self.config.CARTEIRA
        boleto.agencia_cedente   = self.config.AGENCIA
        boleto.conta_cedente     = self.config.CONTA # TODO: what about digito-verificador?
        boleto.cedente_documento = self.config.CNPJ
        boleto.cedente_endereco  = self.config.ENDERECO
        boleto.cedente           = self.config.EMPRESA


        boleto.data_vencimento    = payment.due_date
        boleto.data_documento     = date.today()
        boleto.data_processamento = date.today()

        boleto.instrucoes    = self._build_instructions()
        boleto.demonstrativo = self._build_description(payment)
        boleto.sacado        = self._build_sacado(payment)

        boleto.valor_documento = payment.amount
        return boleto

    def _build_description(self, payment):
        return [
            u"produto: {}".format(payment.purchase.description),
            u"titular: {}".format(payment.purchase.customer.name)
        ]

    def _build_sacado(self, payment):
        return [
            payment.purchase.buyer.name,
            payment.purchase.buyer.complete_address,
            payment.purchase.buyer.document
        ]

    def _build_instructions(self):
        return [
            u"****NAO RECEBER APOS VENCIMENTO******",
            u"NAO UTILIZE PAGAMENTO VIA DOC, DEPOSITO OU TRANSFERENCIA."
        ]
