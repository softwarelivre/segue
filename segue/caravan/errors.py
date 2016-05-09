from segue.errors import SegueError, SegueGenericError
from segue.babel import _l

class InvalidCaravan(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'caravan code is not valid' }

class AccountAlreadyHasCaravan(SegueError):
    code = 400
    def to_json(self):
        return { 'message': 'this account already has a caravan' }

class AccountHasAlreadyInvited(SegueGenericError):
    MESSAGE = _l('You can not invited the same person twice')


class AccountIsARider(SegueGenericError):
    MESSAGE = _l('This account is already in a caravan')


class InvitedYourself(SegueGenericError):
    MESSAGE = _l('You can not invite yourself')


class InvitedAlreadyProcessed(SegueGenericError):
    MESSAGE = _l('This invite has already been accepted or declined')

class AccountHasATicket(SegueGenericError):
    MESSAGE = _l('You already have a bought a ticket for the event')

class CorporateCanNotJoinACaravan(SegueGenericError):
    MESSAGE = _l('You can not join a caravan, because you have a corporate account')