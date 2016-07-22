from datetime import datetime

from segue.factory import Factory
from segue.hasher import Hasher

from models import Certificate, AttendantCertificate, SpeakerCertificate, VolunteerCertificate, PressCertificate

class CertificateFactory(Factory):
    model = Certificate

    def __init__(self, hasher=None):
        self.hasher = hasher or Hasher(10)

    def create(self, account, ticket, language, target_model=Certificate):
        entity = target_model()
        entity.account    = account
        entity.ticket     = ticket
        entity.name       = account.certificate_name
        entity.language   = language
        entity.hash_code  = self.hasher.generate()
        entity.issue_date = datetime.now()
        return entity

class AttendantCertificateFactory(CertificateFactory):
    model = AttendantCertificate

    def create(self, account, ticket, language='pt', **payload):
        return super(AttendantCertificateFactory, self).create(account, ticket, language, target_model=AttendantCertificate)

class VolunteerCertificateFactory(CertificateFactory):
    model = VolunteerCertificate

    def create(self, account, ticket, language='pt', **payload):
        return super(VolunteerCertificateFactory, self).create(account, ticket, language, target_model=VolunteerCertificate)

class PressCertificateFactory(CertificateFactory):
    model = PressCertificate

    def create(self, account, ticket, language='pt', **payload):
        return super(PressCertificateFactory, self).create(account, ticket, language, target_model=PressCertificate)

class SpeakerCertificateFactory(CertificateFactory):
    model = SpeakerCertificate

    def create(self, account, ticket, language='pt', talk=None):
        if not talk: raise ArgumentError()
        entity = super(SpeakerCertificateFactory, self).create(account, ticket, language, target_model=SpeakerCertificate)
        entity.talk = talk
        return entity
