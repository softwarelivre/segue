from segue.core import db
from segue.hasher import Hasher
from segue.document.services import DocumentService

from factories import SpeakerCertificateFactory, AttendantCertificateFactory, VolunteerCertificateFactory, PressCertificateFactory
from models import Certificate, AttendantCertificate, SpeakerCertificate, Prototype, PressCertificate
from errors import CertificateCannotBeIssued, CertificateAlreadyIssued

class CertificateService(object):

    VALID_CATEGORIES = (
        'normal',
        'student',
        'gov-promocode',
        'corporate-promocode',
        'caravan',
        'caravan-leader',
        'corporate-promocode',
        'proponent',
        'proponent-student'
    )

    VOLUNTEER_CATEGORY = 'volunteer'
    PRESS_CATEGORY = 'press'


    def __init__(self, documents=None):
        self.documents = documents or DocumentService()
        self.factories = dict(
            speaker   = SpeakerCertificateFactory(),
            attendant = AttendantCertificateFactory(),
            volunteer = VolunteerCertificateFactory(),
            press     = PressCertificateFactory(),
        )

    def issuable_certificates_for(self, account, exclude_issued=True):
        candidates = []
        tickets = account.satisfied_purchases
        if not tickets: return []

        speaker_ticket = self.speaker_ticket(tickets)
        if account.presented_talks:
            for talk in account.presented_talks:
                candidates.append(Prototype(kind='speaker', account=account, ticket=speaker_ticket, talk=talk))


        for ticket in tickets:
            if ticket.category == CertificateService.VOLUNTEER_CATEGORY:
                candidates.append(Prototype(kind='volunteer', account=account, ticket=ticket))
            if ticket.category == CertificateService.PRESS_CATEGORY:
                candidates.append(Prototype(kind='press', account=account, ticket=ticket))
            if ticket.category in CertificateService.VALID_CATEGORIES:
                candidates.append(Prototype(kind='attendant', account=account, ticket=ticket))

        issued_certs = self.issued_certificates_for(account)

        if exclude_issued:
            return filter(lambda x: not self._is_like_any(x, issued_certs), candidates)
        else:
            return candidates

    def issue_certificate(self, account, ticket_id, kind, **payload):
        if not account: raise ValueError()

        db.session.flush()

        issued_certs   = self.issued_certificates_for(account)
        issuable_certs = self.issuable_certificates_for(account, exclude_issued=False)

        ticket = self._get_ticket(ticket_id)
        new_cert = self.factories[kind].create(account=account, ticket=ticket, **payload)

        if self._is_like_any(new_cert, issued_certs): raise CertificateAlreadyIssued()
        #if not self._is_like_any(new_cert, issuable_certs): raise CertificateCannotBeIssued()

        self.documents.svg_to_pdf(new_cert.template_file, 'certificate', new_cert.hash_code, new_cert.template_vars)

        db.session.add(new_cert)
        db.session.commit()

        return new_cert

    def speaker_ticket(self, tickets):
        for ticket in tickets:
            if ticket.category == 'speaker':
                return ticket
        return None

    def issued_certificates_for(self, account):
        return Certificate.query.filter(Certificate.account == account).all()

    def _is_like_any(self, candidate, issued_certs):
        return any([ issued.is_like(candidate) for issued in issued_certs ])

    def _get_ticket(self, ticket_id):
        from segue.purchase.models import Purchase
        return Purchase.query.filter(Purchase.id==ticket_id).first() or abort(404)