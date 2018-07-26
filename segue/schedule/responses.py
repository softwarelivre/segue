from segue.responses import BaseResponse

class RoomResponse(BaseResponse):
    def __init__(self, room, links=True):
        self.id          = room.id
        self.name        = room.name
        self.capacity    = room.capacity
        self.translation = room.translation
        self.position    = room.position
        if links:
           self.add_link('slots', room.slots, 'slots.of_room', room_id=room.id)

class SlotResponse(BaseResponse):
    def __init__(self, slot, embeds=False, links=True):
        self.id           = slot.id
        self.begins       = slot.begins
        self.hour         = slot.begins.hour
        self.duration     = slot.duration
        self.room         = slot.room.id
        self.room_name    = slot.room.name
        self.status       = slot.status
        self.last_updated = slot.last_updated
        self.recordings = [ r.url for r in slot.recordings ]

        if embeds:
            self.talk = TalkShortResponse.create(slot.talk)

        if links:
            self.add_link('room', slot.room, 'rooms.get_one', room_id=slot.room_id)
            self.add_link('talk', slot.talk, 'talks.get_one', talk_id=slot.talk_id)

class TalkShortResponse(BaseResponse):
    def __init__(self, talk):
        self.id    = talk.id
        self.title = talk.title
        self.owner = talk.owner.name
        self.owner_email = talk.owner.email
        self.track = talk.track.name_pt
        self.last_updated = talk.last_updated
        self.status = talk.status
        self.coauthors = list(set([ x.name for x in talk.coauthors ]))

class NotificationResponse(BaseResponse):
    def __init__(self, notification):
        self.id           = notification.id
        self.kind         = notification.kind
        self.hash         = notification.hash
        self.deadline     = notification.deadline
        self.status       = notification.status
        self.deadline     = notification.deadline
        self.sent         = notification.sent
        self.is_expired   = notification.is_expired

        if self.kind == 'slot':
            self.slot     = SlotResponse.create(notification.slot, links=False)
            self.proposal = notification.slot.talk
        elif self.kind == 'call':
            self.proposal = notification.proposal

class RoomSummaryByDayResponse(BaseResponse):
    def __init__(self, room_id, room_summary):
        self.day = room_summary['day']
        self.last_update = room_summary['last_updated']

        self.add_link('slots', room_summary, 'slots.of_room', room_id=room_id, day=room_summary['day'])

class ScheduleSummaryResponse(BaseResponse):
    def __init__(self, summary):
        self.room_id = summary['room_id']
        self.room_name = summary['room_name']
        self.days = [RoomSummaryByDayResponse.create(summary['room_id'], day) for day in summary['days']]

