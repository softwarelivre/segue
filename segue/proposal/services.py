from ..core import db
from ..errors import NotAuthorized

import schema
from factories import ProposalFactory, InviteFactory
from models    import Proposal, ProposalInvite

class ProposalService(object):
    def __init__(self, db_impl=None):
        self.db = db_impl or db

    def create(self, data, owner):
        proposal = ProposalFactory.from_json(data, schema.new_proposal)
        proposal.owner = owner
        db.session.add(proposal)
        db.session.commit()
        return proposal

    def get_one(self, proposal_id):
        return Proposal.query.get(proposal_id)

    def query(self, **kw):
        return Proposal.query.filter_by(**kw).all()

    def modify(self, proposal_id, data, by=None):
        proposal = self.get_one(proposal_id)
        if not self.check_ownership(proposal, by): raise NotAuthorized

        for name, value in ProposalFactory.clean_for_update(data).items():
            setattr(proposal, name, value)
        db.session.add(proposal)
        db.session.commit()
        return proposal

    def check_ownership(self, proposal, alleged):
        if isinstance(proposal, int): proposal = self.get_one(proposal)
        return proposal and alleged and proposal.owner_id == alleged.id

class InviteService(object):
    def __init__(self, proposals=None):
        self.proposals = proposals or ProposalService()

    def list(self, proposal_id, by=None):
        proposal = self.proposals.get_one(proposal_id)
        if not self.proposals.check_ownership(proposal, by): raise NotAuthorized
        return proposal.invites

    def get_one(self, invite_id):
        return ProposalInvite.query.get(invite_id)

    def get_by_hash(self, invite_hash):
        candidates = ProposalInvite.query.filter_by(hash=invite_hash).all()
        return candidates[0] if len(candidates) else None

    def create(self, proposal_id, data, by=None):
        proposal = self.proposals.get_one(proposal_id)
        if not self.proposals.check_ownership(proposal, by): raise NotAuthorized

        invite = InviteFactory.from_json(data, schema.new_invite)
        invite.proposal = proposal

        db.session.add(invite)
        db.session.commit()

        # TODO: send email

        return invite

    def answer(self, hash, accepted=True):
        invite = self.get_by_hash(hash)
        if not invite: return None

        invite.status = 'accepted' if accepted else 'declined'
        db.session.add(invite)
        db.session.commit()
        return invite

