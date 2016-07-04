import yaml
import os.path
import glob
import codecs

from segue.errors import SegueError
from segue.core import mailer, config
from flask_mail import Message, Attachment

class EmailIsNotValid(SegueError): pass

class TemplatedMessage(object):
    def __init__(self, template):
        self.template = template
        self.variables = { 'backend_url': config.BACKEND_URL, 'frontend_url': config.FRONTEND_URL }
        self.recipients = []
        self.attachments = []

    def given(self, **args):
        self.variables.update(**args)

    def to(self, name, email):
        self.recipients.append((name, email,))

    def append_attachment(self, attachment_name, file_path, mine_type):
        with open(file_path, 'r') as fp:
            attachment = Attachment(attachment_name, mine_type, fp.read())
            self.attachments.append(attachment)

    def build(self):
        subject = unicode(self.template['subject']).format(**self.variables)
        body    = unicode(self.template['body']).format(**self.variables)
        bcc     = list(config.MAIL_BCC)

        return Message(subject, body=body, recipients=self.recipients, bcc=bcc, attachments=self.attachments)

class MessageFactory(object):
    def __init__(self):
        base = os.path.join(os.path.dirname(__file__), 'templates')
        pattern = os.path.join(base, '**', '*.yml')

        self._templates = {}
        for template_path in glob.glob(pattern):
            template_name = template_path.replace(base, '').replace('.yml','')[1:]
            self._templates[template_name] = yaml.load(codecs.open(template_path))

    def from_template(self, template_name):
        return TemplatedMessage(self._templates[template_name])


