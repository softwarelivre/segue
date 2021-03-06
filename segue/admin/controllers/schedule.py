from datetime import date

from flask import request, abort
from flask.ext.jwt import current_user

from segue.core import cache, logger
from segue.decorators import jsoned, jwt_only, admin_only

from segue.schedule.services import RoomService, SlotService
from segue.proposal.services import ProposalService

from ..responses import *

class AdminScheduleController(object):
    def __init__(self, rooms=None, slots=None, proposals=None):
        self.current_user = current_user
        self.rooms = rooms or RoomService()
        self.slots = slots or SlotService()
        self.proposals = proposals or ProposalService()

    @jwt_only
    @admin_only
    @jsoned
    def list_rooms(self):
        result = self.rooms.query()
        return RoomResponse.create(result), 200

    @jwt_only
    @admin_only
    @jsoned
    def query_slots(self):
        criteria = request.args.to_dict()
        result = self.slots.query(**criteria)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def overall_situation(self):
        result = SlotSituationResponse()
        #TODO: FIX HARDCODING
        dates = [date(2016, 7, 13), date(2016, 7, 14), date(2016, 7, 15), date(2016, 7, 16)]
        for day in dates:
            result.add_date_info(day, 'used_blocked',     self.slots.count(day=day, blocked=True,  available=False))
            result.add_date_info(day, 'used_non_blocked', self.slots.count(day=day, blocked=False, available=False))
            result.add_date_info(day, 'free_blocked',     self.slots.count(day=day, blocked=True,  available=True))
            result.add_date_info(day, 'free_non_blocked', self.slots.count(day=day, blocked=False, available=True))

        result.add_proposal_info('slotted', self.proposals.count(status='confirmed', slotted=True))
        result.add_proposal_info('pending', self.proposals.count(status='confirmed', slotted=False))
        return result, 200

    @jwt_only
    @admin_only
    @jsoned
    def get_slot(self, slot_id):
        result = self.slots.get_one(slot_id) or abort(404)
        return SlotResponse.create(result, links=False, stretchability=True), 200

    @jwt_only
    @admin_only
    @jsoned
    def stretch_slot(self, slot_id):
        result = self.slots.stretch_slot(slot_id) or abort(404)
        return SlotResponse.create(result, links=False, stretchability=True), 200


    @jwt_only
    @admin_only
    @jsoned
    def unstretch_slot(self, slot_id):
        result = self.slots.unstretch_slot(slot_id) or abort(404)
        return SlotResponse.create(result, links=False, stretchability=True), 200

    @jwt_only
    @admin_only
    @jsoned
    def block_slot(self, slot_id):
        result = self.slots.set_blocked(slot_id, True) or abort(404)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def unblock_slot(self, slot_id):
        result = self.slots.set_blocked(slot_id, False) or abort(404)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def set_talk(self, slot_id):
        proposal_id = request.get_json().get('proposal_id', None) or abort(400)
        logger.info("user {} set the talk of slot {} to be {}".format(self.current_user.email, slot_id, proposal_id))
        result = self.slots.set_talk(slot_id, proposal_id) or abort(404)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def empty_slot(self, slot_id):
        logger.info("user {} set the talk of slot {} to be empty".format(self.current_user.email, slot_id))
        result = self.slots.empty_slot(slot_id) or abort(404)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def annotate_slot(self, slot_id):
        content = request.get_json().get('content')
        result = self.slots.annotate(slot_id, content) or abort(404)
        return SlotResponse.create(result, links=False), 200

    @jwt_only
    @admin_only
    @jsoned
    def set_status(self, slot_id):
        status = request.get_json().get('status')
        if not status: abort(400)
        result = self.slots.set_status(slot_id, status) or abort(404)
        return SlotResponse.create(result, links=False), 200

