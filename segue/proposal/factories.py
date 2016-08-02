import schema
from segue.factory import Factory
from models import Proposal, ProposalInvite, NonSelectionNotice

class ProposalFactory(Factory):
    model = Proposal

    QUERY_WHITELIST = ('owner_id', 'coauthor_id')

    #TODO: REMOVE
    #UPDATE_WHITELIST = schema.edit_proposal["properties"].keys()

    #TODO: REMOVE
    #@classmethod
    #def clean_for_update(self, data):
    #    return { c:v for c,v in data.items() if c in ProposalFactory.UPDATE_WHITELIST }

class InviteFactory(Factory):
    model = ProposalInvite

    @classmethod
    def for_account(cls, proposal, account, status='accepted'):
        invite = ProposalInvite(recipient = account.email)
        invite.name = account.name
        invite.status = status
        invite.proposal = proposal
        invite.account = account
        return invite
