import flask

from flask import request, abort
from flask.ext.jwt import current_user
from webargs.flaskparser import parser

from segue.decorators import jsoned, jwt_only, admin_only
from segue.core import logger
from segue.schema import Field

from segue.proposal.services import ProposalService, InviteService

from ..responses import ProposalDetailResponse, ProposalShortResponse, ProposalInviteResponse

class AdminProposalController(object):
    def __init__(self, service=None, invites=None):
        self.service = service or ProposalService()
        self.invites = invites or InviteService()
        self.current_user = current_user

    @jwt_only
    @admin_only
    @jsoned
    def list(self):
        parms = parser.parse({
                'title': Field.str(),
                'type': Field.str(),
                'status': Field.str(),
                'author_name': Field.str(),
                'track_id': Field.int(),
                'slotted': Field.bool()
            },
            request
        )
        result = self.service.lookup(as_user=self.current_user, **parms)
        return ProposalShortResponse.create(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def create(self):
        data = request.get_json()
        owner_id = data.get('owner_id', None) or abort(400)
        result = self.service.create(data, owner_id, enforce_deadline=False)
        return result, 200

    @jwt_only
    @jsoned
    def modify(self, proposal_id):
        data = request.get_json()
        result = self.service.modify(proposal_id, data, by=self.current_user, allow_modify_owner=True, enforce_deadline=False) or flask.abort(404)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def set_coauthors(self, proposal_id=None):
        data = request.get_json()
        if not isinstance(data, list): abort(400)
        result = self.invites.set_coauthors(proposal_id, data)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def set_status(self, proposal_id=None):
        status = request.get_json().get('status')
        if not status: abort(400)
        result = self.service.set_status(proposal_id, status)
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def list_invites(self, proposal_id=None):
        proposal = self.service.get_one(proposal_id) or abort(404)
        return ProposalInviteResponse.create(proposal.invites.all()), 200

    @jwt_only
    @admin_only
    @jsoned
    def get_one(self, proposal_id=None):
        result = self.service.get_one(proposal_id)
        return ProposalDetailResponse.create(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def change_track(self, proposal_id):
        data = request.get_json()
        old_track_id = self.service.get_one(proposal_id).track_id
        new_track_id = data.get('track_id', None) or flask.abort(400)
        result = self.service.change_track(proposal_id, new_track_id)

        logger.info("user %s changed track of proposal %d. track was %d, now is %d",
            self.current_user.email, proposal_id, old_track_id, new_track_id
        )

        return ProposalDetailResponse(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def add_tag(self, proposal_id, tag_name):
        result = self.service.tag_proposal(proposal_id, tag_name)
        logger.info("user %s added tag %s to proposal %d", self.current_user.email, tag_name, proposal_id)
        return ProposalDetailResponse(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def remove_tag(self, proposal_id, tag_name):
        result = self.service.untag_proposal(proposal_id, tag_name)
        logger.info("user %s removed tag %s from proposal %d", self.current_user.email, tag_name, proposal_id)
        return ProposalDetailResponse(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def remove_invite(self, proposal_id, invite_id):
        self.invites.remove(invite_id) or abort(400)
        logger.info("user {} removed invite {} from proposal {}".format(self.current_user.email, invite_id, proposal_id))
        return '', 204