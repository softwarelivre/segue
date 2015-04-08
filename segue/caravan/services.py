from segue.core import db
from segue.errors import AccountAlreadyHasCaravan, NotAuthorized

import schema

from models import Caravan, CaravanInvite
from factories import CaravanFactory, CaravanInviteFactory

class CaravanService(object):
    def __init__(self):
        pass

    def get_one(self, caravan_id, by=None):
        result = Caravan.query.get(caravan_id)
        if self._check_ownership(result, by):
            return result
        raise NotAuthorized()

    def _check_ownership(self, entity, alleged):
        return entity and alleged and entity.owner == alleged

    def get_by_owner(self, owner):
        return Caravan.query.filter(Caravan.owner == owner).first()

    def create(self, data, owner):
        if self.get_by_owner(owner): raise AccountAlreadyHasCaravan()

        caravan = CaravanFactory.from_json(data, schema.create)
        caravan.owner = owner
        db.session.add(caravan)
        db.session.commit()
        return caravan

class CaravanInviteService(object):
    def __init__(self, caravans=None, hasher=None, accounts = None, mailer=None):
        self.caravans  = caravans  or CaravanService()
        self.hasher    = hasher    or Hasher()
        self.mailer    = mailer    or MailerService()

    def list(self, caravan_id, by=None):
        return self.caravans.get_one(caravan_id, by).invites

    def create(self, caravan_id, data, by=None):
        caravan = self.caravans.get_one(caravan_id, by)

        invite = CaravanInviteFactory.from_json(data, schema.new_invite)
        invite.caravan = caravan
        invite.hash    = self.hasher.generate()

        db.session.add(invite)
        db.session.commit()

        self.mailer.caravan_invite(invite)

        return invite

    def get_by_hash(self, invite_hash):
        return CaravanInvite.query.filter(CaravanInvite.hash == invite_hash).first()
