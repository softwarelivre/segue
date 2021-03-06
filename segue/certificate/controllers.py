import flask

from flask import request
from flask.ext.jwt import current_user

from segue.proposal.services import ProposalService
from segue.decorators import jsoned, jwt_only

from services import CertificateService
from responses import CertificateResponse, PrototypeResponse

class CertificateController(object):
    def __init__(self, service=None, proposals=None):
        self.service      = service or CertificateService()
        self.proposals    = proposals or ProposalService()
        self.current_user = current_user

    @jwt_only
    @jsoned
    def list(self, account_id):
        if self.current_user.id != account_id: flask.abort(403)

        issued   = self.service.issued_certificates_for(self.current_user)
        issuable = self.service.issuable_certificates_for(self.current_user)
        response = CertificateResponse.create(issued) + PrototypeResponse.create(issuable)
        return response, 200

    @jwt_only
    @jsoned
    def issue(self, account_id):
        #ticket_id == person.id == purchase.id OMG!!!
        if self.current_user.id != account_id: flask.abort(403)
        descriptor = request.get_json().get('descriptor', None) or flask.abort(400)
        ticket_id  = request.get_json().get('ticket_id', None) or flask.abort(400)

        kind = descriptor.split("-")[0]
        payload = dict(language=self.current_user.guessed_language)
        if kind == 'speaker':
            payload['talk'] = self.proposals.get_one(descriptor.split("-")[1], strict=True)

        result = self.service.issue_certificate(self.current_user, ticket_id, kind, **payload)

        return CertificateResponse.create(result), 200
