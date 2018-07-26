# encoding: utf-8
import sys
from collections import defaultdict
from datetime import datetime

from segue.proposal.services import ProposalService
from segue.judge.services import RankingService
from segue.schedule.services import SlotService
from support import *;

from segue.core import u

def available_slots():
    from segue.schedule.models import Slot
    
    multiuso_id = 8
    return Slot.query.filter(Slot.blocked == False, Slot.talk == None, Slot.room_id != multiuso_id).all()

def slotize(tid=0, commit=False):
    init_command()

    total = ProposalService().query(status='confirmed')
    slotted = filter(lambda x:     x.slotted, total)
    pending = filter(lambda x: not x.slotted, total)

    #ranking = RankingService().classificate(int(tid), status='confirmed', slotted=False)
    ranking = RankingService().classificate(int(tid), slotted=False)

    free_slots = available_slots()
    sorted_slots = sorted(free_slots, key=slot_value, reverse=True)

    print "=========== STARTING SLOTIZE ============="
    print "TOTAL OF TALKS: {}{}{}  ".format(F.GREEN, len(total), F.RESET)
    print "ALREADY SLOTTED: {}{}{} ".format(F.GREEN, len(slotted), F.RESET)
    print "SLOT PENDING: {}{}{}    ".format(F.GREEN, len(pending), F.RESET)
    print "TOTAL FREE SLOTS: {}{}{}".format(F.GREEN, len(free_slots), F.RESET)

    for idx, ranked in enumerate(ranking):
        if idx > len(sorted_slots) - 1:
            continue

        slot = sorted_slots[idx]
        print "{}{}{}: proposal with rank {}{}{} gets slot {}{}{} at room {}{}{} (value={}{}{})".format(
                F.RED, idx, F.RESET,
                F.GREEN, ranked.rank, F.RESET,
                F.GREEN, slot.begins, F.RESET,
                F.GREEN, slot.room.name, F.RESET,
                F.GREEN, slot_value(slot), F.RESET
        )
        if commit:
            message = 'slotize, rank {}, run {}'.format(ranked.rank, datetime.now())
            SlotService().set_talk(slot.id, ranked.proposal.id, annotation=message)

def slot_value(slot):
    value = 0

    if slot.room.capacity >= 200:
        value += 1

    if slot.begins.hour in (10, 12, 14, 16):
        if slot.begins.hour == 10:
          value += 4
        if slot.begins.hour == 12:
          value += 3
        if slot.begins.hour == 14:
          value += 2
        if slot.begins.hour == 16:
          value += 1

    return value
