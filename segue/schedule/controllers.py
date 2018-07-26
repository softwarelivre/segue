import flask

from flask import request

from segue.core import config, cache
from segue.decorators import jsoned, accepts_html

from responses import RoomResponse, SlotResponse, NotificationResponse, ScheduleSummaryResponse
from services import RoomService, SlotService, NotificationService

class RoomController(object):
    def __init__(self, service=None):
        self.service = service or RoomService()

    @jsoned
    def get_one(self, room_id):
        result = self.service.get_one(room_id) or flask.abort(404)
        return RoomResponse.create(result), 200

    @cache.cached(timeout=60)
    @jsoned
    def list_all(self):
        result = self.service.query()
        return RoomResponse.create(result), 200
    
    @cache.cached(timeout=60)
    @jsoned
    def summary(self):
        from sqlalchemy import func, cast, DATE      
        from segue.models import Slot, Proposal, Room
        from itertools import chain

        event_days = ['2018-07-11', '2018-07-12', '2018-07-13', '2018-07-14']
        rooms = Room.query.all()

        summary = []

        for room in rooms:
            summary_by_day = []
            for day in event_days:
                slots = Slot.query.join(Proposal).filter(Slot.room_id==room.id).filter(cast(Slot.begins, DATE)==day).all()
               
                update_dates = []
                update_dates.extend([slot.last_updated for slot in slots if slot.last_updated])
                update_dates.extend([slot.talk.last_updated for slot in slots if slot.talk.last_updated])
                
                last_updated = max(update_dates) if update_dates else None

                summary_by_day.append({'day': day,'last_updated': last_updated})
            
            room_summary = {
                'room_id': room.id,
                'room_name': room.name,
                'days': summary_by_day
            }
            summary.append(room_summary)

        return ScheduleSummaryResponse.create(summary), 200       


class SlotController(object):
    def __init__(self, service=None):
        self.service = service or SlotService()

    @cache.cached(timeout=60)
    @jsoned
    def of_room(self, room_id, day=None):
        if day:
            result = self.service.query(room=room_id, day=day)
        else:
            result = self.service.query(room=room_id)
        return SlotResponse.create(result, embeds=True, links=False), 200

    @jsoned
    def get_one(self, room_id, slot_id):
        result = self.service.get_one(slot_id) or flask.abort(404)
        return SlotResponse.create(result), 200

class NotificationController(object):
    def __init__(self, service=None):
        self.service = service or NotificationService()

    @jsoned
    @accepts_html
    def get_by_hash(self, hash_code, wants_html=False):
        notification = self.service.get_by_hash(hash_code) or flask.abort(404)
        if wants_html:
            path = '/#/notification/{}/{}/answer'.format(hash_code, notification.kind)
            return flask.redirect(config.FRONTEND_URL + path)
        else:
            return NotificationResponse.create(notification), 200

    @jsoned
    def accept(self, hash_code):
        notification = self.service.accept_notification(hash_code)
        return NotificationResponse.create(notification), 200

    @jsoned
    def decline(self, hash_code):
        notification = self.service.decline_notification(hash_code)
        return NotificationResponse.create(notification), 200