class MailerService(object):
    def __init__(self, templates=None, message_factory=None):
        self.message_factory = message_factory or MessageFactory()

    def proposal_invite(self, invite):
        message = self.message_factory.from_template('proposal/invite')
        message.given(invite=invite, proposal=invite.proposal, owner=invite.proposal.owner)
        message.to(invite.name, invite.recipient)

        return mailer.send(message.build())

    def notify_payment(self, purchase):
        customer = purchase.customer
        product  = purchase.product

        message = self.message_factory.from_template('purchase/confirmation')
        message.given(customer=customer, purchase=purchase, product=product)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_donation_promocode_available(self, customer, promocode):

        message = self.message_factory.from_template('donation/promocode_available')
        message.given(customer=customer, promocode=promocode)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_corporate_promocode_available(self, corporate):
        customer = corporate.owner

        message = self.message_factory.from_template('corporate/promocode_available')
        message.given(corporate=corporate)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())


    def notify_corporate_payment(self, purchase, promocodes):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned
        hash_codes = ''
        for p in promocodes:
            hash_codes += p.hash_code + ' '

        message = self.message_factory.from_template('purchase/corporate_confirmation')
        message.given(customer=customer, corporate=corporate, hash_codes=hash_codes)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_corporate_promocode(self, purchase, promocodes):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned
        hash_codes = ''
        for p in promocodes:
            hash_codes += p.hash_code + ' '

        message = self.message_factory.from_template('purchase/corporate_promocode_especial')
        message.given(customer=customer, corporate=corporate, hash_codes=hash_codes)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())



    def notify_corporate_promocode_payment(self, purchase, promocode):
        customer = purchase.customer
        corporate = promocode.creator

        message = self.message_factory.from_template('purchase/corporate_promocode_confirmation')
        message.given(customer=customer, corporate=corporate, purchase=purchase, promocode=promocode)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_gov_purchase_in_analysis(self, purchase):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned

        message = self.message_factory.from_template('purchase/gov_analysis')
        message.given(customer=customer, corporate=corporate, purchase=purchase)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_gov_purchase(self, purchase):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned

        message = self.message_factory.from_template('purchase/gov')
        message.given(customer=customer, corporate=corporate, purchase=purchase)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())


    def notify_gov_purchase_analysed(self, purchase, promocodes):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned
        hash_codes = ''
        for p in promocodes:
            hash_codes += p.hash_code + ' '

        message = self.message_factory.from_template('purchase/gov_confirmation')
        message.given(customer=customer, corporate=corporate, hash_codes=hash_codes)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_gov_purchase_received(self, purchase):
        customer = purchase.customer
        corporate = purchase.customer.corporate_owned

        message = self.message_factory.from_template('purchase/gov_analysis')
        message.given(customer=customer, corporate=corporate, purchase=purchase)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_student_purchase_received(self, purchase):
        customer = purchase.customer
        product = purchase.product

        message = self.message_factory.from_template('purchase/student_analysis')
        message.given(customer=customer, product=product, purchase=purchase)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())


    def notify_student_document_analyzed(self, purchase):
        customer = purchase.customer
        product = purchase.product

        message = self.message_factory.from_template('purchase/student_confirmation')
        message.given(customer=customer, product=product, purchase=purchase)
        message.to(customer.name, customer.email)

        return mailer.send(message.build())

    def notify_donation(self, purchase, claim_check_file_path):
        customer = purchase.customer
        product  = purchase.product

        message = self.message_factory.from_template('donation/confirmation')
        message.given(customer=customer, purchase=purchase, product=product)
        message.to(customer.name, customer.email)
        message.append_attachment('recibo.pdf', claim_check_file_path, 'application/pdf')
        return mailer.send(message.build())

    def notify_promocode(self, customer, promocode, claim_check_file_path):
        from segue.models import SurveyAnswer
        survey = SurveyAnswer.query\
            .filter(SurveyAnswer.survey=='fisl17_donation_shirt')\
            .filter(SurveyAnswer.question=='size')\
            .filter(SurveyAnswer.account_id==customer.id).all()


        message = self.message_factory.from_template('promocode/confirmation')
        message.given(customer=customer, promocode=promocode, survey=survey)
        message.to(customer.name, customer.email)
        message.append_attachment('recibo.pdf', claim_check_file_path, 'application/pdf')
        return mailer.send(message.build())

    def notify_claimcheck(self, purchase, claim_check_file_path):
            customer = purchase.customer

            message = self.message_factory.from_template('claimcheck/notification')
            message.given(customer=customer)
            message.to(customer.name, customer.email)
            message.append_attachment('recibo.pdf', claim_check_file_path, 'application/pdf')

            return mailer.send(message.build())


    def caravan_invite(self, invite):
        message = self.message_factory.from_template('caravan/invite')
        message.given(invite=invite, caravan=invite.caravan, owner=invite.caravan.owner)
        message.to(invite.name, invite.recipient)

        return mailer.send(message.build())


    def caravan_leader(self, caravan, purchase):
        leader = caravan.owner

        message = self.message_factory.from_template('caravan/leader')
        message.given(leader=leader, caravan=caravan, purchase=purchase)
        message.to(leader.name, leader.email)

        return mailer.send(message.build())


    def reset_password(self, account, reset):
        message = self.message_factory.from_template('account/reset_password')
        message.given(account=account,reset=reset)
        message.to(account.name, account.email)

        return mailer.send(message.build())

    def invite_judge(self, token):
        message = self.message_factory.from_template('judge/invite')
        message.given(token=token)
        message.to('', token.email)

        return mailer.send(message.build())

    def call_proposal(self, notification):
        message = self.message_factory.from_template('schedule/call_proposal')
        message.given(
            notification   = notification,
            account        = notification.account,
            proposal       = notification.proposal,
            deadline_hours = notification.deadline.strftime("%H:%M"),
            deadline_day   = notification.deadline.strftime("%d/%m/%Y")
        )
        message.to(notification.account.name, notification.account.email)
        return mailer.send(message.build())

    def notify_slot(self, notification):
        message = self.message_factory.from_template('schedule/notify_slot')
        message.given(
            room               = notification.slot.room,
            account            = notification.account,
            proposal           = notification.slot.talk,
            notification       = notification,
            deadline_day       = notification.deadline.strftime("%d/%m/%Y"),
            deadline_hours     = notification.deadline.strftime("%H:%M"),
            presentation_day   = notification.slot.begins.strftime("%d/%m/%Y"),
            presentation_hours = notification.slot.begins.strftime("%H:%M")
        )
        message.to(notification.account.name, notification.account.email)
        return mailer.send(message.build())

    def non_selection(self, notice):
        message = self.message_factory.from_template('proposal/non_selection')
        message.given(
            notice = notice,
            account = notice.account
        )
        message.to(notice.account.name, notice.account.email)
        return mailer.send(message.build())

    def reception_mail(self, person):
        if not person.email: raise EmailIsNotValid()
        message = self.message_factory.from_template('reception/{}-{}'.format(person.status, person.reception_desk))
        message.given(
            person = person,
        )
        message.to(person.name, person.email)
        return mailer.send(message.build())

    def certificates_available(self, account, certificates):
        if not certificates: return
        message = self.message_factory.from_template('certificates/available')
        message.given(account=account)
        message.to(account.name, account.email)
        return mailer.send(message.build())

